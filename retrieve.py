import argparse
import chromadb
import torch
from sentence_transformers import SentenceTransformer
import av
from PIL import Image
import numpy as np

from moods import MOODS, get_query_prompt
from mxm import MusixmatchClient


def load_video_frames(video_path, fps=None, max_frames=8, target_height=720):
    container = av.open(video_path)
    frames = []

    if fps is not None:
        interval = 1.0 / fps
        next_target_time = 0.0
        container.seek(0)
        for frame in container.decode(video=0):
            t = frame.time
            if t is None:
                continue
            if t >= next_target_time:
                img = frame.to_image()
                w, h = img.size
                if h > target_height:
                    new_w = int((target_height / h) * w)
                    img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)
                frames.append(img)
                next_target_time += interval
    else:
        # Attempt to sample uniformly across the video
        try:
            total_frames = container.streams.video[0].frames
        except Exception:
            total_frames = 0

        if total_frames > 0:
            indices = set(
                np.linspace(
                    0, total_frames - 1, min(max_frames, total_frames), dtype=int
                )
            )
        else:
            indices = None

        container.seek(0)
        for i, frame in enumerate(container.decode(video=0)):
            if indices is not None:
                if i in indices:
                    img = frame.to_image()
                    w, h = img.size
                    if h > target_height:
                        new_w = int((target_height / h) * w)
                        img = img.resize(
                            (new_w, target_height), Image.Resampling.LANCZOS
                        )
                    frames.append(img)
                if i > max(indices):
                    break
            else:
                img = frame.to_image()
                w, h = img.size
                if h > target_height:
                    new_w = int((target_height / h) * w)
                    img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)
                frames.append(img)
                if len(frames) >= max_frames:
                    break
    return frames


def get_track_id(chunk_id: str, metadata: dict) -> str:
    track_id = metadata.get("track_id")
    if track_id:
        return str(track_id)
    if "_stanza_" in chunk_id:
        return chunk_id.rsplit("_stanza_", 1)[0]
    return chunk_id


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve song lyrics based on a video or image query."
    )
    parser.add_argument(
        "query_path", type=str, help="Path to the video or image file (e.g., query.mp4)"
    )
    parser.add_argument("--genre", type=str, default=None, help="Filter by genre")
    parser.add_argument(
        "--artist", type=str, default=None, help="Filter by artist name"
    )
    parser.add_argument(
        "--mood",
        type=str,
        default=None,
        choices=MOODS,
        help=f"Thematic mood for lyrics matching ({', '.join(MOODS)})",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=None,
        help="Frames per second to sample from the video",
    )
    parser.add_argument(
        "--top_k", type=int, default=5, help="Number of results to retrieve"
    )
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading SentenceTransformer model on {device}...")
    model = SentenceTransformer("Qwen/Qwen3-VL-Embedding-2B", trust_remote_code=True, device=device)

    print("Embedding query...")
    is_video = args.query_path.lower().endswith(
        (".mp4", ".avi", ".mov", ".mkv", ".webm")
    )

    if is_video:
        print(f"Extracting and downsampling frames from video: {args.query_path}")
        media_data = load_video_frames(args.query_path, fps=args.fps)
        media_key = "video"
    else:
        media_data = Image.open(args.query_path)
        w, h = media_data.size
        if h > 720:
            new_w = int((720 / h) * w)
            media_data = media_data.resize((new_w, 720), Image.Resampling.LANCZOS)
        media_key = "image"

    system_prompt = get_query_prompt(args.mood)
    user_text = "Match these visuals to song lyrics:"

    if args.mood:
        print(f"Using mood: {args.mood}")

    query_embedding = model.encode(
        [{media_key: media_data, "text": user_text}],
        prompt=system_prompt,
    )[0].tolist()

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./lyrics_catalog_db")
    collection = client.get_collection(name="song_lyrics_min")

    # Build the where clause for metadata filtering
    where_conditions = []
    if args.genre:
        where_conditions.append({"genre": args.genre})
    if args.artist:
        where_conditions.append({"artist_name": args.artist})

    where_clause = None
    if len(where_conditions) > 1:
        where_clause = {"$and": where_conditions}
    elif len(where_conditions) == 1:
        where_clause = where_conditions[0]

    print("Searching for matches...")
    # Execute the search with a larger top_k to allow for deduplication
    search_k = args.top_k * 5
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=search_k,
        where=where_clause,
        include=["metadatas", "distances"],
    )

    print("\n--- Search Results ---")
    if not results["ids"] or not results["ids"][0]:
        print("No results found.")
        return

    unique_results = []
    seen_tracks = set()

    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        metadata = results["metadatas"][0][i]
        track_id = get_track_id(chunk_id, metadata)

        if track_id not in seen_tracks:
            seen_tracks.add(track_id)
            unique_results.append(
                {
                    "id": chunk_id,
                    "distance": results["distances"][0][i],
                    "metadata": metadata,
                }
            )

            # Stop once we have top_k unique tracks
            if len(unique_results) == args.top_k:
                break

    try:
        mxm_client = MusixmatchClient()
    except ValueError as e:
        print(f"Warning: {e}")
        mxm_client = None

    for i, res in enumerate(unique_results):
        track_id = get_track_id(res["id"], res["metadata"])
        details = (
            mxm_client.fetch_match_details(track_id, res["id"])
            if mxm_client
            else {}
        )

        print(f"\nMatch {i+1}:")
        print(f"  ID:       {res['id']}")
        print(f"  Distance: {res['distance']:.4f}")
        print(f"  Artist:   {details.get('artist_name') or 'Unknown'}")
        print(f"  Song:     {details.get('track_name') or 'Unknown'}")
        print(f"  Genre:    {res['metadata'].get('genre', 'Unknown')}")
        print(f"  Track ID: {track_id}")

        stanza = details.get("stanza")
        if stanza:
            lyrics_snippet = stanza.replace("\n", " / ")
            print(f"  Lyrics:   {lyrics_snippet}")
        else:
            print("  Lyrics:   (unavailable)")


if __name__ == "__main__":
    main()
