
# app/core/input_handler.py

from app.core.spell_checker import correct_spelling
from app.core.safety import is_content_safe
import html
import re

def process_input(raw_query: str):
    """
    Handles the initial processing of user input.
    1. Sanitizes the input to prevent injection attacks.
    2. Corrects spelling.
    3. Performs a safety check.
    """
    # 1. Sanitize Input
    safe_query = sanitize_input(raw_query)
    if not safe_query:
        return None, "Message blocked because it contained unsafe or disallowed content."

    # 2. Correct Spelling
    corrected_query = correct_spelling(safe_query)

    # 3. Safety Check
    is_safe, safety_message = is_content_safe(corrected_query)
    if not is_safe:
        return None, safety_message

    return corrected_query, None


def sanitize_input(user_text: str) -> str:
    """
    Sanitize user input to prevent script/HTML injection.
    - Remove <script>, <iframe>, <style>, <object>, <embed> blocks
    - Remove any remaining tags
    - Escape special HTML characters
    Returns cleaned text ('' if result is empty).
    """
    if not user_text:
        return ""
    # Remove dangerous tag blocks (case-insensitive)
    user_text = re.sub(
        r"(?i)<(script|iframe|style|object|embed).*?>.*?</\1>",
        "",
        user_text,
        flags=re.DOTALL,
    )
    # Remove any remaining tags
    user_text = re.sub(r"<.*?>", "", user_text)
    # Escape special chars (&, <, >, etc.)
    cleaned = html.escape(user_text)
    return cleaned.strip()
