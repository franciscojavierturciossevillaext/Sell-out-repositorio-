"""
SharePoint service – wraps Microsoft Graph Drive API calls.

Graph endpoints used:
  List children  : GET /sites/{site-id}/drives/{drive-id}/items/{item-id}/children
  Get item       : GET /sites/{site-id}/drives/{drive-id}/items/{item-id}
  Download       : GET /sites/{site-id}/drives/{drive-id}/items/{item-id}/content

When running in stub/demo mode (no Graph credentials) the service returns
synthetic data so the rest of the application can be exercised end-to-end.
"""

import logging
from datetime import datetime
from typing import Optional

from app.config import get_settings
from app.models.document_models import SharePointFile
from app.services.graph_client import get_graph_client

logger = logging.getLogger(__name__)


class SharePointService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._graph = get_graph_client()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _drive_root(self) -> str:
        site_id = self._settings.SHAREPOINT_SITE_ID
        drive_id = self._settings.SHAREPOINT_DRIVE_ID
        if site_id and drive_id:
            return f"/sites/{site_id}/drives/{drive_id}"
        if site_id:
            return f"/sites/{site_id}/drive"
        # Fallback – authenticated user's OneDrive (useful for quick local testing)
        return "/me/drive"

    def _item_path(self, folder_path: str) -> str:
        root = self._drive_root()
        if folder_path in ("", "root"):
            return f"{root}/root"
        return f"{root}/root:/{folder_path.strip('/')}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_folder(
        self, folder_path: str = "root", drive_id: Optional[str] = None
    ) -> list[SharePointFile]:
        """
        Return the list of files (not sub-folders) inside *folder_path*.

        Parameters
        ----------
        folder_path:
            Path relative to the drive root, e.g. ``"General/Reports"``.
        drive_id:
            Optional override of the drive configured in settings.
        """
        if self._graph.is_stub:
            logger.info("SharePointService: returning stub data (no Graph credentials).")
            return _stub_files(folder_path)

        item_path = self._item_path(folder_path)
        children_url = f"{item_path}:/children" if "root:/" in item_path else f"{item_path}/children"

        try:
            data = await self._graph.get(children_url, params={"$top": 200})
        except Exception as exc:
            logger.error("Graph list-folder failed: %s", exc)
            raise

        files: list[SharePointFile] = []
        for item in data.get("value", []):
            if "folder" in item:
                continue  # skip sub-folders for now
            files.append(
                SharePointFile(
                    id=item["id"],
                    name=item["name"],
                    size=item.get("size"),
                    mime_type=item.get("file", {}).get("mimeType"),
                    web_url=item.get("webUrl"),
                    last_modified=item.get("lastModifiedDateTime"),
                    download_url=item.get("@microsoft.graph.downloadUrl"),
                )
            )
        return files

    async def download_file(self, file_id: str) -> bytes:
        """Download raw bytes for a file by its Graph item id."""
        if self._graph.is_stub:
            return b"[stub content for file %b]" % file_id.encode()

        url = f"{self._drive_root()}/items/{file_id}/content"
        return await self._graph.get_bytes(url)


# ---------------------------------------------------------------------------
# Stub data for demo / offline development
# ---------------------------------------------------------------------------

def _stub_files(folder_path: str) -> list[SharePointFile]:
    return [
        SharePointFile(
            id="stub-001",
            name="Sell_Out_Report_Q1.pdf",
            size=204800,
            mime_type="application/pdf",
            web_url=f"https://example.sharepoint.com/{folder_path}/Sell_Out_Report_Q1.pdf",
            last_modified=datetime(2024, 3, 15),
        ),
        SharePointFile(
            id="stub-002",
            name="CRM_Strategy_2024.docx",
            size=81920,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            web_url=f"https://example.sharepoint.com/{folder_path}/CRM_Strategy_2024.docx",
            last_modified=datetime(2024, 4, 1),
        ),
        SharePointFile(
            id="stub-003",
            name="Sales_Data_April.xlsx",
            size=40960,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            web_url=f"https://example.sharepoint.com/{folder_path}/Sales_Data_April.xlsx",
            last_modified=datetime(2024, 4, 30),
        ),
        SharePointFile(
            id="stub-004",
            name="Presentation_Q1_Review.pptx",
            size=1048576,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            web_url=f"https://example.sharepoint.com/{folder_path}/Presentation_Q1_Review.pptx",
            last_modified=datetime(2024, 3, 20),
        ),
        SharePointFile(
            id="stub-005",
            name="Notes.md",
            size=2048,
            mime_type="text/markdown",
            web_url=f"https://example.sharepoint.com/{folder_path}/Notes.md",
            last_modified=datetime(2024, 5, 1),
        ),
    ]
