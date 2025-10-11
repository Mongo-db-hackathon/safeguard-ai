import base64
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI()

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string for OpenAI.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")