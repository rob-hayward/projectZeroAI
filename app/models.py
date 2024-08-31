from pydantic import BaseModel
from typing import List, Optional


class InputData(BaseModel):
    id: str
    data: str


class KeywordExtraction(BaseModel):
    keywords: List[str]


class OutputData(BaseModel):
    id: str
    keyword_extraction: KeywordExtraction


class AsyncProcessingResponse(BaseModel):
    task_id: str
    message: str
    status: str


class AsyncProcessingResult(BaseModel):
    status: str
    processed_data: Optional[OutputData] = None