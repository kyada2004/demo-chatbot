import re
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
candidate_labels = ["safe", "unsafe"]

UNSAFE_PATTERNS = [
    r"\b(kill|murder|assassinate)\b",
    r"\b(suicide|self-harm)\b",
    r"\b(bomb|terror|attack)\b",
    r"\b(hate speech|racist|sexist)\b",
    r"\b(explicit|porn|nsfw)\b",
]

# Whitelist common safe queries
WHITELIST = ["hello", "hi", "hey", "how are you", "greetings"]

def is_content_safe(text):
    if text.lower().strip() in WHITELIST:
        return True, ""
    try:
        result = classifier(text, candidate_labels)
        if result['labels'][0] == 'unsafe' and result['scores'][0] > 0.85:
            return False, "⚠️ This query cannot be answered due to safety policy."
        # Regex fallback
        text_lower = text.lower()
        for pattern in UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                return False, f"⚠️ Your query was blocked due to: '{pattern}'"
        return True, ""
    except Exception as e:
        print(f"[Safety Error] {e}")
        text_lower = text.lower()
        for pattern in UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                return False, f"⚠️ Your query was blocked due to: '{pattern}'"
        return True, ""
