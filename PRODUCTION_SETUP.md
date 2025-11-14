# 🚀 Production Setup Guide

Complete guide to deploy the D2C Analytics & Forecasting Platform to production.

## 📋 Prerequisites

- Ubuntu 20.04+ (or similar Linux)
- Docker & Docker Compose installed
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- Minimum 4GB RAM, 2 CPU cores

## 🔧 Step-by-Step Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd claude
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production .env

# Edit configuration
nano .env
```

**CRITICAL: Update these values:**
- `SECRET_KEY`: Generate strong key (`openssl rand -hex 32`)
- `POSTGRES_PASSWORD`: Strong database password
- `MONGO_ROOT_PASSWORD`: MongoDB root password
- `REDIS_PASSWORD`: Redis password
- Update all API keys (Shopify, Facebook, Google)
- Update CORS origins with your domain
- Set SENTRY_DSN for error tracking

### 3. Generate SSL Certificates

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

#### Option B: Self-signed (Development only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem
```

### 4. Update Nginx Configuration

```bash
nano nginx/nginx.conf

# Update:
# - server_name with your domain
# - SSL certificate paths
# - Allowed IP ranges for /metrics
```

### 5. Initialize Databases

```bash
# Create initial migration
docker-compose -f docker-compose.prod.yml run --rm api alembic revision --autogenerate -m "Initial migration"

# Review migration file
nano alembic/versions/[generated_file].py

# Apply migration
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

### 6. Deploy Application

```bash
# Run deployment script
./scripts/deploy.sh
```

This will:
- Build Docker images
- Start all services (API, PostgreSQL, MongoDB, Redis, Nginx)
- Run database migrations
- Perform health checks

### 7. Verify Deployment

```bash
# Check service health
curl https://yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "postgresql": "healthy",
    "mongodb": "healthy"
  }
}

# Check running services
docker-compose -f docker-compose.prod.yml ps
```

### 8. Set Up Monitoring

#### Prometheus (Metrics)

```bash
# Access metrics endpoint
curl https://yourdomain.com/metrics
```

#### Sentry (Error Tracking)

1. Create account at sentry.io
2. Create new project
3. Copy DSN to `.env` as `SENTRY_DSN`
4. Restart services

#### Flower (Celery Monitoring)

Access at `http://yourdomain.com:5555` (configure firewall)

### 9. Set Up Backups

#### PostgreSQL Backup

```bash
# Create backup script
cat > backup-postgres.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U d2c_user d2c_analytics | gzip > \
  backups/postgres_$DATE.sql.gz

# Keep only last 30 days
find backups/ -name "postgres_*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup-postgres.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /path/to/backup-postgres.sh" | crontab -
```

#### MongoDB Backup

```bash
# Create backup script
cat > backup-mongo.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T mongodb \
  mongodump --archive | gzip > backups/mongo_$DATE.gz

# Keep only last 30 days
find backups/ -name "mongo_*.gz" -mtime +30 -delete
EOF

chmod +x backup-mongo.sh

# Add to cron
echo "0 3 * * * /path/to/backup-mongo.sh" | crontab -
```

### 10. Security Hardening

```bash
# Set up firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Regular updates
sudo apt update && sudo apt upgrade -y
```

## 🔄 Maintenance Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f postgres
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

### Restart Services

```bash
# Restart API only
docker-compose -f docker-compose.prod.yml restart api

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

### Database Migrations

```bash
# Create new migration
docker-compose -f docker-compose.prod.yml run --rm api \
  alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose -f docker-compose.prod.yml run --rm api \
  alembic upgrade head

# Rollback migration
docker-compose -f docker-compose.prod.yml run --rm api \
  alembic downgrade -1
```

### Scale Workers

```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

### Database Shell Access

```bash
# PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U d2c_user -d d2c_analytics

# MongoDB
docker-compose -f docker-compose.prod.yml exec mongodb \
  mongosh d2c_analytics
```

## 📊 Performance Tuning

### PostgreSQL

```bash
# Edit postgresql.conf
docker-compose -f docker-compose.prod.yml exec postgres \
  vi /var/lib/postgresql/data/postgresql.conf

# Recommended settings for 4GB RAM:
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### API Workers

```bash
# Adjust workers in Dockerfile.prod
# Formula: (2 x CPU cores) + 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "9"]
```

## 🔒 Security Checklist

- [ ] Strong passwords for all services
- [ ] SECRET_KEY is randomly generated
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] API docs disabled in production (DEBUG=False)
- [ ] CORS configured with specific domains
- [ ] Database backups automated
- [ ] Sentry error tracking enabled
- [ ] Rate limiting configured
- [ ] Security headers in Nginx
- [ ] Non-root Docker user
- [ ] Environment variables not committed
- [ ] Fail2ban installed
- [ ] Regular updates scheduled

## 📈 Monitoring

### Health Checks

```bash
# API health
curl https://yourdomain.com/health

# PostgreSQL health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# MongoDB health
docker-compose -f docker-compose.prod.yml exec mongodb \
  mongosh --eval "db.adminCommand('ping')"
```

### Resource Monitoring

```bash
# Docker stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check env variables
docker-compose -f docker-compose.prod.yml config

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker-compose -f docker-compose.prod.yml exec api python -c \
  "from app.core.database import engine; engine.connect()"

# Test MongoDB connection
docker-compose -f docker-compose.prod.yml exec api python -c \
  "from app.core.mongodb import get_sync_mongo_client; get_sync_mongo_client().admin.command('ping')"
```

### High Memory Usage

```bash
# Check memory usage
docker stats --no-stream

# Restart services with limits
docker-compose -f docker-compose.prod.yml up -d \
  --scale celery-worker=2 \
  --memory="2g" --memory-swap="2g"
```

## 📞 Support

For issues:
1. Check logs: `docker-compose logs`
2. Review GitHub issues
3. Check documentation
4. Contact support

## 🎉 You're Live!

Your D2C Analytics Platform is now running in production!

**Next Steps:**
1. Connect first store (Shopify/WooCommerce)
2. Integrate marketing channels
3. Set up Shiprocket
4. Monitor performance
5. Iterate based on user feedback

**Happy analyzing! 📊🚀**
