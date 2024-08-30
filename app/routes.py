from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models import InputData, OutputData, WordDefinitions, TextAnalysis, AsyncProcessingResponse, AsyncProcessingResult
from keybert import KeyBERT
from transformers import pipeline
import torch
import logging
from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY
import asyncio
from redis import asyncio as aioredis
import json
from collections import Counter
from typing import Dict, Tuple, List

router = APIRouter()

# Initialize KeyBERT with the specified model
kw_model = KeyBERT(model=AI_MODEL_NAME)

# Initialize T5 model for definition generation
definition_model = pipeline("text2text-generation", model="t5-base", device=0 if torch.cuda.is_available() else -1)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Redis client
redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url("redis://localhost")
    return redis

def simple_offensive_check(text: str) -> bool:
    offensive_words = ['badword1', 'badword2', 'badword3']  # Add your own list of offensive words
    return any(word in text.lower() for word in offensive_words)

@router.post("/process_text", response_model=OutputData)
async def process_text(input_data: InputData = Body(...)):
    try:
        logging.info(f"Received text processing request for id: {input_data.id}")

        if not input_data.data.strip():
            raise HTTPException(status_code=422, detail="Content cannot be empty")

        word_definitions, keyword_frequencies = process_with_ai(input_data.data)
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
    redis = await get_redis()
    result = await redis.get(task_id)
    if result is None:
        return AsyncProcessingResult(status="processing")
    return AsyncProcessingResult(status="completed", processed_data=json.loads(result))

def extract_keywords(text: str) -> Dict[str, int]:
    logging.info("Extracting keywords and frequencies.")
    try:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),
            stop_words='english',
            top_n=MAX_KEYWORDS,
            diversity=KEYWORD_DIVERSITY
        )

        keyword_frequencies = dict(Counter(keyword for keyword, _ in keywords))
        return keyword_frequencies

    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")

def generate_definitions(keywords: List[str], text: str) -> Dict[str, str]:
    logging.info("Generating definitions for keywords.")
    try:
        definitions = {}
        for keyword in keywords:
            prompt = f"Define '{keyword}' in the context of the following text: {text[:500]}..."
            response = definition_model(prompt, max_length=100, num_return_sequences=1)
            definition = response[0]['generated_text'].strip()
            definition = definition.replace(f"'{keyword}'", keyword).capitalize()
            if not definition.endswith('.'):
                definition += '.'
            definitions[keyword] = definition
        return definitions
    except Exception as e:
        logging.error(f"Error during definition generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during definition generation: {str(e)}")

def process_with_ai(text: str) -> Tuple[Dict[str, str], Dict[str, int]]:
    keyword_frequencies = extract_keywords(text)
    word_definitions = generate_definitions(list(keyword_frequencies.keys()), text)
    return word_definitions, keyword_frequencies

async def process_with_ai_async(input_data: InputData, task_id: str):
    try:
        word_definitions, keyword_frequencies = process_with_ai(input_data.data)
        is_offensive = simple_offensive_check(input_data.data)

        result = OutputData(
            word_definitions=WordDefinitions(definitions=word_definitions),
            text_analysis=TextAnalysis(
                keyword_frequencies=keyword_frequencies,
                is_offensive=is_offensive
            )
        )

        redis = await get_redis()
        await redis.set(task_id, json.dumps(result.dict()))
    except Exception as e:
        logging.error(f"Error during async keyword extraction: {str(e)}")
        redis = await get_redis()
        await redis.set(task_id, json.dumps({"status": "error", "message": str(e)}))