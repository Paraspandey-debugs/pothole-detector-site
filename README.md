# 🛣️ PotholeVision: Automated Road Pothole Detection & Infrastructure Severity Audit

A production-ready computer vision web application and REST API for automated asphalt pothole detection, cavity area ratio measurement, and municipal road infrastructure maintenance severity auditing.

Powered by a fine-tuned **Ultralytics YOLOv8n** model trained on the multi-national **Road Damage Dataset 2022 (RDD2022)**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Ultralytics YOLOv8](https://img.shields.io/badge/YOLO-v8n-orange.svg)](https://github.com/ultralytics/ultralytics)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- **Accurate Pothole Detection:** Detects road potholes (D40) with bounding boxes, confidence scores, and surface cavity fill masks.
- **Road Cavity Area Ratio Measurement:** Computes spatial cavity coverage percentage ($\sum w \cdot h$) to evaluate surface volume loss.
- **Infrastructure Severity Ranking:** Automatically grades road conditions into **Normal**, **Low**, **Moderate**, **High**, and **Critical** with actionable municipal repair priorities (P0 to P4).
- **Interactive Modern UI:**
  - 1-click test sample gallery (Severe cavities, dual potholes, single cavity, highway defects, clean pavement).
  - Drag-and-drop or file upload for custom road imagery.
  - Live adjustable Confidence (5%–90%) and IoU NMS threshold sliders.
  - Toggle between **Annotated Detection**, **Original Image**, and **Side-by-Side** comparison.
  - Interactive Cavity Inventory table detailing bounding box coordinates, dimensions, area, and road lane position.
  - Export capabilities: Download Annotated Image (`.jpg`), JSON Audit Data (`.json`), or CSV Report (`.csv`).
- **Developer REST API:** Full OpenAPI / Swagger documentation (`/docs`) with `/api/detect`, `/api/detect-sample`, and `/health` endpoints.
- **Render Ready:** Includes `render.yaml`, `Dockerfile`, `Procfile`, and CPU-optimized `requirements.txt` for 1-click cloud deployment.

---

## 🧠 Model Weights & Origin

The model weights (`weights/yolov8n_pothole_100ep.pt`, 6.3 MB) originate from the fine-tuned 100-epoch training run in the research project:
- **Architecture:** YOLOv8n (3.2M parameters)
- **Dataset:** Road Damage Dataset 2022 (RDD2022) across multi-national road networks (Czech Republic, India, Japan, USA).
- **Benchmark Performance:**
  - Validation mAP@0.5: **0.2718** (Up from 0.1152 in baseline, **+135.9% gain**)
  - Infrastructure Audit Spearman Rank Correlation: **$\rho = 0.8485$** ($p = 1.51 \times 10^{-16}$)
  - Inference Latency: **~35–50 ms on CPU** / **3.0 ms on GPU** (~330 FPS)

---

## 🚀 Quickstart (Local Development)

### 1. Clone & Install Dependencies
```bash
cd pothole-detector-site

# Optional: Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (CPU PyTorch is used for fast, lightweight install)
pip install -r requirements.txt
```

### 2. Start Web Server
```bash
python3 app.py
# or using uvicorn directly:
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## ☁️ Deploying to Render (Free Tier)

This repository is optimized for **[Render](https://render.com/) Free Tier** (512MB RAM):
- The model weights file is only **6.3 MB** and committed directly in `weights/`.
- `requirements.txt` points to the lightweight CPU PyTorch wheel, cutting build size from 3.5GB to ~150MB and completing in **< 60 seconds**.
- Pre-configured `render.yaml` blueprint handles zero-configuration deployment.

### 1-Click Blueprint Deploy:
1. Push this directory to your GitHub account.
2. In Render, go to **Blueprints** &rarr; Connect your repository.
3. Click **Apply**!

👉 **Read [DEPLOY.md](DEPLOY.md) for full step-by-step instructions and troubleshooting.**

---

## 📡 REST API Reference

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```
**Response:**
```json
{
  "status": "healthy",
  "service": "pothole-detection-api",
  "model": "YOLOv8n-Pothole-100ep",
  "weights_loaded": true,
  "weights_file_present": true
}
```

### 2. Detect Potholes in Uploaded Image
```bash
curl -X POST "http://localhost:8000/api/detect" \
  -F "file=@road_sample.jpg" \
  -F "conf=0.20" \
  -F "iou=0.45"
```
**Response:**
```json
{
  "success": true,
  "pothole_count": 2,
  "total_cavity_ratio": 0.0435,
  "surface_damage_percentage": 4.35,
  "severity": {
    "level": "HIGH",
    "label": "High Deterioration",
    "score": 75,
    "priority": "P1 - High",
    "action": "Significant road damage risking vehicle tire/rim damage. Prioritize milling and resurfacing."
  },
  "detections": [
    {
      "id": 1,
      "class_name": "pothole",
      "confidence": 0.465,
      "confidence_percentage": "46.5%",
      "bbox": { "xmin": 340, "ymin": 420, "xmax": 560, "ymax": 590, "width": 220, "height": 170 },
      "area_pixels": 37400,
      "area_percentage": 2.85,
      "location": "Center Lane (Immediate Foreground)"
    }
  ],
  "timing": {
    "inference_time_ms": 38.5,
    "total_time_ms": 52.1
  },
  "annotated_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

---

## 📁 Repository Structure

```
pothole-detector-site/
├── app.py                     # FastAPI application & REST endpoints
├── model_loader.py            # YOLOv8 inference, bounding boxes & severity logic
├── weights/
│   └── yolov8n_pothole_100ep.pt  # Fine-tuned YOLOv8n weights (6.3 MB)
├── static/
│   ├── index.html             # Tailwind CSS interactive dashboard
│   ├── css/
│   │   └── custom.css         # Styling, glassmorphism & radar animations
│   ├── js/
│   │   └── app.js             # Client upload, tabs, metrics & export handlers
│   └── samples/               # 5 Bundled road sample test images
├── Dockerfile                 # Multi-stage lightweight Docker runtime
├── .dockerignore              # Files excluded from Docker builds
├── render.yaml                # Render Blueprint infrastructure spec
├── requirements.txt           # CPU-optimized PyTorch dependencies
├── Procfile                   # Process file for cloud hosting
├── DEPLOY.md                  # Comprehensive Render deployment guide
└── README.md                  # Project documentation
```

---

## 📜 License

MIT License. Developed for automated road condition monitoring and infrastructure safety auditing.
