"""
Text processing utilities: cleaning, truncation, token estimation.
"""

import re
from typing import List, Optional


def clean_text(text: str) -> str:
    """
    Clean raw extracted text: remove excessive whitespace, fix encoding artifacts.
    """
    # Remove null bytes
    text = text.replace("\x00", "")
    # Normalise whitespace (keep single newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def truncate_text(text: str, max_chars: int = 4000, suffix: str = "...") -> str:
    """Truncate text to max_chars, appending suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars / token for English)."""
    return len(text) // 4


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using a simple regex."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from a text string."""
    url_pattern = re.compile(
        r"https?://[^\s\[\]()\"']+"
    )
    return url_pattern.findall(text)


def markdown_to_plain(text: str) -> str:
    """Strip common markdown syntax for plain-text display."""
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", text)
    # Remove code fences
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()
