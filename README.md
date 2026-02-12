# Turkish Sign Language Dataset Scraper

A professional Python toolkit to scrape sign language word data and batch download videos from https://tidsozluk.aile.gov.tr/

## 📋 Overview

This project consists of two main scripts:

1. **listele.py** - Selenium-based web scraper that extracts word names and IDs
2. **main.py** - Batch video downloader with concurrent downloads

## 🎯 Features

### listele.py (Web Scraper)
- ✅ Dynamically loads all words from the website
- ✅ Extracts word names and video IDs from onclick attributes
- ✅ Automatically calculates folder IDs based on video IDs
- ✅ Constructs full video URLs
- ✅ Handles Turkish character encoding (UTF-8)
- ✅ Saves results to `kelime_mapping.json`

### main.py (Video Downloader)
- ✅ Concurrent downloads (configurable workers)
- ✅ Automatic filename sanitization
- ✅ Skip already downloaded videos
- ✅ Detailed progress reporting
- ✅ Robust error handling
- ✅ Download summary statistics

## 🔧 Installation

### Requirements
```bash
pip install selenium webdriver-manager requests
```

### Chrome Driver
The script automatically downloads the correct Chrome WebDriver via `webdriver-manager`.

## 📖 Usage

### Step 1: Extract Words and IDs

Run the scraper to generate the mapping file:

```bash
python listele.py
```

**Expected Output:**
```
🔄 Accessing https://tidsozluk.aile.gov.tr/
⏳ Waiting for content to load...
📜 Scrolling to load all words...
🔍 Extracting words and IDs...
Found 5000 items
  [1] ✓ Anne                 -> vid_id: 01-01, folder: 0001
  [2] ✓ Aynı                 -> vid_id: 02-15, folder: 0002
  ...
✅ Total words extracted: 5000
💾 Saved to kelime_mapping.json
✔ Browser closed
```

**Output File:** `kelime_mapping.json`
```json
{
    "Anne": {
        "vid_id": "01-01",
        "folder_id": "0001",
        "url": "https://tidsozluk.aile.gov.tr/vidz_proc/0001/degiske/01-01_cr_0.1.mp4"
    },
    "Aynı": {
        "vid_id": "02-15",
        "folder_id": "0002",
        "url": "https://tidsozluk.aile.gov.tr/vidz_proc/0002/degiske/02-15_cr_0.1.mp4"
    }
}
```

### Step 2: Download Videos

Run the downloader to fetch all videos:

```bash
python main.py
```

**Expected Output:**
```
============================================================
🎥 Turkish Sign Language Dataset Video Downloader
============================================================

📖 Loading kelime_mapping.json...
📊 Found 5000 words to download
📁 Created folder: tid_dataset

⬇️  Starting downloads (3 concurrent)...

[1/5000] ✓ Anne                      ✓ Downloaded (2.45MB)
[2/5000] ✓ Aynı                      ✓ Downloaded (1.82MB)
[3/5000] ✗ TestWord                  Video not found (404)
[4/5000] ✓ Başka                     Already exists (3.12MB)
...

============================================================
📈 Download Summary
============================================================
✓ Successfully downloaded: 4850
⊘ Already existed:        125
✗ Failed:                 25
  Total words:            5000
📂 Output folder:         C:\Users\Yusuf\Documents\python\WebScraper\tid_dataset
============================================================
```

## 📁 File Structure

```
WebScraper/
├── listele.py              # Main web scraper
├── main.py                 # Video downloader
├── kelime_mapping.json     # Generated mapping (output from listele.py)
├── tid_dataset/            # Downloaded videos (output from main.py)
│   ├── Anne.mp4
│   ├── Aynı.mp4
│   └── ...
└── README.md              # This file
```

## 🔑 URL Pattern

The video URL is constructed as:
```
https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4
```

Where:
- **folder_id**: Derived from first part of vid_id, zero-padded to 4 digits
  - Example: `22` → `0022`
- **vid_id**: Extracted from the onclick attribute (format: `XX-XX`)

## ⚙️ Configuration

### listele.py
Edit these settings in the script:
```python
# Enable headless mode (no browser window)
options.add_argument("--headless")

# Adjust wait times
wait.until(EC.presence_of_all_elements_located(), timeout=20)
```

### main.py
Edit these settings in the script:
```python
MAX_WORKERS = 3           # Number of concurrent downloads
CHUNK_SIZE = 1024 * 1024  # 1MB chunks
REQUEST_TIMEOUT = 30      # 30 seconds per request
```

## 🐛 Troubleshooting

### Issue: No words found
- **Cause**: Website structure may have changed
- **Solution**: Inspect the HTML to find the correct XPath for word elements

### Issue: 404 errors on videos
- **Cause**: Some videos may not be available
- **Solution**: Normal behavior - check the summary statistics. The script skips unavailable videos automatically.

### Issue: Slow downloads
- **Cause**: Network or server rate limiting
- **Solution**: Reduce `MAX_WORKERS` or increase `REQUEST_TIMEOUT`

### Issue: Chrome driver fails
- **Cause**: Chrome not installed or incompatible version
- **Solution**: Install latest Chrome or use `webdriver-manager` to auto-manage

## 📊 Performance Tips

1. **Increase concurrent workers** (if server allows):
   ```python
   MAX_WORKERS = 5  # More parallel downloads
   ```

2. **Use headless mode** (faster):
   ```python
   options.add_argument("--headless")
   ```

3. **Run during off-peak hours** to avoid rate limiting

4. **Use resume functionality**: The downloader skips already downloaded files

## 📝 License

This project was created for educational and research purposes.

## 🤝 Contributing

To improve this script:
1. Report bugs with detailed error messages
2. Suggest XPath updates if website structure changes
3. Share performance optimizations

---

**Last Updated:** February 12, 2026
**Status:** ✅ Production Ready
