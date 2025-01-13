# app/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import queries
from ..core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    queries.router,
    prefix=settings.API_V1_STR,
    tags=["impact-analysis"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to Impact Analysis API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }