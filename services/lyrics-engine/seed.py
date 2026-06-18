"""DANGER — destructive placeholder seeding script. DISABLED by default.

This script DELETES and RECREATES the `song_lyrics_min` collection. The production
catalog is the user's real ChromaDB (installed into `lyrics_catalog_db/`), so running
this would WIPE the user's data permanently.

It is intentionally gated behind an explicit opt-in and is kept only for reference /
local experiments against a throwaway database. To run it you must BOTH:
  - set the environment variable `ALLOW_SEED_RESET=1`, and
  - pass a path to a catalog JSON file as the first CLI argument.

The original placeholder `catalog.json` has been removed; there is no default catalog.
"""

import json
import os
import sys

import chromadb

from embeddings import embed_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lyrics_catalog_db")
COLLECTION_NAME = "song_lyrics_min"


def main() -> None:
    if os.environ.get("ALLOW_SEED_RESET") != "1":
        raise SystemExit(
            "Refusing to run: this script wipes the real catalog. "
            "Set ALLOW_SEED_RESET=1 to override (DESTRUCTIVE)."
        )
    if len(sys.argv) < 2:
        raise SystemExit("Usage: ALLOW_SEED_RESET=1 python seed.py <catalog.json>")

    catalog_path = sys.argv[1]
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for i, song in enumerate(catalog):
        stanza = song["stanza"]
        print(f"[{i + 1}/{len(catalog)}] embedding {song['track_id']} ...")
        vector = embed_text(stanza)
        ids.append(f"{song['track_id']}_0")
        embeddings.append(vector)
        documents.append(stanza)
        metadatas.append(
            {
                "track_id": song["track_id"],
                "track_name": song["track_name"],
                "artist_name": song["artist_name"],
                "mood": song.get("mood", ""),
                "stanza": stanza,
            }
        )

    collection.add(
        ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
    )
    print(f"Seeded {collection.count()} stanzas into '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    main()
