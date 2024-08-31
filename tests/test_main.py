from fastapi.testclient import TestClient
from app import app
import pytest
from unittest.mock import AsyncMock, patch
import json

client = TestClient(app)


@pytest.fixture
def mock_redis():
    with patch('app.routes.get_redis', new_callable=AsyncMock) as mock:
        yield mock.return_value


def test_process_text():
    response = client.post("/process_text", json={
        "id": "test1",
        "data": "This is a test sentence for AI and ML.",
    })
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "keyword_extraction" in result
    assert "keywords" in result["keyword_extraction"]
    assert isinstance(result["keyword_extraction"]["keywords"], list)


def test_process_text_empty():
    response = client.post("/process_text", json={"id": "test2", "data": ""})
    assert response.status_code == 422  # Validation error


def test_process_text_short():
    response = client.post("/process_text", json={
        "id": "test3",
        "data": "Short.",
    })
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "keyword_extraction" in result
    assert "keywords" in result["keyword_extraction"]


def test_process_text_spanish():
    response = client.post("/process_text", json={
        "id": "test4",
        "data": "La inteligencia artificial y el aprendizaje automático están transformando la tecnología.",
    })
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "keyword_extraction" in result
    assert "keywords" in result["keyword_extraction"]


def test_process_text_special_chars():
    response = client.post("/process_text", json={
        "id": "test5",
        "data": "AI & ML are key to Industry 4.0! Integration of IoT, big data, and smart algorithms.",
    })
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert "keyword_extraction" in result
    assert "keywords" in result["keyword_extraction"]


@pytest.mark.asyncio
async def test_process_text_async(mock_redis):
    response = client.post("/process_text_async", json={
        "id": "async_test1",
        "data": "This is a test sentence for async processing.",
    })
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["status"] == "processing"


@pytest.mark.asyncio
async def test_get_result(mock_redis):
    mock_result = {
        "id": "test_id",
        "keyword_extraction": {
            "keywords": ["test", "keyword"]
        }
    }
    mock_redis.get.return_value = json.dumps(mock_result)
    response = client.get("/get_result/test_task_id")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert "processed_data" in result
    assert "id" in result["processed_data"]
    assert "keyword_extraction" in result["processed_data"]
    assert "keywords" in result["processed_data"]["keyword_extraction"]


@pytest.mark.asyncio
async def test_get_result_processing(mock_redis):
    mock_redis.get.return_value = None
    response = client.get("/get_result/test_task_id")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
