from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from .dataset import DatasetItem

@dataclass
class SequenceSample:
    label: str
    vid_id: str
    features: np.ndarray  # shape: (sequence_len, feature_dim)


def extract_feature_vector_from_frame(frame: np.ndarray, frame_size: int = 32) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (frame_size, frame_size), interpolation=cv2.INTER_AREA)
    normalized = resized.astype(np.float32) / 255.0
    return normalized.flatten()


def _resample_features(feature_list: list[np.ndarray], sequence_len: int) -> np.ndarray:
    if not feature_list:
        raise ValueError("No frames extracted")

    arr = np.stack(feature_list, axis=0)
    if len(feature_list) == sequence_len:
        return arr

    idx = np.linspace(0, len(feature_list) - 1, sequence_len)
    idx = np.round(idx).astype(int)
    return arr[idx]


def extract_sequence_from_video(
    video_path: Path,
    sequence_len: int = 30,
    max_frames: int = 120,
    frame_size: int = 32,
) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    frame_features: list[np.ndarray] = []

    read_count = 0
    while read_count < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frame_features.append(extract_feature_vector_from_frame(frame, frame_size=frame_size))
        read_count += 1

    cap.release()

    if not frame_features:
        raise RuntimeError(f"No valid frames found: {video_path}")

    return _resample_features(frame_features, sequence_len)


def build_feature_dataset(
    items: Iterable[DatasetItem],
    sequence_len: int = 30,
    max_frames: int = 120,
    frame_size: int = 32,
) -> list[SequenceSample]:
    samples: list[SequenceSample] = []
    total = 0
    skipped = 0

    for item in items:
        total += 1
        try:
            seq = extract_sequence_from_video(
                item.path,
                sequence_len=sequence_len,
                max_frames=max_frames,
                frame_size=frame_size,
            )
            samples.append(SequenceSample(label=item.label, vid_id=item.vid_id, features=seq))
        except Exception:
            skipped += 1

    print(f"[features] total: {total} | success: {len(samples)} | skipped: {skipped}")
    return samples
