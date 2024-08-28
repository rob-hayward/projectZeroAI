# /Users/rob/PycharmProjects/projectZeroAI/tests/test_main.py
from fastapi.testclient import TestClient
from app import app
import pytest
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime, timezone

client = TestClient(app)

@pytest.fixture
def mock_redis():
    with patch('app.routes.get_redis', new_callable=AsyncMock) as mock:
        yield mock.return_value

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to projectZeroAI!"}

def test_process_text():
    response = client.post("/process_text", json={"content": "This is a test sentence for AI and ML."})
    assert response.status_code == 200
    result = response.json()
    assert "ai_tags" in result
    assert "processed_at" in result

def test_process_text_empty():
    response = client.post("/process_text", json={"content": ""})
    assert response.status_code == 422  # Validation error

def test_process_text_short():
    response = client.post("/process_text", json={"content": "Short."})
    assert response.status_code == 200
    result = response.json()
    assert "ai_tags" in result

def test_process_text_spanish():
    response = client.post("/process_text", json={"content": "La inteligencia artificial y el aprendizaje automático están transformando la tecnología."})
    assert response.status_code == 200
    result = response.json()
    assert "ai_tags" in result

def test_process_text_special_chars():
    response = client.post("/process_text", json={"content": "AI & ML are key to Industry 4.0! Integration of IoT, big data, and smart algorithms."})
    assert response.status_code == 200
    result = response.json()
    assert "ai_tags" in result

@pytest.mark.asyncio
async def test_process_text_async(mock_redis):
    response = client.post("/process_text_async", json={"content": "This is a test sentence for async processing."})
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["status"] == "processing"

@pytest.mark.asyncio
async def test_get_result(mock_redis):
    mock_redis.get.return_value = json.dumps({
        "ai_tags": {"test": 0.5},
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    })
    response = client.get("/get_result/test_task_id")
    assert response.status_code == 200
    result = response.json()
    assert "ai_tags" in result
    assert "processed_at" in result
    assert result["status"] == "completed"

@pytest.mark.asyncio
async def test_get_result_processing(mock_redis):
    mock_redis.get.return_value = None
    response = client.get("/get_result/test_task_id")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
