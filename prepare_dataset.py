from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from sign_translator.dataset import load_dataset_index
from sign_translator.landmarks import build_feature_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract landmark feature sequences from sign videos")
    parser.add_argument("--dataset", default="tid_dataset", help="Raw video dataset directory")
    parser.add_argument("--output", default="processed/sign_dataset.npz", help="Output NPZ path")
    parser.add_argument("--sequence-len", type=int, default=30)
    parser.add_argument("--max-frames", type=int, default=120)
    parser.add_argument("--frame-size", type=int, default=32)
    args = parser.parse_args()

    items = load_dataset_index(args.dataset)
    samples = build_feature_dataset(
        items,
        sequence_len=args.sequence_len,
        max_frames=args.max_frames,
        frame_size=args.frame_size,
    )

    if not samples:
        raise RuntimeError("No samples extracted. Check dataset quality.")

    labels = [s.label for s in samples]
    vid_ids = [s.vid_id for s in samples]
    features = np.stack([s.features for s in samples], axis=0)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, X=features, y=np.array(labels), vid=np.array(vid_ids))

    print(f"[saved] {out}")
    print(f"[shape] X={features.shape}")


if __name__ == "__main__":
    main()
