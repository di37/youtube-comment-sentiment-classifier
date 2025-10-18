# GitHub Actions Workflows

This directory contains two CI/CD workflows for deploying the YouTube Sentiment Classifier to EC2 at **40.172.234.207:6889**.

## 📋 Available Workflows

### 1. `cicd.yaml` - Self-Hosted Runner Deployment (Recommended)

**Status**: ✅ **Primary workflow** - Auto-deploys on push to `main`

**Features:**
- ✅ Automatic deployment when code is pushed to `main`
- ✅ Continuous Integration (lint + test)
- ✅ Build and push Docker image to AWS ECR
- ✅ Deploy to EC2 using self-hosted runner
- ✅ Health checks and automatic cleanup

**Requirements:**
- Self-hosted GitHub Actions runner on EC2
- GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REPOSITORY_NAME`, `AWS_ECR_LOGIN_URI`

**How it works:**
```yaml
on:
  push:
    branches: [main]
```

**Jobs:**
1. **Integration** (ubuntu-latest)
   - Lint with flake8
   - Run unit tests
   
2. **Build-and-Push** (ubuntu-latest)
   - Build Docker image
   - Push to AWS ECR
   
3. **Continuous-Deployment** (self-hosted runner on EC2)
   - Pull image from ECR
   - Stop old container
   - Run new container on port 6889
   - Health check
   - Cleanup old images

---

### 2. `deploy.yml` - SSH-Based Deployment (Alternative)

**Status**: ⚡ **Manual trigger only** - For when self-hosted runner is unavailable

**Features:**
- ✅ No self-hosted runner required
- ✅ SSH-based deployment from GitHub-hosted runners
- ✅ Hardcoded EC2 IP: 40.172.234.207
- ⚠️ Manual trigger only (workflow_dispatch)

**Additional Requirements:**
- GitHub Secrets: `EC2_USER`, `EC2_SSH_KEY` (in addition to AWS secrets)

**How to use:**
1. Go to **Actions** tab in GitHub
2. Select "CI/CD Pipeline - SSH Deployment"
3. Click **Run workflow**
4. Choose `main` branch
5. Click **Run workflow**

**Jobs:**
1. **Build-and-Push** (ubuntu-latest)
   - Build and push to ECR
   
2. **Deploy-to-EC2-SSH** (ubuntu-latest)
   - SSH into EC2 at 40.172.234.207
   - Execute deployment script
   - Pull and run container
   - Health check

---

## 🔑 Required GitHub Secrets

### For Both Workflows:

| Secret | Description | Example |
|--------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | `wJalrXUtnFEMI/K7MDENG/...` |
| `AWS_REGION` | AWS region | `me-central-1` |
| `ECR_REPOSITORY_NAME` | ECR repository name | `isham/simple-ml-app` |
| `AWS_ECR_LOGIN_URI` | ECR registry URI | `384887233198.dkr.ecr.me-central-1.amazonaws.com` |

### Additional for SSH Deployment (`deploy.yml`):

| Secret | Description | Example |
|--------|-------------|---------|
| `EC2_USER` | SSH username | `ubuntu` |
| `EC2_SSH_KEY` | Private SSH key (PEM file content) | `-----BEGIN RSA PRIVATE KEY-----\n...` |

## 🚀 Setting Up GitHub Secrets

### Via GitHub Web UI:

1. Go to repository **Settings**
2. **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with name and value

### Via GitHub CLI:

```bash
# Install GitHub CLI: https://cli.github.com/

# Authenticate
gh auth login

# Set AWS secrets
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
gh secret set AWS_REGION
gh secret set ECR_REPOSITORY_NAME
gh secret set AWS_ECR_LOGIN_URI

# Set SSH secrets (for deploy.yml)
gh secret set EC2_USER
gh secret set EC2_SSH_KEY < /path/to/your-key.pem
```

## 🏃 Self-Hosted Runner Setup

### On GitHub:

1. Go to **Settings** → **Actions** → **Runners**
2. Click **New self-hosted runner**
3. Select **Linux** and **x64**
4. Copy the download and configuration commands

### On EC2 (40.172.234.207):

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Create runner directory
mkdir actions-runner && cd actions-runner

# Download runner (check GitHub for latest version)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (use the command from GitHub UI)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN

# When prompted for labels, add: self-hosted, self-hosted-me-central

# Install as service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

## 📊 Workflow Comparison

| Feature | cicd.yaml (Self-Hosted) | deploy.yml (SSH) |
|---------|------------------------|------------------|
| **Trigger** | Automatic (push to main) | Manual only |
| **Runner** | Self-hosted on EC2 | GitHub-hosted |
| **Speed** | Fast (no SSH overhead) | Slower (SSH setup) |
| **Setup** | Requires runner install | Just SSH key needed |
| **Use Case** | Production (automated) | Backup/emergency |
| **Linting** | ✅ Yes | ❌ No |
| **Testing** | ✅ Yes | ❌ No |

## 🔄 Typical Deployment Flow

### Using cicd.yaml (Recommended):

```bash
# 1. Make changes locally
git add .
git commit -m "feat: add new feature"

# 2. Push to main branch
git push origin main

# 3. Pipeline automatically:
#    - Lints and tests code
#    - Builds Docker image
#    - Pushes to ECR
#    - Deploys to EC2:40.172.234.207:6889
#    - Runs health check

# 4. Access your API
curl http://40.172.234.207:6889/health
```

### Using deploy.yml (Manual):

1. Go to GitHub **Actions** tab
2. Select "CI/CD Pipeline - SSH Deployment"
3. Click **Run workflow** button
4. Wait for completion
5. Access API at http://40.172.234.207:6889

## 🐛 Troubleshooting

### Self-Hosted Runner Issues

```bash
# Check runner status
ssh ubuntu@40.172.234.207
cd ~/actions-runner
sudo ./svc.sh status

# View logs
sudo journalctl -u actions.runner.* -f

# Restart runner
sudo ./svc.sh restart
```

### Pipeline Failures

**Build fails:**
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Review build logs in GitHub Actions

**ECR push fails:**
- Verify AWS credentials are correct
- Check ECR repository exists
- Ensure IAM permissions for ECR

**Deployment fails:**
- Check Docker is running on EC2: `docker ps`
- Verify AWS CLI configured on EC2: `aws configure list`
- Check security group allows port 6889

**Container won't start:**
```bash
# SSH to EC2
docker logs youtube-sentiment-api
docker inspect youtube-sentiment-api
```

### Health Check Fails

```bash
# From EC2
curl http://localhost:6889/health

# Check container
docker ps | grep youtube-sentiment-api

# Check logs
docker logs -f youtube-sentiment-api
```

## 📈 Monitoring

### View Workflow Runs:

1. Go to **Actions** tab
2. Click on any workflow run
3. Expand jobs to see detailed logs

### Monitor Container on EC2:

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Live logs
docker logs -f youtube-sentiment-api

# Container stats
docker stats youtube-sentiment-api

# List all containers
docker ps -a
```

## 🎯 Next Steps

1. ✅ Ensure GitHub secrets are configured
2. ✅ Set up self-hosted runner on EC2 (for cicd.yaml)
3. ✅ Configure security group for port 6889
4. ✅ Push code to main to trigger pipeline
5. ✅ Verify deployment at http://40.172.234.207:6889

## 📚 Related Documentation

- **[CICD_SETUP_GUIDE.md](../../CICD_SETUP_GUIDE.md)** - Complete setup instructions
- **[deployment/README.md](../../deployment/README.md)** - Deployment scripts
- **[deployment/deploy_to_ecr.py](../../deployment/deploy_to_ecr.py)** - Manual ECR push script

---

**EC2 Instance**: 40.172.234.207  
**API Port**: 6889  
**Container Name**: youtube-sentiment-api  
**ECR Repository**: isham/simple-ml-app  
**Region**: me-central-1
