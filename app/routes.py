# /Users/rob/PycharmProjects/projectZeroAI/app/routes.py
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from keybert import KeyBERT
import logging
from datetime import datetime, timezone
from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY
import asyncio
from redis import asyncio as aioredis
import json

router = APIRouter()

# Initialize KeyBERT with the specified model
kw_model = KeyBERT(model=AI_MODEL_NAME)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Redis client
redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url("redis://localhost")
    return redis

class TextInput(BaseModel):
    content: str

def simple_offensive_check(text: str) -> bool:
    offensive_words = ['badword1', 'badword2', 'badword3']  # Add your own list of offensive words
    return any(word in text.lower() for word in offensive_words)

@router.post("/process_text")
async def process_text(body: TextInput = Body(...)):
    try:
        logging.info(f"Received text processing request")
        logging.info(f"Text content: {body.content}")

        if not body.content.strip():
            raise HTTPException(status_code=422, detail="Content cannot be empty")

        if simple_offensive_check(body.content):
            raise HTTPException(status_code=400, detail="Content flagged as potentially offensive")

        # Generate AI tags
        ai_tags = process_with_ai(body.content)

        return JSONResponse(content={
            "ai_tags": ai_tags,
            "processed_at": datetime.now(timezone.utc).isoformat()
        })

    except HTTPException as he:
        logging.error(f"HTTP exception occurred: {str(he)}")
        raise he
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process_text_async")
async def process_text_async(background_tasks: BackgroundTasks, body: TextInput = Body(...)):
    try:
        if simple_offensive_check(body.content):
            raise HTTPException(status_code=400, detail="Content flagged as potentially offensive")

        task_id = f"task_{datetime.now(timezone.utc).isoformat()}"
        background_tasks.add_task(process_with_ai_async, body.content, task_id)
        return JSONResponse(content={
            "task_id": task_id,
            "message": "Text processing started",
            "status": "processing"
        })
    except HTTPException as he:
        logging.error(f"HTTP exception occurred: {str(he)}")
        raise he
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_result/{task_id}")
async def get_result(task_id: str):
    redis = await get_redis()
    result = await redis.get(task_id)
    if result is None:
        return JSONResponse(content={"status": "processing"})
    return JSONResponse(content=json.loads(result))

def process_with_ai(text: str) -> dict:
    logging.info("Processing text with KeyBERT for keyword extraction.")
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),
            stop_words='english',
            top_n=MAX_KEYWORDS,
            diversity=KEYWORD_DIVERSITY
        )
        return {keyword: score for keyword, score in keywords}
    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")

async def process_with_ai_async(text: str, task_id: str):
    try:
        # Simulate long-running process
        await asyncio.sleep(10)
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),
            stop_words='english',
            top_n=MAX_KEYWORDS,
            diversity=KEYWORD_DIVERSITY
        )
        result = {
            "ai_tags": {keyword: score for keyword, score in keywords},
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        redis = await get_redis()
        await redis.set(task_id, json.dumps(result))
    except Exception as e:
        logging.error(f"Error during async keyword extraction: {str(e)}")
        redis = await get_redis()
        await redis.set(task_id, json.dumps({"status": "error", "message": str(e)}))

# TODO: Add more AI processing functions as needed
# TODO: Implement more advanced NLP tasks
