from __future__ import annotations

from urllib.parse import urlparse
import re

ALLOWED_HOSTS = {
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
    "m.twitter.com",
}

_STATUS_PATH_RE = re.compile(r"^/.+/status/(?P<id>\d+)")


class InvalidTweetUrl(ValueError):
    pass


def normalize_tweet_url(raw_url: str) -> str:
    raw_url = (raw_url or "").strip()
    if not raw_url:
        raise InvalidTweetUrl("URL is required")

    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise InvalidTweetUrl("Only http/https URLs are allowed")

    host = (parsed.netloc or "").lower()
    if host not in ALLOWED_HOSTS:
        raise InvalidTweetUrl("Only x.com or twitter.com status links are supported")

    match = _STATUS_PATH_RE.match(parsed.path or "")
    if not match:
        raise InvalidTweetUrl("Only status URLs are supported")

    status_id = match.group("id")
    path_parts = [p for p in (parsed.path or "").split("/") if p]
    username = path_parts[0]

    return f"https://twitter.com/{username}/status/{status_id}"
