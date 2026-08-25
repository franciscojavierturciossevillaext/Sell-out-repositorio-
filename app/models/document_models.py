"""Pydantic models shared across the application."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SharePoint / file listing
# ---------------------------------------------------------------------------

class SharePointFile(BaseModel):
    id: str
    name: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    web_url: Optional[str] = None
    last_modified: Optional[datetime] = None
    download_url: Optional[str] = None


class ListFolderRequest(BaseModel):
    folder_path: str = Field(
        default="root",
        description="Relative path inside the SharePoint drive, e.g. 'General/Reports'",
    )
    drive_id: Optional[str] = Field(
        default=None,
        description="Override the default drive id from settings",
    )


class ListFolderResponse(BaseModel):
    folder_path: str
    files: list[SharePointFile]
    total: int


# ---------------------------------------------------------------------------
# Document ingestion
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    file_ids: list[str] = Field(
        description="List of SharePoint file ids returned by list-folder",
    )
    force_reingest: bool = False


class DocumentChunk(BaseModel):
    doc_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any] = {}


class IngestedDocument(BaseModel):
    doc_id: str
    file_name: str
    mime_type: Optional[str] = None
    chunks: int
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "ok"
    error: Optional[str] = None


class IngestResponse(BaseModel):
    ingested: list[IngestedDocument]
    failed: list[IngestedDocument]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

class SummarizeRequest(BaseModel):
    doc_ids: Optional[list[str]] = Field(
        default=None,
        description="Document ids to summarize. If None, summarize all ingested docs.",
    )
    max_length: int = Field(default=300, ge=50, le=2000)


class SummarizeResponse(BaseModel):
    summaries: dict[str, str]  # doc_id -> summary text


class AskRequest(BaseModel):
    question: str
    doc_ids: Optional[list[str]] = Field(
        default=None,
        description="Restrict search to these doc ids. None = search all.",
    )
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]  # doc_ids used


# ---------------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
