from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routes import router, get_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create Redis connection
    await get_redis()
    yield
    # Shutdown: close Redis connection
    await close_redis()

app = FastAPI(lifespan=lifespan)

app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to projectZeroAI!"}