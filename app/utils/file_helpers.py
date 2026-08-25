"""Utility helpers for file handling."""

import mimetypes
import os
import tempfile
from pathlib import Path


# Supported file extensions and their categories
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".csv": "csv",
    ".md": "text",
    ".txt": "text",
    ".json": "json",
}


def get_file_category(file_name: str) -> str:
    """Return a category string for the given file name, or 'unknown'."""
    ext = Path(file_name).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, "unknown")


def is_supported(file_name: str) -> bool:
    return get_file_category(file_name) != "unknown"


def guess_mime_type(file_name: str) -> str:
    mime, _ = mimetypes.guess_type(file_name)
    return mime or "application/octet-stream"


def safe_temp_file(suffix: str = "") -> str:
    """Return a path for a temporary file that the caller is responsible for deleting."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Split *text* into overlapping chunks of roughly *chunk_size* characters.
    Simple character-level splitter – good enough for an MVP.
    """
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
