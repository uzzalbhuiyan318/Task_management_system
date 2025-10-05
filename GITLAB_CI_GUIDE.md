# GitLab CI/CD Configuration Guide for Django Task Management System

## Overview
This `.gitlab-ci.yml` file sets up a complete CI/CD pipeline with testing, building, and deployment stages.

## Pipeline Stages

### 1. **Test Stage**
- **lint**: Checks Python code quality using flake8
- **test**: Runs Django unit tests
- **security_check**: Scans for security vulnerabilities using Safety and Bandit

### 2. **Build Stage**
- **build**: Collects static files and performs deployment checks

### 3. **Deploy Stage**
- **deploy_staging**: Deploys to staging environment (manual trigger)
- **deploy_production**: Deploys to production environment (manual trigger)
- **deploy_docker**: Builds and pushes Docker images (manual trigger)

## Setup Instructions

### 1. Configure GitLab CI/CD Variables

Go to your GitLab project: **Settings > CI/CD > Variables** and add:

#### For SSH Deployment:
- `STAGING_HOST`: Staging server IP/hostname
- `STAGING_USER`: SSH username for staging
- `STAGING_PASSWORD`: SSH password for staging (or use SSH keys)
- `STAGING_PATH`: Path to deploy on staging server
- `PROD_HOST`: Production server IP/hostname
- `PROD_USER`: SSH username for production
- `PROD_PASSWORD`: Production SSH password (or use SSH keys)
- `PROD_PATH`: Path to deploy on production server

#### For Docker Deployment:
- `CI_REGISTRY`: GitLab Container Registry URL
- `CI_REGISTRY_USER`: GitLab username
- `CI_REGISTRY_PASSWORD`: GitLab access token

#### Django Specific:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False for production
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### 2. Enable GitLab Container Registry

1. Go to **Settings > General > Visibility**
2. Enable **Container Registry**

### 3. Customize Deployment Scripts

Edit the deployment jobs in `.gitlab-ci.yml` to match your infrastructure:

#### Option A: SSH Deployment
Uncomment the SSH deployment commands in `deploy_staging` and `deploy_production` jobs.

#### Option B: Docker Deployment
Use the `deploy_docker` job to build and push Docker images.

### 4. Server Prerequisites

#### For Direct Deployment:
- Python 3.12+
- PostgreSQL
- Nginx/Apache
- Gunicorn
- SSH access

#### For Docker Deployment:
- Docker
- Docker Compose

### 5. Pipeline Triggers

- **Automatic**: Tests run on all branches and merge requests
- **Manual**: Deployments require manual approval
- **Tags**: Production deployments can be triggered by creating tags

## Usage Examples

### Running the Pipeline

1. **Push to any branch**: Tests will run automatically
2. **Push to `develop` branch**: Can manually deploy to staging
3. **Push to `main` branch**: Can manually deploy to production
4. **Create a tag**: Can trigger production deployment

### Manual Deployment

1. Go to **CI/CD > Pipelines**
2. Find your pipeline
3. Click the **play** button on the deployment job you want to run

## Docker Deployment

### Building the Docker Image Locally

```bash
docker build -t task-management-system .
```

### Running with Docker Compose

```bash
# Create .env file with your configuration
docker-compose up -d
```

### Stopping Services

```bash
docker-compose down
```

## Environment Files

Create a `.env` file in the project root for local Docker deployment:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DB_NAME=taskmanager_db
DB_USER=taskmanager_user
DB_PASSWORD=your-secure-password
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

## Nginx Configuration

Create `nginx.conf` for the Nginx service:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /static/ {
            alias /app/staticfiles/;
        }

        location /media/ {
            alias /app/media/;
        }
    }
}
```

## Troubleshooting

### Pipeline Fails on Test Stage
- Check Python version compatibility
- Verify requirements.txt exists
- Review test configuration

### Deployment Fails
- Verify server credentials in GitLab Variables
- Check SSH access to deployment servers
- Ensure all environment variables are set

### Docker Build Fails
- Check Dockerfile syntax
- Verify base image availability
- Review build logs for specific errors

## Security Best Practices

1. ✅ Never commit sensitive data (passwords, keys) to the repository
2. ✅ Use GitLab CI/CD Variables for secrets
3. ✅ Enable "Masked" and "Protected" for sensitive variables
4. ✅ Use SSH keys instead of passwords when possible
5. ✅ Keep dependencies updated
6. ✅ Review security scan results regularly

## Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For issues or questions, please refer to the project documentation or create an issue in the GitLab repository.

---

**Created**: October 5, 2025
**Project**: Task Management System
**Version**: 1.0.1
