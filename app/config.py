# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AI model configuration
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'distilbert-base-nli-mean-tokens')
MAX_KEYWORDS = int(os.getenv('MAX_KEYWORDS', 10))
KEYWORD_DIVERSITY = float(os.getenv('KEYWORD_DIVERSITY', 0.7))

# API configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost')
REDIS_TIMEOUT = float(os.getenv('REDIS_TIMEOUT', 5.0))

