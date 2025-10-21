"""FastAPI health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Health check endpoint.

    Returns 200 OK if the service is running.
    This endpoint is used by Docker healthcheck and monitoring systems.
    """
    return {"status": "ok"}
