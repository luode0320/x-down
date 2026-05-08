from __future__ import annotations

from app.resolver import ResolvedVideo, Variant


def test_healthz(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_resolve_rejects_invalid_url(client) -> None:
    response = client.post("/api/v1/resolve", json={"url": "https://example.com/a/status/1"})
    assert response.status_code == 400
    assert "x.com" in response.json()["detail"].lower()


def test_resolve_success(client, monkeypatch) -> None:
    def fake_resolve_video(url: str, prefer: str = "mp4") -> ResolvedVideo:
        return ResolvedVideo(
            id="res_demo123",
            tweet_url="https://twitter.com/a/status/1",
            title="Video Title",
            duration=33,
            resolved_at="2026-05-08T00:00:00+00:00",
            expires_at="2026-05-08T00:05:00+00:00",
            variants=[
                Variant(
                    quality="720p",
                    mime="video/mp4",
                    url="https://video.twimg.com/demo.mp4",
                    size_bytes=123,
                )
            ],
        )

    monkeypatch.setattr("app.main.resolve_video", fake_resolve_video)

    response = client.post(
        "/api/v1/resolve",
        json={"url": "https://x.com/a/status/1", "prefer": "mp4"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "res_demo123"
    assert body["variants"][0]["quality"] == "720p"
    assert body["variants"][0]["download_url"] == "https://video.twimg.com/demo.mp4"
