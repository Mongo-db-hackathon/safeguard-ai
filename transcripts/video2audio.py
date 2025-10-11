import os
import subprocess
from pathlib import Path

def extract_audio(video_path: str, codec="libmp3lame") -> str:
    # Handle relative paths by resolving them relative to the project root
    if not os.path.isabs(video_path):
        # Get the project root (parent of transcripts directory)
        project_root = Path(__file__).parent.parent
        video = project_root / video_path
    else:
        video = Path(video_path)
    
    audio_path = video.with_suffix(".mp3")

    # Skip if output file already exists
    if audio_path.exists():
        print(f"Skipping: {audio_path} already exists")
        return str(audio_path)

    cmd = [
        "ffmpeg",
        "-i", str(video),
        "-vn",                   # no video
        "-acodec", codec,        # audio codec
        "-q:a", "4",             # quality 0–9 (lower = better)
        "-y",                    # overwrite output files without asking
        str(audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(audio_path)

# Example
if __name__ == "__main__":
    audio_file = extract_audio("video.mp4")
    print(f"Extracted: {audio_file}")