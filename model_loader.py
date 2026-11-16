"""
model_loader.py - Pothole Detection and Severity Assessment Engine using YOLOv8
"""

import base64
import io
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

# Default weights path
DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "weights" / "yolov8n_pothole_100ep.pt"


class PotholeDetector:
    def __init__(self, weights_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
        self.weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        if not self.weights_path.exists():
            raise FileNotFoundError(f"Model weights not found at: {self.weights_path}")
        
        self.device = device
        # Load YOLO model
        self.model = YOLO(str(self.weights_path))
        # Warmup model once with a blank frame
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self.model.predict(dummy, verbose=False, device=self.device)

    def _determine_quadrant(self, x_center_norm: float, y_center_norm: float) -> str:
        """Determines road position quadrant based on normalized coordinates."""
        if x_center_norm < 0.33:
            h_pos = "Left Lane"
        elif x_center_norm > 0.66:
            h_pos = "Right Lane"
        else:
            h_pos = "Center Lane"

        if y_center_norm < 0.40:
            v_pos = "Distant"
        elif y_center_norm > 0.75:
            v_pos = "Immediate Foreground"
        else:
            v_pos = "Mid-Road"

        return f"{h_pos} ({v_pos})"

    def _calculate_severity(self, total_cavity_ratio: float, count: int) -> Dict[str, Any]:
        """
        Calculates infrastructure audit severity and municipal maintenance recommendations.
        Consistent with the RDD2022 severity audit methodology.
        """
        damage_percentage = round(total_cavity_ratio * 100.0, 3)

        if count == 0:
            return {
                "level": "NORMAL",
                "label": "Good Condition",
                "color": "#10B981",  # Green
                "badge_class": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                "score": 0,
                "damage_percentage": damage_percentage,
                "priority": "P4 - None",
                "action": "Surface in good condition. Standard routine inspection cycle.",
            }
        elif total_cavity_ratio < 0.005 and count <= 2:
            score = max(10, min(35, int(damage_percentage * 50) + count * 5))
            return {
                "level": "LOW",
                "label": "Minor Surface Defects",
                "color": "#3B82F6",  # Blue
                "badge_class": "bg-blue-500/10 text-blue-400 border-blue-500/20",
                "score": score,
                "damage_percentage": damage_percentage,
                "priority": "P3 - Low",
                "action": "Minor localized potholes. Schedule for routine quarterly patch repairs.",
            }
        elif total_cavity_ratio < 0.02 and count <= 4:
            score = max(40, min(65, int(damage_percentage * 30) + count * 8))
            return {
                "level": "MODERATE",
                "label": "Moderate Deterioration",
                "color": "#F59E0B",  # Amber
                "badge_class": "bg-amber-500/10 text-amber-400 border-amber-500/20",
                "score": score,
                "damage_percentage": damage_percentage,
                "priority": "P2 - Medium",
                "action": "Moderate pavement degradation. Schedule targeted bituminous asphalt patching.",
            }
        elif total_cavity_ratio < 0.05:
            score = max(70, min(85, int(damage_percentage * 15) + count * 6))
            return {
                "level": "HIGH",
                "label": "High Deterioration",
                "color": "#F97316",  # Orange
                "badge_class": "bg-orange-500/10 text-orange-400 border-orange-500/20",
                "score": score,
                "damage_percentage": damage_percentage,
                "priority": "P1 - High",
                "action": "Significant road damage risking vehicle tire/rim damage. Prioritize milling and resurfacing.",
            }
        else:
            score = min(100, max(88, int(damage_percentage * 10) + count * 5))
            return {
                "level": "CRITICAL",
                "label": "Critical / Hazardous Cavity",
                "color": "#EF4444",  # Red
                "badge_class": "bg-red-500/10 text-red-400 border-red-500/20",
                "score": score,
                "damage_percentage": damage_percentage,
                "priority": "P0 - Emergency",
                "action": "Severe structural pavement collapse. Immediate warning signage and urgent emergency road repair required.",
            }

    def detect(
        self,
        image_input: Union[np.ndarray, Image.Image, bytes],
        conf_threshold: float = 0.20,
        iou_threshold: float = 0.45,
        draw_labels: bool = True,
        draw_mask: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs pothole detection and severity auditing on the input image.
        Returns detailed bounding box coordinates, metrics, and base64 annotated image.
        """
        start_time = time.perf_counter()

        # Load image into BGR numpy array
        if isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise ValueError("Could not decode image from bytes.")
        elif isinstance(image_input, Image.Image):
            img_rgb = np.array(image_input)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 2:
                img_bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            elif image_input.shape[2] == 4:
                img_bgr = cv2.cvtColor(image_input, cv2.COLOR_RGBA2BGR)
            else:
                img_bgr = image_input.copy()
        else:
            raise TypeError("Unsupported image input type.")

        orig_h, orig_w = img_bgr.shape[:2]
        total_image_pixels = float(orig_w * orig_h)

        # Run inference
        inf_start = time.perf_counter()
        results = self.model.predict(
            source=img_bgr,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False,
            device=self.device,
        )
        inf_time_ms = round((time.perf_counter() - inf_start) * 1000.0, 2)

        res = results[0]
        boxes = res.boxes

        detections: List[Dict[str, Any]] = []
        total_cavity_area_ratio = 0.0
        total_cavity_area_pixels = 0

        # Annotation canvas
        annotated_bgr = img_bgr.copy()
        overlay = img_bgr.copy()

        if len(boxes) > 0:
            # Extract coordinates
            xyxy_arr = boxes.xyxy.cpu().numpy()
            xywhn_arr = boxes.xywhn.cpu().numpy()
            conf_arr = boxes.conf.cpu().numpy()
            cls_arr = boxes.cls.cpu().numpy()

            for idx, (xyxy, xywhn, conf, cls_id) in enumerate(
                zip(xyxy_arr, xywhn_arr, conf_arr, cls_arr)
            ):
                xmin, ymin, xmax, ymax = [int(v) for v in xyxy]
                # Clamp coordinates
                xmin = max(0, min(xmin, orig_w - 1))
                xmax = max(0, min(xmax, orig_w - 1))
                ymin = max(0, min(ymin, orig_h - 1))
                ymax = max(0, min(ymax, orig_h - 1))

                w_px = max(0, xmax - xmin)
                h_px = max(0, ymax - ymin)
                box_area_px = int(w_px * h_px)

                # Normalized metrics
                cx_n, cy_n, w_n, h_n = [float(v) for v in xywhn]
                area_ratio = float(w_n * h_n)
                area_percentage = round((box_area_px / total_image_pixels) * 100.0, 3)

                total_cavity_area_ratio += area_ratio
                total_cavity_area_pixels += box_area_px

                quadrant = self._determine_quadrant(cx_n, cy_n)
                conf_val = float(conf)

                pothole_id = idx + 1
                detections.append({
                    "id": pothole_id,
                    "class_name": "pothole",
                    "confidence": round(conf_val, 4),
                    "confidence_percentage": f"{conf_val * 100:.1f}%",
                    "bbox": {
                        "xmin": xmin,
                        "ymin": ymin,
                        "xmax": xmax,
                        "ymax": ymax,
                        "width": w_px,
                        "height": h_px,
                    },
                    "normalized_bbox": {
                        "x_center": round(cx_n, 4),
                        "y_center": round(cy_n, 4),
                        "width": round(w_n, 4),
                        "height": round(h_n, 4),
                    },
                    "area_pixels": box_area_px,
                    "area_percentage": area_percentage,
                    "location": quadrant,
                })

                # Visual color based on confidence & severity
                if conf_val > 0.40:
                    box_color = (0, 0, 240)      # Bright Red (BGR)
                    fill_color = (40, 40, 240)
                elif conf_val > 0.25:
                    box_color = (0, 140, 255)    # Orange (BGR)
                    fill_color = (0, 165, 255)
                else:
                    box_color = (0, 215, 255)    # Amber/Yellow (BGR)
                    fill_color = (0, 230, 255)

                # 1. Draw cavity semi-transparent mask fill
                if draw_mask:
                    cv2.rectangle(overlay, (xmin, ymin), (xmax, ymax), fill_color, -1)

                # 2. Draw thick bounding box
                thickness = max(2, int(min(orig_w, orig_h) / 300))
                cv2.rectangle(annotated_bgr, (xmin, ymin), (xmax, ymax), box_color, thickness)

                # 3. Draw label badge
                if draw_labels:
                    label_text = f"#{pothole_id} Pothole {conf_val * 100:.1f}%"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = max(0.45, min(orig_w, orig_h) / 1200.0)
                    font_thickness = max(1, int(font_scale * 2))

                    (txt_w, txt_h), baseline = cv2.getTextSize(
                        label_text, font, font_scale, font_thickness
                    )
                    
                    label_y = max(ymin - 6, txt_h + 8)
                    label_x = xmin

                    # Label background pill
                    cv2.rectangle(
                        annotated_bgr,
                        (label_x, label_y - txt_h - 6),
                        (label_x + txt_w + 10, label_y + 4),
                        box_color,
                        -1,
                    )
                    # Text
                    cv2.putText(
                        annotated_bgr,
                        label_text,
                        (label_x + 5, label_y - 2),
                        font,
                        font_scale,
                        (255, 255, 255),
                        font_thickness,
                        cv2.LINE_AA,
                    )

            # Blend mask overlay
            if draw_mask:
                alpha = 0.28
                cv2.addWeighted(overlay, alpha, annotated_bgr, 1 - alpha, 0, annotated_bgr)

        # Calculate severity and road assessment
        count = len(detections)
        severity = self._calculate_severity(total_cavity_area_ratio, count)

        # Total process time
        total_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Encode images to JPEG Base64
        _, orig_buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        _, annot_buf = cv2.imencode(".jpg", annotated_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

        orig_b64 = f"data:image/jpeg;base64,{base64.b64encode(orig_buf).decode('utf-8')}"
        annot_b64 = f"data:image/jpeg;base64,{base64.b64encode(annot_buf).decode('utf-8')}"

        return {
            "success": True,
            "pothole_count": count,
            "total_cavity_ratio": round(total_cavity_area_ratio, 5),
            "total_cavity_pixels": total_cavity_area_pixels,
            "surface_damage_percentage": severity["damage_percentage"],
            "severity": severity,
            "detections": detections,
            "image_metadata": {
                "width": orig_w,
                "height": orig_h,
                "aspect_ratio": round(orig_w / orig_h, 3),
                "total_pixels": int(total_image_pixels),
            },
            "parameters": {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
            },
            "timing": {
                "inference_time_ms": inf_time_ms,
                "total_time_ms": total_time_ms,
            },
            "annotated_image": annot_b64,
            "original_image": orig_b64,
        }
