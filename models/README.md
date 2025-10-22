# Face Recognition Models

This directory contains the pre-trained models for face recognition.

## Required Model

**SFace Model** (OpenCV Zoo)
- File: `face_recognition_sface_2021dec.onnx`
- Size: ~36.9 MB
- Source: https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface
- License: MIT

### Download Instructions

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" -OutFile "models/face_recognition_sface_2021dec.onnx"
```

**Linux/macOS:**
```bash
curl -L "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" -o models/face_recognition_sface_2021dec.onnx
```

**Python:**
```python
import urllib.request
from pathlib import Path

url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
Path("models").mkdir(exist_ok=True)
urllib.request.urlretrieve(url, "models/face_recognition_sface_2021dec.onnx")
```

## Model Details

- **Input**: 112x112 RGB images
- **Output**: 128-dimensional face embeddings (L2-normalized)
- **Compatible**: Output format matches `face_recognition` library for easy migration
- **Performance**: Fast inference on CPU (~10-50ms per face)

## Notes

- Model files are excluded from Git (see `.gitignore`) due to size
- Download the model before running face encoding/recognition features
- The model is automatically loaded by `FaceEncoder` class
