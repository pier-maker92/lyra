import asyncio
import random
import webbrowser
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

import chromadb
import uvicorn
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer

from moods import MOODS
from mxm import MusixmatchClient
from retrieve import get_device, retrieve_from_path

STATIC_DIR = Path(__file__).resolve().parent / "static"
DB_PATH = Path(__file__).resolve().parent / "lyrics_catalog_db"
QUERIES_DIR = Path(__file__).resolve().parent / "queries_720p"
RANDOM_SEED = 42
PORT = 8000
URL = f"http://127.0.0.1:{PORT}"


class AppState:
    model: SentenceTransformer | None = None
    collection = None
    mxm_client: MusixmatchClient | None = None
    videos: list[str] = []
    video_index: int = 0


state = AppState()


def load_shuffled_videos() -> list[str]:
    names = sorted(p.name for p in QUERIES_DIR.glob("*.mp4"))
    if not names:
        return []
    rng = random.Random(RANDOM_SEED)
    shuffled = names.copy()
    rng.shuffle(shuffled)
    return shuffled


def current_video() -> dict:
    if not state.videos:
        raise HTTPException(status_code=404, detail="No query videos found in queries_720p/")
    name = state.videos[state.video_index]
    return {"name": name, "url": f"/videos/{name}"}


def advance_video() -> dict:
    if not state.videos:
        raise HTTPException(status_code=404, detail="No query videos found in queries_720p/")
    state.video_index = (state.video_index + 1) % len(state.videos)
    return current_video()


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = get_device()
    print(f"Loading model on {device}...")
    state.model = SentenceTransformer(
        "Qwen/Qwen3-VL-Embedding-2B", trust_remote_code=True, device=device
    )

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=str(DB_PATH))
    state.collection = client.get_collection(name="song_lyrics_min")

    try:
        state.mxm_client = MusixmatchClient()
    except ValueError as e:
        print(f"Warning: {e}")
        state.mxm_client = None

    state.videos = load_shuffled_videos()
    print(f"Loaded {len(state.videos)} query videos (seed={RANDOM_SEED})")
    print(f"Ready — open {URL} in Safari")
    webbrowser.open(URL)
    yield


app = FastAPI(title="Lyra", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/moods")
async def list_moods():
    return {"moods": MOODS}


@app.get("/api/query/video")
async def get_query_video():
    return current_video()


@app.post("/api/query/next")
async def next_query_video():
    return advance_video()


@app.get("/videos/{filename}")
async def serve_video(filename: str):
    if filename not in state.videos:
        raise HTTPException(status_code=404, detail="Video not found.")
    path = QUERIES_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(path, media_type="video/mp4")


@app.post("/api/retrieve")
async def retrieve(
    query_name: str = Form(...),
    mood: str | None = Form(None),
    top_k: int = Form(5),
):
    if mood and mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Choose: {MOODS}")
    if query_name not in state.videos:
        raise HTTPException(status_code=400, detail="Invalid query video.")

    query_path = QUERIES_DIR / query_name
    try:
        loop = asyncio.get_event_loop()
        matches = await loop.run_in_executor(
            None,
            partial(
                retrieve_from_path,
                str(query_path),
                state.model,
                state.collection,
                mood=mood or None,
                fps=4,
                max_duration=5.0,
                top_k=top_k,
                mxm_client=state.mxm_client,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"mood": mood, "query": query_name, "matches": matches}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
