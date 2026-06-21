"""Visual-to-Lyrics retrieval CLI.

Embeds a video/image query (mood-agnostic, purely visual) using TinyCLIP,
then queries a local ChromaDB catalog of song lyrics for the top candidates.
The mood is precomputed and stored in each stanza's metadata, so the response
exposes a "best" ordering (pure visual distance) plus a dynamic bucket per
mood that was actually retrieved.
"""

import argparse

import av
import chromadb
import numpy as np
from PIL import Image

from embedding import get_device, load_model
from moods import MOODS
from mxm import MusixmatchClient, get_stanza_index, extract_stanza

# ── constants ─────────────────────────────────────────────────────────────────
MODEL_NAME = "wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M"
DB_PATH = "./TinyCLAPdb"
COLLECTION_NAME = "song_lyrics_min"
CANDIDATE_K = 100
MAX_FRAMES = 8


# ── frame extraction ──────────────────────────────────────────────────────────


def extract_video_frames(
    video_path: str, fps: int = 4, target_height: int = 720
) -> list[Image.Image]:
    """Extract frames from a video at the given fps, resized to target_height."""
    container = av.open(video_path)
    stream = container.streams.video[0]

    # Compute the step: skip frames to approximate the desired fps
    source_fps = float(stream.average_rate or stream.guessed_rate or 30)
    step = max(1, int(round(source_fps / fps)))

    frames: list[Image.Image] = []
    for i, frame in enumerate(container.decode(video=0)):
        if i % step != 0:
            continue
        img = frame.to_image()
        w, h = img.size
        if h > target_height:
            new_w = int((target_height / h) * w)
            img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)
        frames.append(img)
    container.close()
    return frames


def load_image(image_path: str, target_height: int = 720) -> Image.Image:
    """Load and optionally resize a single image."""
    img = Image.open(image_path)
    w, h = img.size
    if h > target_height:
        new_w = int((target_height / h) * w)
        img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)
    return img


# ── embedding ─────────────────────────────────────────────────────────────────


def embed_frames(model, images: list[Image.Image]) -> list[float]:
    """Embed every frame individually and average into one query vector.

    Follows the same logic as the replit embed_visual_frames: embed each frame,
    then element-wise mean.  Uses SentenceTransformer.encode with image inputs.
    """
    frame_embeddings = []
    for img in images:
        vec = model.encode(img)
        frame_embeddings.append(vec)

    if len(frame_embeddings) == 1:
        return frame_embeddings[0].tolist()

    avg = np.mean(frame_embeddings, axis=0)
    return avg.tolist()


# ── id parsing ────────────────────────────────────────────────────────────────


def parse_embedding_id(embedding_id: str) -> tuple[str, int]:
    """Split a catalog embedding id ``{track_id}_stanza_{j}`` or ``{track_id}_stanza_{j}_{chunk}`` into its parts."""
    marker = "_stanza_"
    idx = embedding_id.rfind(marker)
    if idx == -1:
        return embedding_id, 0
    track_id = embedding_id[:idx]

    remainder = embedding_id[idx + len(marker) :]
    if "_" in remainder:
        stanza_part = remainder.split("_")[0]
    else:
        stanza_part = remainder

    try:
        stanza_index = int(stanza_part)
    except ValueError:
        stanza_index = 0
    return track_id, stanza_index


# ── main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve song lyrics based on a video or image query."
    )
    parser.add_argument("query_path", type=str, help="Path to the video or image file")
    parser.add_argument(
        "--fps",
        type=int,
        default=4,
        help="Frames per second to extract from video (default: 4)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=CANDIDATE_K,
        help=f"Number of candidates to pull from ChromaDB (default: {CANDIDATE_K})",
    )
    parser.add_argument(
        "--explicit",
        action="store_true",
        default=False,
        help="Include explicit results (default: clean only)",
    )
    args = parser.parse_args()

    # ── load model ────────────────────────────────────────────────────────
    device = get_device()
    print(f"Loading {MODEL_NAME} on {device}...")
    model = load_model(device, model_name=MODEL_NAME)

    # ── extract frames / load image ───────────────────────────────────────
    is_video = args.query_path.lower().endswith(
        (".mp4", ".avi", ".mov", ".mkv", ".webm")
    )

    if is_video:
        print(f"Extracting frames from video: {args.query_path} (fps={args.fps})")
        images = extract_video_frames(args.query_path, fps=args.fps)
        if not images:
            raise ValueError(f"No frames extracted from {args.query_path}")
    else:
        print(f"Loading image: {args.query_path}")
        images = [load_image(args.query_path)]

    # Cap to MAX_FRAMES, sampling evenly (including first and last)
    if len(images) > MAX_FRAMES:
        last = len(images) - 1
        images = [images[round(i * last / (MAX_FRAMES - 1))] for i in range(MAX_FRAMES)]

    print(f"Embedding {len(images)} frame(s)...")

    # ── embed query ───────────────────────────────────────────────────────
    query_embedding = embed_frames(model, images)

    # ── query ChromaDB ────────────────────────────────────────────────────
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    print("Searching for matches...")
    filters = [
        {"language": "en"},
        {"length_bin": {"$in": ["25-50", "50-75", "75-100", "100-125", "125-150"]}},
        {"explicit": 0},
    ]

    where = filters[0] if len(filters) == 1 else {"$and": filters}

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=args.top_k,
        where=where,
        include=["distances", "metadatas"],
    )

    ids = (result.get("ids") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]

    if not ids:
        print("No results found.")
        return

    # ── organise picks into best + per-mood buckets ───────────────────────
    best_picks: list[tuple[str, int, float, str]] = []
    per_mood_picks: dict[str, list[tuple[str, int, float, str]]] = {}
    needed_tracks: set[str] = set()

    for embedding_id, dist, meta in zip(ids, distances, metadatas):
        track_id, stanza_index = parse_embedding_id(str(embedding_id))
        needed_tracks.add(track_id)

        mood = str(meta.get("mood") or "Unknown") if meta else "Unknown"

        pick = (track_id, stanza_index, float(dist), mood)
        best_picks.append(pick)
        per_mood_picks.setdefault(mood, []).append(pick)

    # ── resolve lyrics via Musixmatch ─────────────────────────────────────
    try:
        mxm = MusixmatchClient()
    except ValueError as e:
        print(f"Warning: {e}")
        mxm = None

    def resolve(picks: list[tuple[str, int, float, str]]) -> list[dict]:
        matches = []
        for track_id, stanza_index, distance, mood in picks:
            if mxm is None:
                matches.append(
                    {
                        "track_id": track_id,
                        "stanza_index": stanza_index,
                        "distance": distance,
                        "mood": mood,
                        "artist": "Unknown",
                        "track": "Unknown",
                        "lyrics": "(unavailable)",
                    }
                )
                continue

            details = mxm.fetch_match_details(
                track_id, f"{track_id}_stanza_{stanza_index}"
            )
            artist = details.get("artist_name") or "Unknown"
            track = details.get("track_name") or "Unknown"
            stanza_text = details.get("stanza")
            lyrics = (
                stanza_text.replace("\n", " / ") if stanza_text else "(unavailable)"
            )

            matches.append(
                {
                    "track_id": track_id,
                    "stanza_index": stanza_index,
                    "distance": distance,
                    "mood": mood,
                    "artist": artist,
                    "track": track,
                    "lyrics": lyrics,
                }
            )
        return matches

    best_matches = resolve(best_picks)

    # ── deduplicate by lyrics text AND track_id ───────────────────────────
    seen_lyrics: set[str] = set()
    seen_tracks: set[str] = set()
    unique_matches: list[dict] = []
    for m in best_matches:
        if m["lyrics"] not in seen_lyrics and m["track_id"] not in seen_tracks:
            seen_lyrics.add(m["lyrics"])
            seen_tracks.add(m["track_id"])
            unique_matches.append(m)

    # ── print best lyrics only ────────────────────────────────────────────
    print()
    print("\n\n".join(m["lyrics"] for m in unique_matches))


if __name__ == "__main__":
    main()
