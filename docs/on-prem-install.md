# On-Premise Installation

Deploy Transport Coordinator on a production company's own hardware.

## Requirements

- Docker Desktop (or Docker Engine + Compose)
- Python 3.12+ (for database migrations)
- Node.js 22+ (for web UI development build)

## Quick install

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:

1. Build and start API, PostgreSQL (PostGIS), and Redis via Docker
2. Run Alembic migrations
3. Print URLs for API and web UI

## Manual steps

```bash
# Infrastructure + API
docker compose -f docker/compose.yml up -d --build

# Migrations
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e "packages/solver" -e "packages/geospatial" -e "apps/api"
make migrate

# Web coordinator + driver PWA
cd apps/web && npm install && npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Coordinator dashboard | http://localhost:5173 |
| Driver PWA | http://localhost:5173/driver |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## Production build (web)

```bash
cd apps/web
npm run build
# Serve dist/ behind nginx or Caddy alongside the API
```

## Environment

Copy `.env.example` to `.env` and adjust:

- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Redis for distance matrix cache
- `CORS_ORIGINS` — web UI origin(s)
- `AI_ENABLED=false` — keep off unless running Ollama (Phase 3)

## Air-gapped studios

For networks without internet:

1. Pre-build Docker images on a connected machine
2. Self-host Nominatim + OSRM (Phase 6)
3. Set `AI_ENABLED=false`

## Upgrades

```bash
git pull
docker compose -f docker/compose.yml up -d --build
source .venv/bin/activate && make migrate
```
