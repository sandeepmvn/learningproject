# Azure DevOps CI/CD and App Service Deployment Guide

Complete guide for setting up CI/CD pipelines in Azure DevOps and deploying the Team Trip Expense Tracker to Azure App Service.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Resources Setup](#azure-resources-setup)
3. [Azure DevOps Configuration](#azure-devops-configuration)
4. [Pipeline Overview](#pipeline-overview)
5. [Deployment Process](#deployment-process)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
8. [Production Best Practices](#production-best-practices)

---

## Prerequisites

### Required Accounts and Tools

- **Azure Subscription** with permissions to create resources
- **Azure DevOps organization** and project
- **Git repository** in Azure Repos or GitHub
- **Azure CLI** installed locally (optional, for manual configuration)

### Required Azure Resources

- Azure App Service (Linux, Python 3.12)
- Azure App Service Plan (B1 or higher recommended)
- Optional: Azure SQL Database (for production, instead of SQLite)
- Optional: Application Insights (for monitoring)

---

## Azure Resources Setup

### 1. Create Azure App Service

#### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → **Web App**
3. Configure the web app:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or select existing
   - **Name**: `expense-tracker-api` (must be globally unique)
   - **Publish**: Code
   - **Runtime stack**: Python 3.12
   - **Operating System**: Linux
   - **Region**: Choose nearest region
4. Configure App Service Plan:
   - **Plan**: Create new
   - **SKU**: B1 (Basic) or higher
5. Click **Review + Create** → **Create**

#### Option B: Using Azure CLI

```powershell
# Login to Azure
az login

# Set variables
$resourceGroup = "expense-tracker-rg"
$location = "eastus"
$appServicePlan = "expense-tracker-plan"
$webAppName = "expense-tracker-api"

# Create resource group
az group create --name $resourceGroup --location $location

# Create App Service Plan
az appservice plan create `
  --name $appServicePlan `
  --resource-group $resourceGroup `
  --sku B1 `
  --is-linux

# Create Web App
az webapp create `
  --resource-group $resourceGroup `
  --plan $appServicePlan `
  --name $webAppName `
  --runtime "PYTHON:3.12"

# Configure startup command
az webapp config set `
  --resource-group $resourceGroup `
  --name $webAppName `
  --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

### 2. Configure App Service Settings

Set application settings in Azure Portal:

1. Navigate to your App Service
2. Go to **Configuration** → **Application settings**
3. Add the following settings:

| Name | Value |
|------|-------|
| `DATABASE_URL` | `sqlite:///./data/expense_tracker.db` |
| `PYTHONUNBUFFERED` | `1` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `WEBSITES_PORT` | `8000` |

Or using Azure CLI:

```powershell
az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $webAppName `
  --settings `
    DATABASE_URL="sqlite:///./data/expense_tracker.db" `
    PYTHONUNBUFFERED="1" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
    WEBSITES_PORT="8000"
```

### 3. Create Development Environment (Optional)

For a complete dev/prod setup, create a second App Service:

```powershell
$webAppNameDev = "expense-tracker-api-dev"

az webapp create `
  --resource-group $resourceGroup `
  --plan $appServicePlan `
  --name $webAppNameDev `
  --runtime "PYTHON:3.12"
```

---

## Azure DevOps Configuration

### 1. Create Azure DevOps Project

1. Go to [Azure DevOps](https://dev.azure.com)
2. Create a new project: **Expense Tracker**
3. Choose version control: **Git**

### 2. Import Repository

Push your code to Azure Repos:

```powershell
# Navigate to project directory
Set-Location 'D:\copilotdemo-april\cli-examples\learningproject'

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Add Azure DevOps remote (replace with your repo URL)
git remote add origin https://dev.azure.com/yourorg/ExpenseTracker/_git/expense-tracker
git push -u origin main
```

### 3. Create Service Connection

Connect Azure DevOps to your Azure subscription:

1. In Azure DevOps, go to **Project Settings**
2. Select **Service connections**
3. Click **New service connection**
4. Choose **Azure Resource Manager**
5. Select **Service principal (automatic)**
6. Configure:
   - **Scope level**: Subscription
   - **Subscription**: Select your Azure subscription
   - **Resource group**: Select your resource group
   - **Service connection name**: `Azure-ServiceConnection`
7. Click **Save**

**Important**: The service connection name must match the `azureSubscription` variable in `azure-pipelines.yml`.

### 4. Create Environments

Create environments for deployment approvals:

1. Go to **Pipelines** → **Environments**
2. Create two environments:
   - **Development**: No approvals
   - **Production**: Add approvals and checks

To add approvals to Production:

1. Click **Production** environment
2. Click **...** → **Approvals and checks**
3. Add **Approvals**
4. Select approvers
5. Save

### 5. Configure Pipeline Variables

1. Go to **Pipelines** → **Library**
2. Create a variable group: **expense-tracker-variables**
3. Add variables:

| Variable | Value | Secret |
|----------|-------|--------|
| `azureAppServiceName` | `expense-tracker-api` | No |
| `azureSubscription` | `Azure-ServiceConnection` | No |
| `pythonVersion` | `3.12` | No |

Update `azure-pipelines.yml` to reference this variable group if needed.

---

## Pipeline Overview

### Pipeline Stages

The `azure-pipelines.yml` includes three stages:

#### 1. **Build Stage**

- Runs on every commit to `main` or `develop`
- Installs Python dependencies
- Runs automated tests with pytest
- Generates code coverage reports
- Publishes test results
- Archives application files
- Publishes build artifacts

#### 2. **Deploy to Development**

- Triggers only on commits to `develop` branch
- Downloads build artifacts
- Deploys to development App Service
- No manual approval required

#### 3. **Deploy to Production**

- Triggers only on commits to `main` branch
- Requires manual approval (if configured)
- Downloads build artifacts
- Deploys to production App Service

### Pipeline Triggers

```yaml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    exclude:
      - README.md
      - frontend/**
```

The pipeline triggers on:
- Commits to `main` or `develop` branches
- Excludes changes to documentation and frontend

---

## Deployment Process

### Automatic Deployment Workflow

1. **Developer pushes code** to `develop` or `main` branch
2. **Build stage** runs automatically:
   - Installs dependencies
   - Runs tests
   - Creates deployment package
3. **Deploy stage** runs automatically:
   - Downloads artifacts
   - Deploys to appropriate environment
   - Runs health checks

### Manual Deployment

You can also trigger deployments manually:

1. Go to **Pipelines** → **Pipelines**
2. Select your pipeline
3. Click **Run pipeline**
4. Choose branch and parameters
5. Click **Run**

### First-Time Setup Steps

1. **Update `azure-pipelines.yml`** with your App Service names:
   ```yaml
   variables:
     azureAppServiceName: 'your-app-service-name'
     azureSubscription: 'your-service-connection-name'
   ```

2. **Commit and push** the pipeline file:
   ```powershell
   git add azure-pipelines.yml
   git commit -m "Add Azure DevOps pipeline"
   git push origin main
   ```

3. **Create the pipeline** in Azure DevOps:
   - Go to **Pipelines** → **Create Pipeline**
   - Select **Azure Repos Git**
   - Select your repository
   - Choose **Existing Azure Pipelines YAML file**
   - Select `/azure-pipelines.yml`
   - Click **Run**

---

## Environment Configuration

### Environment Variables

Configure these in Azure App Service Application Settings:

#### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/expense_tracker.db` |
| `PYTHONUNBUFFERED` | Enable real-time logging | `1` |
| `WEBSITES_PORT` | Port for the application | `8000` |

#### Optional Settings for Production

| Setting | Description | Example |
|---------|-------------|---------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Application Insights | `InstrumentationKey=xxx` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | Enable build on deployment | `true` |

### Database Configuration

#### Development: SQLite (Default)

```
DATABASE_URL=sqlite:///./data/expense_tracker.db
```

#### Production: Azure SQL Database (Recommended)

1. Create Azure SQL Database
2. Update connection string:
   ```
   DATABASE_URL=postgresql://username:password@server.postgres.database.azure.com:5432/expense_tracker?sslmode=require
   ```
3. Update `requirements.txt`:
   ```
   psycopg2-binary==2.9.9
   ```

### CORS Configuration

If you have a frontend on a different domain, update `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Monitoring and Troubleshooting

### View Application Logs

#### Azure Portal

1. Navigate to App Service
2. Go to **Monitoring** → **Log stream**
3. View real-time logs

#### Azure CLI

```powershell
az webapp log tail `
  --resource-group $resourceGroup `
  --name $webAppName
```

### Enable Application Insights

1. Create Application Insights resource
2. Navigate to App Service → **Application Insights**
3. Click **Turn on Application Insights**
4. Select your Application Insights resource

### Common Issues and Solutions

#### Issue: Application not starting

**Solution**: Check startup command in App Service Configuration:
```
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Issue: Module not found errors

**Solution**: Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set, or include a `.deployment` file:
```
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

#### Issue: Database errors

**Solution**: Check DATABASE_URL is correct and data directory exists

#### Issue: Pipeline fails on tests

**Solution**: Review test results in Azure DevOps:
1. Go to pipeline run
2. Click **Tests** tab
3. Review failed tests

### Health Check Endpoint

The application includes a health check endpoint:
```
GET https://your-app.azurewebsites.net/health
```

Response:
```json
{
  "status": "ok"
}
```

---

## Production Best Practices

### 1. Use Azure SQL Database

Replace SQLite with Azure SQL Database or PostgreSQL for production:

```python
# Update app/database.py to support both
def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./data/expense_tracker.db")
```

### 2. Enable HTTPS Only

```powershell
az webapp update `
  --resource-group $resourceGroup `
  --name $webAppName `
  --https-only true
```

### 3. Configure Custom Domain

1. Purchase/configure domain
2. Add custom domain in App Service
3. Enable SSL certificate

### 4. Set Up Deployment Slots

Create staging slot for zero-downtime deployments:

```powershell
az webapp deployment slot create `
  --resource-group $resourceGroup `
  --name $webAppName `
  --slot staging
```

Update pipeline to deploy to slot first, then swap.

### 5. Enable Auto-Scaling

Configure auto-scaling rules:

1. Go to App Service Plan → **Scale out**
2. Add rules based on:
   - CPU percentage
   - Memory percentage
   - HTTP queue length

### 6. Security Hardening

- Store secrets in Azure Key Vault
- Use managed identities
- Enable Azure AD authentication
- Implement rate limiting
- Add API keys for authentication

### 7. Backup Strategy

Enable App Service backups:

1. Go to App Service → **Backups**
2. Configure backup schedule
3. Set retention policy

### 8. Monitoring and Alerts

Set up alerts in Application Insights:

- Response time > 3 seconds
- Failed requests > 5%
- Server errors (5xx)
- Availability < 99%

---

## Pipeline Customization

### Add Security Scanning

Add to `azure-pipelines.yml`:

```yaml
- script: |
    pip install bandit
    bandit -r app/ -f json -o bandit-report.json
  displayName: 'Run security scan'
```

### Add Linting

```yaml
- script: |
    pip install flake8
    flake8 app/ --max-line-length=120
  displayName: 'Run linting'
```

### Add Database Migrations

If using Alembic for migrations:

```yaml
- script: |
    pip install alembic
    alembic upgrade head
  displayName: 'Run database migrations'
```

---

## Quick Reference Commands

### Azure CLI Commands

```powershell
# View App Service logs
az webapp log tail -g $resourceGroup -n $webAppName

# Restart App Service
az webapp restart -g $resourceGroup -n $webAppName

# List App Settings
az webapp config appsettings list -g $resourceGroup -n $webAppName

# SSH into container
az webapp ssh -g $resourceGroup -n $webAppName

# View deployment history
az webapp deployment list -g $resourceGroup -n $webAppName
```

### Useful URLs

- **Azure Portal**: https://portal.azure.com
- **Azure DevOps**: https://dev.azure.com
- **App Service URL**: https://[your-app-name].azurewebsites.net
- **Kudu (SCM)**: https://[your-app-name].scm.azurewebsites.net
- **API Docs**: https://[your-app-name].azurewebsites.net/docs

---

## Summary

Your CI/CD pipeline is now configured to:

✅ Automatically build and test on every commit  
✅ Deploy to development on `develop` branch  
✅ Deploy to production on `main` branch  
✅ Run automated tests with coverage reporting  
✅ Publish test results and artifacts  
✅ Support environment-based deployments  

For support and more information:
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure DevOps Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
