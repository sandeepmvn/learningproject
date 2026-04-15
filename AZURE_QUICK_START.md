# Azure DevOps CI/CD Setup - Quick Reference

## ✅ What Has Been Created

### CI/CD Pipeline Files

1. **`azure-pipelines.yml`** - Complete Azure DevOps pipeline with:
   - Build stage (install, test, package)
   - Deploy to Development (on `develop` branch)
   - Deploy to Production (on `main` branch)
   - Automated testing with coverage reports
   - Artifact publishing

2. **`startup.sh`** - Azure App Service startup script

3. **`.azure/config.json`** - Azure App Service configuration template

4. **`.env.azure`** - Azure-specific environment variables template

### Documentation

5. **`AZURE_DEPLOYMENT.md`** - Complete deployment guide covering:
   - Prerequisites and setup
   - Azure resources creation
   - Azure DevOps configuration
   - Service connections
   - Environment setup
   - Monitoring and troubleshooting
   - Production best practices

6. **`README.md`** - Main project documentation

## 🚀 Quick Setup Steps

### Step 1: Create Azure Resources

```powershell
# Login to Azure
az login

# Variables
$resourceGroup = "expense-tracker-rg"
$location = "eastus"
$appServicePlan = "expense-tracker-plan"
$webAppName = "expense-tracker-api"  # Must be globally unique

# Create resources
az group create --name $resourceGroup --location $location

az appservice plan create `
  --name $appServicePlan `
  --resource-group $resourceGroup `
  --sku B1 `
  --is-linux

az webapp create `
  --resource-group $resourceGroup `
  --plan $appServicePlan `
  --name $webAppName `
  --runtime "PYTHON:3.12"

# Configure startup
az webapp config set `
  --resource-group $resourceGroup `
  --name $webAppName `
  --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Add app settings
az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $webAppName `
  --settings `
    DATABASE_URL="sqlite:///./data/expense_tracker.db" `
    PYTHONUNBUFFERED="1" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
    WEBSITES_PORT="8000"
```

### Step 2: Configure Azure DevOps

1. **Create Service Connection**
   - Go to Project Settings → Service connections
   - Create new Azure Resource Manager connection
   - Name it: `Azure-ServiceConnection`

2. **Create Environments**
   - Go to Pipelines → Environments
   - Create: `Development`
   - Create: `Production` (add approvals)

3. **Update `azure-pipelines.yml`**
   - Replace `expense-tracker-api` with your App Service name
   - Commit and push:
     ```powershell
     git add azure-pipelines.yml
     git commit -m "Add Azure DevOps pipeline"
     git push origin main
     ```

4. **Create Pipeline**
   - Go to Pipelines → New Pipeline
   - Select Azure Repos Git
   - Select your repository
   - Choose existing YAML file: `/azure-pipelines.yml`
   - Run the pipeline

### Step 3: Deploy

**Automatic Deployment:**
- Push to `develop` branch → deploys to Development
- Push to `main` branch → deploys to Production

**Manual Deployment:**
- Go to Pipelines → Run pipeline
- Select branch and run

## 📋 Pipeline Variables to Update

In `azure-pipelines.yml`, update these:

```yaml
variables:
  azureAppServiceName: 'your-unique-app-name'  # Change this
  azureSubscription: 'Azure-ServiceConnection'  # Must match service connection name
  pythonVersion: '3.12'
```

## 🔍 Verify Deployment

After deployment, test these URLs:

```
# Health check
https://your-app-name.azurewebsites.net/health

# API docs
https://your-app-name.azurewebsites.net/docs

# API info
https://your-app-name.azurewebsites.net/
```

## 🛠️ Common Configuration Tasks

### View Logs
```powershell
az webapp log tail -g expense-tracker-rg -n expense-tracker-api
```

### Restart App Service
```powershell
az webapp restart -g expense-tracker-rg -n expense-tracker-api
```

### Update App Settings
```powershell
az webapp config appsettings set `
  -g expense-tracker-rg `
  -n expense-tracker-api `
  --settings KEY="VALUE"
```

## 📊 Pipeline Stages Explained

### Build Stage
- ✅ Install Python 3.12
- ✅ Install dependencies from `requirements.txt`
- ✅ Run pytest with coverage
- ✅ Publish test results
- ✅ Publish code coverage
- ✅ Archive application files
- ✅ Publish build artifacts

### Deploy to Development
- ✅ Triggers on `develop` branch
- ✅ Downloads build artifacts
- ✅ Deploys to Dev App Service
- ✅ No approval required

### Deploy to Production
- ✅ Triggers on `main` branch
- ✅ Downloads build artifacts
- ✅ Requires manual approval (if configured)
- ✅ Deploys to Production App Service

## 🔐 Required Permissions

**Azure Subscription:**
- Contributor role on resource group
- Or specific permissions to create App Service

**Azure DevOps:**
- Build Administrator
- Release Administrator
- Or Project Administrator

## 📝 Checklist Before First Deployment

- [ ] Azure subscription is active
- [ ] Resource group created
- [ ] App Service created with unique name
- [ ] App Service configured with Python 3.12 runtime
- [ ] Startup command configured
- [ ] App settings configured
- [ ] Azure DevOps project created
- [ ] Service connection created and named correctly
- [ ] Environments created (Development, Production)
- [ ] `azure-pipelines.yml` updated with your App Service name
- [ ] Code pushed to Azure Repos or GitHub
- [ ] Pipeline created in Azure DevOps
- [ ] First pipeline run successful

## 🎯 Next Steps After Deployment

1. **Test the API** at your App Service URL
2. **Set up Application Insights** for monitoring
3. **Configure custom domain** (optional)
4. **Enable HTTPS only**
5. **Set up deployment slots** for staging
6. **Configure auto-scaling** rules
7. **Set up alerts** for errors and performance
8. **Implement authentication** (Azure AD or API keys)

## 📚 Additional Resources

- Full deployment guide: `AZURE_DEPLOYMENT.md`
- Docker deployment: `DOCKER_DEPLOYMENT.md`
- Frontend setup: `frontend/README.md`
- Main documentation: `README.md`

## 🆘 Troubleshooting

**Pipeline fails on build:**
- Check Python version is 3.12
- Verify all dependencies in `requirements.txt`

**Pipeline fails on tests:**
- Review test results in Azure DevOps
- Check test logs for failures

**Deployment succeeds but app doesn't work:**
- Check App Service logs
- Verify startup command
- Check app settings (especially DATABASE_URL)
- Test health endpoint

**Service connection issues:**
- Verify subscription permissions
- Recreate service connection
- Check service principal hasn't expired

## 💡 Pro Tips

1. **Use variable groups** in Azure DevOps for shared variables
2. **Enable branch policies** to require PR reviews
3. **Set up deployment slots** for zero-downtime deployments
4. **Use Azure Key Vault** for secrets
5. **Enable Application Insights** from day one
6. **Configure auto-scaling** before going to production
7. **Set up backup** schedules for your App Service

---

**You're all set for Azure deployment! 🎉**
