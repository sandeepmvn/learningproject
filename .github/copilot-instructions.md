# Project Guidelines

## Stack And Scope
- Backend: FastAPI + SQLAlchemy 2.0 in [app/main.py](app/main.py) and [app/services.py](app/services.py).
- Frontend: React (Vite + Tailwind) in [frontend/src](frontend/src).
- Tests: API workflow tests in [tests/test_api.py](tests/test_api.py).
- CI/CD: GitHub Actions in [.github/workflows/ci.yml](.github/workflows/ci.yml) and [.github/workflows/cd.yml](.github/workflows/cd.yml).

## Build And Test
Use these commands unless a task explicitly needs a different workflow.

```bash
# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest tests/ -v --cov=app --cov-report=xml --cov-report=html

# Frontend
cd frontend
npm install
npm run dev
npm run lint
npm run build
```

## Architecture Boundaries
- Keep API route handlers in [app/main.py](app/main.py) thin; put business rules in [app/services.py](app/services.py).
- Keep persistence and session wiring in [app/database.py](app/database.py) and ORM models in [app/models.py](app/models.py).
- Keep request/response validation in [app/schemas.py](app/schemas.py).
- In the frontend, keep network calls in [frontend/src/api/client.js](frontend/src/api/client.js) and [frontend/src/api/trips.js](frontend/src/api/trips.js); keep pages/components focused on UI logic.

## Project Conventions
- Use SQLAlchemy 2.0 typed patterns (`Mapped[...]`, `mapped_column`, explicit relationships) to match [app/models.py](app/models.py).
- For money values, follow the Decimal rounding approach in [app/services.py](app/services.py) (`Decimal`, cent quantization, `ROUND_HALF_UP`); avoid float-based calculations.
- Return API errors via `HTTPException` with clear `detail` messages consistent with existing endpoints.
- Follow existing naming and file conventions: `.jsx` for React components/pages and `.js` for frontend utilities/API modules.

## Common Pitfalls
- Frontend `/api/*` calls rely on Vite dev proxy rewrite in [frontend/vite.config.js](frontend/vite.config.js); this is dev-server behavior, not automatic production routing.
- `get_db` depends on app lifespan-initialized session factory in [app/main.py](app/main.py) and [app/database.py](app/database.py); do not bypass this pattern.
- Local default DB is SQLite unless `DATABASE_URL` is provided; keep environment-specific DB behavior in mind when adding data migrations or tests.

## Documentation Links
- Project overview and local setup: [README.md](README.md)
- Docker usage and deployment details: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- Azure deployment details: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- Quick Azure CLI path: [AZURE_QUICK_START.md](AZURE_QUICK_START.md)
- GitHub Actions workflow behavior: [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)
