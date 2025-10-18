# CI/CD Pipeline Setup Guide

Complete guide for the YouTube Sentiment Classifier CI/CD pipeline deployment to EC2 at **40.172.234.207:6889**.

## 🎯 Pipeline Overview

You have **TWO** deployment options:

### Option 1: Self-Hosted Runner (Recommended - `cicd.yaml`)
- ✅ **Automatic deployment** on push to `main`
- ✅ Faster deployment (no SSH overhead)
- ✅ Already configured in `cicd.yaml`
- ⚠️ Requires GitHub Actions runner installed on EC2

### Option 2: SSH Deployment (`deploy.yml`)
- ✅ No runner setup required
- ✅ Works from GitHub-hosted runners
- ⚠️ Manual trigger only
- ⚠️ Requires SSH key configuration

## 📦 Current Setup

- **EC2 Instance**: `40.172.234.207`
- **API Port**: `6889`
- **ECR Push Script**: `deployment/deploy_to_ecr.py` (boto3-based)
- **Primary Workflow**: `.github/workflows/cicd.yaml` (self-hosted runner)
- **Alternative Workflow**: `.github/workflows/deploy.yml` (SSH-based)

## 🚀 Quick Start (Self-Hosted Runner - Recommended)

### Required GitHub Secrets

Configure these secrets in GitHub (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCY` |
| `AWS_REGION` | AWS region | `me-central-1` |
| `ECR_REPOSITORY_NAME` | ECR repository name | `isham/simple-ml-app` |
| `AWS_ECR_LOGIN_URI` | ECR registry URI | `384887233198.dkr.ecr.me-central-1.amazonaws.com` |

### How It Works

1. **Push code to main** → Pipeline automatically triggers
2. **Build & Test** (ubuntu-latest runner)
   - Lint code with flake8
   - Run unit tests
3. **Build & Push to ECR** (ubuntu-latest runner)
   - Build Docker image from `deployment/Dockerfile`
   - Push to AWS ECR
4. **Deploy to EC2** (self-hosted runner on EC2)
   - Pull latest image from ECR
   - Stop old container
   - Start new container on port 6889
   - Health check at `http://localhost:6889/health`

### Pipeline Flow

```
Push to main
     │
     ▼
┌────────────────┐
│ Lint & Test    │ (GitHub-hosted)
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Build & Push   │ (GitHub-hosted)
│ to ECR         │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Pull & Deploy  │ (Self-hosted on EC2: 40.172.234.207)
│ Port: 6889     │
└────────────────┘
```

## 🔧 Setting Up Self-Hosted Runner on EC2

If you haven't set up the self-hosted runner yet:

### 1. On GitHub

1. Go to your repository → **Settings** → **Actions** → **Runners**
2. Click **New self-hosted runner**
3. Select **Linux** and **x64**
4. Copy the download and configuration commands

### 2. On EC2 (40.172.234.207)

SSH into your EC2 instance:

```bash
ssh -i your-key.pem ubuntu@40.172.234.207
```

Follow the GitHub commands to download and configure the runner:

```bash
# Create a folder for the runner
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner (paste the config command from GitHub)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN

# Add custom labels when prompted
# Labels: self-hosted, self-hosted-me-central

# Install and start the runner as a service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 3. Verify Runner

- Go to GitHub → Settings → Actions → Runners
- You should see your runner with status "Idle" (green)

## 📝 Using the Python ECR Deployment Script

Your `deployment/deploy_to_ecr.py` script can be used for **manual deployments**:

### Prerequisites

```bash
pip install boto3 docker python-dotenv
```

### Configuration

Edit `deployment/deploy_to_ecr.py`:

```python
# Configuration (lines 67-75)
AWS_REGION = "me-central-1"
AWS_ACCOUNT_ID = "384887233198"
ECR_REPOSITORY = "isham/simple-ml-app"
IMAGE_TAG = "latest"
BUILD_PLATFORM = "linux/amd64"  # For standard EC2
```

### Usage

```bash
# Option 1: Run from deployment directory
cd deployment
python deploy_to_ecr.py

# Option 2: Run from project root
python deployment/deploy_to_ecr.py
```

The script will:
1. ✓ Authenticate with AWS ECR using boto3
2. ✓ Build Docker image (with cross-platform support)
3. ✓ Tag image for ECR
4. ✓ Push to ECR registry

## 🔐 EC2 Security Group Configuration

Ensure your EC2 security group allows:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | Your IP | Management access |
| Custom TCP | 6889 | 0.0.0.0/0 | API access (or restrict to your IP range) |
| HTTPS | 443 | 0.0.0.0/0 | Outbound for ECR pulls |

Update using AWS CLI:

```bash
# Get your security group ID
SECURITY_GROUP_ID=$(aws ec2 describe-instances \
  --filters "Name=ip-address,Values=40.172.234.207" \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text \
  --region me-central-1)

# Allow API access on port 6889
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 6889 \
  --cidr 0.0.0.0/0 \
  --region me-central-1
```

## 🌐 Accessing Your API

After deployment:

- **Health Check**: http://40.172.234.207:6889/health
- **API Documentation**: http://40.172.234.207:6889/docs
- **Root Endpoint**: http://40.172.234.207:6889/

Test the API:

```bash
# Health check
curl http://40.172.234.207:6889/health

# Test prediction
curl -X POST "http://40.172.234.207:6889/predict" \
  -H "Content-Type: application/json" \
  -d '{"comment": "This video is amazing!"}'
```

## 🔄 Alternative: SSH-Based Deployment

If you don't want to use self-hosted runners, use the SSH-based workflow:

### Additional Secrets Required

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `EC2_USER` | SSH username | `ubuntu` (or `ec2-user` for Amazon Linux) |
| `EC2_SSH_KEY` | Private key content | `cat your-key.pem` (copy entire output) |

### Manual Trigger

1. Go to **Actions** tab on GitHub
2. Select **CI/CD Pipeline - SSH Deployment**
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow**

## 🐛 Troubleshooting

### Pipeline Fails at Build Step

```bash
# Check Dockerfile syntax
docker build -f deployment/Dockerfile -t test .
```

### Pipeline Fails at ECR Push

```bash
# Verify ECR repository exists
aws ecr describe-repositories \
  --repository-names isham/simple-ml-app \
  --region me-central-1

# Check AWS credentials
aws sts get-caller-identity
```

### Self-Hosted Runner Not Working

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Check runner status
cd ~/actions-runner
sudo ./svc.sh status

# Restart runner
sudo ./svc.sh stop
sudo ./svc.sh start

# View runner logs
sudo journalctl -u actions.runner.* -f
```

### Container Not Starting

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Check container logs
docker logs youtube-sentiment-api

# Check if port is in use
sudo netstat -tuln | grep 6889

# Check Docker images
docker images | grep simple-ml-app

# Manually run container for testing
docker run -it --rm \
  -p 6889:6889 \
  -e AWS_ACCESS_KEY_ID="your-key" \
  -e AWS_SECRET_ACCESS_KEY="your-secret" \
  -e AWS_REGION="me-central-1" \
  -e MLFLOW_TRACKING_URI="http://3.29.129.159:5000" \
  384887233198.dkr.ecr.me-central-1.amazonaws.com/isham/simple-ml-app:latest
```

### Health Check Fails

```bash
# From EC2, check if app is listening
curl http://localhost:6889/health

# Check container is running
docker ps | grep youtube-sentiment-api

# Check security group allows port 6889
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.to-port,Values=6889" \
  --region me-central-1
```

## 📊 Monitoring Your Deployment

### View GitHub Actions Logs

1. Go to **Actions** tab
2. Click on latest workflow run
3. Expand each job to see detailed logs

### Monitor EC2 Container

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# View live logs
docker logs -f youtube-sentiment-api

# Check container stats
docker stats youtube-sentiment-api

# Check container health
docker inspect youtube-sentiment-api | grep -A 10 Health
```

### Set Up CloudWatch (Optional)

For production monitoring, consider:
- CloudWatch Container Insights
- CloudWatch Logs for application logs
- CloudWatch Alarms for health checks

## 🎉 Success Checklist

- [ ] GitHub secrets configured
- [ ] Self-hosted runner installed and running on EC2
- [ ] Security group allows port 6889
- [ ] Pipeline runs successfully on push to main
- [ ] Container starts and passes health check
- [ ] API accessible at http://40.172.234.207:6889
- [ ] API docs accessible at http://40.172.234.207:6889/docs

## 📚 Additional Resources

- **Workflows**:
  - Primary: `.github/workflows/cicd.yaml` (auto-deployment)
  - Alternative: `.github/workflows/deploy.yml` (manual SSH)
- **Scripts**:
  - ECR Push: `deployment/deploy_to_ecr.py`
  - Manual Deploy: `deployment/deploy_to_ec2.sh`
- **Documentation**:
  - Deployment: `deployment/README.md`
  - Workflow Details: `.github/workflows/README.md`

---

**Questions?** Check the troubleshooting section or review the workflow logs in GitHub Actions.
