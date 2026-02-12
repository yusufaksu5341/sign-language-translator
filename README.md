# Sign Language Translator (Google Meet + Local AI)

This repository now includes an end-to-end pipeline to:

1. Read sign videos from `tid_dataset/` with robust label parsing
2. Extract frame embeddings from videos (OpenCV)
3. Train a sign-to-text classifier
4. Run real-time webcam inference
5. Connect Google Meet video frames to a local inference API via Chrome extension

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Prepare dataset features

Expected filename format in `tid_dataset/`:

```text
<word>_<vid-id>.mp4
Example: Anlamak_12-01.mp4
```

Run:

```bash
python prepare_dataset.py --dataset tid_dataset --output processed/sign_dataset.npz --frame-size 32
```

## 3) Train model

```bash
python train_model.py --input processed/sign_dataset.npz --model models/sign_classifier.joblib --min-samples-per-class 2 --max-classes 200
```

This saves:
- `models/sign_classifier.joblib`

`--max-classes 200` keeps training fast for MVP. Increase later for broader vocabulary.

## 4) Real-time webcam inference

```bash
python inference_webcam.py --model models/sign_classifier.joblib
```

Press `q` to quit.

## 5) Google Meet integration (MVP)

### Start local API

```bash
python serve_inference.py --model models/sign_classifier.joblib --host 127.0.0.1 --port 8000
```

### Load extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder
5. Open Google Meet (`https://meet.google.com/*`)

The extension overlays prediction text on screen and sends video frames to local API.

## Important Notes

- This is an MVP baseline. Accuracy depends heavily on dataset quality and diversity.
- For production quality, use sequence models (Transformer/LSTM/TCN), better augmentation, and domain adaptation for webcam/Meet conditions.
- Keep camera permissions and privacy disclosures compliant before public release.

## Project Files

- `prepare_dataset.py` - Extract landmark sequences from videos
- `train_model.py` - Train classifier
- `inference_webcam.py` - Webcam sign-to-text
- `serve_inference.py` - Local inference API for extension
- `sign_translator/dataset.py` - Dataset parsing/validation
- `sign_translator/landmarks.py` - Landmark extraction utilities
- `extension/manifest.json` - Chrome extension manifest
- `extension/content.js` - Meet frame capture + overlay
