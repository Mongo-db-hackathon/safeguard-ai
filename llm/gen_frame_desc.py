from typing import Optional
import os

from llm.encode_image_to_64 import encode_image_to_base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()

from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from llm.encode_image_to_64 import encode_image_to_base64

load_dotenv()

# point OpenAI client to Fireworks endpoint + key
fw_client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_1"),
)

def generate_frame_description_fireworks(image_path: str) -> Optional[str]:
    try:
        base64_image = encode_image_to_base64(image_path)

        resp = fw_client.chat.completions.create(
            # pick a Fireworks VLM; qwen2.5-vl-32b is solid
            model="accounts/fireworks/models/qwen2p5-vl-32b-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Describe this video frame. Objects, people, actions, setting, and any visible text. Be concise."},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ],
            }],
            max_tokens=300,
        )

        desc = resp.choices[0].message.content
        print(f"✓ Generated description for {os.path.basename(image_path)}")
        return desc
    except Exception as e:
        print(f"Error generating description for {image_path}: {e}")
        return None

def generate_frame_description_openai(image_path: str) -> Optional[str]:
    """
    Generate a description of the frame content using OpenAI vision model.

    Args:
        image_path (str): Path to the image file

    Returns:
        Optional[str]: Description of the frame content or None if failed
    """
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)

        # Create the prompt for frame description
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4 vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe what you see in this video frame. Include details about objects, people, actions, setting, and any text visible. Be specific and descriptive but concise.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        description = response.choices[0].message.content
        print(f"✓ Generated description for {os.path.basename(image_path)}")
        return description

    except Exception as e:
        print(f"Error generating description for {image_path}: {e}")
        return None

def generate_frame_description(image_path: str) -> Optional[str]:
    return generate_frame_description_fireworks(image_path)