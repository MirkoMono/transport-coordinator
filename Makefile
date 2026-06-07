.PHONY: dev setup infra api web test lint migrate ai start stop desktop

start:
	@chmod +x scripts/*.sh scripts/*.command 2>/dev/null || chmod +x scripts/*.sh
	@./scripts/start.sh

stop:
	@chmod +x scripts/stop.sh
	@./scripts/stop.sh

desktop:
	@chmod +x scripts/install-desktop-shortcut.sh scripts/*.command scripts/*.sh
	@./scripts/install-desktop-shortcut.sh

infra:
	@command -v docker >/dev/null 2>&1 || (echo "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" && echo "Or run without Docker: make setup-local" && exit 1)
	docker compose -f docker/compose.yml -f docker/compose.dev.yml up -d postgres redis

migrate:
	cd apps/api && alembic upgrade head

api:
	cd apps/api && uvicorn transport_api.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

ai:
	@command -v docker >/dev/null 2>&1 || (echo "Docker required for Ollama profile" && exit 1)
	docker compose -f docker/compose.yml -f docker/compose.ai.yml --profile ai up -d ollama
	@echo "Pull Gemma: docker compose -f docker/compose.yml -f docker/compose.ai.yml exec ollama ollama pull gemma2:2b"
	@echo "Set AI_ENABLED=true in .env and restart API"

test:
	pip install -e "packages/solver[dev]" -e "packages/geospatial[dev]" -e "packages/ai[dev]" -e "apps/api[dev]"
	pytest packages/solver packages/geospatial packages/ai apps/api -q

lint:
	ruff check packages/solver packages/geospatial packages/ai apps/api
	cd apps/web && npm run typecheck

dev: infra
	@echo "Infra ready. Run 'make api' and 'make web' in separate terminals."

setup:
	@chmod +x scripts/*.sh
	@./scripts/dev-setup.sh

setup-local:
	@chmod +x scripts/*.sh
	@./scripts/dev-no-docker.sh
