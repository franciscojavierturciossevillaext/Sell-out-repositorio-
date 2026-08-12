# SharePoint Document Agent – MVP

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/franciscojavierturciossevillaext/Sell-out-repositorio-)

Backend FastAPI service that connects to **Microsoft SharePoint** via the **Microsoft Graph API**, ingests documents, and exposes endpoints for basic document analysis and Q&A.

---

## ⚡ Quickstart (3 ways)

### Option A – GitHub Codespaces (recommended, zero local setup)

1. Click **"Open in GitHub Codespaces"** badge above (or go to the repo → green **Code** button → **Codespaces** tab → **Create codespace on main**).
2. Wait ~60 s for the container to build – dependencies install automatically.
3. In the terminal that opens, run:
   ```bash
   bash start.sh
   ```
4. Codespaces will show a popup **"Open in browser"** – click it, or navigate to the forwarded port 8000.
5. Go to the **`/docs`** path for the interactive Swagger UI.

### Option B – One-command local start

```bash
bash start.sh
```
Then open **http://localhost:8000/docs**

### Option C – Manual steps

```bash
pip install -r requirements.txt
cp .env.example .env   # edit .env if you have Azure credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **No Azure credentials?**  
> The app starts in **stub mode** automatically – you can test every endpoint with synthetic data, no SharePoint connection needed.

---

## Table of Contents

1. [Architecture overview](#architecture-overview)
2. [Project structure](#project-structure)
3. [Endpoints](#endpoints)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running locally](#running-locally)
7. [Quick demo (stub mode)](#quick-demo-stub-mode)
8. [Connecting to a real SharePoint site](#connecting-to-a-real-sharepoint-site)
9. [Supported file formats](#supported-file-formats)
10. [MVP limitations and production roadmap](#mvp-limitations-and-production-roadmap)

---

## Architecture overview

```
Client
  │
  ▼
FastAPI app (app/main.py)
  ├── GET  /health
  ├── POST /sharepoint/list-folder      ──► SharePointService ──► Microsoft Graph API
  ├── POST /documents/ingest            ──► DocumentParser (PDF, DOCX, PPTX, XLSX, CSV, MD, TXT)
  ├── POST /analysis/summarize          ──► AnalysisService (in-memory store)
  └── POST /analysis/ask                ──► AnalysisService (keyword search MVP)
```

**Authentication flow** (client-credentials / app-only):

```
App (MSAL) ──► Azure Entra ID ──► access token ──► Graph API ──► SharePoint
```

---

## Project structure

```
.
├── app/
│   ├── main.py                  FastAPI bootstrap, middleware, router registration
│   ├── config.py                Settings from environment variables (pydantic-settings)
│   ├── models/
│   │   └── document_models.py   Shared Pydantic request/response models
│   ├── routes/
│   │   ├── health.py            GET /health
│   │   ├── sharepoint.py        POST /sharepoint/list-folder
│   │   ├── documents.py         POST /documents/ingest
│   │   └── analysis.py          POST /analysis/summarize  POST /analysis/ask
│   ├── services/
│   │   ├── graph_client.py      Thin async wrapper over Microsoft Graph REST API
│   │   ├── sharepoint_service.py  Lists and downloads files from SharePoint
│   │   ├── document_parser.py   Extracts plain text from supported file types
│   │   ├── analysis_service.py  In-memory document store + keyword Q&A / summariser
│   │   └── ppt_service.py       Generates .pptx from analysis results
│   └── utils/
│       └── file_helpers.py      Shared utilities (MIME types, chunking, …)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Service health check |
| `POST` | `/sharepoint/list-folder` | List files in a SharePoint folder |
| `POST` | `/documents/ingest` | Download and parse files from SharePoint |
| `POST` | `/analysis/summarize` | Summarize ingested documents |
| `POST` | `/analysis/ask` | Answer a question over ingested documents |

Full interactive documentation is available at **`http://localhost:8000/docs`** once the server is running.

---

## Installation

**Prerequisites:** Python ≥ 3.11

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/franciscojavierturciossevillaext/Sell-out-repositorio-.git
cd Sell-out-repositorio-

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes* | Your Azure Active Directory tenant id |
| `AZURE_CLIENT_ID` | Yes* | App registration client id |
| `AZURE_CLIENT_SECRET` | Yes* | App registration client secret |
| `SHAREPOINT_SITE_ID` | Yes* | Graph site id (see below) |
| `SHAREPOINT_DRIVE_ID` | No | Drive id inside the site (defaults to the site's default document library) |
| `SHAREPOINT_ROOT_FOLDER` | No | Default folder path (default: `root`) |
| `OPENAI_API_KEY` | No | OpenAI API key (for future LLM-based analysis) |
| `LOG_LEVEL` | No | Logging level (`DEBUG`, `INFO`, `WARNING`, …) |

\* Required for real SharePoint access. **If not set, the app runs in stub mode** with synthetic data.

### How to find your SharePoint Site ID

```
GET https://graph.microsoft.com/v1.0/sites?search=<your-site-name>
```

Or using the site hostname:

```
GET https://graph.microsoft.com/v1.0/sites/bayergroup.sharepoint.com:/sites/EstrategiaCRM
```

---

## Running locally

```bash
# Easiest – one script does everything:
bash start.sh

# Or with make:
make run

# Or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** in your browser for the Swagger UI.

---

## Quick demo (stub mode)

When Azure credentials are **not** configured the service returns synthetic stub data.  You can exercise the full workflow without any cloud dependencies:

```bash
# 1. Start the server (no .env needed)
uvicorn app.main:app --reload

# 2. List stub files
curl -s -X POST http://localhost:8000/sharepoint/list-folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "General/Reports"}' | python -m json.tool

# 3. Ingest the stub files
curl -s -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_ids": ["stub-001", "stub-002", "stub-003", "stub-004", "stub-005"]}' \
  | python -m json.tool

# 4. Summarize
curl -s -X POST http://localhost:8000/analysis/summarize \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

# 5. Ask a question
curl -s -X POST http://localhost:8000/analysis/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the CRM strategy?"}' | python -m json.tool
```

---

## Connecting to a real SharePoint site

### 1. Register an Azure App

1. Go to [Azure Portal → App registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps).
2. **New registration** → give it a name (e.g. `SharePoint-Agent`).
3. Under **Certificates & secrets** → create a client secret.  Copy it immediately.
4. Under **API permissions** → add:
   - `Microsoft Graph` → `Application permissions`:
     - `Sites.Read.All`
     - `Files.Read.All`
5. **Grant admin consent**.

### 2. Update `.env`

```
AZURE_TENANT_ID=<Directory (tenant) ID>
AZURE_CLIENT_ID=<Application (client) ID>
AZURE_CLIENT_SECRET=<the secret you copied>
SHAREPOINT_SITE_ID=<site id from Graph>
```

### 3. Verify

```bash
curl -s http://localhost:8000/health
```

---

## Supported file formats

| Extension | Category | Parser used |
|-----------|----------|-------------|
| `.txt`, `.md` | text | built-in |
| `.json` | json | built-in |
| `.csv` | csv | pandas |
| `.pdf` | pdf | pypdf |
| `.docx` | docx | python-docx |
| `.pptx` | pptx | python-pptx |
| `.xlsx`, `.xls` | xlsx | pandas + openpyxl |

Parser libraries are optional dependencies.  If a library is missing the endpoint returns a placeholder message explaining how to install it.

---

## MVP limitations and production roadmap

### Current MVP limitations

| Area | MVP behaviour | Production target |
|------|--------------|-------------------|
| **Authentication** | Client-credentials (app-only) via MSAL | Delegated user auth (OAuth2 PKCE) for per-user access control |
| **Document storage** | In-memory Python dict (lost on restart) | Persistent DB (PostgreSQL, Azure CosmosDB, etc.) |
| **Vector search** | Keyword frequency (TF-style) | Semantic embeddings + vector DB (pgvector, Azure AI Search, Pinecone) |
| **Summarisation** | First ~300 chars of document | LLM call (OpenAI GPT-4, Azure OpenAI) |
| **Q&A** | Keyword-matched chunk retrieval | RAG pipeline with LLM |
| **PPT generation** | Simple title + body slides | Branded template with charts, images, data tables |
| **Pagination** | Lists up to 200 files | Full Graph pagination (`@odata.nextLink`) |
| **Error handling** | Basic HTTP exceptions | Retry logic, circuit breakers, structured error codes |
| **Security** | CORS * (open) | Proper CORS origin list + API key / JWT auth |
| **Deployment** | Local only | Docker container + cloud hosting (Azure Container Apps, etc.) |

### Shared-link SharePoint access

The SharePoint link shared in the issue (`bayergroup.sharepoint.com/…`) uses a **sharing link**.  To access it programmatically:

1. **Preferred:** register an Azure app with `Sites.Read.All` + `Files.Read.All` permissions and use the site/drive/folder path approach (as implemented here).
2. **Alternative:** use Graph's [sharing link decode endpoint](https://learn.microsoft.com/en-us/graph/api/shares-get):  
   ```
   GET https://graph.microsoft.com/v1.0/shares/{base64-encoded-sharing-url}/driveItem/children
   ```
   This requires `Files.Read.All` on the app as well.

The second approach (stub-free) would only require setting the sharing URL instead of the full site/drive ids and is a simple extension to `SharePointService.list_folder`.
