from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assistant import router as assistant_router
from app.api.audit import router as audit_router
from app.api.health import router as health_router
from app.api.proposals import router as proposals_router
from app.api.pull_requests import router as pull_requests_router
from app.api.sprints import router as sprints_router
from app.api.team import router as team_router
from app.api.usage import router as usage_router
from app.config import settings

app = FastAPI(
    title="SprintMate API",
    description="Sprint risk engine and AI investigation assistant for DevCore",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(sprints_router, prefix="/api")
app.include_router(pull_requests_router, prefix="/api")
app.include_router(team_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(usage_router, prefix="/api")
app.include_router(proposals_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "SprintMate API is running", "docs_url": "/docs"}
