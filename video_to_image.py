import os
from pathlib import Path

import cv2


def video_to_images(video_path, output_dir="frames", interval_seconds=2):
    """
    Convert a video to images by extracting frames every specified interval.

    Args:
        video_path (str): Path to the input video file
        output_dir (str): Directory to save extracted frames (default: "frames")
        interval_seconds (float): Time interval between frame extractions (default: 2 seconds)

    Returns:
        int: Number of frames extracted
    """

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Error: Could not open video file {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f"Video info: {fps:.2f} FPS, {total_frames} frames, {duration:.2f} seconds")

    # Calculate frame interval
    frame_interval = int(fps * interval_seconds)

    frame_count = 0
    extracted_count = 0

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            # Extract frame every interval_seconds
            if frame_count % frame_interval == 0:
                # Create filename with timestamp
                timestamp = frame_count / fps
                filename = f"frame_{extracted_count:04d}_t{timestamp:.1f}s.jpg"
                filepath = os.path.join(output_dir, filename)

                # Save frame as image
                cv2.imwrite(filepath, frame)
                extracted_count += 1
                print(f"Extracted frame {extracted_count}: {filename}")

            frame_count += 1

    finally:
        cap.release()

    print(f"Extraction complete! {extracted_count} frames saved to '{output_dir}'")
    return extracted_count