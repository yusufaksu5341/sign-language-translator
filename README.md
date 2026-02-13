# Sign Language Translator (Google Meet + Roboflow)

This project uses your Roboflow model (`turk-isaret-dili/2`) for live sign prediction from Google Meet frames.

## Requirements

- Python 3.10+
- A Roboflow API key
- `dataset1/` folder in project root (optional but recommended)

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Start inference API (Roboflow)

```bash
python serve_inference.py --api-key YOUR_ROBOFLOW_API_KEY --model-id turk-isaret-dili/2 --dataset dataset1 --host 127.0.0.1 --port 8000
```

Or set environment variable:

```powershell
$env:ROBOFLOW_API_KEY="YOUR_ROBOFLOW_API_KEY"
python serve_inference.py --model-id turk-isaret-dili/2 --dataset dataset1 --host 127.0.0.1 --port 8000
```

## 3) One-command run (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -RoboflowApiKey YOUR_ROBOFLOW_API_KEY -StartApi -KeepApiRunning
```

### Fast start (auto command file)

```powershell
powershell -ExecutionPolicy Bypass -File .\start_roboflow_api.ps1
```

Or double click:

- `start_roboflow_api.bat`

## 4) Load Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `extension/`
5. Open Google Meet (`https://meet.google.com/*`)

Overlay output format:

- `Sign: <label> (<confidence>)`

## Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected fields include `mode: roboflow`, `model_id`, and `dataset1_found`.

## Notes

- Local sklearn/TID model training scripts are still in repo for optional experimentation.
- Runtime prediction path now uses Roboflow API instead of local TID model files.
