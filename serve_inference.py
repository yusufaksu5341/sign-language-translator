from __future__ import annotations

import argparse
import base64
from collections import Counter
from collections import defaultdict, deque
import os
from pathlib import Path

import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from pydantic import BaseModel
import requests
import uvicorn


class PredictRequest(BaseModel):
    session_id: str
    image_base64: str


class ModelRuntime:
    def __init__(
        self,
        api_key: str,
        model_id: str,
        api_url: str = "https://detect.roboflow.com",
        min_confidence: float = 0.35,
        dataset_path: str = "dataset1",
    ):
        if not api_key:
            raise ValueError("Roboflow API key not set. Use --api-key or ROBOFLOW_API_KEY environment variable.")

        self.mode = "roboflow"
        self.api_key = api_key
        self.model_id = model_id.strip().strip("/")
        self.api_url = api_url.rstrip("/")
        self.min_confidence = float(min_confidence)
        self.dataset_path = Path(dataset_path)
        self.dataset_exists = self.dataset_path.exists()

        self.sequence_len = 4
        self.pred_history: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=5))
        self.buffers: dict[str, deque[bytes]] = defaultdict(lambda: deque(maxlen=self.sequence_len))

    def decode_image_bytes(self, image_base64: str) -> bytes:
        data = image_base64.split(",")[-1]
        binary = base64.b64decode(data)
        arr = np.frombuffer(binary, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data")
        ok, encoded = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise ValueError("Image encoding failed")
        return encoded.tobytes()

    def infer_roboflow(self, image_bytes: bytes) -> dict:
        url = f"{self.api_url}/{self.model_id}"
        params = {
            "api_key": self.api_key,
            "confidence": int(max(0.0, min(1.0, self.min_confidence)) * 100),
            "overlap": 40,
        }
        files = {"file": ("frame.jpg", image_bytes, "image/jpeg")}

        response = requests.post(url, params=params, files=files, timeout=12)
        if response.status_code >= 400:
            raise RuntimeError(f"Roboflow HTTP {response.status_code}: {response.text[:200]}")
        return response.json()

    @staticmethod
    def pick_best_prediction(result: dict) -> tuple[str, float]:
        predictions = result.get("predictions") or []
        if not predictions:
            return "", 0.0

        best = max(predictions, key=lambda p: float(p.get("confidence", 0.0)))
        text = str(best.get("class") or "").strip()
        confidence = float(best.get("confidence", 0.0))
        return text, confidence

    def predict(self, session_id: str, image_base64: str) -> dict:
        image_bytes = self.decode_image_bytes(image_base64)

        buf = self.buffers[session_id]
        buf.append(image_bytes)

        if len(buf) < self.sequence_len:
            return {"text": "", "confidence": 0.0, "ready": False}

        result = self.infer_roboflow(buf[-1])
        text, confidence = self.pick_best_prediction(result)

        hist = self.pred_history[session_id]
        if text:
            hist.append(text)
            text = Counter(hist).most_common(1)[0][0]

        return {
            "text": text,
            "confidence": confidence,
            "ready": True,
            "source": "roboflow",
            "dataset1_found": self.dataset_exists,
        }


runtime: ModelRuntime | None = None
app = FastAPI(title="Sign Translator Inference API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict")
def predict(req: PredictRequest):
    if runtime is None:
        return {"error": "Model not loaded"}
    try:
        return runtime.predict(req.session_id, req.image_base64)
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/health")
def health():
    return {
        "ok": True,
        "runtime_loaded": runtime is not None,
        "mode": getattr(runtime, "mode", "unknown"),
        "model_id": getattr(runtime, "model_id", ""),
        "dataset1_found": getattr(runtime, "dataset_exists", False),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Roboflow inference API for browser extension")
    parser.add_argument("--api-key", default=os.getenv("ROBOFLOW_API_KEY", ""))
    parser.add_argument("--model-id", default=os.getenv("ROBOFLOW_MODEL_ID", "turk-isaret-dili/2"))
    parser.add_argument("--api-url", default=os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com"))
    parser.add_argument("--min-confidence", type=float, default=float(os.getenv("ROBOFLOW_MIN_CONFIDENCE", "0.35")))
    parser.add_argument("--dataset", default=os.getenv("DATASET1_PATH", "dataset1"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global runtime
    runtime = ModelRuntime(
        api_key=args.api_key,
        model_id=args.model_id,
        api_url=args.api_url,
        min_confidence=args.min_confidence,
        dataset_path=args.dataset,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
