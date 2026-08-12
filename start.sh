#!/usr/bin/env bash
# start.sh – One-command startup for the SharePoint Document Agent
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   SharePoint Document Agent – Startup   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Install / verify dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q
echo "   ✅ Dependencies ready."

# 2. Create .env from example if missing
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  .env file created from .env.example."
  echo "   The server will start in STUB MODE (no real SharePoint calls)."
  echo "   To connect to SharePoint, edit .env and fill in:"
  echo "     AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, SHAREPOINT_SITE_ID"
fi

echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "   API docs → http://localhost:8000/docs"
echo ""

# 3. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
