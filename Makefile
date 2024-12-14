.PHONY: dev test build migrate clean deploy deploy-local deploy-prod install lint help

# Development
dev:
	docker-compose up --build

# Testing
test:
	cd backend && cargo test
	cd frontend && npm test

# Building
build:
	cd backend && cargo build --release
	cd frontend && npm run build

# Database
migrate:
	cd backend && cargo sqlx migrate run

# Deployment
deploy-local:
	./deploy/deploy.sh -e local

deploy-prod:
	./deploy/deploy.sh -e prod

deploy-backend:
	./deploy/deploy.sh -c backend -e $(ENV)

deploy-frontend:
	./deploy/deploy.sh -c frontend -e $(ENV)

# Installation
install:
	cd frontend && npm install
	cd backend && cargo build

# Linting
lint:
	cd backend && cargo clippy -- -D warnings
	cd frontend && npm run lint

# Cleanup
clean:
	docker-compose down -v
	cd backend && cargo clean
	cd frontend && rm -rf node_modules dist

# Help
help:
	@echo "Available commands:"
	@echo "  make dev              - Start development environment"
	@echo "  make test             - Run all tests"
	@echo "  make build            - Build for production"
	@echo "  make migrate          - Run database migrations"
	@echo "  make deploy-local     - Deploy locally"
	@echo "  make deploy-prod      - Deploy to production"
	@echo "  make deploy-backend   - Deploy backend (ENV=local|prod)"
	@echo "  make deploy-frontend  - Deploy frontend (ENV=local|prod)"
	@echo "  make install          - Install dependencies"
	@echo "  make lint             - Run linters"
	@echo "  make clean            - Clean up build artifacts"