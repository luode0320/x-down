from __future__ import annotations

from pydantic import BaseModel, Field


class ResolveRequest(BaseModel):
    url: str = Field(min_length=1, description="x.com or twitter.com status URL")
    prefer: str = Field(default="mp4", description="preferred output format")


class MediaVariant(BaseModel):
    quality: str
    mime: str
    url: str
    download_url: str | None = None
    size_bytes: int | None = None


class ResolveResponse(BaseModel):
    id: str
    tweet_url: str
    title: str
    duration: int | None = None
    resolved_at: str
    expires_at: str
    variants: list[MediaVariant]


class ErrorResponse(BaseModel):
    error: str
