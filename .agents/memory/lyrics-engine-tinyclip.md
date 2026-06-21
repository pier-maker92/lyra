---
name: lyrics-engine local TinyCLIP embeddings
description: How the lyrics-engine embeds queries locally with TinyCLIP, plus the torch/transformers install gotchas in this repo.
---

# Local TinyCLIP in lyrics-engine

The query encoder is local TinyCLIP `wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M` loaded
via `sentence-transformers`, embedding images into the 512-dim CLIP space of the
catalog (`TinyCLAPdb`). The catalog was built with ST `model.encode(image)`, so the
query path MUST match that exact encoder — swap one without the other and retrieval
silently degrades.

## transformers 5.x get_image_features is NOT the projected embedding
**Why:** with transformers ~5.12, `CLIPModel.get_image_features(...)` returned
token-level hidden states `(1, 197, 256)`, NOT the pooled+projected `(1, 512)` image
embedding. Using it as the query vector would mismatch the catalog.
**How to apply:** get the 512-dim vector from ANY of these (all identical, cosine 1.0,
and NOT L2-normalized): `SentenceTransformer.encode(img)`, `model(...).image_embeds`,
or manual `visual_projection(vision_model(px).pooler_output)`. Prefer ST `.encode`.

## Python runtime + installing torch here
**Why:** the engine runs on the `.pythonlibs` (pip/UPM) interpreter, NOT the uv venv.
`installLanguagePackages` (uv add) FAILS for ML packages: the repo's pre-existing giant
`[tool.uv.sources]` map in `pyproject.toml` pins them to the explicit `pytorch-cpu`
index (which lacks most of them), and `requires-python = ">=3.11"` makes uv also try to
solve for 3.14 (no wheels). Do NOT try to "fix" that uv.sources block — it is template
config and removing it is out of scope / risky.
**How to apply:** install ML deps with pip into `.pythonlibs`:
`python3 -m pip install --index-url https://download.pytorch.org/whl/cpu torch`, then
`python3 -m pip install sentence-transformers transformers pillow` from PyPI. Keep
`requirements.txt` in sync (with `--extra-index-url` for the torch CPU wheels).

## Startup + cost
The model is warmed in the FastAPI `lifespan` (no first-request init stall) and embedding
runs via `asyncio.to_thread(embed_frames, ...)` so it never blocks the event loop. The
model weights download from HF Hub on first load; that cache must persist for production
or every cold start re-downloads.
