# Getting YOLO Models for Hailo (No Conversion Needed!)

## TL;DR
You **DO NOT need to convert models yourself**. Use pre-converted `.hef` files from Hailo.

---

## Method 1: Use hailo-rpi5-examples (Easiest)

```bash
# On Raspberry Pi
cd ~/reachy-mini-dev/hailo_poc

# Make download script executable
chmod +x download_models.sh

# Run it
./download_models.sh
```

This will:
1. Check for models in `~/hailo-rpi5-examples/resources/`
2. Copy any .hef files to `hailo_poc/models/`
3. Tell you what to do if none found

---

## Method 2: Download from Hailo Model Zoo

### Option A: Browse Web Interface
1. Visit: https://hailo.ai/developer-zone/model-zoo/
2. Search for: "YOLOv8n"
3. Filter by: Hailo-8L (your chip)
4. Download the `.hef` file
5. Transfer to Pi via OneDrive/SCP

### Option B: Direct GitHub Download
```bash
# On Raspberry Pi
cd ~/reachy-mini-dev/hailo_poc/models

# Clone Model Zoo (large repo, be patient)
git clone https://github.com/hailo-ai/hailo_model_zoo.git /tmp/hailo_zoo

# Find compiled models
find /tmp/hailo_zoo -name "*.hef" -type f

# Copy the one you need (example path - verify actual location)
cp /tmp/hailo_zoo/hailo_model_zoo/compiled/hailo8l/yolov8n.hef ./

# Cleanup
rm -rf /tmp/hailo_zoo
```

---

## Method 3: Use Hailo Tappas Examples

The `hailo-rpi5-examples` repo often includes example models:

```bash
# Clone if you haven't
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git

# Check for models
find ~/hailo-rpi5-examples -name "*.hef"

# Copy to your project
cp ~/hailo-rpi5-examples/resources/*.hef ~/reachy-mini-dev/hailo_poc/models/
```

---

## Available Pre-Converted Models

Models typically available from Hailo (no conversion needed):

### Object Detection
- ✅ **yolov8n.hef** - YOLO v8 nano (fastest)
- ✅ **yolov8s.hef** - YOLO v8 small (more accurate)
- ✅ **yolov5n.hef** - YOLO v5 nano
- ✅ **yolov6n.hef** - YOLO v6 nano

### Face Detection (if available)
- ✅ **retinaface.hef** - Face detection specialist
- ✅ **yolov8n-face.hef** - Face-specific YOLO (if released)

### Pose Detection
- ✅ **yolov8n-pose.hef** - Human pose estimation

---

## Model Zoo Structure

When you download from Hailo Model Zoo, look for:

```
hailo_model_zoo/
└── hailo_model_zoo/
    └── compiled/
        └── hailo8l/          # Your chip!
            ├── yolov8n.hef
            ├── yolov5n.hef
            └── ... other models
```

**Important:** Make sure you download for **Hailo-8L** (not Hailo-8 or Hailo-15)!

---

## Verify Model After Download

```bash
# Check file exists and size
ls -lh ~/reachy-mini-dev/hailo_poc/models/yolov8n.hef

# Should be around 6-50 MB depending on model
# If it's < 1 MB, might be corrupted

# Test with our script
cd ~/reachy-mini-dev/hailo_poc
python3 test_yolo_hailo.py
```

---

## If You Really Need Custom Models (Future)

**Only if** pre-converted models don't meet your needs:

### Cloud x86 Linux VM Options:
- **AWS EC2**: t3.medium Ubuntu instance
- **Google Cloud**: e2-medium Ubuntu VM
- **Azure**: Standard B2s Ubuntu VM
- **DigitalOcean**: Basic Droplet Ubuntu

**Cost:** ~$0.05-0.10/hour (destroy after conversion)

**Steps:**
1. Spin up x86 Ubuntu VM
2. Install Hailo Dataflow Compiler
3. Convert ONNX → .hef
4. Download .hef file
5. Destroy VM

**But again: Not needed for YOLOv8n!** ✅

---

## Summary

✅ **Use pre-converted models** from Hailo (easiest)
✅ **No laptop conversion** needed
✅ **No special hardware** required
✅ **Just download .hef files** to Pi

**Next Step:** Run `./download_models.sh` on your Pi! 🚀
