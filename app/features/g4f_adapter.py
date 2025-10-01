import asyncio
import logging
from g4f.client import Client

logging.basicConfig(level=logging.INFO)
client = Client()

# --- Text Generation ---
async def generate_text(prompt: str, model: str = "gpt-4o-mini", timeout: int = 10, retries: int = 2):
    for attempt in range(retries):
        try:
            logging.info(f"[TextGen] Model: {model}, Attempt {attempt + 1}/{retries}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
                stream=True
            )
            for chunk in response:
                yield chunk
            return
        except Exception as e:
            logging.warning(f"[TextGen] Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)
            else:
                logging.error("[TextGen] All retries failed.")
                yield "Error: Unable to generate text after multiple retries."
                return

# --- Image Generation ---
async def generate_image(prompt: str, model: str = "dall-e-3", timeout: int = 10, retries: int = 2):
    for attempt in range(retries):
        try:
            logging.info(f"[ImageGen] Model: {model}, Attempt {attempt + 1}/{retries}")
            response = await client.images.generate(model=model, prompt=prompt, timeout=timeout)
            if hasattr(response, "data") and response.data:
                return response.data[0].url
            raise ValueError("No image data returned")
        except Exception as e:
            logging.warning(f"[ImageGen] Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)
            else:
                logging.error("[ImageGen] All retries failed.")
                return f"Error: Unable to generate image after {retries} retries."
