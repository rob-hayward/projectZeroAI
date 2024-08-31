# projectZeroAI

projectZeroAI is a microservice built with FastAPI that focuses on keyword extraction from text input. 
It utilizes the KeyBERT model to extract the most relevant keywords from a given text, providing a simple and efficient API for text analysis.

## Features

- Extract keywords from text input
- Asynchronous processing support
- RESTful API endpoints
- Redis integration for handling asynchronous tasks
- Configurable keyword extraction parameters

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- KeyBERT
- Redis
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/projectZeroAI.git
   cd projectZeroAI
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file in the root directory. You can use the `.env.example` file as a template.

## Configuration

The project uses environment variables for configuration. You can set these in your `.env` file or in your system environment. Key configurations include:

- `AI_MODEL_NAME`: The name of the KeyBERT model to use (default: 'distilbert-base-nli-mean-tokens')
- `MAX_KEYWORDS`: Maximum number of keywords to extract (default: 10)
- `KEYWORD_DIVERSITY`: Diversity of keywords (default: 0.7)
- `API_HOST`: Host to run the API on (default: '0.0.0.0')
- `API_PORT`: Port to run the API on (default: 5001)
- `LOG_LEVEL`: Logging level (default: 'INFO')
- `REDIS_URL`: URL for Redis connection (default: 'redis://localhost')

## Usage

To start the server, run:

```
python main.py
```

Or with uvicorn directly:

```
uvicorn app:app --host 0.0.0.0 --port 5001 --reload
```

### API Endpoints

1. `POST /process_text`
   - Process text and extract keywords synchronously
   - Request body: `{"id": "unique_id", "data": "text to process"}`
   - Response: `{"id": "unique_id", "keyword_extraction": {"keywords": ["keyword1", "keyword2", ...]}}`

2. `POST /process_text_async`
   - Start asynchronous text processing
   - Request body: `{"id": "unique_id", "data": "text to process"}`
   - Response: `{"task_id": "task_unique_id", "message": "Text processing started", "status": "processing"}`

3. `GET /get_result/{task_id}`
   - Get the result of an asynchronous processing task
   - Response: `{"status": "completed", "processed_data": {"id": "unique_id", "keyword_extraction": {"keywords": ["keyword1", "keyword2", ...]}}}`

### Example Usage

```python
import requests

# Synchronous processing
response = requests.post("http://localhost:5000/process_text", json={
    "id": "doc1",
    "data": "Artificial Intelligence and Machine Learning are transforming various industries."
})
print(response.json())

# Asynchronous processing
response = requests.post("http://localhost:5000/process_text_async", json={
    "id": "doc2",
    "data": "Natural Language Processing is a subfield of AI focusing on human-computer interactions."
})
task_id = response.json()["task_id"]

# Get async result
result = requests.get(f"http://localhost:5000/get_result/{task_id}")
print(result.json())
```

## Testing

To run the tests, execute:

```
pytest tests/test_main.py
```

## Contributing

Contributions to projectZeroAI are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-branch-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-branch-name`
5. Submit a pull request

## License

[MIT License](LICENSE)

## Contact

For any queries or support, please contact Rob Hayward at hayward.m.rob@gmail.com.