from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY, API_HOST, API_PORT, LOG_LEVEL
import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)

