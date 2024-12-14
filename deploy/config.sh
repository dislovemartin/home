#!/bin/bash

# Common settings
export PROJECT_NAME="aimodels"
export AWS_REGION="us-east-1"

# Local development settings
export LOCAL_DB_USER="postgres"
export LOCAL_DB_PASSWORD="postgres"
export LOCAL_DB_NAME="aimodels"
export LOCAL_DB_PORT="5432"

# Production settings
export PROD_ECR_REPOSITORY="aimodels-backend"
export PROD_ECS_CLUSTER="aimodels-cluster"
export PROD_ECS_SERVICE="aimodels-backend-service"
export PROD_S3_BUCKET="aimodels-frontend"

# Database settings
export DB_MAX_CONNECTIONS="10"
export DB_ACQUIRE_TIMEOUT="3"

# Application settings
export RUST_LOG="info"
export RUST_BACKTRACE="1"

# Function to load environment-specific variables
load_env() {
    local env=$1
    if [ "$env" = "prod" ]; then
        export VITE_API_URL="https://api.aimodels.example.com"
        export DATABASE_URL="postgresql://${PROD_DB_USER}:${PROD_DB_PASSWORD}@${PROD_DB_HOST}:5432/${PROD_DB_NAME}"
    else
        export VITE_API_URL="http://localhost:3000"
        export DATABASE_URL="postgresql://${LOCAL_DB_USER}:${LOCAL_DB_PASSWORD}@localhost:${LOCAL_DB_PORT}/${LOCAL_DB_NAME}"
    fi
}

# Function to validate required environment variables
validate_env() {
    local env=$1
    local required_vars=(
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "STRIPE_PUBLIC_KEY"
        "STRIPE_SECRET_KEY"
        "STRIPE_WEBHOOK_SECRET"
    )

    if [ "$env" = "prod" ]; then
        required_vars+=(
            "PROD_DB_USER"
            "PROD_DB_PASSWORD"
            "PROD_DB_HOST"
            "PROD_DB_NAME"
        )
    fi

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: Required environment variable $var is not set"
            return 1
        fi
    done
    return 0
} 