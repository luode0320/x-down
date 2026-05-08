from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from uuid import uuid4

import yt_dlp

from app.settings import settings
from app.urls import InvalidTweetUrl, normalize_tweet_url


class ResolveError(RuntimeError):
    pass


_ANSI_ESCAPE_RE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text or "").strip()


def _classify_tweet_visibility(tweet_url: str) -> str | None:
    oembed_url = f"https://publish.twitter.com/oembed?url={quote(tweet_url, safe='')}"
    try:
        with urlopen(oembed_url, timeout=8) as response:  # noqa: S310
            if response.status == 200:
                return None
    except HTTPError as exc:
        if exc.code in {401, 403, 404}:
            try:
                payload = json.loads(exc.read().decode("utf-8", errors="ignore"))
                text = str(payload.get("error") or "").lower()
            except Exception:  # noqa: BLE001
                text = ""
            if "not authorized" in text:
                return "This tweet is not publicly accessible (private/deleted/restricted)."
            if exc.code == 404:
                return "This tweet is unavailable or may have been deleted."
            return "This tweet is not publicly accessible."
    except (TimeoutError, URLError):
        return None

    return None


class _SilentLogger:
    def debug(self, _msg: str) -> None:
        return

    def warning(self, _msg: str) -> None:
        return

    def error(self, _msg: str) -> None:
        return


@dataclass(frozen=True)
class Variant:
    quality: str
    mime: str
    url: str
    size_bytes: int | None


@dataclass(frozen=True)
class ResolvedVideo:
    id: str
    tweet_url: str
    title: str
    duration: int | None
    resolved_at: str
    expires_at: str
    variants: list[Variant]


def _normalize_duration(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _sort_key(item: dict) -> tuple[int, float]:
    return (int(item.get("height") or 0), float(item.get("tbr") or 0.0))


def _build_variants(info_dict: dict, prefer: str = "mp4") -> list[Variant]:
    formats = info_dict.get("formats") or []
    formats = sorted(formats, key=_sort_key, reverse=True)

    result: list[Variant] = []
    seen_urls: set[str] = set()
    prefer = (prefer or "mp4").lower().strip()

    for fmt in formats:
        url = fmt.get("url")
        if not url or url in seen_urls:
            continue

        if fmt.get("vcodec") == "none":
            continue

        ext = (fmt.get("ext") or "").lower()
        mime_type = (fmt.get("mime_type") or "").lower()

        if prefer == "mp4":
            if "mp4" not in mime_type and ext not in {"mp4", "m4v"}:
                continue

        height = fmt.get("height")
        quality = f"{height}p" if height else str(fmt.get("format_note") or fmt.get("format_id") or "auto")
        size_bytes = fmt.get("filesize") or fmt.get("filesize_approx")
        mime = fmt.get("mime_type") or f"video/{ext or 'mp4'}"

        result.append(
            Variant(
                quality=quality,
                mime=mime,
                url=url,
                size_bytes=int(size_bytes) if size_bytes else None,
            )
        )
        seen_urls.add(url)

    return result


def resolve_video(raw_url: str, prefer: str = "mp4") -> ResolvedVideo:
    try:
        tweet_url = normalize_tweet_url(raw_url)
    except InvalidTweetUrl as exc:
        raise ResolveError(str(exc)) from exc

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "logger": _SilentLogger(),
        "socket_timeout": settings.ytdlp_socket_timeout,
        "retries": settings.ytdlp_retries,
    }

    cookie_file = settings.cookies_file_path
    if not cookie_file:
        raise ResolveError(
            f"Cookies file not found: {settings.ytdlp_cookies_file}. "
            "Please export valid X login cookies before using this service."
        )
    ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(tweet_url, download=False)
    except Exception as exc:  # noqa: BLE001
        message = _strip_ansi(str(exc))
        lowered = message.lower()
        if "no video could be found in this tweet" in lowered:
            visibility_hint = _classify_tweet_visibility(tweet_url)
            if visibility_hint:
                raise ResolveError(visibility_hint) from exc
            raise ResolveError(
                "No downloadable video found in this tweet. It may be text/image-only or media may be inaccessible."
            ) from exc
        if "could not authenticate you" in lowered:
            raise ResolveError("Failed to authenticate with X. Check and refresh your cookies file.") from exc
        raise ResolveError(f"Failed to resolve media: {message}") from exc

    if not info_dict:
        raise ResolveError("Failed to resolve media: empty response")

    variants = _build_variants(info_dict, prefer=prefer)
    if not variants:
        raise ResolveError("No direct video variants found for this tweet")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.resolve_ttl_seconds)

    return ResolvedVideo(
        id=f"res_{uuid4().hex[:12]}",
        tweet_url=tweet_url,
        title=str(info_dict.get("title") or "Untitled"),
        duration=_normalize_duration(info_dict.get("duration")),
        resolved_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        variants=variants,
    )
