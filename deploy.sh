#!/bin/bash
set -e

# Function to display script usage
usage() {
    echo "Usage: $0 [-e <environment>]"
    echo "  -e    Environment (dev/prod), defaults to dev"
    exit 1
}

# Default values
ENV="dev"

# Parse command line arguments
while getopts "e:h" opt; do
    case $opt in
        e) ENV="$OPTARG" ;;
        h) usage ;;
        ?) usage ;;
    esac
done

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    echo "Error: Environment must be either 'dev' or 'prod'"
    exit 1
fi

echo "Deploying in $ENV environment..."

# Prepare SQLx for offline mode
if [[ "$ENV" == "prod" ]]; then
    echo "Preparing SQLx for offline mode..."
    cd backend
    ./prepare.sh
    cd ..
fi

# Choose the appropriate compose file
COMPOSE_FILE="docker-compose.yml"
if [[ "$ENV" == "prod" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# Stop any running containers
echo "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start fresh
echo "Starting containers..."
if [[ "$ENV" == "prod" ]]; then
    docker-compose -f $COMPOSE_FILE up -d --build
else
    docker-compose -f $COMPOSE_FILE up --build
fi

echo "Deployment complete!" 