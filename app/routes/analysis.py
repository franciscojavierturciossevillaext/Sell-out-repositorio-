"""Analysis routes – summarize and Q&A over ingested documents."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.document_models import AskRequest, AskResponse, SummarizeRequest, SummarizeResponse
from app.services import analysis_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/summarize", response_model=SummarizeResponse, summary="Summarize ingested documents")
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    Return a short summary for each requested document.

    - **doc_ids**: list of document ids to summarize. If omitted, all ingested documents are summarized.
    - **max_length**: maximum character length for each summary.
    """
    ids = request.doc_ids or analysis_service.get_all_doc_ids()
    if not ids:
        raise HTTPException(
            status_code=404,
            detail="No documents ingested yet. Call POST /documents/ingest first.",
        )

    summaries: dict[str, str] = {}
    for doc_id in ids:
        summaries[doc_id] = analysis_service.summarize(doc_id, max_length=request.max_length)

    return SummarizeResponse(summaries=summaries)


@router.post("/ask", response_model=AskResponse, summary="Ask a question about ingested documents")
async def ask(request: AskRequest) -> AskResponse:
    """
    Answer a natural-language question using the ingested document corpus.

    **MVP behaviour**: keyword-based retrieval.  Replace ``analysis_service.answer_question``
    with an LLM + vector-search implementation for production quality.

    - **question**: the question to answer.
    - **doc_ids**: restrict search to these document ids. ``null`` = search all.
    - **top_k**: number of text chunks to include in the answer context.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    answer, sources = analysis_service.answer_question(
        question=request.question,
        doc_ids=request.doc_ids,
        top_k=request.top_k,
    )
    return AskResponse(question=request.question, answer=answer, sources=sources)
