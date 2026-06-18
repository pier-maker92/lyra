import os
from pathlib import Path

import requests

BASE_URL = "https://api.musixmatch.com/ws/1.1"


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    content = env_path.read_text(encoding="utf-8").strip()
    if not content:
        return

    if "=" in content.splitlines()[0]:
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    else:
        os.environ.setdefault("MXM_KEY", content)


def get_api_key() -> str:
    _load_env()
    api_key = os.environ.get("MXM_KEY")
    if not api_key:
        raise ValueError(
            "Musixmatch API key not found. Set MXM_KEY in .env or the environment."
        )
    return api_key


def _mxm_get(endpoint: str, params: dict) -> dict | None:
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params={**params, "apikey": get_api_key()},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    header = data.get("message", {}).get("header", {})
    if header.get("status_code") != 200:
        return None
    return data.get("message", {}).get("body")


def get_stanza_index(chunk_id: str) -> int:
    if "_stanza_" in chunk_id:
        return int(chunk_id.rsplit("_stanza_", 1)[1])
    return 0


def extract_stanza(lyrics_txt: str, stanza_index: int) -> str | None:
    stanzas = [s.strip() for s in lyrics_txt.split("\n\n") if s.strip()]
    if 0 <= stanza_index < len(stanzas):
        return stanzas[stanza_index]
    return None


class MusixmatchClient:
    def __init__(self):
        self._track_cache: dict[str, dict | None] = {}
        self._lyrics_cache: dict[str, str | None] = {}

    def fetch_track_info(self, track_id: str) -> dict | None:
        if track_id not in self._track_cache:
            body = _mxm_get("track.get", {"track_id": track_id})
            if not body:
                self._track_cache[track_id] = None
            else:
                track = body.get("track", {})
                self._track_cache[track_id] = {
                    "artist_name": track.get("artist_name"),
                    "track_name": track.get("track_name"),
                }
        return self._track_cache[track_id]

    def fetch_lyrics(self, track_id: str) -> str | None:
        if track_id not in self._lyrics_cache:
            body = _mxm_get("track.lyrics.get", {"track_id": track_id})
            if not body:
                self._lyrics_cache[track_id] = None
            else:
                self._lyrics_cache[track_id] = body.get("lyrics", {}).get(
                    "lyrics_body"
                )
        return self._lyrics_cache[track_id]

    def fetch_match_details(self, track_id: str, chunk_id: str) -> dict:
        track_info = self.fetch_track_info(track_id) or {}
        lyrics_txt = self.fetch_lyrics(track_id)
        stanza_index = get_stanza_index(chunk_id)
        stanza = extract_stanza(lyrics_txt, stanza_index) if lyrics_txt else None

        return {
            "artist_name": track_info.get("artist_name"),
            "track_name": track_info.get("track_name"),
            "stanza": stanza,
        }
