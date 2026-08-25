"""SharePoint routes."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.document_models import ListFolderRequest, ListFolderResponse
from app.services.sharepoint_service import SharePointService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sharepoint", tags=["sharepoint"])


@router.post("/list-folder", response_model=ListFolderResponse, summary="List files in a SharePoint folder")
async def list_folder(request: ListFolderRequest) -> ListFolderResponse:
    """
    List all files inside a SharePoint folder.

    - **folder_path**: relative path inside the drive (e.g. ``"General/Reports"``).
      Use ``"root"`` for the drive root.
    - **drive_id**: optional override for the drive configured in settings.

    When Microsoft Graph credentials are not configured the endpoint returns
    synthetic stub data so the rest of the workflow can be tested offline.
    """
    svc = SharePointService()
    try:
        files = await svc.list_folder(
            folder_path=request.folder_path,
            drive_id=request.drive_id,
        )
    except Exception as exc:
        logger.error("list_folder error: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"SharePoint error: {exc}") from exc

    return ListFolderResponse(
        folder_path=request.folder_path,
        files=files,
        total=len(files),
    )
