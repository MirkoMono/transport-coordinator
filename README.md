# Transport Coordinator

Film production transport coordinator with VRP optimization. Assign crew pickups across vehicles, minimize transit time, and generate driver manifests.

**License:** Apache 2.0 (open-core community edition)

## Quick Start (demo on your Mac — no Docker)

### Prerequisites

- Python 3.12+
- Node.js 22+

```bash
git clone https://github.com/MirkoMono/transport-coordinator.git
cd transport-coordinator
make setup-local    # once
./scripts/start.sh  # opens http://localhost:5173
```

**Desktop shortcut (macOS):** `make desktop` — adds Start/Stop icons to your Desktop.

**Swedish demo manual:** [docs/demo-manual-sv.md](docs/demo-manual-sv.md) · **Share with others:** [docs/dela-appen.md](docs/dela-appen.md)

**Mobile test (same Wi‑Fi):** `./scripts/start.sh --mobile` — open the printed URL on your phone.

Stop: `./scripts/stop.sh` or `make stop`

---

### Full stack (Docker)

- Docker & Docker Compose

### 1. Start infrastructure

```bash
make infra
```

Starts PostgreSQL (PostGIS) and Redis.

### 2. Run API

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e "packages/solver[dev]" -e "packages/geospatial[dev]" -e "packages/ai[dev]" -e "apps/api[dev]"
make api
```

API: http://localhost:8000 — docs at http://localhost:8000/docs

Run database migrations (with infra running):

```bash
make migrate
```

### 3. Run web UI

```bash
cd apps/web && npm install && npm run dev
```

Web: http://localhost:5173

### Full Docker stack

```bash
docker compose -f docker/compose.yml up --build
```

## Project Structure

```
apps/
  api/          FastAPI backend
  web/          React coordinator dashboard (PWA-ready)
packages/
  solver/       OR-Tools VRP solver
docker/         Compose files and Dockerfiles
memory.md       Persistent dev context (read first each session)
```

## Development

```bash
make test    # Run Python tests
make lint    # Ruff + TypeScript check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions.

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| 0 | ✅ Done | Monorepo, Docker, CI, UI shell |
| 1 | ✅ Done | OR-Tools solver, geocoding, map UI, Redis cache, PDF manifests |
| 2 | ✅ Done | Driver PWA, route diff, call-time, locked re-optimize, ICS |
| 3 | 🚧 In progress | Address geocoding, AI call-sheet parse (Gemma/Ollama) |
| 4 | Planned | Open source release (GHCR, demo GIF) |

Full plan in [memory.md](memory.md).
