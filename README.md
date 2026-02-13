# Sign Language Translator (Google Meet + Roboflow)

Bu proje artık tek akış kullanır:

- Dataset kaynağı: `dataset1/`
- Inference: `inference_sdk.InferenceHTTPClient`
- Model: `turk-isaret-dili/2`

Diğer dataset index/profile/annotation akışları kaldırıldı.

## 1) Kurulum

```bash
pip install -r requirements.txt
```

## 2) Lokal API başlat

```bash
python serve_inference.py --api-key YOUR_ROBOFLOW_API_KEY --model-id turk-isaret-dili/2 --dataset dataset1 --host 127.0.0.1 --port 8000
```

PowerShell kısa yol:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_roboflow_api.ps1
```

## 3) Extension yükle

1. `chrome://extensions` aç
2. **Developer mode** aç
3. **Load unpacked** seç
4. `extension/` klasörünü yükle
5. Google Meet aç (`https://meet.google.com/*`)

## API mantığı

- `serve_inference.py`, Roboflow çağrısını `InferenceHTTPClient` ile yapar.
- Python `<3.13` ortamda `inference_sdk` kullanılır; `3.13+` için aynı arayüzde HTTP fallback otomatik devreye girer.
- Sonuçlar `dataset1/` içindeki dosya adlarından çıkarılan etiketlerle filtrelenir.
- `dataset1/` içinde olmayan sınıflar bastırılır.

## Health check

```bash
curl http://127.0.0.1:8000/health
```

Beklenen alanlar: `mode`, `model_id`, `dataset1_found`, `dataset1_labels_count`.
