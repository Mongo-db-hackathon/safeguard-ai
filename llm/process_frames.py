from typing import Dict, Optional
import os
from pathlib import Path
import time
from get_voyage_embed import get_voyage_embedding
from gen_frame_desc import generate_frame_description
from PIL import Image


def process_single_frame(
    image_path: str, input_type: str = "document"
) -> Optional[Dict]:
    """
    Process a single frame to get both embedding and description.

    Args:
        image_path (str): Path to the image file
        input_type (str): Input type for embedding ("document" or "query")

    Returns:
        Optional[Dict]: Dictionary with 'embedding' and 'frame_description' or None if failed
    """
    try:
        # Load image using PIL for embedding
        image = Image.open(image_path)

        # Get embedding using Voyage AI
        embedding = get_voyage_embedding(image, input_type)

        # Generate description using OpenAI
        frame_description = generate_frame_description(image_path)

        if embedding is not None and frame_description is not None:
            return {"embedding": embedding, "frame_description": frame_description}
        else:
            print(f"Failed to process {image_path} - missing embedding or description")
            return None
    except Exception as e:
        print(f"Error processing frame {image_path}: {e}")
        return None


import time


def process_frames_to_embeddings_with_descriptions(
    frames_dir: str = "frames",
    input_type: str = "document",
    delay_seconds: float = 0.5,
    cut_off_frame: float = 300,
) -> Dict[str, Dict]:
    """
    Process all images in frames folder and get both Voyage AI embeddings and OpenAI descriptions.

    Args:
        frames_dir (str): Directory containing frame images (default: "frames")
        input_type (str): Input type for embeddings ("document" or "query")
        delay_seconds (float): Delay between API calls to avoid rate limits

    Returns:
        Dict[str, Dict]: Dictionary mapping image filenames to {'embedding': [...], 'frame_description': '...'}
    """

    # Check if frames directory exists
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"Frames directory '{frames_dir}' not found")

    # Get all image files from the directory
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    image_files = []

    for file in os.listdir(frames_dir):
        if Path(file).suffix.lower() in image_extensions:
            image_files.append(os.path.join(frames_dir, file))

    if not image_files:
        print(f"No image files found in '{frames_dir}'")
        return {}

    print(f"Found {len(image_files)} images in '{frames_dir}'")
    print("Processing frames for embeddings and descriptions...")

    # Process each image
    frame_data = {}
    failed_count = 0

    for i, image_path in enumerate(sorted(image_files), 1):
        print(f"\nProcessing {i}/{len(image_files)}: {os.path.basename(image_path)}")

        result = process_single_frame(image_path, input_type)

        if result is not None:
            # Add the frame number to the frame data
            result["frame_number"] = i
            # Extract the frame timestamp from the image path "frame_0001_t2.0s.jpg"
            # FIXED: Extract actual timestamp from "t2.0s" part, not frame number
            filename = os.path.basename(image_path)
            try:
                # Look for pattern like "t2.0s" in filename
                # timestamp_part = [part for part in filename.split("_") if part.startswith("t") and part.endswith("s.jpg")][0]
                # Extract number from "t2.0s.jpg" -> "2.0"
                timestamp_part = [
                    part
                    for part in filename.split("_")
                    if part.startswith("t") and part.endswith("s.jpg")
                ][0]
                result["frame_timestamp"] = float(
                    timestamp_part[1:-5]
                )  # Remove "t" and "s.jpg"
                print(f"✅ Timestamp parsed successfully: {result['frame_timestamp']}")
            except (IndexError, ValueError) as e:
                print(
                    f"⚠️ Could not parse timestamp from {filename}, using frame number: {e}"
                )
                # Fallback to frame number if parsing fails
                result["frame_timestamp"] = float(i * 2)  # Assume 2-second intervals
            frame_data[os.path.basename(image_path)] = result
            print(
                f"✓ Complete - Embedding: {len(result['embedding'])}D, Description: {len(result['frame_description'])} chars"
            )
        else:
            failed_count += 1

        # Add delay to respect rate limits (especially for OpenAI)
        if i < len(image_files):  # Don't delay after the last image
            time.sleep(delay_seconds)

        if cut_off_frame is not None and i == cut_off_frame:
            break

    print(f"\n🎉 Completed! Successfully processed {len(frame_data)} frames")
    if failed_count > 0:
        print(f"⚠️ Failed to process {failed_count} frames")

    return frame_data