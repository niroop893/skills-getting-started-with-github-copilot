# Variables
TOOLBOX_API_CONTAINER = toolbox-api
CATALOG_WRITER_CONTAINER = catalog-writer

# Detect Windows/Git Bash environment
ifdef MSYSTEM
	SLEEP_CMD = sleep
	DOCKER_EXEC = docker exec
else
	SLEEP_CMD = sleep
	DOCKER_EXEC = docker exec
endif

.PHONY: help setup start stop test coverage clean status logs shell

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Simplified Digital Toolbox API Makefile"
	@echo "======================================="
	@echo ""
	@echo "Essential Commands:"
	@echo "  setup     - Complete environment setup (one-time)"
	@echo "  start     - Start all services (API, Celery, App)"
	@echo "  test      - Run all tests"
	@echo "  coverage  - Run tests with coverage report"
	@echo "  stop      - Stop all services"
	@echo "  clean     - Clean up environment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  status    - Show container and service status"
	@echo "  logs      - Show API container logs"
	@echo "  shell     - Open shell in API container"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup    # First time only"
	@echo "  make start    # Start everything"
	@echo "  make test     # Run tests"
	@echo "  make coverage # Run with coverage"

#
# Main Workflow Commands
#

# Complete environment setup
setup:
	@echo "🚀 Setting up Digital Toolbox API environment..."
	@echo "Starting Docker containers..."
	docker compose up -d
	@echo "Waiting for containers to initialize..."
	$(SLEEP_CMD) 10
	@echo "Installing dependencies..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && pip install -r requirements-dev.txt"
	$(DOCKER_EXEC) $(CATALOG_WRITER_CONTAINER) bash -c "cd /app && pip install flask requests"
	@echo "Setting up Redis..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && apt-get update && apt-get install -y redis-server procps lsof"
	@echo "Starting Redis..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && redis-server --daemonize yes"
	@echo ""
	@echo "✅ Setup complete! Next step: make start"

# Start all services
start:
	@echo "🔄 Starting all services..."
	@echo "Ensuring Redis is running..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && redis-server --daemonize yes || true"
	@echo "Creating required directories..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "mkdir -p /var/www/digitaltoolbox-repository && cp /app/categories.json /var/www/digitaltoolbox-repository/categories.json"
	@echo "Starting Celery worker..."
	$(DOCKER_EXEC) -d $(TOOLBOX_API_CONTAINER) bash -c "cd /app && nohup celery -A src.digitaltoolbox.celery_tasks worker -l info > celery.log 2>&1 &"
	@echo "Starting Flask API..."
	$(DOCKER_EXEC) -d $(TOOLBOX_API_CONTAINER) bash -c "cd /app && nohup python -m src.digitaltoolbox --port 8082 > api.log 2>&1 &"
	@echo "Starting catalog writer app..."
	$(DOCKER_EXEC) -d $(CATALOG_WRITER_CONTAINER) bash -c "cd /app && python app.py" || true
	@echo "Waiting for services to initialize..."
	$(SLEEP_CMD) 15
	@echo ""
	@echo "✅ Services started!"
	@echo "Testing API connectivity..."
	@curl -f http://localhost:8082/user 2>/dev/null && echo "✅ API is responding!" || echo "⚠️  API not ready yet, wait a moment and try 'make status'"

# Update these if they exist in your Makefile:
install-test:
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && pip install pytest pytest-cov coverage"
	docker exec $(TOOLBOX_API_CONTAINER) bash -c "cd /app && python -m pytest tests -v"

test:
	docker exec $(TOOLBOX_API_CONTAINER) bash -c "cd /app && python -m pytest tests -v"

test-coverage:
	docker exec $(TOOLBOX_API_CONTAINER) bash -c "cd /app && python -m pytest --cov=src --cov-report=html --cov-report=term-missing tests -v"

install-test-coverage:
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "cd /app && pip install pytest pytest-cov coverage"
	docker exec $(TOOLBOX_API_CONTAINER) bash -c "cd /app && python -m pytest --cov=src --cov-report=html --cov-report=term-missing tests -v"
# Stop all services
stop:
	@echo "🛑 Stopping services..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "pkill -f celery" 2>/dev/null || true
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "pkill -f 'python -m src.digitaltoolbox'" 2>/dev/null || true
	$(DOCKER_EXEC) $(CATALOG_WRITER_CONTAINER) bash -c "pkill -f 'python app.py'" 2>/dev/null || true
	docker compose down
	@echo "✅ Services stopped!"

# Clean up environment
clean:
	@echo "🧹 Cleaning up..."
	make stop
	docker compose down -v
	docker system prune -f
	rm -rf htmlcov/ .coverage .pytest_cache/
	@echo "✅ Cleanup completed!"

#
# Utility Commands
#

# Show status
status:
	@echo "📊 System Status"
	@echo "==============="
	@echo ""
	@echo "Docker Containers:"
	docker ps --filter "name=$(TOOLBOX_API_CONTAINER)" --filter "name=$(CATALOG_WRITER_CONTAINER)"
	@echo ""
	@echo "API Health Check:"
	@curl -f http://localhost:8082/user 2>/dev/null && echo "✅ API is healthy" || echo "❌ API not responding"
	@echo ""
	@echo "Service Processes:"
	@echo "API Container:"
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) ps aux | grep -E "(celery|python)" | grep -v grep || echo "  No services running"
	@echo "App Container:"
	$(DOCKER_EXEC) $(CATALOG_WRITER_CONTAINER) ps aux | grep python | grep -v grep || echo "  No services running"

# Show logs
logs:
	@echo "📋 Showing API container logs (press Ctrl+C to exit)..."
	docker logs -f $(TOOLBOX_API_CONTAINER)

# Open shell
shell:
	@echo "🐚 Opening shell in API container..."
	docker exec -it $(TOOLBOX_API_CONTAINER) bash

#
# Development Shortcuts
#

# Restart services only
restart:
	@echo "🔄 Restarting services..."
	$(DOCKER_EXEC) $(TOOLBOX_API_CONTAINER) bash -c "(pkill -f celery || true) && (pkill -f 'python -m src.digitaltoolbox' || true)"
	$(DOCKER_EXEC) $(CATALOG_WRITER_CONTAINER) bash -c "pkill -f 'python app.py'" 2>/dev/null || true
	$(SLEEP_CMD) 5
	make start

# Development workflow
dev: setup start
	@echo "🎯 Development environment ready!"
	@echo "Run 'make test' or 'make coverage' to verify everything works"