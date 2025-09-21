#!/bin/bash
# Production deployment script for TinyCode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 TinyCode Production Deployment Script${NC}"
echo "=================================================="

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️ Ollama not found, will need to be installed separately${NC}"
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs/nginx ssl data/{plans,backups,audit_logs,index}

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chmod 755 data
chmod 750 data/{plans,backups,audit_logs}
chmod 755 logs

# Copy environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating environment file...${NC}"
    cp .env.production .env
    echo -e "${YELLOW}⚠️ Please update .env with your configuration${NC}"
fi

# Build containers
echo -e "${YELLOW}Building Docker containers...${NC}"
cd docker
docker-compose build --no-cache

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 30

# Health checks
echo -e "${YELLOW}Running health checks...${NC}"

# Check TinyCode API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TinyCode API is healthy${NC}"
else
    echo -e "${RED}❌ TinyCode API health check failed${NC}"
    echo "Container logs:"
    docker-compose logs tinyllama
fi

# Check Redis
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is healthy${NC}"
else
    echo -e "${RED}❌ Redis health check failed${NC}"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Prometheus is healthy${NC}"
else
    echo -e "${RED}❌ Prometheus health check failed${NC}"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Grafana is healthy${NC}"
else
    echo -e "${RED}❌ Grafana health check failed${NC}"
fi

# Display service URLs
echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo "=================================================="
echo "Service URLs:"
echo "• TinyCode API: http://localhost:8000"
echo "• Health Check: http://localhost:8000/health"
echo "• Metrics: http://localhost:8000/metrics"
echo "• Prometheus: http://localhost:9090"
echo "• Grafana: http://localhost:3000 (admin/admin123)"
echo ""
echo "Logs:"
echo "• View all logs: docker-compose logs -f"
echo "• TinyCode logs: docker-compose logs -f tinyllama"
echo "• Nginx logs: tail -f logs/nginx/access.log"
echo ""
echo "Management:"
echo "• Stop services: docker-compose down"
echo "• Restart: docker-compose restart"
echo "• Update: docker-compose pull && docker-compose up -d"
echo ""
echo -e "${YELLOW}⚠️ Remember to:${NC}"
echo "1. Update .env with your API keys and configuration"
echo "2. Configure SSL certificates in ssl/ directory"
echo "3. Set up nginx reverse proxy for production"
echo "4. Configure monitoring alerts"
echo "5. Set up log rotation"
echo "6. Test backup and recovery procedures"