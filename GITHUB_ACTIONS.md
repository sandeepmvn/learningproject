# GitHub Actions CI/CD Pipelines

This project includes automated CI/CD pipelines using GitHub Actions. These workflows automatically run tests, linting, and build checks on every push and pull request.

## 📋 Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:** Runs on every push to `main` or `develop` branches and on all pull requests

**Jobs:**

#### Backend Tests
- Sets up Python 3.12
- Installs dependencies from `requirements.txt`
- Runs pytest with coverage reporting
- Uploads coverage reports to Codecov

#### Frontend Lint & Build
- Sets up Node.js 18
- Installs dependencies from `frontend/package.json`
- Runs ESLint to check code quality
- Builds the React app with Vite

#### Docker Build
- Builds the Docker image (verification only, does not push)
- Uses Docker layer caching for faster builds

### 2. CD Workflow (`.github/workflows/cd.yml`)

**Triggers:** Runs automatically on push to `main` branch (after CI passes)

**Purpose:** Builds and pushes Docker image to GitHub Container Registry (GHCR)

**Features:**
- Automatically tags images with branch name, semantic version tags, and commit SHA
- Uses layer caching for efficient builds
- Requires `GITHUB_TOKEN` (automatically provided by GitHub)

## 🚀 Getting Started

### Prerequisites

1. **Ensure your repository is on GitHub** with these branches:
   - `main` (production)
   - `develop` (development)

2. **For frontend builds**, ensure `package-lock.json` exists:
   ```bash
   cd frontend
   npm install
   ```

3. **Commit the workflows**:
   ```bash
   git add .github/workflows/
   git commit -m "Add GitHub Actions CI/CD workflows"
   git push
   ```

### Enable Docker Image Publishing

The CD workflow automatically publishes to GitHub Container Registry. To pull images later, use:

```bash
docker pull ghcr.io/<your-org>/<your-repo>:latest
```

## 🔧 Configuration

### Update Python Version
If you need a different Python version, edit `.github/workflows/ci.yml`:
```yaml
matrix:
  python-version: ['3.11']  # Change here
```

### Update Node.js Version
If you need a different Node.js version, edit `.github/workflows/ci.yml`:
```yaml
node-version: '20'  # Change here
```

### Disable Jobs
Comment out jobs you don't need:
```yaml
# backend-tests:  # Disabled
# frontend-lint:  # Disabled
```

## 📊 Viewing Results

1. Go to your GitHub repository
2. Click the **Actions** tab
3. Select a workflow run to view:
   - ✅ Passed jobs (green)
   - ❌ Failed jobs (red)
   - Detailed logs for each step

## 🐛 Troubleshooting

### Tests Failing
- Check the logs in the GitHub Actions tab
- Ensure all tests pass locally: `pytest tests/ -v`

### Frontend Build Failing
- Verify Node modules: `cd frontend && npm install`
- Check for linting errors: `cd frontend && npm run lint`

### Docker Push Failing
- This only runs on pushes to `main` after all tests pass
- Check that your repository settings allow package publishing

## 🔐 Secrets & Permissions

No additional secrets required! The workflows use:
- `${{ secrets.GITHUB_TOKEN }}` - automatically provided
- Default GitHub Actions permissions

## 📈 Next Steps

1. **Test locally** before committing:
   ```bash
   pytest tests/ -v
   cd frontend && npm run lint
   docker build -t expense-tracker .
   ```

2. **Monitor** workflow runs in the Actions tab

3. **Create a release** to trigger semantic versioning in Docker tags

4. **Integrate** with deployment platforms (Azure, AWS, etc.) by adding deployment jobs

