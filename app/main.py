from fastapi import FastAPI
from app.routers import intake

app = FastAPI(
    title="LLM Microservice",
    description="A bare-minimum FastAPI setup for LLM services",
    version="0.1.0"
)

app.include_router(intake.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the LLM Microservice",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "llm-microservice"}
