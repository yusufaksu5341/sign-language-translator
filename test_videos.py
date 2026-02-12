"""Check downloaded videos - test which ones work"""
import os
import json
import requests

folder = "tid_dataset"
mapping_file = "kelime_mapping.json"

print("\n[*] Checking downloaded videos...\n")

# Load mapping
with open(mapping_file, "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Check file sizes
print(f"[*] Analyzing {len(mapping)} words from mapping\n")

working = []
broken = []
missing = []

for word, info in mapping.items():
    filepath = os.path.join(folder, f"{word}.mp4")
    url = info["url"]
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        if size > 5000:  # Normal video > 5KB
            working.append((word, size))
        else:
            broken.append((word, size))
    else:
        missing.append(word)

print(f"[OK] Working videos: {len(working)}")
print(f"[!] Broken/Empty videos: {len(broken)}")
print(f"[?] Missing videos: {len(missing)}\n")

if broken:
    print("Broken videos (too small):")
    for word, size in broken[:10]:
        print(f"  - {word}: {size} bytes")
    print()

if missing:
    print("Missing videos (not downloaded):")
    for word in missing[:10]:
        print(f"  - {word}")
    print()

# Test URLs
print("[*] Testing 10 random URLs...\n")
import random
test_urls = [info["url"] for info in list(mapping.values())[:10]]

for url in test_urls:
    try:
        response = requests.head(url, timeout=5)
        status = response.status_code
        size = response.headers.get("content-length", "?")
        print(f"  [{status}] {url[:60]}... (size: {size})")
    except Exception as e:
        print(f"  [FAIL] {url[:60]}... ({str(e)[:30]})")

print("\n[Summary]")
print(f"Total words: {len(mapping)}")
print(f"Files working: {len(working)}")
print(f"Success rate: {len(working) / len(mapping) * 100:.1f}%")
