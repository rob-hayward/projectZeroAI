from app.config import AI_MODEL_NAME, MAX_KEYWORDS, KEYWORD_DIVERSITY, API_HOST, API_PORT, LOG_LEVEL
import uvicorn
import logging
import argparse
import signal
import sys

# Setup logging
logging.basicConfig(level=LOG_LEVEL)


def signal_handler(sig, frame):
    logging.info("Shutting down gracefully...")
    sys.exit(0)


def run_server(port=API_PORT):
    logging.info(f"Starting projectZeroAI with {AI_MODEL_NAME}")
    logging.info(f"Max keywords: {MAX_KEYWORDS}, Keyword diversity: {KEYWORD_DIVERSITY}")
    logging.info(f"Server will run on {API_HOST}:{port}")

    config = uvicorn.Config("app:app", host=API_HOST, port=port, reload=True)
    server = uvicorn.Server(config)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server.run()
    except KeyboardInterrupt:
        logging.info("Received interrupt signal. Shutting down...")
    finally:
        logging.info("Cleaning up resources...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the projectZeroAI server")
    parser.add_argument("--port", type=int, default=API_PORT, help="Port to run the server on")
    args = parser.parse_args()

    run_server(args.port)