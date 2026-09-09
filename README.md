# Visual Wiring Definition Tool

Visual Wiring Definition Tool is an engineering MVP for defining reusable component pinouts, placing component instances on a React Flow canvas, connecting exact pins, validating the resulting topology, and exporting interface definitions. Component templates and saved projects—not spreadsheets—are the source of truth.

## Architecture

```text
Component Library → ComponentTemplate → ComponentInstance → React Flow
                                                        ↓
FastAPI + SQLite ← saved Project + pin references ← Connections
        ├── deterministic Rule Engine
        ├── pin-level NetworkX Graph Engine
        └── validated CSV / Excel export
```

- Frontend: React, TypeScript, Vinext/Next-compatible App Router, `@xyflow/react`.
- Backend: FastAPI, Pydantic, SQLite, NetworkX, pandas, openpyxl.
- Rules: [`backend/app/rules.json`](backend/app/rules.json), loaded by both the backend validator and the frontend instant-check API.
- Persistence: [`backend/wiring.db`](backend/wiring.db) by default; the file is runtime data and is not committed.

## Data model

- `ComponentTemplate` owns Connector and Pin definitions. A Pin contains `number`, `name`, `type`, `direction`, and `allow_multiple`.
- `ComponentInstance` references `template_id` and stores its React Flow `position`.
- `Connection` contains only an ID and two Endpoint references. It never duplicates signal/type metadata.
- `Project` owns its name, instances, connections, ID, and timestamps.

## Run locally

Backend (Python 3.11+):

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn app.main:app --reload --app-dir backend --port 8000
```

Frontend, in another terminal:

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env.local` if the API is not at `http://localhost:8000/api`. API documentation is available at `http://localhost:8000/docs`.

## Complete workflow

1. Select **+** in Component Library to create a template. Define one or more connectors and set Pin count; the table creates all rows at once for bulk editing.
2. Edit Pin name, type, direction, and multiple-connection behavior directly in the table. Templates can also be imported/exported as JSON.
3. Create or open a project, then drag templates onto the canvas. Double-clicking a library item also creates an instance.
4. Expand/collapse connectors or search pins inside a large 32/33-pin node. Drag between exact Pin handles to connect them.
5. Select **Save & Validate**. Instances, positions, and connections are written to SQLite, then the authoritative backend validator runs.
6. Fix violations from the Validation panel; selecting a connection violation focuses its edge.
7. After validation passes, export CSV or formatted Excel from the header. Export endpoints validate the saved project again before returning a file.

Refreshing or reopening the browser restores saved templates, projects, node positions, and connections from SQLite.

## Validation

The deterministic engine checks endpoint existence, configured Pin-type compatibility, direction, duplicate incoming connections with `allow_multiple`, cycles, disconnected components, required paths, and configurable sequential chains. The graph contains unique Pin Endpoint nodes and connection edges; a component projection is used only for topology-level cycle/path checks.

Sequential chains are generic rules. The demo configuration validates numeric BIC ordering from `P2` to `P1`, detecting skipped members, missing links, duplicate inputs, and loops without hard-coding BIC logic in Python.

Run the tests:

```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q
npm test
```

The backend suite covers valid CAN, type mismatches, NTC/GPIO, 12V/5V, missing pins, duplicate inputs, `allow_multiple`, cycles, sequential chains, path validation, SQLite reopen, and CSV export.

## API

Main resources:

- `GET/POST /api/component-templates`
- `GET/PUT/DELETE /api/component-templates/{id}`
- `POST /api/component-templates/import`
- `GET/POST /api/projects`
- `GET/PUT/DELETE /api/projects/{id}`
- `POST /api/projects/{id}/validate`
- `GET /api/projects/{id}/export/csv`
- `GET /api/projects/{id}/export/excel`

AI, RAG, Neo4j, and agent frameworks are deliberately outside this MVP. A future review layer can propose candidate definitions and rules, but deterministic validation remains authoritative.
