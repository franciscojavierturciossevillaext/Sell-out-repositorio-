"""
PowerPoint generation service.

MVP implementation: creates a simple presentation from a dict of
{ slide_title -> slide_body_text }.

Production upgrade path:
  - Use a proper template file (.pptx) for brand styling.
  - Add charts, tables and images pulled from analysis results.
  - Stream the file back rather than buffering in memory.
"""

from __future__ import annotations

import io
import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_presentation(slides_data: list[dict[str, str]]) -> bytes:
    """
    Build a .pptx file from *slides_data* and return it as raw bytes.

    Each item in *slides_data* must have:
      - ``title``: slide title
      - ``body``:  slide body text (may include ``\\n`` for line breaks)

    Returns
    -------
    bytes
        Raw .pptx file content.

    Raises
    ------
    ImportError
        If python-pptx is not installed.
    """
    try:
        from pptx import Presentation  # type: ignore
        from pptx.util import Inches, Pt  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "python-pptx is required for PPT generation. "
            "Install it with: pip install python-pptx"
        ) from exc

    prs = Presentation()
    title_slide_layout = prs.slide_layouts[1]   # Title and Content layout

    for slide_info in slides_data:
        slide = prs.slides.add_slide(title_slide_layout)
        title_shape = slide.shapes.title
        body_shape = slide.placeholders[1]

        if title_shape:
            title_shape.text = slide_info.get("title", "")

        tf = body_shape.text_frame
        tf.word_wrap = True
        tf.text = slide_info.get("body", "")

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()


def build_slides_from_summaries(summaries: dict[str, Any]) -> list[dict[str, str]]:
    """
    Convert a summaries dict (doc_id -> summary_text) into slide data
    suitable for ``create_presentation``.
    """
    slides = [
        {
            "title": "Document Analysis Summary",
            "body": f"Total documents summarised: {len(summaries)}",
        }
    ]
    for doc_id, summary in summaries.items():
        slides.append(
            {
                "title": doc_id,
                "body": summary or "No summary available.",
            }
        )
    return slides
