import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# Maps our source hints to Google Translate language codes
LANG_MAP = {
    "UK": "uk",  # Ukrainian
    "RO": "ro",  # Romanian
}


def _is_likely_english(text: str) -> bool:
    """Skip translation if text is already predominantly ASCII/Latin."""
    if not text:
        return True
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    return sum(1 for c in letters if ord(c) < 128) / len(letters) > 0.85


def translate(text: str, source_lang: str = None) -> str:
    """
    Translate text to English using Google Translate (free, no API key).
    Falls back to original text on any error.
    source_lang: 'UK' for Ukrainian, 'RO' for Romanian, None for auto-detect.
    """
    if not text or not text.strip():
        return text
    # If source_lang is explicitly set (not auto), always translate.
    # Only skip the English check when auto-detecting — Romanian looks Latin but isn't English.
    if source_lang is None and _is_likely_english(text):
        return text

    src = LANG_MAP.get(source_lang, "auto") if source_lang else "auto"
    # Google Translate has a ~5000 char limit per call
    text = text[:4999]
    try:
        result = GoogleTranslator(source=src, target="en").translate(text)
        logger.debug("Translated [%s→en]: %.60s", src, text)
        return result or text
    except Exception as e:
        logger.warning("Translation failed, using original: %s", e)
        return text


def translate_pair(title: str, summary: str, source_lang: str = None) -> tuple[str, str]:
    """Translate title and summary, skipping any that are already English."""
    translated_title = translate(title, source_lang=source_lang)
    translated_summary = translate(summary, source_lang=source_lang)
    return translated_title, translated_summary
