"""Musixmatch client.

Given a Musixmatch ``track_id`` (encoded in each Chroma embedding id), fetches the
artist name and track title (``track.get``) and the full lyrics (``track.lyrics.get``).

A single ``/analyze`` request can surface up to ~25 matches, so lookups are
deduplicated through a module-level in-memory cache keyed by ``track_id`` and the two
endpoint calls for one track run in parallel. Any error or malformed response is
propagated explicitly — there is no silent fallback.
"""

import asyncio
import os
from dataclasses import dataclass

import httpx

MUSIXMATCH_BASE = "https://api.musixmatch.com/ws/1.1"

# Process-wide cache so repeated track_ids (within and across requests) hit the API once.
_cache: dict[str, "TrackData"] = {}
_locks: dict[str, asyncio.Lock] = {}


@dataclass(frozen=True)
class TrackData:
    artist: str
    track: str
    lyrics: str


class MusixmatchError(RuntimeError):
    """Raised when Musixmatch fails or returns an unusable response."""


def _api_key() -> str:
    key = os.environ.get("MUSIXMATCH_API_KEY")
    if not key:
        raise MusixmatchError("MUSIXMATCH_API_KEY is not set")
    return key


async def _call(client: httpx.AsyncClient, endpoint: str, params: dict) -> dict:
    query = {**params, "apikey": _api_key(), "format": "json"}
    resp = await client.get(f"{MUSIXMATCH_BASE}/{endpoint}", params=query)
    resp.raise_for_status()
    payload = resp.json()
    message = payload.get("message") or {}
    status = (message.get("header") or {}).get("status_code")
    if status != 200:
        raise MusixmatchError(f"Musixmatch {endpoint} returned status {status}")
    body = message.get("body")
    if not body:
        raise MusixmatchError(f"Musixmatch {endpoint} returned an empty body")
    return body


def _clean_lyrics_body(body: str) -> str:
    """Drop the Musixmatch free-tier disclaimer block if present.

    Paid (full-lyrics) plans do not include it, but stripping it keeps stanza
    indexing aligned with how the catalog was embedded.
    """
    lines: list[str] = []
    for line in body.split("\n"):
        if "NOT for Commercial use" in line:
            break
        lines.append(line)
    return "\n".join(lines).strip()


async def fetch_track(client: httpx.AsyncClient, track_id: str) -> TrackData:
    """Fetch and cache artist, title and full lyrics for a Musixmatch track_id."""
    cached = _cache.get(track_id)
    if cached is not None:
        return cached

    lock = _locks.setdefault(track_id, asyncio.Lock())
    async with lock:
        cached = _cache.get(track_id)
        if cached is not None:
            return cached

        track_body, lyrics_body = await asyncio.gather(
            _call(client, "track.get", {"track_id": track_id}),
            _call(client, "track.lyrics.get", {"track_id": track_id}),
        )

        track = track_body.get("track") or {}
        artist = (track.get("artist_name") or "").strip()
        title = (track.get("track_name") or "").strip()
        raw_lyrics = ((lyrics_body.get("lyrics") or {}).get("lyrics_body") or "").strip()
        lyrics = _clean_lyrics_body(raw_lyrics)

        if not artist or not title or not lyrics:
            raise MusixmatchError(
                f"Musixmatch returned incomplete data for track {track_id} "
                f"(artist={bool(artist)}, title={bool(title)}, lyrics={bool(lyrics)})"
            )

        data = TrackData(artist=artist, track=title, lyrics=lyrics)
        _cache[track_id] = data
        return data
