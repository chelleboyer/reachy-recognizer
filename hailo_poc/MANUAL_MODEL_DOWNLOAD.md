# Manual Model Download Instructions

## The Problem
Pre-converted Hailo models aren't automatically included in the repos. You need to download them manually.

---

## ✅ EASIEST METHOD: Direct Download

### On your Windows laptop:

1. **Download YOLOv8n for Hailo-8L:**
   - Try this direct link (may need updating):
   ```
   https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8l/yolov8n.hef
   ```
   
2. **If link doesn't work, visit:**
   - Hailo Model Zoo: https://github.com/hailo-ai/hailo_model_zoo
   - Navigate to: `hailo_model_zoo/compiled/hailo8l/`
   - Download: `yolov8n.hef` (or similar YOLO variant)

3. **Transfer to Pi:**
   ```powershell
   # Via OneDrive
   Copy-Item yolov8n.hef "$env:USERPROFILE\OneDrive\reachy-models\"
   
   # Or via SCP
   scp yolov8n.hef pi@<pi-ip>:~/reachy-mini-dev/hailo_poc/models/
   ```

---

## 🔍 Alternative: Browse Hailo Developer Zone

### Option 1: Hailo Website (Requires Free Account)
1. Visit: https://hailo.ai/developer-zone/
2. Create free developer account
3. Navigate to Model Zoo
4. Download YOLOv8n for Hailo-8L
5. Transfer to Pi

### Option 2: GitHub Model Zoo
1. Visit: https://github.com/hailo-ai/hailo_model_zoo
2. Browse to: `hailo_model_zoo/compiled/hailo8l/`
3. Look for:
   - `yolov8n.hef` (nano - fastest)
   - `yolov8s.hef` (small - more accurate)
   - `yolov5n.hef` (alternative)

---

## 📦 On Raspberry Pi (if you have internet)

### Automated attempt:
```bash
cd ~/reachy-mini-dev/hailo_poc
chmod +x download_models_manual.sh
./download_models_manual.sh
```

This script will:
1. Search hailo-rpi5-examples for models
2. Try to wget YOLOv8n directly
3. Offer to clone Model Zoo
4. Give manual download instructions

### Manual wget (if you have the URL):
```bash
cd ~/reachy-mini-dev/hailo_poc/models
wget https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8l/yolov8n.hef

# Check file downloaded
ls -lh yolov8n.hef
# Should be ~6-15 MB
```

---

## 🎯 What You Need

**Minimum requirement:**
- One `.hef` model file for Hailo-8L
- Preferably: `yolov8n.hef` (best for face detection)
- Alternative: `yolov5n.hef` or `yolov8s.hef`

**File size:** 5-50 MB (varies by model)
**Format:** `.hef` (Hailo Executable Format)
**Target:** Hailo-8L (your AI Hat chip)

---

## ✅ Verify Model

```bash
# Check file exists
ls -lh ~/reachy-mini-dev/hailo_poc/models/yolov8n.hef

# Should output something like:
# -rw-r--r-- 1 pi pi 12M Nov 9 10:00 yolov8n.hef

# If file size is < 1 MB, it's probably corrupted
```

---

## 🚀 Once You Have the Model

```bash
cd ~/reachy-mini-dev/hailo_poc

# Test Hailo hardware
python3 test_hailo.py

# Test YOLO inference (will auto-detect your model)
python3 test_yolo_hailo.py
```

---

## 📋 Troubleshooting

### "wget: command not found"
```bash
sudo apt install wget
```

### "Model not found"
```bash
# List what's in models directory
ls -la ~/reachy-mini-dev/hailo_poc/models/

# Make sure .hef file is there
```

### "Cannot download from S3"
- URLs may change between Hailo versions
- Visit GitHub repo directly to browse files
- Or use Hailo Developer Zone website

---

## 💡 Pro Tip

Once you get ONE model working, you can:
1. Test the full pipeline
2. Benchmark performance
3. Decide if you need a different model
4. Download more models later if needed

**Don't let model download block you!** Even one working model is enough to validate the Hailo PoC.

---

## Need Help?

**Can't find the model?**
- Check: https://github.com/hailo-ai/hailo_model_zoo/tree/master/hailo_model_zoo/cfg/networks
- Look for pre-compiled models for Hailo-8L

**Link broken?**
- Hailo updates their Model Zoo regularly
- Check latest docs: https://github.com/hailo-ai/hailo-rpi5-examples

**Still stuck?**
- Let me know what error you're seeing
- Or share the output of `./download_models_manual.sh`
