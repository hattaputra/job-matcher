from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs

app = FastAPI(
    title="Job Matcher API",
    description="AI-powered job description analyzer for Senior Data Engineers",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
