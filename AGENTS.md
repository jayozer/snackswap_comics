# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/` houses FastAPI code: `api/` (routes), `core/` (settings + env), `services/` (scoring, retrieval, rendering), `models/` (Pydantic schemas), entrypoint `main.py`.
- Data + assets live in `data/seeds/seed_data.py`, `backend/storage/`, and `backend/images/`; architecture notes and plans are in `docs/`.
- Frontend uses Next.js/TypeScript in `frontend/` with `src/` for app code and `public/` for static assets.

## Build, Test, and Development Commands
- Backend setup: `cd backend && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt` (or `uv pip install -e ".[dev]"` for tooling). Copy env: `cp .env.example .env`.
- Qdrant Cloud is pre-configured in `.env` (QDRANT_URL and QDRANT_API_KEY). No local setup needed.
- Seed vectors: `cd backend && ./seed_data.sh` (requires `.env` + running Qdrant).
- Run API with reload: `cd backend && ./run_server.sh`.
- Gemini smoke test: `cd backend && python test_gemini.py` (verifies API key + SDKs).
- Frontend: `cd frontend && npm install && npm run dev`; prod build `npm run build && npm start`; lint `npm run lint`.

## Coding Style & Naming Conventions
- Python: 4-space indent, Black/Ruff config (line length 100); prefer type hints, snake_case modules/functions, PascalCase Pydantic models/classes. Keep FastAPI endpoints thin and push logic into `services/`.
- Frontend: TypeScript + Next 14; components in `src/` use PascalCase filenames and default exports; favor functional components/hooks; Tailwind utility classes live on JSX nodes with shared tokens in `tailwind.config.js`.
- Env hygiene: do not commit `.env`; update `.env.example` when adding keys.

## Testing Guidelines
- Backend uses pytest (dev extra). Name files `test_*.py` mirroring modules under `backend/tests` or alongside services. Focus on deterministic units (scoring, data transforms) and integration stubs against Qdrant fixtures. Use `pytest-asyncio` for async routes; optional `pytest --cov=app` for coverage.
- Frontend: no formal tests yet; at minimum run `npm run lint` before PRs.

## Commit & Pull Request Guidelines
- Commits follow Conventional Commit prefixes seen in history (`feat`, `chore`, `docs`, etc.); keep scopes concise (e.g., `feat: add swap scoring weights`).
- PRs include summary, linked issue, risk/rollback notes, and testing proof (commands or UI screenshots). Flag changes needing new env vars or data migrations (`seed_data.py`). Keep PRs small and call out API contract or docs impacts.

## Security & Configuration Tips
- Required env keys: `GEMINI_API_KEY`, `QDRANT_URL`, `GEMINI_VISION_MODEL`, `GEMINI_WRITER_MODEL`, `MAX_UPLOAD_SIZE_MB`. Store secrets locally only; rotate keys used in `test_gemini.py` checks. Default dev URLs bind to localhost—avoid exposing ports publicly.
