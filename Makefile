.PHONY: dev api web test test-api

dev:
	@echo "Iniciando API y Web..."
	uvicorn api.main:app --reload --port 8000 & \
	cd web && npm run dev

api:
	uvicorn api.main:app --reload --port 8000

web:
	cd web && npm run dev

test:
	pytest tests/ -v

test-api:
	pytest tests/api/ -v
