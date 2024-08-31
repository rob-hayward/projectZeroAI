from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from app.models import InputData, OutputData, KeywordExtraction, AsyncProcessingResponse, AsyncProcessingResult
from keybert import KeyBERT
import logging
from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY
from redis import asyncio as aioredis
import json
from typing import List

router = APIRouter()

# Initialize KeyBERT with the specified model
kw_model = KeyBERT(model=AI_MODEL_NAME)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Redis client
redis_client = None


async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url("redis://localhost")
    return redis_client


async def close_redis():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


def extract_keywords(text: str) -> List[str]:
    logging.info("Extracting keywords.")
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),
            stop_words='english',
            top_n=MAX_KEYWORDS,
            diversity=KEYWORD_DIVERSITY
        )

        return [keyword for keyword, _ in keywords]

    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")


@router.post("/process_text", response_model=OutputData)
async def process_text(input_data: InputData = Body(...)):
    try:
        logging.info(f"Received text processing request for id: {input_data.id}")

        if not input_data.data.strip():
            raise HTTPException(status_code=422, detail="Content cannot be empty")

        keywords = extract_keywords(input_data.data)

        return OutputData(
            id=input_data.id,
            keyword_extraction=KeywordExtraction(keywords=keywords)
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process_text_async", response_model=AsyncProcessingResponse)
async def process_text_async(background_tasks: BackgroundTasks, input_data: InputData = Body(...)):
    try:
        task_id = f"task_{input_data.id}"
        background_tasks.add_task(process_text_async_task, input_data, task_id)
        return AsyncProcessingResponse(
            task_id=task_id,
            message="Text processing started",
            status="processing"
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_result/{task_id}", response_model=AsyncProcessingResult)
async def get_result(task_id: str):
    redis_conn = await get_redis()
    result = await redis_conn.get(task_id)
    if result is None:
        return AsyncProcessingResult(status="processing")
    return AsyncProcessingResult(status="completed", processed_data=json.loads(result))


async def process_text_async_task(input_data: InputData, task_id: str):
    try:
        keywords = extract_keywords(input_data.data)

        result = OutputData(
            id=input_data.id,
            keyword_extraction=KeywordExtraction(keywords=keywords)
        )

        redis_conn = await get_redis()
        await redis_conn.set(task_id, json.dumps(result.model_dump()))
    except Exception as e:
        logging.error(f"Error during async keyword extraction: {str(e)}")
        redis_conn = await get_redis()
        await redis_conn.set(task_id, json.dumps({"status": "error", "message": str(e)}))