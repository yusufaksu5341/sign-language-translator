import requests
import re

# Test real video URL from my older tests
test_urls = [
    "https://tidsozluk.aile.gov.tr/vidz_proc/0001/degiske/01-02_cr_0.1.mp4",
    "https://tidsozluk.aile.gov.tr/vidz_proc/0001/degiske/1-1_cr_0.1.mp4",  # Try different format
    "https://tidsozluk.aile.gov.tr/vidz_proc/0001/degiske/1-2_cr_0.1.mp4",
]

print("Testing URLs and checking content sizes...")
for url in test_urls:
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        print(f"\n{url}")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Length: {r.headers.get('content-length', 'unknown')}")
        
        # Get full content to check size
        r2 = requests.get(url, timeout=5)
        content_size = len(r2.content)
        print(f"  Actual Size: {content_size} bytes ({content_size/1024:.1f}KB)")
        
        # Check if it's actually a video
        if r2.content[:4] == b'\x00\x00\x00\x20':
            print(f"  [✓] Valid MP4 file detected")
        elif content_size < 50000:
            print(f"  [✗] Too small - likely error page")
            print(f"      Content preview: {r2.content[:100]}")
    except Exception as e:
        print(f"\n{url}")
        print(f"  Error: {e}")
