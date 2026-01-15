# Railway Deployment Guide - Step by Step

Complete guide to deploy your DD1750 Generator on Railway.app

---

## 🎯 Pre-Deployment Checklist

Before you start:
- ✅ GitHub account connected to Claude AI
- ✅ Railway account created (railway.app)
- ✅ This code pushed to your GitHub repository
- ✅ Tested locally (optional but recommended)

---

## 📦 Step 1: Push to GitHub

### If you haven't already:

```bash
# Initialize git in your project directory
cd dd1750-generator-railway
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: DD1750 Generator with OCR"

# Create repository on GitHub (do this in GitHub UI first)
# Then connect it:
git remote add origin https://github.com/YOUR_USERNAME/dd1750-generator-railway.git

# Push
git push -u origin main
```

### Files that should be in your repo:
```
dd1750-generator-railway/
├── app.py
├── dd1750_ocr.py
├── dd1750_core.py
├── Dockerfile
├── requirements.txt
├── railway.json
├── .gitignore
├── README.md
├── RAILWAY_DEPLOYMENT_GUIDE.md (this file)
└── templates/
    └── index.html
```

---

## 🚂 Step 2: Deploy on Railway

### Method A: Deploy via Railway Dashboard (Easiest)

1. **Go to [railway.app](https://railway.app)**

2. **Sign in with GitHub**
   - Click "Login"
   - Choose "Continue with GitHub"
   - Authorize Railway

3. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `dd1750-generator-railway` repository

4. **Railway Auto-Detects Configuration**
   - Railway sees your Dockerfile
   - Automatically uses it for build
   - Sets up environment

5. **Wait for Build** (3-5 minutes)
   - Watch the build logs
   - Railway installs system dependencies
   - Builds Docker image
   - Deploys application

6. **Get Your URL**
   - Once deployed, Railway assigns a URL
   - Format: `https://your-app-name.up.railway.app`
   - Click "View App" or copy the URL

7. **Test Your Deployment**
   - Open the URL in your browser
   - You should see the DD1750 Generator interface
   - Try uploading a BOM to test

### Method B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project (in your project directory)
cd dd1750-generator-railway
railway link

# Deploy
railway up

# Get URL
railway open
```

---

## ⚙️ Step 3: Configure Environment Variables (Optional but Recommended)

### In Railway Dashboard:

1. **Go to your project**

2. **Click on "Variables" tab**

3. **Add these variables:**

| Variable | Value | Why |
|----------|-------|-----|
| `SECRET_KEY` | [random-string-here] | Secures session cookies |
| `FLASK_ENV` | `production` | Production mode |

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

4. **Click "Add" for each variable**

5. **Railway will automatically redeploy** with new variables

---

## 🔍 Step 4: Verify Deployment

### Check Health Endpoint:
```
https://your-app.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "dd1750-generator"
}
```

### Test Full Workflow:

1. **Upload Files**
   - Go to your Railway URL
   - Upload a BOM PDF
   - Upload a blank DD1750 template

2. **OCR Processing**
   - Should see "Processing BOM with OCR..."
   - Wait 30-60 seconds

3. **Review Items**
   - Should see extracted items in table
   - Check confidence scores
   - Edit if needed

4. **Generate DD1750**
   - Verify all items
   - Click "Generate DD1750"
   - Should download PDF

---

## 📊 Step 5: Monitor Your Deployment

### Railway Dashboard Features:

1. **Logs**
   - Click "View Logs"
   - See real-time application logs
   - Check for errors

2. **Metrics**
   - View CPU usage
   - View memory usage
   - View request count

3. **Deployments**
   - See deployment history
   - Roll back if needed
   - View build logs

---

## 🔧 Troubleshooting Common Issues

### Issue: Build Failed

**Check:**
- Dockerfile is in root directory
- All files committed to Git
- requirements.txt has all dependencies

**Solution:**
```bash
# Verify files in repo
git ls-files

# Should see:
# Dockerfile
# requirements.txt
# app.py
# etc.
```

### Issue: App Crashes on Start

**Check Railway Logs:**
1. Go to Railway dashboard
2. Click "View Logs"
3. Look for error messages

**Common causes:**
- Missing PORT environment variable (Railway should set this automatically)
- Import errors (missing dependencies)
- Tesseract not installed (check Dockerfile)

**Solution:**
Check that Dockerfile includes:
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0
```

### Issue: OCR Not Working

**Symptoms:**
- Upload works but processing fails
- "Error during upload" message

**Check:**
1. Railway logs for specific error
2. File size (max 50MB)
3. PDF is valid format

**Solution:**
- Ensure Tesseract installed (check build logs)
- Try with different PDF
- Check Railway logs for specific error

### Issue: Slow Performance

**Causes:**
- Large PDF files
- High-resolution scans
- Railway free tier limits

**Solutions:**
1. Upgrade to Railway Pro ($20/month)
2. Reduce PDF file size before upload
3. Use lower resolution scans (300 DPI is sufficient)

### Issue: Session Lost / Can't Generate

**Cause:**
- Session expired
- Railway restarted
- SECRET_KEY changed

**Solution:**
1. Set persistent SECRET_KEY in Railway variables
2. Upload files again
3. Check that cookies are enabled in browser

---

## 🚀 Step 6: Custom Domain (Optional)

### Add Your Own Domain:

1. **In Railway Dashboard:**
   - Go to Settings
   - Click "Domains"
   - Click "Add Domain"

2. **Enter your domain:**
   - Example: `dd1750.yourunit.mil`

3. **Configure DNS:**
   - Add CNAME record:
   ```
   Type: CNAME
   Name: dd1750
   Value: your-app.railway.app
   ```

4. **Wait for DNS propagation** (5-60 minutes)

5. **Access via custom domain:**
   - `https://dd1750.yourunit.mil`

---

## 📈 Step 7: Scaling (For Heavy Use)

### If you need more performance:

1. **Upgrade to Railway Pro**
   - $20/month
   - Better performance
   - More resources

2. **Enable Autoscaling**
   - Railway dashboard → Settings
   - Adjust worker count in Dockerfile:
   ```dockerfile
   CMD gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app
   ```
   - More workers = handle more concurrent requests

3. **Monitor Usage**
   - Check Railway metrics
   - Watch for bottlenecks
   - Adjust as needed

---

## 🔒 Step 8: Security Best Practices

### For Production Use:

1. **Set Strong SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Add to Railway variables

2. **Enable HTTPS Only** (Railway does this automatically)

3. **Set Secure Cookie Flags** (Already in code)
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   ```

4. **Regular Updates**
   - Update dependencies monthly
   - Monitor for security patches
   - Test before deploying updates

5. **Access Control** (Future enhancement)
   - Add user authentication
   - Limit to authorized users
   - Implement rate limiting

---

## 📱 Step 9: Share with Your Unit

### Once deployed and tested:

1. **Share the URL:**
   ```
   https://your-app.railway.app
   ```

2. **Create User Guide:**
   - Screenshot the interface
   - Write step-by-step instructions
   - Include examples

3. **Train Users:**
   - 15-minute demo
   - Hands-on practice
   - Q&A session

4. **Set Up Support:**
   - Create email/chat channel
   - Document common issues
   - Be available for questions

---

## 🆘 Getting Help

### If you run into issues:

1. **Check Railway Logs**
   - Most informative for debugging

2. **Search Railway Community**
   - https://help.railway.app

3. **Check GitHub Issues**
   - Look for similar problems
   - Open new issue if needed

4. **Railway Discord**
   - Active community
   - Railway staff available

5. **Email Support**
   - For urgent production issues

---

## ✅ Deployment Success Checklist

Use this checklist to verify your deployment:

### Pre-Deployment
- [ ] Code pushed to GitHub
- [ ] Dockerfile in root directory
- [ ] requirements.txt complete
- [ ] Tested locally (optional)

### Deployment
- [ ] Railway project created
- [ ] GitHub repo connected
- [ ] Build completed successfully
- [ ] App is running (check logs)
- [ ] URL is accessible

### Configuration
- [ ] SECRET_KEY set in Railway
- [ ] Environment variables configured
- [ ] Logs are readable
- [ ] Metrics visible

### Testing
- [ ] Health endpoint responds
- [ ] Can upload files
- [ ] OCR processes correctly
- [ ] Items display in table
- [ ] Can edit items
- [ ] Verification works
- [ ] DD1750 generates
- [ ] PDF downloads correctly

### Production Ready
- [ ] Tested with 10+ real BOMs
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] User guide created
- [ ] Support plan in place
- [ ] Unit trained
- [ ] Monitoring set up

---

## 🎉 You're Done!

Your DD1750 Generator is now live on Railway!

**Next Steps:**
1. Test thoroughly with real BOMs
2. Train your unit
3. Monitor usage
4. Collect feedback
5. Iterate and improve

**Remember:**
- Railway URL: `https://your-app.railway.app`
- Health check: `https://your-app.railway.app/health`
- Logs: Railway Dashboard → View Logs

---

**Questions?**
- Check Railway docs: https://docs.railway.app
- Review this guide again
- Open GitHub issue
- Contact Railway support

**Good luck with your deployment! 🚂🎖️**
