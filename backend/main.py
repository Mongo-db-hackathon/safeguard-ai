from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# ✅ Serve static video files
VIDEO_FOLDER = "/Users/shamathmika./Desktop/Hackathons/MongoDB/safeguard-ai/videos"
app.mount("/videos", StaticFiles(directory=VIDEO_FOLDER), name="videos")

# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use ["http://localhost:5173"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Pydantic models
class ChatRequest(BaseModel):
    message: str

class VideoResult(BaseModel):
    path: str
    timestamp: int

class ChatResponse(BaseModel):
    reply: str
    videos: list[VideoResult]


@app.post("/api/chat", response_model=ChatResponse)
async def handle_chat(req: ChatRequest):
    print(f"💬 Message from frontend: {req.message}")
    await asyncio.sleep(3)  # simulate processing time

    # ✅ Dynamically fetch .mp4 videos from folder
    all_files = [
        f for f in os.listdir(VIDEO_FOLDER)
        if f.lower().endswith(".mp4")
    ]

    # Just simulate timestamps for now
    videos = [
        {"path": file, "timestamp": (i + 1) * 10}
        for i, file in enumerate(all_files)
    ]

    reply = f"{len(videos)} relevant video clip(s) found:" if videos else "No videos found."

    return {
        "reply": reply,
        "videos": videos,
    }
