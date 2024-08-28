# /Users/rob/PycharmProjects/projectZeroAI/conftest.py
from fastapi import FastAPI
from .routes import router

app = FastAPI()

# Include the routes from routes.py
app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to projectZeroAI!"}
