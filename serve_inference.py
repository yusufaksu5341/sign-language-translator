from __future__ import annotations

import argparse
import base64
from collections import Counter
from collections import defaultdict, deque
import importlib
import os
from pathlib import Path

import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from pydantic import BaseModel
import requests
import uvicorn

try:
    InferenceHTTPClient = importlib.import_module("inference_sdk").InferenceHTTPClient
except Exception:
    class InferenceHTTPClient:
        def __init__(self, api_url: str, api_key: str):
            self.api_url = api_url.rstrip("/")
            self.api_key = api_key

        def infer(self, image_input, model_id: str) -> dict:
            model_key = model_id.strip().strip("/")

            if isinstance(image_input, np.ndarray):
                ok, encoded = cv2.imencode(".jpg", image_input, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if not ok:
                    raise ValueError("Image encoding failed")
                image_bytes = encoded.tobytes()
            elif isinstance(image_input, (str, Path)):
                image_bytes = Path(image_input).read_bytes()
            elif isinstance(image_input, (bytes, bytearray)):
                image_bytes = bytes(image_input)
            else:
                raise TypeError("Unsupported input type for infer")

            response = requests.post(
                f"{self.api_url}/{model_key}",
                params={"api_key": self.api_key},
                files={"file": ("frame.jpg", image_bytes, "image/jpeg")},
                timeout=15,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Roboflow HTTP {response.status_code}: {response.text[:200]}")
            return response.json()


class PredictRequest(BaseModel):
    session_id: str
    image_base64: str


class ModelRuntime:
    def __init__(
        self,
        api_key: str,
        model_id: str,
        api_url: str = "https://serverless.roboflow.com",
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
        self.client = InferenceHTTPClient(api_url=self.api_url, api_key=self.api_key)

        self.dataset_path = Path(dataset_path)
        self.dataset_exists = self.dataset_path.exists()
        self.dataset_labels = self.load_dataset_labels()
        self.dataset_label_keys = {self.normalize_label(label) for label in self.dataset_labels}

        self.sequence_len = 4
        self.pred_history: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=5))
        self.buffers: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=self.sequence_len))

    @staticmethod
    def normalize_label(text: str) -> str:
        normalized = text.strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        return normalized.strip("_")

    def _label_from_filename(self, stem: str) -> str:
        raw = stem.strip()
        split_tokens = ["_sample", "-sample", "_color", "-color"]
        lowered = raw.lower()
        for token in split_tokens:
            idx = lowered.find(token)
            if idx > 0:
                return raw[:idx]
        if "_" in raw:
            return raw.split("_", 1)[0]
        if "-" in raw:
            return raw.split("-", 1)[0]
        return raw

    def load_dataset_labels(self) -> list[str]:
        if not self.dataset_exists or not self.dataset_path.is_dir():
            return []

        labels: set[str] = set()
        valid_suffixes = {".mp4", ".avi", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
        for path in self.dataset_path.iterdir():
            if not path.is_file() or path.suffix.lower() not in valid_suffixes:
                continue
            label = self._label_from_filename(path.stem)
            cleaned = label.strip(" _-")
            if cleaned:
                labels.add(cleaned)
        return sorted(labels)

    def decode_image(self, image_base64: str) -> np.ndarray:
        data = image_base64.split(",")[-1]
        binary = base64.b64decode(data)
        arr = np.frombuffer(binary, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data")
        return img

    def infer_roboflow(self, img: np.ndarray) -> dict:
        return self.client.infer(img, model_id=self.model_id)

    @staticmethod
    def pick_best_prediction(result: dict) -> tuple[str, float]:
        predictions = result.get("predictions") or []
        if not predictions:
            return "", 0.0

        best = max(predictions, key=lambda p: float(p.get("confidence", 0.0)))
        text = str(best.get("class") or "").strip()
        confidence = float(best.get("confidence", 0.0))
        return text, confidence

    def keep_prediction(self, text: str, confidence: float) -> tuple[str, float]:
        if confidence < self.min_confidence:
            return "", 0.0

        if not text:
            return "", 0.0

        if not self.dataset_label_keys:
            return text, float(confidence)

        key = self.normalize_label(text)
        if key in self.dataset_label_keys:
            return text, float(confidence)

        return "", 0.0

    def predict(self, session_id: str, image_base64: str) -> dict:
        frame = self.decode_image(image_base64)

        buf = self.buffers[session_id]
        buf.append(frame)

        if len(buf) < self.sequence_len:
            return {"text": "", "confidence": 0.0, "ready": False}

        result = self.infer_roboflow(buf[-1])
        text, confidence = self.pick_best_prediction(result)
        text, confidence = self.keep_prediction(text, confidence)

        hist = self.pred_history[session_id]
        if text:
            hist.append(text)
            text = Counter(hist).most_common(1)[0][0]

        return {
            "text": text,
            "confidence": float(confidence),
            "ready": True,
            "source": "roboflow",
            "dataset1_found": self.dataset_exists,
            "dataset1_labels_count": len(self.dataset_labels),
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
        "dataset1_labels_count": len(getattr(runtime, "dataset_labels", []) or []),
        "dataset1_labels_preview": (getattr(runtime, "dataset_labels", []) or [])[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Roboflow inference API for browser extension")
    parser.add_argument("--api-key", default=os.getenv("ROBOFLOW_API_KEY", ""))
    parser.add_argument("--model-id", default=os.getenv("ROBOFLOW_MODEL_ID", "turk-isaret-dili/2"))
    parser.add_argument("--api-url", default=os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com"))
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
