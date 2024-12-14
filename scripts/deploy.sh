#!/bin/bash
set -e

# Check for required tools
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting." >&2; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed. Aborting." >&2; exit 1; }

# Check for required environment variables
required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_REGION"
    "TF_VAR_db_password"
    "STRIPE_PUBLIC_KEY"
    "STRIPE_SECRET_KEY"
    "STRIPE_WEBHOOK_SECRET"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Create S3 bucket for Terraform state
echo "Creating Terraform state bucket..."
aws s3api create-bucket \
    --bucket aimodels-terraform-state \
    --region us-east-1 \
    2>/dev/null || true

# Enable versioning on the bucket
aws s3api put-bucket-versioning \
    --bucket aimodels-terraform-state \
    --versioning-configuration Status=Enabled

# Initialize and apply Terraform
echo "Initializing Terraform..."
cd terraform
terraform init

echo "Applying Terraform configuration..."
terraform apply -auto-approve

# Get outputs
ECR_REPO=$(terraform output -raw ecr_repository_url)
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain)
ALB_DNS=$(terraform output -raw alb_dns_name)

echo "Infrastructure deployment complete!"
echo "ECR Repository: $ECR_REPO"
echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo "ALB DNS: $ALB_DNS"

# Build and push backend image
echo "Building and pushing backend image..."
cd ../backend
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
docker build -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

# Build and deploy frontend
echo "Building and deploying frontend..."
cd ../frontend
npm ci
VITE_API_URL="http://$ALB_DNS" npm run build

# Sync frontend build to S3
aws s3 sync dist s3://aimodels-frontend --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='$CLOUDFRONT_DOMAIN'].Id" --output text)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "Deployment complete!"
echo "Frontend URL: https://$CLOUDFRONT_DOMAIN"
echo "Backend URL: http://$ALB_DNS" 