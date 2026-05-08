from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.resolver import ResolveError, resolve_video
from app.schemas import ResolveRequest, ResolveResponse, MediaVariant

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="x-down direct resolver", version="2.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/v1/resolve", response_model=ResolveResponse)
def resolve_endpoint(payload: ResolveRequest) -> ResolveResponse:
    try:
        resolved = resolve_video(payload.url, prefer=payload.prefer)
    except ResolveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ResolveResponse(
        id=resolved.id,
        tweet_url=resolved.tweet_url,
        title=resolved.title,
        duration=resolved.duration,
        resolved_at=resolved.resolved_at,
        expires_at=resolved.expires_at,
        variants=[
            MediaVariant(
                quality=v.quality,
                mime=v.mime,
                url=v.url,
                size_bytes=v.size_bytes,
            )
            for v in resolved.variants
        ],
    )
