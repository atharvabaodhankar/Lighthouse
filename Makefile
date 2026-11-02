.PHONY: help install dev test lint format clean docker-build docker-up docker-down

PYTHON ?= python
PIP ?= pip

help:
	@echo "Lighthouse — Production-Grade DNS Shield & Traffic Intelligence"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install production and dev dependencies"
	@echo "  make dev            Run local FastAPI development server"
	@echo "  make test           Run automated test suite (unittest)"
	@echo "  make lint           Run linting check"
	@echo "  make format         Auto-format code"
	@echo "  make docker-build   Build Lighthouse dashboard container"
	@echo "  make docker-up      Start Docker Compose stack"
	@echo "  make docker-down    Stop Docker Compose stack"
	@echo "  make clean          Clean temporary files and cache artifacts"

install:
	$(PIP) install -r requirements.txt

dev:
	$(PYTHON) run.py

test:
	$(PYTHON) -m unittest discover tests -v

lint:
	$(PYTHON) -m ruff check . || echo "Ruff not installed, running syntax check" && $(PYTHON) -m compileall app/ tests/

format:
	$(PYTHON) -m black app/ tests/ || echo "Black not installed"

docker-build:
	docker build -t lighthouse-dashboard:latest .

docker-up:
	docker compose -f docker-compose.dashboard.yml up -d

docker-down:
	docker compose -f docker-compose.dashboard.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache build dist *.egg-info 2>/dev/null || true
