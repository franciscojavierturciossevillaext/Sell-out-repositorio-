"""Document ingestion routes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.document_models import IngestRequest, IngestResponse, IngestedDocument
from app.services import analysis_service
from app.services.document_parser import parse_document
from app.services.sharepoint_service import SharePointService
from app.utils.file_helpers import is_supported

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse, summary="Ingest documents from SharePoint")
async def ingest_documents(request: IngestRequest) -> IngestResponse:
    """
    Download and parse a list of SharePoint files (identified by their
    Graph item ids) and store the extracted text for later analysis.

    - **file_ids**: list of Graph item ids (as returned by ``/sharepoint/list-folder``).
    - **force_reingest**: if ``true``, re-ingest documents even if already stored.
    """
    svc = SharePointService()
    ingested: list[IngestedDocument] = []
    failed: list[IngestedDocument] = []

    for file_id in request.file_ids:
        # Try to resolve a file name from a previous list call – fall back to the id.
        file_name = file_id  # we'll update this once we can inspect the bytes

        if not request.force_reingest and analysis_service.document_exists(file_id):
            ingested.append(
                IngestedDocument(
                    doc_id=file_id,
                    file_name=file_name,
                    chunks=0,
                    ingested_at=datetime.now(timezone.utc),
                    status="already_ingested",
                )
            )
            continue

        try:
            content: bytes = await svc.download_file(file_id)

            # For stub mode the file_name is just the id; in real mode we'd fetch metadata.
            # Use the id as file name if it looks like a stub id, otherwise keep it.
            if file_id.startswith("stub-"):
                # Map stub ids to realistic file names for demo purposes
                _stub_names = {
                    "stub-001": "Sell_Out_Report_Q1.pdf",
                    "stub-002": "CRM_Strategy_2024.docx",
                    "stub-003": "Sales_Data_April.xlsx",
                    "stub-004": "Presentation_Q1_Review.pptx",
                    "stub-005": "Notes.md",
                }
                file_name = _stub_names.get(file_id, f"{file_id}.txt")
            else:
                # In production you'd fetch the item metadata from Graph.
                file_name = f"{file_id}.bin"

            if not is_supported(file_name):
                failed.append(
                    IngestedDocument(
                        doc_id=file_id,
                        file_name=file_name,
                        chunks=0,
                        status="unsupported_format",
                        error=f"File type not supported: '{file_name}'",
                    )
                )
                continue

            text = parse_document(file_name, content)
            num_chunks = analysis_service.store_document(
                doc_id=file_id,
                file_name=file_name,
                mime_type="",
                text=text,
            )
            ingested.append(
                IngestedDocument(
                    doc_id=file_id,
                    file_name=file_name,
                    chunks=num_chunks,
                    ingested_at=datetime.now(timezone.utc),
                    status="ok",
                )
            )
        except Exception as exc:
            logger.error("Ingest error for '%s': %s", file_id, exc, exc_info=True)
            failed.append(
                IngestedDocument(
                    doc_id=file_id,
                    file_name=file_name,
                    chunks=0,
                    status="error",
                    error=str(exc),
                )
            )

    return IngestResponse(ingested=ingested, failed=failed)
