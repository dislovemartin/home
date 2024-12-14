#!/bin/bash
set -e

# Load configuration
source "$(dirname "$0")/config.sh"

# Parse command line arguments
ENVIRONMENT="local"
COMPONENT="all"

print_usage() {
    echo "Usage: $0 [-e environment] [-c component]"
    echo "  -e: Environment (local/prod) [default: local]"
    echo "  -c: Component (all/frontend/backend) [default: all]"
    exit 1
}

while getopts "e:c:h" opt; do
    case $opt in
        e) ENVIRONMENT="$OPTARG" ;;
        c) COMPONENT="$OPTARG" ;;
        h) print_usage ;;
        \?) print_usage ;;
    esac
done

# Validate environment
if [ "$ENVIRONMENT" != "local" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "Error: Invalid environment. Must be 'local' or 'prod'"
    exit 1
fi

# Validate component
if [ "$COMPONENT" != "all" ] && [ "$COMPONENT" != "frontend" ] && [ "$COMPONENT" != "backend" ]; then
    echo "Error: Invalid component. Must be 'all', 'frontend', or 'backend'"
    exit 1
fi

# Load environment-specific variables
load_env "$ENVIRONMENT"

# Validate environment variables
validate_env "$ENVIRONMENT" || exit 1

# Function to deploy backend
deploy_backend() {
    echo "Deploying backend for $ENVIRONMENT..."
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        # Build and push Docker image
        aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
        docker build -t "$PROD_ECR_REPOSITORY:latest" ./backend
        docker tag "$PROD_ECR_REPOSITORY:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROD_ECR_REPOSITORY:latest"
        docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROD_ECR_REPOSITORY:latest"

        # Update ECS service
        aws ecs update-service \
            --cluster "$PROD_ECS_CLUSTER" \
            --service "$PROD_ECS_SERVICE" \
            --force-new-deployment \
            --region "$AWS_REGION"
    else
        # Local deployment
        docker-compose up -d --build backend
    fi
}

# Function to deploy frontend
deploy_frontend() {
    echo "Deploying frontend for $ENVIRONMENT..."
    
    # Install dependencies
    cd frontend
    npm ci
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        # Build for production
        npm run build
        
        # Deploy to S3
        aws s3 sync dist "s3://$PROD_S3_BUCKET" \
            --delete \
            --cache-control "public, max-age=31536000"
        
        # Invalidate CloudFront cache if distribution ID is set
        if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
            aws cloudfront create-invalidation \
                --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --paths "/*"
        fi
    else
        # Local deployment
        npm run dev
    fi
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    cd backend
    cargo sqlx migrate run
}

# Main deployment logic
if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "backend" ]; then
    deploy_backend
fi

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "frontend" ]; then
    deploy_frontend
fi

echo "Deployment complete!"
if [ "$ENVIRONMENT" = "local" ]; then
    echo "Local URLs:"
    echo "Frontend: http://localhost:5173"
    echo "Backend: http://localhost:3000"
else
    echo "Production URLs:"
    echo "Frontend: $VITE_API_URL"
    echo "Backend: https://api.aimodels.example.com"
fi 