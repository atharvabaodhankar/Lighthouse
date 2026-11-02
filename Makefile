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
	$(PYTHON) -m compileall app/ scripts/ tests/
	@$(PYTHON) -c "import ruff" 2>/dev/null && $(PYTHON) -m ruff check . || echo "Ruff check skipped (ruff optional dependency not installed)"

format:
	@$(PYTHON) -c "import black" 2>/dev/null && $(PYTHON) -m black app/ scripts/ tests/ || echo "Black format skipped (black optional dependency not installed)"

docker-build:
	docker build -t lighthouse-dashboard:latest .

docker-up:
	docker compose -f docker-compose.dashboard.yml up -d

docker-down:
	docker compose -f docker-compose.dashboard.yml down

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]') if p.is_file()]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('*.egg-info')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('build')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('dist')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('.pytest_cache')]"

