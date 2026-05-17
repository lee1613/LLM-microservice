from fastapi import FastAPI
from app.intake import router as intake
from app.verification import router as verification
from app.eligibility import router as eligibility
from app.medical import router as medical
from app.adjudication import router as adjudication

app = FastAPI(
    title="LLM Microservice",
    description="A bare-minimum FastAPI setup for LLM services",
    version="0.1.0"
)

app.include_router(intake.router)
app.include_router(verification.router)
app.include_router(eligibility.router)
app.include_router(medical.router)
app.include_router(adjudication.router)

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
