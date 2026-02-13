from __future__ import annotations

import argparse
import base64
from collections import defaultdict, deque

import cv2
import joblib
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from sign_translator.landmarks import extract_feature_vector_from_frame


class PredictRequest(BaseModel):
    session_id: str
    image_base64: str


class ModelRuntime:
    def __init__(self, model_path: str):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.label_encoder = bundle["label_encoder"]
        self.sequence_len = int(bundle["sequence_len"])
        feature_dim = int(bundle["feature_dim"])
        self.frame_size = int(np.sqrt(feature_dim))
        self.buffers: dict[str, deque[np.ndarray]] = defaultdict(lambda: deque(maxlen=self.sequence_len))

    def decode_image(self, image_base64: str) -> np.ndarray:
        data = image_base64.split(",")[-1]
        binary = base64.b64decode(data)
        arr = np.frombuffer(binary, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data")
        return img

    def predict(self, session_id: str, image_base64: str) -> dict:
        frame = self.decode_image(image_base64)
        feat = extract_feature_vector_from_frame(frame, frame_size=self.frame_size)

        buf = self.buffers[session_id]
        buf.append(feat)

        if len(buf) < self.sequence_len:
            return {"text": "", "confidence": 0.0, "ready": False}

        x = np.stack(buf, axis=0).reshape(1, -1)
        probs = self.model.predict_proba(x)[0]
        best_idx = int(np.argmax(probs))
        confidence = float(probs[best_idx])
        text = str(self.label_encoder.inverse_transform([best_idx])[0])
        return {"text": text, "confidence": confidence, "ready": True}


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
    return {"ok": True, "runtime_loaded": runtime is not None}


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve local inference API for browser extension")
    parser.add_argument("--model", default="models/sign_classifier.joblib")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global runtime
    runtime = ModelRuntime(args.model)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
