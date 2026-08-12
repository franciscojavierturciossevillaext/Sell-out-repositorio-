"""FastAPI application bootstrap."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import analysis, documents, health, sharepoint

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

app = FastAPI(
    title="SharePoint Document Agent",
    description=(
        "MVP backend that connects to Microsoft SharePoint via Graph API, "
        "ingests documents and exposes analysis endpoints.\n\n"
        "**Note:** When Azure credentials are not configured the service runs in "
        "*stub mode* and returns synthetic data."
    ),
    version="0.1.0",
)

# Allow all origins in development; tighten this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sharepoint.router)
app.include_router(documents.router)
app.include_router(analysis.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "SharePoint Document Agent API – visit /docs for the interactive UI."}
