# Sign Language Dataset Scraper

This repository contains a single end-to-end Python pipeline that:

1. Crawls Turkish Sign Language dictionary pages (`A-Z`) with pagination
2. Extracts word names and video URLs directly from HTML
3. Downloads all videos with normalized filenames

It does **not** use `kelime_mapping.json`.

## Current Output

- Discovered videos: ~3400
- Naming format: `Word_vid-id.mp4`
- Output folder: `tid_dataset/`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Full scrape + download

```bash
python main.py --workers 10
```

### Test run (first N videos)

```bash
python main.py --max-downloads 20 --workers 4
```

## Useful Options

- `--output` output folder (default: `tid_dataset`)
- `--workers` parallel download workers (default: `8`)
- `--timeout` request timeout seconds (default: `30`)
- `--retries` retry count (default: `4`)
- `--max-downloads` limit for test runs (default: `0`, means all)

## Notes

- Large media files are ignored by `.gitignore`.
- The script deduplicates by `vid_id`.
- Filenames are sanitized for Windows compatibility.
