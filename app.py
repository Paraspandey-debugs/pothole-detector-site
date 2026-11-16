"""
app.py - FastAPI Application for Road Pothole Detection & Infrastructure Severity Auditing
Ready for local development and 1-click Render deployment.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add current directory to path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from model_loader import PotholeDetector

app = FastAPI(
    title="Automated Road Pothole Detection API",
    description="Fine-tuned YOLOv8n pothole detector and road infrastructure severity audit system.",
    version="1.0.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
STATIC_DIR = APP_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Sample images list
SAMPLES = [
    {
        "id": "sample1",
        "filename": "sample1_severe_potholes.jpg",
        "title": "Severe Cavity Clustered",
        "category": "High Risk",
        "description": "Multi-crater road collapse on asphalt lane with severe vehicular hazard.",
        "url": "/static/samples/sample1_severe_potholes.jpg",
    },
    {
        "id": "sample2",
        "filename": "sample2_dual_potholes.jpg",
        "title": "Dual Road Potholes",
        "category": "Moderate",
        "description": "Two distinct asphalt depressions near vehicle driving path.",
        "url": "/static/samples/sample2_dual_potholes.jpg",
    },
    {
        "id": "sample3",
        "filename": "sample3_single_pothole.jpg",
        "title": "Deep Isolated Pothole",
        "category": "Moderate",
        "description": "Isolated sharp cavity on weathered road surface.",
        "url": "/static/samples/sample3_single_pothole.jpg",
    },
    {
        "id": "sample4",
        "filename": "sample4_highway_pothole.jpg",
        "title": "Highway Surface Pothole",
        "category": "Moderate",
        "description": "Localized asphalt rupture on European test highway (Czech Republic).",
        "url": "/static/samples/sample4_highway_pothole.jpg",
    },
    {
        "id": "sample5",
        "filename": "sample5_clean_road.jpg",
        "title": "Intact Pavement",
        "category": "Normal / Clean",
        "description": "Intact road surface with no pothole structural damage (True Negative).",
        "url": "/static/samples/sample5_clean_road.jpg",
    },
]

# Global detector instance
detector: Optional[PotholeDetector] = None


@app.on_event("startup")
def startup_event():
    global detector
    try:
        detector = PotholeDetector()
        print("✓ YOLOv8 Pothole Detector initialized successfully.")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize model at startup: {e}")


def get_detector() -> PotholeDetector:
    global detector
    if detector is None:
        detector = PotholeDetector()
    return detector


@app.get("/", summary="Dashboard Home")
def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={
            "message": "Automated Road Pothole Detection API",
            "docs": "/docs",
            "health": "/health",
        }
    )


@app.get("/health", summary="Health Check for Render")
def health_check():
    """
    Render health check endpoint.
    Used by Render zero-downtime deploy monitors.
    """
    weights_exist = (APP_DIR / "weights" / "yolov8n_pothole_100ep.pt").exists()
    return {
        "status": "healthy" if weights_exist else "degraded",
        "service": "pothole-detection-api",
        "model": "YOLOv8n-Pothole-100ep",
        "weights_loaded": detector is not None,
        "weights_file_present": weights_exist,
    }


@app.get("/api/samples", summary="List Pre-loaded Sample Images")
def list_samples():
    """Returns sample test images for instant one-click demonstration."""
    return {"samples": SAMPLES}


@app.get("/api/info", summary="Model & Benchmark Metadata")
def model_info():
    """Returns architecture specs and benchmark performance from the research study."""
    return {
        "architecture": "Ultralytics YOLOv8n (Nano)",
        "task": "Single-class Object Detection (D40 Pothole)",
        "dataset": "Road Damage Dataset 2022 (RDD2022 multi-national)",
        "training_epochs": 100,
        "weights_size_mb": 6.3,
        "metrics": {
            "mAP50": 0.2718,
            "mAP50_95": 0.0948,
            "spearman_rho_severity_correlation": 0.8485,
        },
        "supported_inputs": ["image/jpeg", "image/png", "image/webp"],
    }


@app.post("/api/detect", summary="Upload Image for Pothole Detection")
async def detect_potholes(
    file: UploadFile = File(..., description="Road image file (JPEG, PNG, WEBP)"),
    conf: float = Form(0.20, description="Confidence threshold between 0.05 and 0.95"),
    iou: float = Form(0.45, description="IoU threshold for NMS between 0.10 and 0.90"),
    draw_labels: bool = Form(True, description="Draw bounding box label text"),
    draw_mask: bool = Form(True, description="Draw semi-transparent cavity mask fill"),
):
    """
    Analyzes an uploaded road image:
    - Detects potholes with bounding boxes and confidence scores
    - Calculates road surface cavity coverage ratio
    - Determines municipal infrastructure severity rating
    - Returns annotated image in Base64
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file type '{file.content_type}' is not a valid image.",
        )

    try:
        contents = await file.read()
        if len(contents) > 20 * 1024 * 1024:  # 20MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 20MB limit.")

        det = get_detector()
        conf_clamped = max(0.05, min(0.95, float(conf)))
        iou_clamped = max(0.10, min(0.90, float(iou)))

        result = det.detect(
            image_input=contents,
            conf_threshold=conf_clamped,
            iou_threshold=iou_clamped,
            draw_labels=bool(draw_labels),
            draw_mask=bool(draw_mask),
        )
        result["filename"] = file.filename
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Inference error processing image: {str(e)}"
        )


@app.post("/api/detect-sample", summary="Run Detection on Pre-loaded Sample")
def detect_sample(
    sample_name: str = Query(..., description="Filename of sample image"),
    conf: float = Query(0.20, description="Confidence threshold"),
    iou: float = Query(0.45, description="IoU threshold"),
    draw_labels: bool = Query(True),
    draw_mask: bool = Query(True),
):
    """Executes detection on one of the bundled sample road images."""
    sample_path = STATIC_DIR / "samples" / sample_name
    if not sample_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Sample '{sample_name}' not found."
        )

    try:
        with open(sample_path, "rb") as f:
            contents = f.read()

        det = get_detector()
        conf_clamped = max(0.05, min(0.95, float(conf)))
        iou_clamped = max(0.10, min(0.90, float(iou)))

        result = det.detect(
            image_input=contents,
            conf_threshold=conf_clamped,
            iou_threshold=iou_clamped,
            draw_labels=bool(draw_labels),
            draw_mask=bool(draw_mask),
        )
        result["filename"] = sample_name
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting server on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=False)
