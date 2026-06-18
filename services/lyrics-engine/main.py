"""Visual-to-Lyrics retrieval engine.

FastAPI service that embeds an uploaded image (conditioned on each mood prompt)
with OpenRouter, queries a local ChromaDB catalog of song lyrics, and returns the
top unique matches per mood.
"""

import asyncio
import os

import chromadb
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from embeddings import embed_visual_frames
from moods import MOODS, get_query_prompt
from musixmatch import MusixmatchError, fetch_track

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lyrics_catalog_db")
COLLECTION_NAME = "song_lyrics_min"
TOP_K = 15
RESULTS_PER_MOOD = 5
MAX_FRAMES = 8
EMBED_CONCURRENCY = 6

app = FastAPI(title="Lyrics Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = chromadb.PersistentClient(path=DB_PATH)


def _collection():
    try:
        return _client.get_collection(COLLECTION_NAME)
    except Exception as exc:  # collection missing
        raise HTTPException(
            status_code=503,
            detail=(
                f"Lyrics catalog collection '{COLLECTION_NAME}' not found at "
                f"{DB_PATH}. Install the real ChromaDB."
            ),
        ) from exc


class AnalyzeRequest(BaseModel):
    frames: list[str]


class LyricMatch(BaseModel):
    lyric: str
    artist: str
    track: str
    distance: float


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def _parse_embedding_id(embedding_id: str) -> tuple[str, int]:
    """Split a catalog embedding id ``{track_id}_stanza_{j}`` into its parts.

    The user's real ChromaDB encodes the Musixmatch track_id plus the stanza index
    in the id; the metadata only carries ``genre``/``language``. track_id itself is
    numeric, so we split on the last ``_stanza_`` separator.
    """
    marker = "_stanza_"
    idx = embedding_id.rfind(marker)
    if idx == -1:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected embedding id format: {embedding_id!r}",
        )
    track_id = embedding_id[:idx]
    stanza_part = embedding_id[idx + len(marker) :]
    try:
        stanza_index = int(stanza_part)
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected stanza index in id: {embedding_id!r}",
        ) from exc
    return track_id, stanza_index


def _dedupe_ids(query_result) -> list[tuple[str, int, float]]:
    """Pick up to RESULTS_PER_MOOD unique tracks from a Chroma query result.

    Returns ``(track_id, stanza_index, distance)`` tuples in ranked order.
    """
    ids = (query_result.get("ids") or [[]])[0]
    distances = (query_result.get("distances") or [[]])[0]
    seen: set[str] = set()
    picks: list[tuple[str, int, float]] = []
    for embedding_id, dist in zip(ids, distances):
        track_id, stanza_index = _parse_embedding_id(str(embedding_id))
        if track_id in seen:
            continue
        seen.add(track_id)
        picks.append((track_id, stanza_index, float(dist)))
        if len(picks) >= RESULTS_PER_MOOD:
            break
    return picks


def _stanza_at(lyrics: str, index: int) -> str:
    """Return the stanza at ``index`` (stanzas are separated by blank lines)."""
    stanzas = [s.strip() for s in lyrics.split("\n\n") if s.strip()]
    if not stanzas:
        raise HTTPException(
            status_code=502, detail="Musixmatch returned lyrics with no stanzas"
        )
    if index < 0 or index >= len(stanzas):
        # The stanza index came from the user's embedding pipeline; if Musixmatch
        # lyrics have fewer stanzas, clamp to the last one rather than dropping the
        # match. (The Musixmatch call itself still fails loudly elsewhere.)
        index = len(stanzas) - 1
    return stanzas[index]


@app.post("/analyze")
async def analyze(req: AnalyzeRequest) -> dict[str, list[LyricMatch]]:
    frames = [f for f in req.frames if isinstance(f, str) and f.startswith("data:")]
    if not frames:
        raise HTTPException(
            status_code=400, detail="frames must contain at least one data URL"
        )
    if len(frames) > MAX_FRAMES:
        # Sample evenly across the clip (including first and last frame) so we
        # keep ~1fps coverage without exploding the number of embedding calls.
        last = len(frames) - 1
        frames = [
            frames[round(i * last / (MAX_FRAMES - 1))] for i in range(MAX_FRAMES)
        ]

    collection = _collection()
    semaphore = asyncio.Semaphore(EMBED_CONCURRENCY)

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            vectors = await asyncio.gather(
                *[
                    embed_visual_frames(
                        client, get_query_prompt(mood), frames, semaphore
                    )
                    for mood in MOODS
                ]
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Embedding provider error: {exc.response.status_code}",
            ) from exc

        # Rank + dedupe each mood, then resolve every unique track once via Musixmatch.
        per_mood_picks: dict[str, list[tuple[str, int, float]]] = {}
        for mood, vector in zip(MOODS, vectors):
            result = collection.query(
                query_embeddings=[vector],
                n_results=TOP_K,
                include=["distances"],
            )
            per_mood_picks[mood] = _dedupe_ids(result)

        needed = list(
            {track_id for picks in per_mood_picks.values() for track_id, _, _ in picks}
        )
        try:
            fetched = await asyncio.gather(
                *[fetch_track(client, track_id) for track_id in needed]
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Musixmatch request failed: {exc.response.status_code}",
            ) from exc
        except MusixmatchError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    tracks = dict(zip(needed, fetched))

    response: dict[str, list[LyricMatch]] = {}
    for mood, picks in per_mood_picks.items():
        matches: list[LyricMatch] = []
        for track_id, stanza_index, distance in picks:
            data = tracks[track_id]
            matches.append(
                LyricMatch(
                    lyric=_stanza_at(data.lyrics, stanza_index),
                    artist=data.artist,
                    track=data.track,
                    distance=distance,
                )
            )
        response[mood] = matches
    return response
