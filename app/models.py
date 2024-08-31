from pydantic import BaseModel
from typing import Dict, Optional, List


class InputData(BaseModel):
    id: str
    data: str


class KeywordInfo(BaseModel):
    definition: str
    documents: List[str]


class WordDefinitions(BaseModel):
    definitions: Dict[str, KeywordInfo]


class TextAnalysis(BaseModel):
    keyword_frequencies: Dict[str, int]
    is_offensive: bool


class OutputData(BaseModel):
    word_definitions: WordDefinitions
    text_analysis: TextAnalysis


class AsyncProcessingResponse(BaseModel):
    task_id: str
    message: str
    status: str


class AsyncProcessingResult(BaseModel):
    status: str
    processed_data: Optional[OutputData] = None
