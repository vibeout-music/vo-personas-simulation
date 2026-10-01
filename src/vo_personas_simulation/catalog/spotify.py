"""Minimal Spotify Web API client (standard library only).

Uses the Client Credentials flow, which gives access to public catalogue data
(search, tracks, artists) without any user login. The client is deliberately
gentle with the API: a steady request rate, Retry-After on 429, backoff on
server errors, and a hard budget of requests per run.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"
MAX_RETRIES = 5


class SpotifyError(RuntimeError):
    pass


class BudgetExhausted(SpotifyError):
    pass


def load_credentials(env_file: Path | None = None) -> tuple[str, str]:
    """Read SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET from the environment or a .env file."""
    values = {}
    if env_file and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    client_id = os.environ.get("SPOTIFY_CLIENT_ID") or values.get("SPOTIFY_CLIENT_ID")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET") or values.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not secret:
        raise SpotifyError(
            "Missing Spotify credentials. Create a .env file in the repository root with:\n"
            "  SPOTIFY_CLIENT_ID=...\n  SPOTIFY_CLIENT_SECRET=...\n"
            "(both are in your app's settings at developer.spotify.com/dashboard)")
    return client_id, secret


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str, *, budget: int, requests_per_second: float = 2.0):
        self._auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self._token: str | None = None
        self._token_expires = 0.0
        self._interval = 1.0 / requests_per_second
        self._last_request = 0.0
        self.budget = budget
        self.requests_made = 0

    # --- public API -------------------------------------------------------------

    def search_tracks(self, query: str, *, market: str | None, limit: int, offset: int) -> dict:
        params = {"q": query, "type": "track", "limit": limit, "offset": offset}
        if market:
            params["market"] = market
        return self._get("/search", params)

    def artist(self, artist_id: str) -> dict:
        return self._get(f"/artists/{artist_id}", {})

    # --- internals ------------------------------------------------------------------

    def _ensure_token(self) -> str:
        if self._token and time.time() < self._token_expires - 60:
            return self._token
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
            "Authorization": f"Basic {self._auth}", "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            raise SpotifyError(f"Could not get a Spotify token ({exc.code}): check your client id and secret") from exc
        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 3600)
        return self._token

    def _throttle(self) -> None:
        wait = self._last_request + self._interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _get(self, path: str, params: dict) -> dict:
        url = f"{API_URL}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
        for attempt in range(MAX_RETRIES):
            if self.requests_made >= self.budget:
                raise BudgetExhausted(f"request budget of {self.budget} used")
            self._throttle()
            self.requests_made += 1
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._ensure_token()}"})
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as exc:
                if exc.code == 429:  # rate limited: wait as long as Spotify asks
                    time.sleep(min(int(exc.headers.get("Retry-After", "5")) + 1, 120))
                elif exc.code == 401:  # token expired early
                    self._token = None
                elif exc.code >= 500:
                    time.sleep(2 ** attempt)
                else:
                    detail = exc.read().decode(errors="replace")[:300]
                    raise SpotifyError(f"GET {path} failed with {exc.code}: {detail}") from exc
            except urllib.error.URLError as exc:
                if attempt == MAX_RETRIES - 1:
                    raise SpotifyError(f"network error: {exc.reason}") from exc
                time.sleep(2 ** attempt)
        raise SpotifyError(f"GET {path} kept failing after {MAX_RETRIES} attempts")
