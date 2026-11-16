from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def get_health() -> dict[str, str]:
    """Return health status of the service."""
    return {
        "status": "ok",
        "app": "SprintMate",
        "version": "0.1.0",
    }
