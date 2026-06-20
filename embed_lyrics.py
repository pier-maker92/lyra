import argparse
import json

import chromadb
import numpy as np
from tqdm import tqdm

from embedding import encode_documents, get_device, load_model
from moods import MOODS, apply_affinity, top_mood


def read_concatenated_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(content):
        while pos < len(content) and content[pos].isspace():
            pos += 1
        if pos >= len(content):
            break
        obj, end_pos = decoder.raw_decode(content, pos)
        yield obj
        pos = end_pos


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def embed_mood_anchors(model) -> dict[str, np.ndarray]:
    """Embed all 20 mood keyword prompts once and return name→vector."""
    print("Embedding mood anchors...")
    mood_names = list(MOODS.keys())
    mood_texts = [m["keywords"] for m in MOODS.values()]
    vectors = encode_documents(model, mood_texts, batch_size=len(mood_texts))
    return {name: vectors[i] for i, name in enumerate(mood_names)}


def assign_mood(
    stanza_vec: np.ndarray,
    mood_anchors: dict[str, np.ndarray],
    genre: str,
) -> str:
    raw_scores = {
        mood: cosine_similarity(stanza_vec, anchor)
        for mood, anchor in mood_anchors.items()
    }
    weighted = apply_affinity(raw_scores, genre)
    return top_mood(weighted)


def main():
    parser = argparse.ArgumentParser(description="Embed lyrics into ChromaDB.")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument(
        "--input_file",
        type=str,
        default="/Users/software/lyra/lyrics_dataset.jsonl",
    )
    args = parser.parse_args()

    device = get_device()
    print(f"Loading SentenceTransformer model on {device}...")
    model = load_model(device)

    mood_anchors = embed_mood_anchors(model)

    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./lyrics_catalog_db")
    collection = client.get_or_create_collection(
        name="song_lyrics_min", metadata={"hnsw:space": "cosine"}
    )

    print(f"Collecting all stanzas from {args.input_file}...")

    all_stanzas = []
    all_ids = []
    all_metadatas = []

    for i, track_data in enumerate(
        tqdm(read_concatenated_json(args.input_file), desc="Reading dataset")
    ):
        try:
            genre = "Unknown"
            try:
                genre_list = track_data["track_data"]["primary_genres"]["music_genre_list"]
                if genre_list:
                    genre = genre_list[0]["music_genre"]["music_genre_name_extended"]
            except (KeyError, IndexError, TypeError):
                pass

            lyrics_txt = track_data.get("lyrics_txt", "")
            if not lyrics_txt:
                continue

            track_id = str(track_data.get("track_id", f"unknown_{i}"))
            stanzas = [s.strip() for s in lyrics_txt.split("\n\n") if s.strip()]

            for j, stanza in enumerate(stanzas):
                all_stanzas.append(stanza)
                all_ids.append(f"{track_id}_stanza_{j}")
                all_metadatas.append({"genre": genre})

        except Exception as e:
            print(f"Error processing track {i}: {e}")
            continue

    total_chunks = len(all_stanzas)
    print(f"Total stanzas collected: {total_chunks}")
    print(f"Embedding and inserting in batches of {args.batch_size}...")

    for i in tqdm(range(0, total_chunks, args.batch_size), desc="Embedding batches"):
        batch_stanzas = all_stanzas[i : i + args.batch_size]
        batch_ids = all_ids[i : i + args.batch_size]
        batch_metadatas = all_metadatas[i : i + args.batch_size]

        embeddings = encode_documents(
            model,
            batch_stanzas,
            batch_size=args.batch_size,
            show_progress_bar=False,
        )

        for j, (vec, meta) in enumerate(zip(embeddings, batch_metadatas)):
            mood = assign_mood(vec, mood_anchors, meta["genre"])
            batch_metadatas[j]["mood"] = mood

        collection.add(
            ids=batch_ids,
            embeddings=embeddings.tolist(),
            metadatas=batch_metadatas,
        )

    print(f"\nDone. Total chunks in DB: {collection.count()}")


if __name__ == "__main__":
    main()
