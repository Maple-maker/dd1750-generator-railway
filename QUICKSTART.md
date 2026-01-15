# Quick Start Guide

Get the DD1750 Generator running in 5 minutes!

---

## 🚂 Deploy to Railway (Fastest - Recommended)

**Takes 5 minutes:**

1. **Push code to GitHub** (if not already done)
2. **Go to [railway.app](https://railway.app)** and sign in with GitHub
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your repository**
5. **Wait 3-5 minutes for build**
6. **Done!** Railway gives you a URL like `https://your-app.railway.app`

**Detailed instructions:** See `RAILWAY_DEPLOYMENT_GUIDE.md`

---

## 💻 Run Locally (For Testing)

**Takes 10 minutes:**

### Prerequisites:
```bash
# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils

# macOS:
brew install tesseract poppler

# Windows: Download from
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Quick Start:
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dd1750-generator-railway.git
cd dd1750-generator-railway

# Run the startup script
./run.sh

# Or manually:
pip install -r requirements.txt
python app.py
```

### Access:
Open your browser to: **http://localhost:8000**

---

## 📋 How to Use

1. **Upload BOM PDF**
   - Any format: printed, scanned, handwritten
   - Max 50MB

2. **Upload DD1750 Template**
   - Blank DD1750 form (PDF)

3. **Click "Extract Items with OCR"**
   - Wait 30-60 seconds

4. **Review & Verify Items**
   - Edit any errors
   - Check each item's verification box
   - Generate button activates when all verified

5. **Click "Generate DD1750"**
   - Downloads instantly
   - Ready to print and use

---

## 🎯 Test Files

**Need test files?**

1. **BOM PDF**: Use any of your unit's BOMs
2. **Blank DD1750**: Download from:
   - [Army Publishing Directorate](https://armypubs.army.mil/)
   - Or use the `blank_1750.pdf` from the project files

---

## 🆘 Troubleshooting

### "Tesseract not found"
```bash
# Install it:
sudo apt-get install tesseract-ocr  # Ubuntu
brew install tesseract              # macOS
```

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Railway build failed
- Check that all files are pushed to GitHub
- Verify Dockerfile is in root directory
- Check Railway logs for specific error

---

## 📞 Need Help?

1. **Check the full guides:**
   - `README.md` - Complete documentation
   - `RAILWAY_DEPLOYMENT_GUIDE.md` - Railway-specific help

2. **Common issues:**
   - See Troubleshooting sections in guides

3. **Still stuck?**
   - Check Railway logs (if deployed)
   - Review error messages carefully
   - Search GitHub issues

---

## ✅ Success Checklist

**Local Development:**
- [ ] Tesseract installed
- [ ] Python dependencies installed
- [ ] App running at localhost:8000
- [ ] Can upload files
- [ ] OCR works
- [ ] DD1750 generates

**Railway Deployment:**
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Build succeeded
- [ ] App accessible at Railway URL
- [ ] Full workflow tested
- [ ] Ready for production use

---

## 🎖️ Ready for Production?

**Before sharing with your unit:**

1. ✅ Test with 10+ real BOMs
2. ✅ Verify output meets Army standards
3. ✅ Train key users
4. ✅ Set up support channel
5. ✅ Monitor first week closely

---

**That's it! You're ready to generate DD1750s! 🚀**
