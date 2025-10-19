# SuperTickets.AI Makefile

.PHONY: help install test lint format clean build run docker-build docker-run setup-dev

# Default target
help:
	@echo "SuperTickets.AI - Available commands:"
	@echo "  install      Install dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the application"
	@echo "  run          Run the application locally"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  setup-dev    Setup development environment"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	pytest tests/ -v --cov=mcp_service --cov-report=html --cov-report=term-missing

# Run specific test file
test-kb:
	pytest tests/test_kb_lookup.py -v

test-tickets:
	pytest tests/test_create_ticket.py -v

test-email:
	pytest tests/test_send_email.py -v

test-integration:
	pytest tests/test_integration.py -v

# Run linting
lint:
	flake8 mcp_service tests
	mypy mcp_service
	bandit -r mcp_service

# Format code
format:
	black mcp_service tests
	isort mcp_service tests

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build the application
build: clean
	python setup.py sdist bdist_wheel

# Run the application locally
run:
	uvicorn mcp_service.main:app --host 0.0.0.0 --port 8000 --reload

# Run in production mode
run-prod:
	uvicorn mcp_service.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker commands
docker-build:
	docker build -t supertickets-ai .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f supertickets-ai

# Development setup
setup-dev: install
	pre-commit install
	mkdir -p credentials logs
	cp .env.example .env
	@echo "Development environment setup complete!"
	@echo "Please edit .env file with your credentials"

# Database setup
setup-db:
	python -c "from mcp_service.utils.supabase_client import create_supabase_tables; print('\\n'.join(create_supabase_tables()))"

# Load knowledge base
load-kb:
	python -c "from mcp_service.utils.embedding_search import EmbeddingSearch; from mcp_service.utils.supabase_client import get_supabase_client; import asyncio; asyncio.run(EmbeddingSearch(get_supabase_client()).load_knowledge_from_json('.kiro/kb/knowledge.json'))"

# Health check
health:
	curl -f http://localhost:8000/health || echo "Service not running"

# API documentation
docs:
	@echo "API Documentation available at:"
	@echo "  Swagger UI: http://localhost:8000/docs"
	@echo "  ReDoc: http://localhost:8000/redoc"

# Security scan
security:
	safety check
	bandit -r mcp_service

# Performance test
perf-test:
	@echo "Running performance tests..."
	# Add performance testing commands here

# Backup
backup:
	@echo "Creating backup..."
	# Add backup commands here

# Deploy
deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands

deploy-prod:
	@echo "Deploying to production..."
	# Add production deployment commands

# Monitoring
monitor:
	@echo "Monitoring endpoints:"
	@echo "  Health: http://localhost:8000/health"
	@echo "  Metrics: http://localhost:9090 (Prometheus)"
	@echo "  Dashboard: http://localhost:3000 (Grafana)"

# Update dependencies
update-deps:
	pip-compile requirements.in
	pip install -r requirements.txt

# Generate API client
generate-client:
	@echo "Generating API client..."
	# Add API client generation commands

# Run all checks
check-all: lint test security
	@echo "All checks passed!"