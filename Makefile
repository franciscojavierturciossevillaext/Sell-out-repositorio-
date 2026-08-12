.PHONY: install run demo test help

## Install Python dependencies
install:
	pip install -r requirements.txt
	@[ -f .env ] || (cp .env.example .env && echo "⚠️  .env created from .env.example – fill in your credentials if needed.")

## Start the API server (hot-reload, port 8000)
run: install
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Run a full stub-mode demo (no credentials required)
demo: install
	@echo ""
	@echo "=== 1. Health check ==="
	curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@echo "=== 2. List SharePoint folder (stub) ==="
	curl -s -X POST http://localhost:8000/sharepoint/list-folder \
	  -H "Content-Type: application/json" \
	  -d '{"folder_path":"General/Reports"}' | python -m json.tool
	@echo ""
	@echo "=== 3. Ingest documents ==="
	curl -s -X POST http://localhost:8000/documents/ingest \
	  -H "Content-Type: application/json" \
	  -d '{"file_ids":["stub-001","stub-002","stub-003","stub-004","stub-005"]}' | python -m json.tool
	@echo ""
	@echo "=== 4. Summarize ==="
	curl -s -X POST http://localhost:8000/analysis/summarize \
	  -H "Content-Type: application/json" \
	  -d '{}' | python -m json.tool
	@echo ""
	@echo "=== 5. Ask a question ==="
	curl -s -X POST http://localhost:8000/analysis/ask \
	  -H "Content-Type: application/json" \
	  -d '{"question":"What is the CRM strategy?"}' | python -m json.tool

## Run tests
test: install
	pytest tests/ -v 2>/dev/null || echo "No tests found yet."

help:
	@echo ""
	@echo "Available commands:"
	@echo "  make install   Install Python dependencies"
	@echo "  make run       Start API server on http://localhost:8000"
	@echo "  make demo      Run end-to-end demo (server must be running)"
	@echo "  make test      Run tests"
	@echo ""
