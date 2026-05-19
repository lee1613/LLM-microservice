from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.intake import router as intake
from app.verification import router as verification
from app.eligibility import router as eligibility
from app.medical import router as medical
from app.adjudication import router as adjudication
from app.disbursement import router as disbursement
from app.dev import router as dev

app = FastAPI(
    title="Health Insurance Claims Pipeline",
    description="Six-node automated health insurance claims processing pipeline",
    version="2.0.0"
)

# Enable CORS for local development and client integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router)
app.include_router(verification.router)
app.include_router(eligibility.router)
app.include_router(medical.router)
app.include_router(adjudication.router)
app.include_router(disbursement.router)
app.include_router(dev)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Fix Swagger UI List[UploadFile] text-input bug by forcing binary format for files array items
    try:
        schemas = openapi_schema.get("components", {}).get("schemas", {})
        body_schema = schemas.get("Body_intake_claim_intake_process_post", {})
        if body_schema:
            files_prop = body_schema.get("properties", {}).get("files", {})
            if files_prop:
                files_prop["items"] = {
                    "type": "string",
                    "format": "binary"
                }
    except Exception as e:
        import logging
        logging.error(f"Failed to patch OpenAPI schema for file upload: {e}")

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
