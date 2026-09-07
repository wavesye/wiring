# Visual Wiring API

Run locally with `uvicorn app.main:app --reload --app-dir backend`. API docs are available at `/docs`.

The server treats templates, instances, and pin references as the source of truth. Both export endpoints run authoritative validation before producing files.
