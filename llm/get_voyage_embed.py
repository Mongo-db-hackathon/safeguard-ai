import os
from typing import List, Optional

from PIL import Image
from dotenv import load_dotenv
import voyageai

load_dotenv()
voyageai_client = voyageai.Client()


def get_voyage_embedding(data: Image.Image | str, input_type: str = "document") -> List:
    """
    Get Voyage AI embeddings for images and text.

    Args:
        data (Image.Image | str): An image or text to embed.
        input_type (str): Input type, either "document" or "query".

    Returns:
        List: Embeddings as a list.
    """
    embedding = voyageai_client.multimodal_embed(
        inputs=[[data]], model="voyage-multimodal-3", input_type=input_type
    ).embeddings[0]
    return embedding




def get_image_embedding(
    image_path: str, input_type: str = "document"
) -> Optional[List[float]]:
    """
    Get embedding for a single image file using Voyage AI.

    Args:
        image_path (str): Path to the image file
        input_type (str): Input type for embedding ("document" or "query")

    Returns:
        Optional[List[float]]: Image embedding vector or None if failed
    """
    try:
        # Load image using PIL
        image = Image.open(image_path)

        # Get embedding using the Voyage AI client
        embedding = get_voyage_embedding(image, input_type)

        print(
            f"✓ Got embedding for {os.path.basename(image_path)} (dimension: {len(embedding)})"
        )
        return embedding

    except Exception as e:
        print(f"Error getting embedding for {image_path}: {e}")
        return None