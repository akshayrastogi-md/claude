# Deployment Guide

## Local Development

### 1. Standard Python

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Seed database (optional)
python scripts/seed_data.py

# Run the application
python app/main.py
```

Access at: http://localhost:8000

### 2. Docker

```bash
# Build and run
docker build -t inventory-forecast-api .
docker run -p 8000:8000 inventory-forecast-api
```

### 3. Docker Compose (with PostgreSQL)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Production Deployment

### Option 1: Traditional Server (Ubuntu/Debian)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# 3. Clone repository
git clone <your-repo-url>
cd inventory-forecast-api

# 4. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 7. Install and configure Nginx
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/api

# Nginx config:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Set up systemd service
sudo nano /etc/systemd/system/inventory-api.service

# Service file:
[Unit]
Description=Inventory Forecast API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/inventory-forecast-api
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target

# 9. Start service
sudo systemctl daemon-reload
sudo systemctl enable inventory-api
sudo systemctl start inventory-api
```

### Option 2: Docker on Server

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone and configure
git clone <your-repo-url>
cd inventory-forecast-api
cp .env.example .env
nano .env

# 4. Build and run
docker-compose up -d

# 5. Set up auto-restart
docker update --restart unless-stopped $(docker ps -q)
```

### Option 3: Cloud Platforms

#### AWS EC2

1. Launch EC2 instance (t3.medium or larger recommended)
2. Install Docker or Python
3. Follow traditional server setup
4. Configure security groups to allow port 80/443

#### Google Cloud Run

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/PROJECT-ID/inventory-forecast-api

# 2. Deploy
gcloud run deploy inventory-forecast-api \
  --image gcr.io/PROJECT-ID/inventory-forecast-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

#### Azure Container Instances

```bash
# 1. Create resource group
az group create --name inventory-api-rg --location eastus

# 2. Build and push image
az acr build --registry <registry-name> --image inventory-forecast-api:latest .

# 3. Deploy
az container create \
  --resource-group inventory-api-rg \
  --name inventory-forecast-api \
  --image <registry-name>.azurecr.io/inventory-forecast-api:latest \
  --dns-name-label inventory-api \
  --ports 8000
```

#### Heroku

```bash
# 1. Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Deploy
heroku create inventory-forecast-api
git push heroku main
heroku ps:scale web=1
```

#### Railway.app

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

#### Render.com

1. Connect GitHub repository
2. Select Docker deployment
3. Configure environment variables
4. Deploy

## Database Setup

### PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql
CREATE DATABASE inventory_forecast;
CREATE USER api_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE inventory_forecast TO api_user;
\q

# Update .env
DATABASE_URL=postgresql://api_user:your-password@localhost/inventory_forecast
```

### Managed Database Services

**AWS RDS**
```
DATABASE_URL=postgresql://user:pass@db-instance.region.rds.amazonaws.com:5432/inventory_forecast
```

**Google Cloud SQL**
```
DATABASE_URL=postgresql://user:pass@/inventory_forecast?host=/cloudsql/project:region:instance
```

**Azure Database**
```
DATABASE_URL=postgresql://user:pass@server.postgres.database.azure.com:5432/inventory_forecast
```

## Performance Tuning

### Uvicorn Workers

```bash
# Single worker (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Resource Requirements

**Minimum (Small deployment)**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB

**Recommended (Medium deployment)**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB

**High Performance**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB
- GPU: Optional (for faster ML training)

## SSL/HTTPS Setup

### Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring

### Basic Health Monitoring

```bash
# Cron job to check health
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart inventory-api
```

### Advanced Monitoring Tools

- **Prometheus + Grafana**: Metrics and dashboards
- **Sentry**: Error tracking
- **Datadog**: Full-stack monitoring
- **New Relic**: APM

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
pg_dump inventory_forecast > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 2 * * * pg_dump inventory_forecast > /backups/backup_$(date +\%Y\%m\%d).sql
```

### Application Backups

```bash
# Backup models and data
tar -czf backup_$(date +%Y%m%d).tar.gz app/ data/ .env
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose scale
version: '3.8'
services:
  api:
    deploy:
      replicas: 4
    ...

  nginx:
    # Load balancer config
```

### Load Balancing

Use Nginx, HAProxy, or cloud load balancers to distribute traffic across multiple instances.

## Security Checklist

- [ ] Use HTTPS/SSL
- [ ] Set strong database passwords
- [ ] Enable firewall (UFW, Security Groups)
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Keep dependencies updated
- [ ] Use non-root Docker user
- [ ] Enable CORS only for trusted domains
- [ ] Regular security audits
- [ ] Implement API authentication (JWT, OAuth)

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart inventory-api
```

### Logs

```bash
# View logs
sudo journalctl -u inventory-api -f

# Docker logs
docker-compose logs -f api
```

## Troubleshooting

### Common Issues

**Port already in use**
```bash
lsof -i :8000
kill -9 <PID>
```

**Out of memory**
- Increase server RAM
- Reduce number of workers
- Optimize ML model parameters

**Slow forecasts**
- Enable caching
- Use simpler models for real-time needs
- Add GPU support

## Support

For issues, check:
1. Application logs
2. Database connectivity
3. Disk space
4. Memory usage
5. Network configuration
