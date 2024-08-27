from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from keybert import KeyBERT
import logging
from datetime import datetime
from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY

router = APIRouter()

# Initialize KeyBERT with the specified model
kw_model = KeyBERT(model=AI_MODEL_NAME)

# Setup logging
logging.basicConfig(level=logging.INFO)


class TextInput(BaseModel):
    content: str


@router.post("/process_text")
async def process_text(body: TextInput = Body(...)):
    try:
        logging.info(f"Received text processing request")
        logging.info(f"Text content: {body.content}")

        # Generate AI tags
        ai_tags = process_with_ai(body.content)

        return JSONResponse(content={
            "ai_tags": ai_tags,
            "processed_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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

# TODO: Add more AI processing functions as needed
# TODO: Implement more advanced NLP tasks
