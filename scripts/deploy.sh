#!/bin/bash

# Production deployment script for D2C Analytics Platform
set -e

echo "🚀 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please copy .env.production to .env and configure it"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check required environment variables
required_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "MONGO_ROOT_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: $var is not set in .env${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment variables loaded${NC}"

# Pull latest changes
echo "📥 Pulling latest code..."
git pull origin main

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Checking service health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Services are healthy!${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Services failed to start properly${NC}"
    docker-compose -f docker-compose.prod.yml logs api
    exit 1
fi

# Show running services
echo -e "\n${GREEN}✅ Deployment successful!${NC}\n"
echo "Running services:"
docker-compose -f docker-compose.prod.yml ps

echo -e "\n📊 Access points:"
echo "  API: http://localhost:8000"
echo "  Health: http://localhost:8000/health"
echo "  Metrics: http://localhost:8000/metrics"
echo "  Flower (Celery monitoring): http://localhost:5555"

echo -e "\n📝 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart api"
echo "  Shell access: docker-compose -f docker-compose.prod.yml exec api bash"

echo -e "\n${YELLOW}⚠️  Remember to:${NC}"
echo "  1. Set up SSL certificates (Let's Encrypt)"
echo "  2. Configure your domain in nginx.conf"
echo "  3. Set up database backups"
echo "  4. Configure monitoring alerts"
