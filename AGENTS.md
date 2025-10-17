# Repository Guidelines

## Project Structure & Module Organization
- Root contains the master dataset (`train.parquet`), top-level documentation, the dual-launch helper `start_apps.sh`, and the integration harness `test_api.py`.
- `legal-dashboard/` holds the full-stack app: `src/` for the React UI (components, assets, theme), `api_server.py` for the Flask API, `public/` for static assets, and `batches.db` for batch history.
- Data utilities live in `utils/` (`add_samples.py`, `clean_parquet.py`, `analyze_tokens.py`) and support dataset maintenance and curation.
- `raw/` stores reference legal text used to seed topics; edit only when curating source material to avoid drift from published training data.

## Build, Test, and Development Commands
- Install frontend dependencies with `cd legal-dashboard && npm install`; backend runtime packages: `pip3 install flask flask-cors flask-sqlalchemy polars groq tiktoken`.
- Local development: run `python3 api_server.py` for the API and `npm run dev` for the UI; `./start_apps.sh` starts both, frees conflicting ports, and tails logs.
- Production bundle: `npm run build`; verify output with `npm run preview` before deployment.
- Execute the API regression suite from the repo root: `python3 test_api.py` (ensure the API is already running).

## Coding Style & Naming Conventions
- JavaScript/JSX uses 2-space indentation, functional components in PascalCase (e.g., `DatasetTable`), hooks/utilities in camelCase, and Material UI theming under `theme/`. Run `npm run lint` to enforce ESLint rules (React Hooks, Refresh, no unused vars).
- Python modules follow 4-space indentation, `snake_case` functions, uppercase constants for configuration (`REQUEST_DELAY`), and prefer type hints + docstrings as shown in `api_server.py`. Utility scripts should emit clear console summaries when run.
- Dataset identifiers follow `practice_area_topic_index` (e.g., `contract_law_formation_001`); keep new IDs unique and descriptive.

## Testing Guidelines
- `test_api.py` covers 34 integration checks across health, stats, search, batch, and import flows; keep it green before pushing.
- When extending endpoints, add focused cases inside `test_api.py` via the shared `test_endpoint` helper and adjust expected fields to match new responses.
- Validate data scripts with a small copy of `train.parquet` before bulk runs to avoid corrupting the canonical file.

## Commit & Pull Request Guidelines
- Maintainers follow short, imperative Conventional Commits with optional scope, e.g., `feat(api): add circuit breaker metrics`; match that style and reference tickets or issue IDs in the body.
- Pull requests should link to the dataset/UI change being validated, note the commands executed (`python3 test_api.py`, manual UI smoke steps), and attach screenshots or curl transcripts whenever responses or visuals change.

## Security & Configuration Tips
- Never commit real Groq API keys; replace the placeholder in `api_server.py` with an environment variable (e.g., export `GROQ_API_KEY` and load it at startup).
- Treat `train.parquet` as the system of record—back it up before bulk edits and avoid introducing sensitive client data into `raw/` or generated artifacts.
