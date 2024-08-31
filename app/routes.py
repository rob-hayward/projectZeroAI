from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models import InputData, OutputData, WordDefinitions, TextAnalysis, AsyncProcessingResponse, \
    AsyncProcessingResult, KeywordInfo
from keybert import KeyBERT
import logging
from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY
import asyncio
from redis import asyncio as aioredis
import json
from collections import Counter, defaultdict
from typing import Dict, Tuple, List
import aiohttp

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


def simple_offensive_check(text: str) -> bool:
    offensive_words = ['badword1', 'badword2', 'badword3']  # Add your own list of offensive words
    return any(word in text.lower() for word in offensive_words)


@router.post("/process_text", response_model=OutputData)
async def process_text(input_data: InputData = Body(...)):
    try:
        logging.info(f"Received text processing request for id: {input_data.id}")

        if not input_data.data.strip():
            raise HTTPException(status_code=422, detail="Content cannot be empty")

        word_definitions, keyword_frequencies = await process_with_ai(input_data.data, input_data.id)
        is_offensive = simple_offensive_check(input_data.data)

        return OutputData(
            word_definitions=WordDefinitions(definitions=word_definitions),
            text_analysis=TextAnalysis(
                keyword_frequencies=keyword_frequencies,
                is_offensive=is_offensive
            )
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
        background_tasks.add_task(process_with_ai_async, input_data, task_id)
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


def extract_keywords(text: str) -> Dict[str, int]:
    logging.info("Extracting keywords and frequencies.")
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),  # Only single words
            stop_words='english',
            top_n=MAX_KEYWORDS,
            diversity=KEYWORD_DIVERSITY
        )

        keyword_frequencies = dict(Counter(keyword for keyword, _ in keywords))
        return keyword_frequencies

    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")


async def generate_definitions(keywords: List[str]) -> Dict[str, str]:
    logging.info("Generating definitions for keywords.")
    definitions = {}
    async with aiohttp.ClientSession() as session:
        for keyword in keywords:
            try:
                async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{keyword}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            meaning = data[0].get('meanings', [])
                            if meaning and len(meaning) > 0:
                                definition = meaning[0].get('definitions', [{}])[0].get('definition', '')
                                definitions[keyword] = definition.capitalize()
                            else:
                                definitions[keyword] = "Definition not found."
                    else:
                        definitions[keyword] = "Definition not found."
            except Exception as e:
                logging.error(f"Error fetching definition for {keyword}: {str(e)}")
                definitions[keyword] = "Error fetching definition."
    return definitions


async def process_with_ai(text: str, document_id: str) -> Tuple[Dict[str, KeywordInfo], Dict[str, int]]:
    keyword_frequencies = extract_keywords(text)
    definitions = await generate_definitions(list(keyword_frequencies.keys()))

    word_definitions = {
        keyword: KeywordInfo(definition=definition, documents=[document_id])
        for keyword, definition in definitions.items()
    }

    return word_definitions, keyword_frequencies


async def process_with_ai_async(input_data: InputData, task_id: str):
    try:
        word_definitions, keyword_frequencies = await process_with_ai(input_data.data, input_data.id)
        is_offensive = simple_offensive_check(input_data.data)

        result = OutputData(
            word_definitions=WordDefinitions(definitions=word_definitions),
            text_analysis=TextAnalysis(
                keyword_frequencies=keyword_frequencies,
                is_offensive=is_offensive
            )
        )

        redis_conn = await get_redis()
        await redis_conn.set(task_id, json.dumps(result.dict()))
    except Exception as e:
        logging.error(f"Error during async keyword extraction: {str(e)}")
        redis_conn = await get_redis()
        await redis_conn.set(task_id, json.dumps({"status": "error", "message": str(e)}))