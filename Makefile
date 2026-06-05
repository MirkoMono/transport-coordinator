.PHONY: dev infra api web test lint

infra:
	docker compose -f docker/compose.yml -f docker/compose.dev.yml up -d postgres redis

api:
	cd apps/api && uvicorn transport_api.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	pip install -e "packages/solver[dev]" -e "packages/geospatial[dev]" -e "apps/api[dev]"
	pytest packages/solver packages/geospatial apps/api -q

lint:
	ruff check packages/solver packages/geospatial apps/api
	cd apps/web && npm run typecheck

dev: infra
	@echo "Infra ready. Run 'make api' and 'make web' in separate terminals."
