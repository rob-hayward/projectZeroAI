# /Users/rob/PycharmProjects/projectZeroAI/app/models.py
from pydantic import BaseModel
from typing import Dict, Optional


class InputData(BaseModel):
    id: str
    data: str
    preface: Optional[str] = None  # Optional context for AI processing


class WordDefinitions(BaseModel):
    definitions: Dict[str, str]  # {word1: definition1, word2: definition2, ...}


class TextAnalysis(BaseModel):
    keyword_frequencies: Dict[str, int]  # {word1: frequency1, word2: frequency2, ...}
    is_offensive: bool


class OutputData(BaseModel):
    word_definitions: WordDefinitions  # For word nodes
    text_analysis: TextAnalysis  # For text nodes


class AsyncProcessingResponse(BaseModel):
    task_id: str
    message: str
    status: str


class AsyncProcessingResult(BaseModel):
    status: str
    processed_data: Optional[OutputData] = None  # None if processing incomplete
