from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

import app.resolver as resolver
from urllib.error import HTTPError


class FakeYDL:
    def __init__(self, options: dict, payload: dict) -> None:
        self.options = options
        self.payload = payload

    def __enter__(self) -> "FakeYDL":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def extract_info(self, url: str, download: bool = False) -> dict:
        assert download is False
        assert "twitter.com" in url
        return self.payload


@pytest.fixture(autouse=True)
def provide_test_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    monkeypatch.setattr(
        resolver,
        "settings",
        SimpleNamespace(
            ytdlp_socket_timeout=15,
            ytdlp_retries=2,
            ytdlp_cookies_file=str(cookie_file),
            cookies_file_path=str(cookie_file),
            resolve_ttl_seconds=300,
        ),
    )


def test_resolve_video_success_filters_and_sorts(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "title": "demo",
        "duration": 12,
        "formats": [
            {
                "url": "https://cdn.example/480.mp4",
                "ext": "mp4",
                "mime_type": "video/mp4",
                "height": 480,
                "filesize": 200,
                "vcodec": "avc1",
                "tbr": 600,
            },
            {
                "url": "https://cdn.example/720.mp4",
                "ext": "mp4",
                "mime_type": "video/mp4",
                "height": 720,
                "filesize": 300,
                "vcodec": "avc1",
                "tbr": 1200,
            },
            {
                "url": "https://cdn.example/audio.m4a",
                "ext": "m4a",
                "mime_type": "audio/mp4",
                "vcodec": "none",
            },
            {
                "url": "https://cdn.example/720.webm",
                "ext": "webm",
                "mime_type": "video/webm",
                "height": 720,
                "vcodec": "vp9",
            },
        ],
    }

    monkeypatch.setattr(
        resolver.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(options=options, payload=payload),
    )

    result = resolver.resolve_video("https://x.com/user/status/100", prefer="mp4")

    assert result.title == "demo"
    assert result.duration == 12
    assert result.tweet_url == "https://twitter.com/user/status/100"
    assert len(result.variants) == 2
    assert result.variants[0].quality == "720p"
    assert result.variants[1].quality == "480p"


def test_resolve_video_raises_when_no_direct_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "title": "no mp4",
        "formats": [
            {
                "url": "https://cdn.example/audio.m4a",
                "ext": "m4a",
                "mime_type": "audio/mp4",
                "vcodec": "none",
            }
        ],
    }

    monkeypatch.setattr(
        resolver.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(options=options, payload=payload),
    )

    with pytest.raises(resolver.ResolveError, match="No direct video variants"):
        resolver.resolve_video("https://x.com/user/status/100", prefer="mp4")


def test_resolve_video_maps_private_tweet_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ydl(_options: dict):
        class _BrokenYDL:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def extract_info(self, _url: str, download: bool = False):
                raise RuntimeError("\x1b[0;31mERROR:\x1b[0m No video could be found in this tweet")

        return _BrokenYDL()

    def fake_urlopen(_url: str, timeout: int = 8):
        payload = json.dumps({"error": "Sorry, you are not authorized to see this status."}).encode("utf-8")
        raise HTTPError(_url, 403, "forbidden", hdrs=None, fp=io.BytesIO(payload))

    monkeypatch.setattr(resolver.yt_dlp, "YoutubeDL", fake_ydl)
    monkeypatch.setattr(resolver, "urlopen", fake_urlopen)

    with pytest.raises(resolver.ResolveError, match="not publicly accessible"):
        resolver.resolve_video("https://x.com/user/status/100", prefer="mp4")


def test_resolve_video_requires_cookie_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        resolver,
        "settings",
        SimpleNamespace(
            ytdlp_socket_timeout=15,
            ytdlp_retries=2,
            ytdlp_cookies_file="config/cookies.txt",
            cookies_file_path=None,
            resolve_ttl_seconds=300,
        ),
    )

    with pytest.raises(resolver.ResolveError, match="Cookies file not found"):
        resolver.resolve_video("https://x.com/user/status/100", prefer="mp4")


def test_resolve_video_normalizes_float_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "title": "float duration",
        "duration": 31.393,
        "formats": [
            {
                "url": "https://cdn.example/720.mp4",
                "ext": "mp4",
                "mime_type": "video/mp4",
                "height": 720,
                "vcodec": "avc1",
            }
        ],
    }

    monkeypatch.setattr(
        resolver.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(options=options, payload=payload),
    )

    result = resolver.resolve_video("https://x.com/user/status/100", prefer="mp4")
    assert result.duration == 31
