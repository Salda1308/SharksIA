# Generador de Diseños — Project Instructions

## Commit Rules
- **NEVER** add "Co-Authored-By: Claude" or any reference to Claude in commit messages
- **NEVER** add any AI tool attribution to commits
- Keep commit messages clean and concise

## Project Overview
Python CLI + FastAPI + Next.js web platform for generating Instagram carousels using Ollama (local AI), Jinja2 SVG templates, and export to PDF/SVG/JPG.

## Stack
- **Backend:** FastAPI on :8000, SQLAlchemy 2.0, SQLite at `storage/db.sqlite3`
- **Frontend:** Next.js 16 App Router (TypeScript + Tailwind) on :3000
- **AI:** Ollama local (`llama3.2`) via `core/ai.py`
- **Renderer:** Jinja2 SVG templates + cairosvg for PDF export

## Running Locally
```bash
# Requires Ollama running: ollama serve
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m uvicorn api.main:app --reload --port 8000
cd web && npm run dev
```

## Key Directories
- `api/` — FastAPI routes, models, auth
- `core/` — AI generation, SVG rendering (shared by CLI and API)
- `formats/carousel/` — Jinja2 templates and prompts
- `web/` — Next.js frontend
- `storage/` — DB, uploads, tmp renders (not committed)

## Environment
Copy `.env.example` to `.env` and fill in `JWT_SECRET` at minimum. Set `DYLD_LIBRARY_PATH=/opt/homebrew/lib` for cairosvg on macOS with Homebrew cairo.
