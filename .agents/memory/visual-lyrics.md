---
name: Visual Lyrics architecture
description: How the Visual Lyrics app is wired across three services, and the production deploy caveat.
---

# Visual Lyrics

Expo mobile app (TikTok/Reels style). User picks a photo/video -> client resizes to a
JPEG data URL (height 720) -> POST /api/analyze -> response is keyed by 5 moods
(love/adventure/funny/chill/party), each an array of lyric matches -> full-screen
reels player (swipe horizontal = change mood, vertical = change match).

## Three services
- `artifacts/mobile` — Expo client (the only artifact for this product).
- `artifacts/api-server` — Express; `/api/analyze` is a thin proxy.
- `services/lyrics-engine` — standalone Python FastAPI (uvicorn, port 8000) doing the
  embeddings (OpenRouter `nvidia/llama-nemotron-embed-vl-1b-v2:free`, 2048-dim, text+image)
  + ChromaDB retrieval. Express proxies to `localhost:8000`.

## Production deploy caveat (important)
**Why:** `services/lyrics-engine` is run by a standalone Replit workflow, NOT registered
as an artifact / not in any `artifact.toml`. Only artifacts deploy. So in a published
backend, `/api/analyze` will fail because nothing serves port 8000.
**How to apply:** Before deploying the backend to production, either (a) make the Python
service an artifact.toml service, or (b) have Express spawn/host it. The Expo client
itself (Expo Launch / App Store) is independent, but it points at the production API
domain, so the backend must be fixed first or analysis breaks in prod.

## Embedding/retrieval note
Mood conditioning works at the prompt level. The catalog is the user's REAL ChromaDB
(collection `song_lyrics_min`, ~80k stanzas, cosine, 2048-dim) installed at
`services/lyrics-engine/lyrics_catalog_db/` (~700MB, not gitignored).

## Real catalog + Musixmatch (important)
Real Chroma ids are `{track_id}_stanza_{j}` (numeric Musixmatch track_id + stanza
index); metadata only has `genre`/`language` — NO lyric/artist/title. So `analyze`
dedupes query hits by `track_id`, then resolves artist/title/lyrics from Musixmatch
(`track.get` + `track.lyrics.get`, keyed by `track_id`) and picks stanza `j` by
splitting lyrics on blank lines (`\n\n`). `musixmatch.py` caches per `track_id`
(process-wide) — one `analyze` can need ~25 tracks, so the cache matters for plan limits.
Musixmatch failures propagate as explicit 502s (no silent fallback). Needs
`MUSIXMATCH_API_KEY` secret.
**Danger:** `seed.py` wipes+rebuilds `song_lyrics_min` — gated behind `ALLOW_SEED_RESET=1`
+ a catalog arg so it can never nuke the real DB. The placeholder `catalog.json` is gone.
