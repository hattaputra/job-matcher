.PHONY: install run dev docker-build docker-up docker-down lint clean help

help:
	@echo "Job Matcher API - Available commands:"
	@echo ""
	@echo "  make install       Install dependencies"
	@echo "  make run           Run API in production mode"
	@echo "  make dev           Run API in development mode (auto-reload)"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start with Docker Compose"
	@echo "  make docker-down   Stop Docker Compose"
	@echo "  make lint          Run code linter"
	@echo "  make clean         Remove cache files"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

lint:
	pip install ruff --quiet
	ruff check app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
