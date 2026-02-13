# Sign Language Translator (Google Meet + Roboflow)

This project uses your Roboflow model (`turk-isaret-dili/2`) for live sign prediction from Google Meet frames.

## Requirements

- Roboflow API key
- Chrome extension load access (`chrome://extensions`)

Python and local API scripts are optional now (only needed if you want local backend flow).

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Configure extension API key

Extension uses `chrome.storage.local` key `roboflow_api_key`.

Default key is auto-defined in `extension/background.js`, so manual entry is not required.

1. Open `chrome://extensions`
2. Find this extension and open **Service Worker** console
3. Run:

```javascript
chrome.storage.local.set({ roboflow_api_key: "YOUR_ROBOFLOW_API_KEY" })
```

## 3) Load Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `extension/`
5. Open Google Meet (`https://meet.google.com/*`)

Overlay output format:

- `Sign: <label> (<confidence>)`

## Optional: local API mode (not required)

```bash
python serve_inference.py --api-key YOUR_ROBOFLOW_API_KEY --model-id turk-isaret-dili/2 --dataset dataset1 --host 127.0.0.1 --port 8000
```

This local mode now combines `dataset1` + Roboflow model output:

- Builds a visual profile from `dataset1` videos
- Blends Roboflow confidence with dataset match score
- Suppresses noisy predictions when frame does not match dataset profile

Optional tuning flags:

```bash
--dataset-sample-videos 350 --min-dataset-match 0.18 --dataset-profile-cache models/dataset1_profile.npz
```

Or set environment variable:

```powershell
$env:ROBOFLOW_API_KEY="YOUR_ROBOFLOW_API_KEY"
python serve_inference.py --model-id turk-isaret-dili/2 --dataset dataset1 --host 127.0.0.1 --port 8000
```

## Optional: one-command local run (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -RoboflowApiKey YOUR_ROBOFLOW_API_KEY -StartApi -KeepApiRunning
```

### Fast start (auto command file)

```powershell
powershell -ExecutionPolicy Bypass -File .\start_roboflow_api.ps1
```

Or double click (optional):

- `start_roboflow_api.bat`

## Optional health check (local API mode)

```bash
curl http://127.0.0.1:8000/health
```

Expected fields include `mode: roboflow`, `model_id`, and `dataset1_found`.

## Notes

- Local sklearn/TID model training scripts are still in repo for optional experimentation.
- Extension runtime prediction path is direct Roboflow (no `.bat` required).
- Before publishing extension publicly, move API key to a backend proxy or rotate this key.
