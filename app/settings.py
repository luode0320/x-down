from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_COOKIES_FILE = BASE_DIR / "config" / "cookies.txt"


@dataclass(frozen=True)
class Settings:
    resolve_ttl_seconds: int = int(os.getenv("RESOLVE_TTL_SECONDS", "300"))
    ytdlp_socket_timeout: int = int(os.getenv("YTDLP_SOCKET_TIMEOUT", "15"))
    ytdlp_retries: int = int(os.getenv("YTDLP_RETRIES", "2"))
    ytdlp_cookies_file: str = os.getenv("YTDLP_COOKIES_FILE", str(DEFAULT_COOKIES_FILE))

    @property
    def cookies_file_path(self) -> str | None:
        path = Path(self.ytdlp_cookies_file)
        if path.exists() and path.is_file():
            return str(path)
        return None


settings = Settings()
