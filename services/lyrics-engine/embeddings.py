"""Local TinyCLIP visual embeddings.

Loads ``wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M`` once and embeds query frames
into the same 512-dim CLIP space as the catalog (``TinyCLAPdb``). Each frame is
embedded individually and averaged into a single query vector — the same logic
used to build the catalog (SentenceTransformer ``model.encode(image)``).
"""

import base64
import binascii
import threading
from io import BytesIO

import numpy as np
from PIL import Image, UnidentifiedImageError
from sentence_transformers import SentenceTransformer

MODEL_NAME = "wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M"

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    """Lazily load (and cache) the TinyCLIP model singleton (thread-safe)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(MODEL_NAME)
    return _model


def _decode_data_url(data_url: str) -> Image.Image:
    """Decode a ``data:image/...;base64,...`` URL into an RGB PIL image."""
    try:
        _, b64 = data_url.split(",", 1)
    except ValueError as exc:
        raise ValueError("malformed data URL") from exc
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid base64 image payload") from exc
    try:
        return Image.open(BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("could not decode image bytes") from exc


def embed_frames(image_data_urls: list[str]) -> list[float]:
    """Embed every frame with TinyCLIP, then average into one query vector."""
    if not image_data_urls:
        raise ValueError("no frames to embed")
    model = get_model()
    vectors = [
        np.asarray(model.encode(_decode_data_url(url)), dtype=np.float32)
        for url in image_data_urls
    ]
    if len(vectors) == 1:
        return vectors[0].tolist()
    return np.mean(vectors, axis=0).tolist()
