from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from sign_translator.dataset import load_dataset_index
from sign_translator.landmarks import build_feature_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one-shot sign index from dataset videos")
    parser.add_argument("--dataset", default="tid_dataset")
    parser.add_argument("--output", default="models/sign_index.npz")
    parser.add_argument("--sequence-len", type=int, default=20)
    parser.add_argument("--max-frames", type=int, default=40)
    parser.add_argument("--frame-size", type=int, default=24)
    args = parser.parse_args()

    items = load_dataset_index(args.dataset)
    samples = build_feature_dataset(
        items,
        sequence_len=args.sequence_len,
        max_frames=args.max_frames,
        frame_size=args.frame_size,
    )
    if not samples:
        raise RuntimeError("No samples built for index")

    X = np.stack([s.features for s in samples], axis=0)
    y = np.array([s.label for s in samples])
    vid = np.array([s.vid_id for s in samples])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, X=X, y=y, vid=vid)

    print(f"[index] saved: {out_path}")
    print(f"[index] shape: {X.shape}")
    print(f"[index] labels: {len(set(y.tolist()))}")


if __name__ == "__main__":
    main()
