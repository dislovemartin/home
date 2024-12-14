#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to log messages
log() {
    local level=$1
    shift
    local color
    case "$level" in
        "INFO") color="$GREEN" ;;
        "WARN") color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        *) color="$NC" ;;
    esac
    echo -e "${color}[$level] $*${NC}"
}

# Function to determine docker compose command
get_docker_compose_cmd() {
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        echo ""
    fi
}

# Function to check required commands
check_requirements() {
    if ! command -v docker >/dev/null 2>&1; then
        log "ERROR" "Docker is not installed. Please install Docker and try again"
        exit 1
    fi

    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    if [ -z "$DOCKER_COMPOSE_CMD" ]; then
        log "ERROR" "Neither docker-compose nor docker compose is available"
        log "ERROR" "Please install Docker Compose and try again"
        log "INFO" "Installation guide: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    export DOCKER_COMPOSE_CMD
}

# Function to validate environment file
validate_env() {
    local required_vars=(
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_DB"
        "VITE_API_URL"
    )
    
    if [ ! -f .env ]; then
        log "WARN" ".env file not found. Creating from template..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log "INFO" "Created .env from .env.example"
        else
            log "ERROR" "No .env.example file found"
            exit 1
        fi
    fi
    
    # Source the .env file
    set -a
    source .env
    set +a
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "ERROR" "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
}

# Function to check Docker status
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log "ERROR" "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to deploy services
deploy_services() {
    log "INFO" "Building and starting services..."
    $DOCKER_COMPOSE_CMD down --remove-orphans || log "WARN" "Failed to stop existing services"
    $DOCKER_COMPOSE_CMD build --no-cache
    $DOCKER_COMPOSE_CMD up -d
}

# Function to wait for database
wait_for_db() {
    log "INFO" "Waiting for database to be ready..."
    local retries=30
    local count=0
    until $DOCKER_COMPOSE_CMD exec -T db pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -ge $retries ]; then
            log "ERROR" "Database failed to start after $retries attempts"
            exit 1
        fi
        log "INFO" "Waiting for database... (attempt $count/$retries)"
        sleep 2
    done
}

# Function to run migrations
run_migrations() {
    log "INFO" "Running database migrations..."
    if ! $DOCKER_COMPOSE_CMD exec -T backend ./backend migrate; then
        log "ERROR" "Failed to run database migrations"
        exit 1
    fi
}

# Main execution
main() {
    log "INFO" "Starting local deployment..."
    
    check_requirements
    validate_env
    check_docker
    deploy_services
    wait_for_db
    run_migrations
    
    log "INFO" "Services are running at:"
    echo "Frontend: http://localhost:5173"
    echo "Backend API: http://localhost:3000"
    echo "Database: postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB"
    
    log "INFO" "Deployment complete!"
    
    if [ -z "${STRIPE_PUBLIC_KEY:-}" ] || [ "$STRIPE_PUBLIC_KEY" = "pk_test_your_stripe_public_key" ]; then
        log "WARN" "Stripe keys not configured. Update them in .env for payment functionality"
    fi
}

# Run main function
main 