from __future__ import annotations

import argparse
from collections import deque

import cv2
import joblib
import numpy as np

from sign_translator.landmarks import extract_feature_vector_from_frame


def draw_text(frame, text: str, confidence: float) -> None:
    cv2.rectangle(frame, (10, 10), (900, 80), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"Prediction: {text} ({confidence:.2f})",
        (20, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run webcam sign-to-text inference")
    parser.add_argument("--model", default="models/sign_classifier.joblib")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--min-confidence", type=float, default=0.25)
    args = parser.parse_args()

    bundle = joblib.load(args.model)
    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    sequence_len = int(bundle["sequence_len"])
    feature_dim = int(bundle["feature_dim"])
    frame_size = int(np.sqrt(feature_dim))

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    sequence_buffer: deque[np.ndarray] = deque(maxlen=sequence_len)
    last_text = "..."
    last_conf = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        feat = extract_feature_vector_from_frame(frame, frame_size=frame_size)
        sequence_buffer.append(feat)

        if len(sequence_buffer) == sequence_len:
            x = np.stack(sequence_buffer, axis=0).reshape(1, -1)
            probs = model.predict_proba(x)[0]
            best_idx = int(np.argmax(probs))
            conf = float(probs[best_idx])
            if conf >= args.min_confidence:
                last_text = str(label_encoder.inverse_transform([best_idx])[0])
                last_conf = conf

        draw_text(frame, last_text, last_conf)
        cv2.imshow("Sign Translator", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
