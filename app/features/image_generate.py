from app.features.g4f_adapter import generate_image as g4f_generate_image
import asyncio
import os
import uuid
import requests

def generate_image(prompt: str) -> dict:
    """
    Generate an image from a text prompt using g4f and save it locally.

    Args:
        prompt (str): Text description for the image.

    Returns:
        dict: {
            "image_path": <local_path> or None,
            "error": <error_message_if_any>
        }
    """
    try:
        image_url = asyncio.run(g4f_generate_image(prompt))

        if isinstance(image_url, str) and image_url.startswith("Error:"):
            return {"image_path": None, "error": image_url}
        
        # The adapter may return a list of URLs
        if isinstance(image_url, list):
            image_url = image_url[0]

        # Download and save the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        image_name = f"{uuid.uuid4()}.png"
        # Correctly join the path components
        image_path = os.path.join("app", "static", "images", image_name)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        with open(image_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return {"image_path": image_path, "error": None}

    except Exception as e:
        return {"image_path": None, "error": str(e)}



