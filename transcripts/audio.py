import os, requests, sys
from pymongo import MongoClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.mongo_client_1 import FRAME_INTELLIGENCE_METADATA, db, TRANSCRIPT_COLL
from transcripts.video2audio import extract_audio

# providers
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "voyage").lower()  # "fireworks" or "voyage"

# keys
FIREWORKS_API_KEY = os.getenv("FIREWORKS_1", "")
VOYAGE_API_KEY     = os.getenv("VOYAGE_API_KEY", "")

# fireworks endpoints and models
ASR_URL = "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions"
ASR_MODEL = os.getenv("ASR_MODEL", "whisper-v3")  # or whisper-v3-turbo
FW_EMBED_URL = "https://api.fireworks.ai/inference/v1/embeddings"
FW_EMBED_MODEL = os.getenv("FW_EMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")
FW_EMBED_DIMS = int(os.getenv("FW_EMBED_DIMS", "512"))

# voyage embeddings
VOYAGE_EMBED_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_EMBED_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3")

# mongo



tx_col = db[TRANSCRIPT_COLL]



def transcribe_with_fireworks(file_path: str):
    audio_path = extract_audio(file_path)
    if not FIREWORKS_API_KEY:
        raise RuntimeError("FIREWORKS_API_KEY missing")
    with open(audio_path, "rb") as f:
        r = requests.post(
            "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {FIREWORKS_API_KEY}",
                "Accept": "application/json"  # ✅ ensures JSON with segments
            },
            files={"file": f},
            data={
                "model": "whisper-v3",
                "temperature": "0",
                "vad_model": "silero",
                "response_format": "verbose_json"  # ✅ include detailed segments
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"ASR failed {r.status_code}: {r.text}")
        return r.json().get("segments", []) or []

def _embed_fireworks(text: str):
    if not FIREWORKS_API_KEY:
        raise RuntimeError("FIREWORKS_API_KEY missing")
    r = requests.post(
        FW_EMBED_URL,
        headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}", "Content-Type": "application/json"},
        json={"model": FW_EMBED_MODEL, "input": text, "dimensions": FW_EMBED_DIMS},
        timeout=30
    )
    if r.status_code != 200:
        raise RuntimeError(f"FW embed failed {r.status_code}: {r.text}")
    return r.json()["data"][0]["embedding"]

def _embed_voyage(text: str):
    if not VOYAGE_API_KEY:
        raise RuntimeError("VOYAGE_API_KEY missing")
    r = requests.post(
        VOYAGE_EMBED_URL,
        headers={"Authorization": f"Bearer {VOYAGE_API_KEY}", "Content-Type": "application/json"},
        json={"model": VOYAGE_EMBED_MODEL, "input": text},
        timeout=30
    )
    if r.status_code != 200:
        raise RuntimeError(f"Voyage embed failed {r.status_code}: {r.text}")
    return r.json()["data"][0]["embedding"]

def embed_text(text: str):
    return _embed_fireworks(text) if EMBED_PROVIDER == "fireworks" else _embed_voyage(text)

import os
from typing import List, Dict

def ingest_transcripts(video_path: str) -> int:
    segs = transcribe_with_fireworks(video_path)
    # Normalize shape just in case
    if isinstance(segs, dict) and "segments" in segs:
        segs = segs["segments"]
    if not segs:
        return 0

    docs: List[Dict] = []
    dim = None

    for s in segs:
        text = (s.get("text") or "").strip()
        if not text:
            continue

        # timestamps in seconds from start
        start = float(s.get("start", s.get("audio_start", 0.0)))
        end   = float(s.get("end",   s.get("audio_end",   start)))

        # embed with Voyage
        vec = embed_text(text)  # uses your function

        if dim is None:
            dim = len(vec)
            print(f"transcript embedding dim = {dim} (provider=voyage, model={VOYAGE_EMBED_MODEL})")

        docs.append({
            "t_start": start,
            "t_end": end,
            "text": text,
            "embed": {                    # small audit block (optional but useful)
                "provider": "voyage",
                "model": VOYAGE_EMBED_MODEL,
                "dims": dim
            },
            "text_embedding": vec
        })

    if not docs:
        return 0

    res = tx_col.insert_many(docs, ordered=False)
    return len(res.inserted_ids)



VIDEO_PATH = "videos/video.mp4"  # or pass-through from your existing var
n_tx = ingest_transcripts(VIDEO_PATH)
print(f"inserted transcript segments: {n_tx}")