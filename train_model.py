from __future__ import annotations

import argparse
from pathlib import Path
import joblib
import numpy as np
from collections import Counter
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import SGDClassifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Train sign-to-text classifier from extracted features")
    parser.add_argument("--input", default="processed/sign_dataset.npz")
    parser.add_argument("--model", default="models/sign_classifier.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--min-samples-per-class", type=int, default=2)
    parser.add_argument("--max-classes", type=int, default=200)
    args = parser.parse_args()

    data = np.load(args.input, allow_pickle=True)
    X = data["X"]
    y = data["y"]

    label_counts_raw = Counter(y.tolist())
    valid_labels = [label for label, count in label_counts_raw.items() if count >= args.min_samples_per_class]

    if args.max_classes > 0 and len(valid_labels) > args.max_classes:
        valid_labels = sorted(valid_labels, key=lambda label: label_counts_raw[label], reverse=True)[: args.max_classes]

    valid_label_set = set(valid_labels)
    keep_mask = np.array([label in valid_label_set for label in y])
    X = X[keep_mask]
    y = y[keep_mask]

    print(f"[train] classes after filtering: {len(valid_label_set)}")
    print(f"[train] samples after filtering: {len(y)}")

    if len(valid_label_set) < 2:
        raise RuntimeError("Need at least 2 classes after filtering.")

    n_samples, seq_len, feat_dim = X.shape
    X_flat = X.reshape(n_samples, seq_len * feat_dim)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    class_counts = Counter(y_encoded.tolist())
    min_class_count = min(class_counts.values())
    stratify_target = y_encoded if min_class_count >= 2 else None

    if stratify_target is not None:
        test_count = int(round(len(y_encoded) * args.test_size))
        if test_count < len(class_counts):
            print("[warn] test split too small for stratification; using non-stratified split.")
            stratify_target = None

    X_train, X_test, y_train, y_test = train_test_split(
        X_flat,
        y_encoded,
        test_size=args.test_size,
        random_state=42,
        stratify=stratify_target,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                SGDClassifier(
                    loss="log_loss",
                    alpha=1e-4,
                    max_iter=2000,
                    tol=1e-3,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    y_prob = np.nan_to_num(y_prob, nan=0.0, posinf=0.0, neginf=0.0)
    row_sums = y_prob.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0.0] = 1.0
    y_prob = y_prob / row_sums

    print(classification_report(y_test, y_pred, zero_division=0))
    top1 = (y_pred == y_test).mean()
    class_ids = model.named_steps["clf"].classes_
    k = min(5, y_prob.shape[1])
    topk_indices = np.argsort(y_prob, axis=1)[:, -k:]
    topk_labels = class_ids[topk_indices]
    top5_hits = [int(y_true in row) for y_true, row in zip(y_test, topk_labels)]
    top5 = float(np.mean(top5_hits))
    print(f"top1_accuracy={top1:.4f}")
    print(f"top5_accuracy={top5:.4f}")

    out_path = Path(args.model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "label_encoder": label_encoder,
            "sequence_len": seq_len,
            "feature_dim": feat_dim,
        },
        out_path,
    )
    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
