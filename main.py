import requests
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configuration
OUTPUT_FOLDER = "tid_dataset"
MAPPING_FILE = "kelime_mapping.json"
MAX_WORKERS = 3  # Number of concurrent downloads
CHUNK_SIZE = 2 * 1024 * 1024  # 2MB chunks
REQUEST_TIMEOUT = 60  # Increased timeout
MAX_RETRIES = 3  # Retry failed downloads
MIN_FILE_SIZE = 1024 * 10  # 10KB minimum (site may have small previews)

# Headers from browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Referer": "https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/A",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Chrome";v="144"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-mobile": "?0",
    "Range": "bytes=0-"
}

def create_output_folder():
    """Creates output folder if it doesn't exist."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"📁 Created folder: {OUTPUT_FOLDER}")

def sanitize_filename(filename):
    """Removes invalid characters from filename."""
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def download_video(word, video_info):
    """
    Downloads a single video with retry logic and streaming fix.
    
    Args:
        word: Word name (for filename)
        video_info: Dict containing 'url' and 'vid_id'
    
    Returns:
        Tuple: (word, success_status, message)
    """
    url = video_info.get("url")
    vid_id = video_info.get("vid_id", "unknown")
    
    if not url:
        return (word, False, "No URL found")
    
    safe_filename = sanitize_filename(word)
    output_path = os.path.join(OUTPUT_FOLDER, f"{safe_filename}.mp4")
    
    # Skip if already downloaded and file is valid
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        if file_size >= MIN_FILE_SIZE:
            file_size_mb = file_size / (1024 * 1024)
            return (word, True, f"Already exists ({file_size_mb:.2f}MB)")
        else:
            # File is incomplete, delete and retry
            try:
                os.remove(output_path)
            except:
                pass
    
    # Retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Download WITHOUT streaming first (to get full content)
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            
            if response.status_code in [200, 206]:  # 200 OK, 206 Partial Content (Range)
                # Write entire content at once
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                # Validate downloaded file
                file_size = os.path.getsize(output_path)
                if file_size < MIN_FILE_SIZE:
                    os.remove(output_path)
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return (word, False, f"File too small ({file_size//1024}KB) after {MAX_RETRIES} attempts")
                
                file_size_mb = file_size / (1024 * 1024)
                return (word, True, f"✓ Downloaded ({file_size_mb:.2f}MB)")
            
            elif response.status_code == 404:
                return (word, False, "Video not found (404)")
            elif response.status_code == 503:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
                return (word, False, "Server unavailable (503)")
            else:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return (word, False, f"HTTP {response.status_code}")
        
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return (word, False, "Timeout after 3 attempts")
        except requests.exceptions.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return (word, False, "Connection error (3 attempts)")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return (word, False, f"Error: {str(e)[:30]}")
    
    return (word, False, "Max retries exceeded")

def main():
    """Main download function."""
    print("=" * 60)
    print("🎥 Turkish Sign Language Dataset Video Downloader")
    print("=" * 60)
    
    # Check if mapping file exists
    if not os.path.exists(MAPPING_FILE):
        print(f"❌ Error: {MAPPING_FILE} not found!")
        print("   Run listele.py first to generate the mapping file.")
        return
    
    # Load mapping
    print(f"\n📖 Loading {MAPPING_FILE}...")
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        word_mapping = json.load(f)
    
    if not word_mapping:
        print("❌ Mapping file is empty!")
        return
    
    total_words = len(word_mapping)
    print(f"📊 Found {total_words} words to download")
    
    # Create output folder
    create_output_folder()
    
    # Download videos concurrently
    print(f"\n⬇️  Starting downloads ({MAX_WORKERS} concurrent)...\n")
    
    successful = 0
    failed = 0
    already_exist = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_video, word, video_info): word 
            for word, video_info in word_mapping.items()
        }
        
        completed = 0
        for future in as_completed(futures):
            word, success, message = future.result()
            completed += 1
            
            status_icon = "✓" if success else "✗"
            print(f"[{completed}/{total_words}] {status_icon} {word:25} {message}")
            
            if success:
                if "Already exists" in message:
                    already_exist += 1
                else:
                    successful += 1
            else:
                failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 Download Summary")
    print("=" * 60)
    print(f"✓ Successfully downloaded: {successful}")
    print(f"⊘ Already existed:        {already_exist}")
    print(f"✗ Failed:                 {failed}")
    print(f"  Total words:            {total_words}")
    print(f"📂 Output folder:         {os.path.abspath(OUTPUT_FOLDER)}")
    print("=" * 60)

if __name__ == "__main__":
    main()