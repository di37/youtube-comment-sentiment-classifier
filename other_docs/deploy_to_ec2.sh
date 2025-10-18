#!/bin/bash

# Deployment script for EC2 instance
# This script is used by the CI/CD pipeline to deploy the Docker container on EC2

set -e  # Exit on any error

echo "=================================="
echo "🚀 YouTube Sentiment API Deployment"
echo "=================================="

# Check required environment variables
required_vars=(
  "AWS_REGION"
  "ECR_REGISTRY"
  "ECR_REPOSITORY"
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "MLFLOW_TRACKING_URI"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Error: $var is not set"
    exit 1
  fi
done

# Login to ECR
echo ""
echo "🔑 Logging into AWS ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Pull the latest image
echo ""
echo "📦 Pulling new Docker image..."
echo "   Image: ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"
docker pull ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

# Stop and remove existing container if it exists
echo ""
echo "🛑 Stopping existing container (if running)..."
if docker ps -a | grep -q youtube-sentiment-api; then
  docker stop youtube-sentiment-api || true
  docker rm youtube-sentiment-api || true
  echo "   ✓ Existing container removed"
else
  echo "   ℹ️  No existing container found"
fi

# Run the new container
echo ""
echo "🚀 Starting new container..."
docker run -d \
  --name youtube-sentiment-api \
  -p 6889:6889 \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
  -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-me-central-1}" \
  -e AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-https://s3.me-central-1.amazonaws.com}" \
  -e MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI}" \
  -e MLFLOW_S3_ENDPOINT_URL="${MLFLOW_S3_ENDPOINT_URL:-https://s3.me-central-1.amazonaws.com}" \
  --restart unless-stopped \
  ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

# Wait for container to be healthy
echo ""
echo "⏳ Waiting for container to be ready..."
sleep 5

# Check container status
if docker ps | grep -q youtube-sentiment-api; then
  echo "   ✓ Container is running"
else
  echo "   ❌ Container failed to start!"
  docker logs youtube-sentiment-api
  exit 1
fi

# Clean up old images
echo ""
echo "🧹 Cleaning up old Docker images..."
docker image prune -f
echo "   ✓ Cleanup completed"

echo ""
echo "=================================="
echo "✅ Deployment Completed Successfully!"
echo "=================================="
echo ""
echo "📊 Container Status:"
docker ps | grep youtube-sentiment-api || true
echo ""
echo "🌐 Application Endpoints:"
echo "   - API URL: http://$(curl -s ifconfig.me):6889"
echo "   - Health Check: http://$(curl -s ifconfig.me):6889/health"
echo "   - API Docs: http://$(curl -s ifconfig.me):6889/docs"
echo ""
echo "💡 Useful Commands:"
echo "   - View logs: docker logs -f youtube-sentiment-api"
echo "   - Stop container: docker stop youtube-sentiment-api"
echo "   - Restart container: docker restart youtube-sentiment-api"
echo "=================================="

