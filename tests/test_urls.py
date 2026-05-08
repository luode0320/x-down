from app.urls import InvalidTweetUrl, normalize_tweet_url


def test_normalize_tweet_url_accepts_x_domain() -> None:
    output = normalize_tweet_url("https://x.com/someuser/status/1234567890?s=20")
    assert output == "https://twitter.com/someuser/status/1234567890"


def test_normalize_tweet_url_rejects_non_status() -> None:
    try:
        normalize_tweet_url("https://x.com/home")
    except InvalidTweetUrl as exc:
        assert "status" in str(exc).lower()
    else:
        raise AssertionError("expected InvalidTweetUrl")


def test_normalize_tweet_url_rejects_other_domains() -> None:
    try:
        normalize_tweet_url("https://example.com/a/status/123")
    except InvalidTweetUrl as exc:
        assert "x.com" in str(exc).lower() or "twitter.com" in str(exc).lower()
    else:
        raise AssertionError("expected InvalidTweetUrl")
