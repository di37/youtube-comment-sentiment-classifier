# ✅ CI/CD Pipeline Setup Complete

## 📦 What Was Created

Your CI/CD pipeline is now ready to deploy to **EC2: 40.172.234.207** on **port 6889**.

### 1. GitHub Actions Workflows

- ✅ **`.github/workflows/cicd.yaml`** - Primary workflow (self-hosted runner)
  - Auto-deploys on push to `main`
  - Includes linting, testing, build, push, and deployment
  
- ✅ **`.github/workflows/deploy.yml`** - Alternative workflow (SSH-based)
  - Manual trigger via GitHub Actions UI
  - No self-hosted runner required

- ✅ **`.github/workflows/README.md`** - Workflows documentation

### 2. Documentation

- ✅ **`CICD_SETUP_GUIDE.md`** - Complete setup instructions
- ✅ **`PIPELINE_STATUS.md`** - Quick reference and status
- ✅ **`deployment/README.md`** - Updated deployment docs
- ✅ **`deployment/deploy_to_ec2.sh`** - Manual deployment script

## 🎯 Pipeline Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Your Existing Setup                                      │
├──────────────────────────────────────────────────────────┤
│ ✓ EC2 Instance: 40.172.234.207                          │
│ ✓ API Port: 6889                                         │
│ ✓ ECR Script: deployment/deploy_to_ecr.py               │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│ New CI/CD Pipeline (cicd.yaml)                          │
├──────────────────────────────────────────────────────────┤
│ 1. Push to main → Triggers workflow                     │
│ 2. Lint & Test (GitHub runner)                          │
│ 3. Build Docker image (GitHub runner)                   │
│ 4. Push to ECR (GitHub runner)                          │
│ 5. Pull & Deploy (Self-hosted runner on EC2)            │
│ 6. Health check at http://40.172.234.207:6889/health    │
└──────────────────────────────────────────────────────────┘
```

## ⚡ Quick Start - 3 Steps to Production

### Step 1: Configure GitHub Secrets (5 minutes)

Go to: **GitHub → Your Repo → Settings → Secrets and variables → Actions**

Click "New repository secret" and add these **5 required secrets**:

```bash
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=me-central-1
ECR_REPOSITORY_NAME=isham/simple-ml-app
AWS_ECR_LOGIN_URI=384887233198.dkr.ecr.me-central-1.amazonaws.com
```

**Quick way using GitHub CLI:**
```bash
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
gh secret set AWS_REGION
gh secret set ECR_REPOSITORY_NAME
gh secret set AWS_ECR_LOGIN_URI
```

### Step 2: Set Up Self-Hosted Runner (10 minutes)

**On GitHub:**
1. Go to **Settings → Actions → Runners**
2. Click **New self-hosted runner**
3. Select **Linux** and **x64**
4. Copy the setup commands

**On your EC2 (40.172.234.207):**
```bash
# SSH into your EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Create runner directory
mkdir actions-runner && cd actions-runner

# Download runner (paste command from GitHub)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (paste command from GitHub, it will include your token)
./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_GENERATED_TOKEN

# When asked for labels, enter: self-hosted, self-hosted-me-central

# Install and start as a service
sudo ./svc.sh install
sudo ./svc.sh start

# Verify it's running
sudo ./svc.sh status
```

Go back to GitHub and you should see your runner with a green "Idle" status!

### Step 3: Test the Pipeline (2 minutes)

```bash
# Make a small change
echo "" >> README.md

# Commit and push to main
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main

# Go to GitHub → Actions tab and watch the pipeline run!
```

## 🎉 Success Indicators

After the pipeline completes, you should see:

✅ **GitHub Actions**: All jobs green  
✅ **EC2 Container**: `docker ps` shows `youtube-sentiment-api` running  
✅ **Health Check**: `curl http://40.172.234.207:6889/health` returns 200  
✅ **API Docs**: http://40.172.234.207:6889/docs accessible  

## 🔧 Your Existing Tools Still Work

Your existing `deployment/deploy_to_ecr.py` script still works for manual deployments:

```bash
cd deployment
python deploy_to_ecr.py
```

## 📊 What Happens When You Push Code

1. **Code pushed to main** → GitHub Actions triggered
2. **Continuous Integration** (GitHub-hosted runner)
   - Lints code with flake8
   - Runs unit tests
3. **Build & Push to ECR** (GitHub-hosted runner)
   - Builds Docker image from `deployment/Dockerfile`
   - Pushes to AWS ECR with `latest` tag
4. **Deploy to EC2** (Self-hosted runner on 40.172.234.207)
   - Pulls latest image from ECR
   - Stops old `youtube-sentiment-api` container
   - Starts new container on port 6889
   - Runs health check
   - Cleans up old images
5. **Your API is live!** 🚀

## 🐛 Troubleshooting

### Runner Not Showing Up?
```bash
ssh ubuntu@40.172.234.207
cd ~/actions-runner
sudo ./svc.sh status
# If not running:
sudo ./svc.sh start
```

### Pipeline Failing?
- Check GitHub Actions logs (Actions tab → Click on workflow run)
- Common issues:
  - GitHub secrets not configured
  - Runner not running on EC2
  - Security group blocking port 6889

### Container Not Starting?
```bash
ssh ubuntu@40.172.234.207
docker logs youtube-sentiment-api
docker ps -a | grep youtube
```

### Can't Access API?
```bash
# Test from EC2 first (should work)
ssh ubuntu@40.172.234.207
curl http://localhost:6889/health

# Check security group allows port 6889 from your IP
aws ec2 describe-security-groups --filters "Name=ip-permission.to-port,Values=6889" --region me-central-1
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `PIPELINE_STATUS.md` | Quick reference and status |
| `CICD_SETUP_GUIDE.md` | Complete detailed setup guide |
| `.github/workflows/README.md` | Workflows documentation |
| `deployment/README.md` | Deployment scripts guide |

## 🎯 Next Actions

1. [ ] **Configure GitHub Secrets** (see Step 1 above)
2. [ ] **Install Self-Hosted Runner** on EC2 (see Step 2 above)
3. [ ] **Ensure Security Group** allows port 6889
4. [ ] **Test Pipeline** by pushing to main (see Step 3 above)
5. [ ] **Verify API** at http://40.172.234.207:6889

## 💡 Pro Tips

- **Watch the first run carefully** - check all steps complete successfully
- **Keep runner running** - monitor with `sudo ./svc.sh status`
- **Check logs often** - `docker logs -f youtube-sentiment-api`
- **Use health check** - `curl http://40.172.234.207:6889/health` before deploying new features

## 🆘 Need Help?

1. Check `PIPELINE_STATUS.md` for quick troubleshooting
2. Review `CICD_SETUP_GUIDE.md` for detailed instructions  
3. Check GitHub Actions logs for error messages
4. SSH to EC2 and check Docker logs

---

**Your Deployment Info:**
- EC2: 40.172.234.207
- Port: 6889
- Container: youtube-sentiment-api
- ECR Repo: isham/simple-ml-app
- Region: me-central-1

**Quick Commands:**
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@40.172.234.207

# Check runner
cd ~/actions-runner && sudo ./svc.sh status

# Check container
docker ps | grep youtube-sentiment-api

# View logs
docker logs -f youtube-sentiment-api

# Test API
curl http://localhost:6889/health
```

🎉 **Your CI/CD pipeline is ready to deploy!**

