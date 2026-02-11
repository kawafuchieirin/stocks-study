.PHONY: install install-backend install-frontend dev dev-backend dev-frontend test lint

# Python実行パス
PYTHON := cd backend && poetry run python
UVICORN := cd backend && poetry run uvicorn

install: install-backend install-frontend

install-backend:
	cd backend && poetry install

install-frontend:
	cd frontend && npm install

dev:
	@echo "バックエンド(8080)とフロントエンド(5173)を同時起動..."
	$(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend:
	$(UVICORN) app.main:app --reload --port 8080

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && poetry run pytest tests/ -v

lint:
	cd backend && poetry run ruff check app/ tests/
	cd backend && poetry run ruff format --check app/ tests/
	cd backend && poetry run mypy app/

format:
	cd backend && poetry run ruff check --fix app/ tests/
	cd backend && poetry run ruff format app/ tests/
