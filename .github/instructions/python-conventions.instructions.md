---
description: "Use when creating or editing Python files in this FastAPI project. Covers SQLAlchemy 2.0 typing patterns, service-layer business rules, schema boundaries, and API error consistency."
name: "Python Backend Conventions"
applyTo: "**/*.py"
---
# Python Backend Conventions

- Keep route handlers in app/main.py thin and focused on request and response orchestration.
- Put business rules and calculations in app/services.py, not in route functions.
- Keep persistence and session wiring in app/database.py and ORM models in app/models.py.
- Keep request and response validation in app/schemas.py.

- Use SQLAlchemy 2.0 typed patterns in models:
  - Use Mapped[...] type annotations.
  - Use mapped_column for fields.
  - Use explicit relationship declarations.

- For money values, use Decimal with cent quantization and ROUND_HALF_UP.
- Avoid float-based currency math.

- Return API errors with HTTPException and clear detail messages that match existing endpoint style.
- Follow existing naming and structure conventions already used in the repository.

- Keep changes small and localized.
- Avoid moving logic across files unless the task specifically requires it.
