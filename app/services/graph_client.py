"""
Microsoft Graph API client.

Authentication uses the OAuth 2.0 client-credentials flow via MSAL.
Set AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET in your .env file.

For the MVP the client falls back to a stub mode when credentials are missing
so that the rest of the application can be exercised without a real Azure tenant.
"""

import logging
from typing import Any, Optional

import httpx

try:
    import msal  # type: ignore
    _MSAL_AVAILABLE = True
except ImportError:
    _MSAL_AVAILABLE = False

from app.config import get_settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


class GraphClient:
    """Thin async wrapper around Microsoft Graph REST API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token: Optional[str] = None
        self._app: Any = None

        if _MSAL_AVAILABLE and all(
            [
                self._settings.AZURE_TENANT_ID,
                self._settings.AZURE_CLIENT_ID,
                self._settings.AZURE_CLIENT_SECRET,
            ]
        ):
            authority = f"https://login.microsoftonline.com/{self._settings.AZURE_TENANT_ID}"
            self._app = msal.ConfidentialClientApplication(
                client_id=self._settings.AZURE_CLIENT_ID,
                client_credential=self._settings.AZURE_CLIENT_SECRET,
                authority=authority,
            )
            logger.info("GraphClient: MSAL app initialised (client-credentials flow).")
        else:
            logger.warning(
                "GraphClient: Azure credentials not configured – running in STUB mode. "
                "Set AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET to enable real calls."
            )

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _acquire_token(self) -> Optional[str]:
        if self._app is None:
            return None
        result = self._app.acquire_token_for_client(scopes=SCOPES)
        if "access_token" in result:
            return result["access_token"]
        logger.error("Token acquisition failed: %s", result.get("error_description"))
        return None

    def _get_headers(self) -> dict[str, str]:
        token = self._acquire_token()
        if not token:
            raise RuntimeError(
                "Cannot acquire Microsoft Graph token. "
                "Check AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET."
            )
        return {
            "Authorization": f"******",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    async def get(self, path: str, params: Optional[dict] = None) -> Any:
        """Perform a GET request against Graph and return the parsed JSON body."""
        url = path if path.startswith("http") else f"{GRAPH_BASE}{path}"
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_bytes(self, url: str) -> bytes:
        """Download raw bytes (e.g. file content) from a URL."""
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.content

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def is_stub(self) -> bool:
        return self._app is None


_client: Optional[GraphClient] = None


def get_graph_client() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
