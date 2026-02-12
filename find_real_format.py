import requests
import time

# Test different URL format variations
base = "https://tidsozluk.aile.gov.tr"
folder = "0001"
word = "Aç"  # First word

# Test variations
test_cases = [
    # Original format
    (f"{base}/vidz_proc/{folder}/degiske/01-02_cr_0.1.mp4", "Format1: 01-02"),
    (f"{base}/vidz_proc/{folder}/degiske/1-2_cr_0.1.mp4", "Format2: 1-2"),
    (f"{base}/vidz_proc/{folder}/degiske/0102_cr_0.1.mp4", "Format3: 0102"),
    (f"{base}/vidz_proc/{folder}/degiske/01-02.mp4", "Format4: 01-02 (no _cr_0.1)"),
    # Different path
    (f"{base}/vidz_proc/01/degiske/01-02_cr_0.1.mp4", "Format5: folder=01 (2digit)"),
]

print(f"Testing {len(test_cases)} URL variations...")
print("=" * 70)

for url, desc in test_cases:
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        size = r.headers.get('content-length', '?')
        status = r.status_code
        
        # Get actual content size if no header
        if size == '?':
            r2 = requests.get(url, timeout=5)
            size = len(r2.content)
            is_video = r2.content[:4] in [b'\x00\x00\x00\x20', b'\x00\x00\x00\x18']  # MP4 magic bytes
        else:
            size = int(size)
            is_video = size > 1000000  # > 1MB likely video
        
        size_mb = size / (1024 * 1024) if isinstance(size, int) else 0
        marker = "[✓]" if is_video and size_mb > 4 else "[✗]"
        
        print(f"{marker} {desc}")
        print(f"    Status: {status}, Size: {size_mb:.1f}MB")
        
    except Exception as e:
        print(f"[✗] {desc}")
        print(f"    Error: {str(e)[:50]}")
    
    time.sleep(0.5)

print("=" * 70)
