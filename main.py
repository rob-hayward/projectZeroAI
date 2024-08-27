from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY, API_HOST, API_PORT, LOG_LEVEL
import uvicorn
from app import app
import logging
import argparse

# Setup logging
logging.basicConfig(level=LOG_LEVEL)

if __name__ == "__main__":
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Run the projectZeroAI server")
    parser.add_argument("--port", type=int, default=API_PORT, help="Port to run the server on")
    args = parser.parse_args()

    # Use the port from command-line args if provided, otherwise use the one from config
    port = args.port

    logging.info(f"Starting projectZeroAI with {AI_MODEL_NAME}")
    logging.info(f"Max keywords: {MAX_KEYWORDS}, Keyword diversity: {KEYWORD_DIVERSITY}")
    logging.info(f"Server will run on {API_HOST}:{port}")
    uvicorn.run("app:app", host=API_HOST, port=port, reload=True)