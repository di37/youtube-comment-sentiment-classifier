# CI/CD Pipeline Status & Quick Reference

## ✅ What's Already Set Up

- ✅ **EC2 Instance**: 40.172.234.207
- ✅ **API Port**: 6889
- ✅ **ECR Push Script**: `deployment/deploy_to_ecr.py` (Python/boto3)
- ✅ **Primary Workflow**: `.github/workflows/cicd.yaml` (self-hosted runner)
- ✅ **Alternative Workflow**: `.github/workflows/deploy.yml` (SSH-based)
- ✅ **Docker Configuration**: `deployment/Dockerfile` + `docker-compose.yaml`

## 🎯 Current Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Developer pushes to main branch                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  GitHub Actions (cicd.yaml)     │
         └──────────────┬──────────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
   ┌────────────────┐     ┌─────────────────┐
   │  Lint & Test   │     │ Build & Push    │
   │  (GitHub)      │ ──> │ to ECR          │
   └────────────────┘     └────────┬────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Self-Hosted Runner  │
                        │  (EC2: 40.172.234.207│
                        │  - Pull from ECR     │
                        │  - Stop old container│
                        │  - Run new container │
                        │  - Health check 6889 │
                        └──────────────────────┘
                                   │
                                   ▼
                        🌐 API Live at:
                        http://40.172.234.207:6889
```

## 🔑 Required Configuration

### 1. GitHub Secrets (Must Configure)

Go to: **GitHub → Settings → Secrets and variables → Actions**

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | AWS IAM Console |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | AWS IAM Console |
| `AWS_REGION` | `me-central-1` | Your AWS region |
| `ECR_REPOSITORY_NAME` | `isham/simple-ml-app` | From `deploy_to_ecr.py` line 69 |
| `AWS_ECR_LOGIN_URI` | `384887233198.dkr.ecr.me-central-1.amazonaws.com` | From `deploy_to_ecr.py` line 68, 78 |

**Optional (for SSH deployment via deploy.yml):**
| `EC2_USER` | `ubuntu` | SSH username |
| `EC2_SSH_KEY` | Content of your `.pem` file | `cat your-key.pem` |

### 2. Self-Hosted Runner Setup (For cicd.yaml)

**On GitHub:**
1. Settings → Actions → Runners → New self-hosted runner
2. Copy the configuration commands

**On EC2 (40.172.234.207):**
```bash
ssh -i your-key.pem ubuntu@40.172.234.207

# Download and configure runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN

# Install and start as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 3. EC2 Security Group

Ensure these ports are open:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH access |
| 6889 | TCP | 0.0.0.0/0 | API access |
| 443 | TCP | 0.0.0.0/0 | HTTPS (outbound) for ECR |

```bash
# Quick command to allow port 6889
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXX \
  --protocol tcp \
  --port 6889 \
  --cidr 0.0.0.0/0 \
  --region me-central-1
```

## 🚀 How to Deploy

### Option 1: Automatic (Recommended)

```bash
# Just push to main!
git add .
git commit -m "your message"
git push origin main

# Pipeline automatically:
# 1. Lints code
# 2. Runs tests
# 3. Builds Docker image
# 4. Pushes to ECR
# 5. Deploys to EC2:6889
```

### Option 2: Manual ECR Push

```bash
# Use your existing Python script
cd deployment
python deploy_to_ecr.py

# Then manually deploy on EC2
ssh ubuntu@40.172.234.207
./deployment/deploy_to_ec2.sh
```

### Option 3: Manual SSH Deployment

1. Go to GitHub → Actions
2. Select "CI/CD Pipeline - SSH Deployment"
3. Click "Run workflow"

## 📊 Quick Checks

### Is the pipeline working?

```bash
# 1. Check GitHub Actions
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# 2. Check runner status
ssh ubuntu@40.172.234.207
cd ~/actions-runner
sudo ./svc.sh status

# 3. Check container on EC2
docker ps | grep youtube-sentiment-api

# 4. Test API
curl http://40.172.234.207:6889/health
```

### Is the API accessible?

```bash
# Health check
curl http://40.172.234.207:6889/health

# API documentation
open http://40.172.234.207:6889/docs

# Test prediction
curl -X POST "http://40.172.234.207:6889/predict" \
  -H "Content-Type: application/json" \
  -d '{"comment": "This is amazing!"}'
```

## 🐛 Quick Troubleshooting

### Pipeline not triggering?
- Check `.github/workflows/cicd.yaml` is in `main` branch
- Verify you pushed to `main` (not another branch)
- Check GitHub Actions is enabled in Settings

### Build fails?
```bash
# Test locally
docker build -f deployment/Dockerfile -t test .
```

### Deployment fails?
```bash
# SSH to EC2 and check logs
ssh ubuntu@40.172.234.207
docker logs youtube-sentiment-api
```

### Health check fails?
```bash
# From EC2
curl http://localhost:6889/health

# Check container
docker ps -a | grep youtube-sentiment-api

# View logs
docker logs -f youtube-sentiment-api
```

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       ├── cicd.yaml          # Primary: Auto-deploy with self-hosted runner
│       ├── deploy.yml         # Alternative: SSH-based deployment
│       └── README.md          # Workflows documentation
├── deployment/
│   ├── deploy_to_ecr.py      # ✅ Your existing ECR push script
│   ├── deploy_to_ec2.sh      # Manual EC2 deployment script
│   ├── Dockerfile            # Docker image definition
│   ├── docker-compose.yaml   # Local dev setup
│   └── README.md             # Deployment docs
├── CICD_SETUP_GUIDE.md       # Complete setup guide
├── PIPELINE_STATUS.md        # This file
└── app.py                    # FastAPI application
```

## 🎯 Next Steps

1. **Configure GitHub Secrets** (5 minutes)
   - Add AWS credentials
   - Add ECR repository details

2. **Set up Self-Hosted Runner** (10 minutes)
   - Download runner on EC2
   - Configure and start service

3. **Test Pipeline** (2 minutes)
   - Make a small change
   - Push to main
   - Watch Actions tab

4. **Verify Deployment** (1 minute)
   - Visit http://40.172.234.207:6889/health
   - Check http://40.172.234.207:6889/docs

## 📞 Support Resources

- **Setup Guide**: See `CICD_SETUP_GUIDE.md`
- **Workflows**: See `.github/workflows/README.md`
- **Deployment**: See `deployment/README.md`

## ✅ Success Checklist

- [ ] GitHub secrets configured
- [ ] Self-hosted runner installed and running
- [ ] Security group allows port 6889
- [ ] Pushed code to main branch
- [ ] Pipeline completed successfully
- [ ] Container running on EC2
- [ ] Health endpoint responds
- [ ] API docs accessible

---

**Quick Links:**
- API: http://40.172.234.207:6889
- Docs: http://40.172.234.207:6889/docs
- Health: http://40.172.234.207:6889/health

**Commands:**
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# View container logs
docker logs -f youtube-sentiment-api

# Restart container
docker restart youtube-sentiment-api

# Check runner
cd ~/actions-runner && sudo ./svc.sh status
```

