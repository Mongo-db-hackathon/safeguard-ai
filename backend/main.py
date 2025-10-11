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
    path: str  # just the filename (or /videos/video.mp4)
    timestamp: int

class ChatResponse(BaseModel):
    reply: str
    videos: list[VideoResult]

@app.post("/api/chat", response_model=ChatResponse)
async def handle_chat(req: ChatRequest):
    print(f"💬 Message from frontend: {req.message}")

    await asyncio.sleep(3)

    # Just send back relative paths to avoid file:// issues
    videos = [
        {"path": "video.mp4", "timestamp": 12},
        {"path": "video.mp4", "timestamp": 37},
        {"path": "video.mp4", "timestamp": 8},
    ]

    return {
        "reply": "Here are 3 relevant video clips I found:",
        "videos": videos,
    }
