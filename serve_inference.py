from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
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


@dataclass
class DatasetProfile:
    mean: np.ndarray
    threshold: float
    sample_count: int


class ModelRuntime:
    def __init__(
        self,
        api_key: str,
        model_id: str,
        api_url: str = "https://detect.roboflow.com",
        min_confidence: float = 0.35,
        dataset_path: str = "dataset1",
        dataset_profile_cache: str = "models/dataset1_profile.npz",
        dataset_sample_videos: int = 350,
        min_dataset_match: float = 0.18,
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
        self.dataset_sample_videos = int(max(20, dataset_sample_videos))
        self.min_dataset_match = float(max(0.0, min(1.0, min_dataset_match)))
        self.dataset_profile_cache = Path(dataset_profile_cache)

        self.sequence_len = 4
        self.pred_history: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=5))
        self.buffers: dict[str, deque[bytes]] = defaultdict(lambda: deque(maxlen=self.sequence_len))
        self.dataset_profile = self.load_or_build_dataset_profile()

    @staticmethod
    def frame_descriptor(img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        return small.reshape(-1)

    def load_or_build_dataset_profile(self) -> DatasetProfile | None:
        if not self.dataset_exists:
            return None

        if self.dataset_profile_cache.exists():
            try:
                data = np.load(self.dataset_profile_cache)
                mean = data["mean"].astype(np.float32)
                threshold = float(np.ravel(data["threshold"])[0])
                if "sample_count" in data.files:
                    sample_count = int(np.ravel(data["sample_count"])[0])
                else:
                    sample_count = 0
                if mean.size == 1024 and threshold > 0:
                    return DatasetProfile(mean=mean, threshold=threshold, sample_count=sample_count)
            except Exception:
                pass

        descriptors: list[np.ndarray] = []
        video_candidates = sorted(self.dataset_path.glob("*_color.mp4"))
        if not video_candidates:
            video_candidates = sorted(self.dataset_path.glob("*.mp4"))

        for video_path in video_candidates[: self.dataset_sample_videos]:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                continue

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            mid = max(0, total // 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                continue
            descriptors.append(self.frame_descriptor(frame))

        if len(descriptors) < 10:
            return None

        mat = np.stack(descriptors, axis=0).astype(np.float32)
        mean = mat.mean(axis=0)
        distances = np.linalg.norm(mat - mean, axis=1)
        threshold = float(np.percentile(distances, 92))
        profile = DatasetProfile(mean=mean, threshold=max(threshold, 1e-6), sample_count=int(mat.shape[0]))

        try:
            self.dataset_profile_cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(
                self.dataset_profile_cache,
                mean=profile.mean,
                threshold=np.array([profile.threshold], dtype=np.float32),
                sample_count=np.array([profile.sample_count], dtype=np.int32),
            )
        except Exception:
            pass

        return profile

    def decode_image(self, image_base64: str) -> np.ndarray:
        data = image_base64.split(",")[-1]
        binary = base64.b64decode(data)
        arr = np.frombuffer(binary, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data")
        return img

    @staticmethod
    def encode_image_bytes(img: np.ndarray) -> bytes:
        ok, encoded = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise ValueError("Image encoding failed")
        return encoded.tobytes()

    def dataset_match_score(self, img: np.ndarray) -> float:
        if self.dataset_profile is None:
            return 1.0

        desc = self.frame_descriptor(img)
        dist = float(np.linalg.norm(desc - self.dataset_profile.mean))
        score = 1.0 - (dist / self.dataset_profile.threshold)
        return float(max(0.0, min(1.0, score)))

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
        frame = self.decode_image(image_base64)
        image_bytes = self.encode_image_bytes(frame)

        buf = self.buffers[session_id]
        buf.append(image_bytes)

        if len(buf) < self.sequence_len:
            return {"text": "", "confidence": 0.0, "ready": False}

        result = self.infer_roboflow(buf[-1])
        text, confidence = self.pick_best_prediction(result)
        dataset_score = self.dataset_match_score(frame)

        blended_confidence = float((0.75 * confidence) + (0.25 * dataset_score))
        if dataset_score < self.min_dataset_match:
            text = ""
            blended_confidence = float(dataset_score)

        hist = self.pred_history[session_id]
        if text:
            hist.append(text)
            text = Counter(hist).most_common(1)[0][0]

        return {
            "text": text,
            "confidence": blended_confidence,
            "ready": True,
            "source": "roboflow",
            "dataset1_found": self.dataset_exists,
            "dataset1_profile_loaded": self.dataset_profile is not None,
            "dataset_match": dataset_score,
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
        "dataset1_profile_loaded": getattr(runtime, "dataset_profile", None) is not None,
        "dataset1_profile_samples": getattr(getattr(runtime, "dataset_profile", None), "sample_count", 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Roboflow inference API for browser extension")
    parser.add_argument("--api-key", default=os.getenv("ROBOFLOW_API_KEY", ""))
    parser.add_argument("--model-id", default=os.getenv("ROBOFLOW_MODEL_ID", "turk-isaret-dili/2"))
    parser.add_argument("--api-url", default=os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com"))
    parser.add_argument("--min-confidence", type=float, default=float(os.getenv("ROBOFLOW_MIN_CONFIDENCE", "0.35")))
    parser.add_argument("--dataset", default=os.getenv("DATASET1_PATH", "dataset1"))
    parser.add_argument("--dataset-profile-cache", default=os.getenv("DATASET1_PROFILE_CACHE", "models/dataset1_profile.npz"))
    parser.add_argument("--dataset-sample-videos", type=int, default=int(os.getenv("DATASET1_SAMPLE_VIDEOS", "350")))
    parser.add_argument("--min-dataset-match", type=float, default=float(os.getenv("DATASET1_MIN_MATCH", "0.18")))
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
        dataset_profile_cache=args.dataset_profile_cache,
        dataset_sample_videos=args.dataset_sample_videos,
        min_dataset_match=args.min_dataset_match,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
