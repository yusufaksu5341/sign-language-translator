import requests
import json

# Test headers from user
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Referer": "https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/A",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Chrome";v="144"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-mobile": "?0",
}

url = "https://tidsozluk.aile.gov.tr/vidz_proc/0022/degiske/22-01_cr_0.1.mp4"

print(f"Testing: {url}\n")
print("=" * 70)

try:
    r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
    print(f"Content-Length: {r.headers.get('content-length', 'unknown')}")
    print(f"Actual Size: {len(r.content)} bytes")
    
    print(f"\nFirst 200 bytes (as text):")
    print(r.content[:200].decode('utf-8', errors='replace'))
    
    print(f"\nFirst 16 bytes (hex):")
    print(r.content[:16].hex())
    
    # Check if it's MP4
    if r.content[:4] in [b'\x00\x00\x00\x20', b'\x00\x00\x00\x18', b'ftypMP42']:
        print("\n✓ Valid MP4 file detected!")
    else:
        print("\n✗ NOT a valid MP4 file!")
        print(f"   Magic: {r.content[:8]}")
        
except Exception as e:
    print(f"Error: {e}")

print("[*] Checking main page for embedded data...\n")

try:
    response = requests.get(base_url + "/tr/", timeout=10)
    html = response.text
    
    # Look for common data patterns
    print("[*] Scanning for embedded data...")
    if "window.data" in html:
        print("    [OK] Found 'window.data'")
    
    # Extract window.data
    match = re.search(r'window\.data\s*=\s*({.*?});', html, re.DOTALL)
    if match:
        print("\n[*] Extracting window.data...\n")
        data_str = match.group(1)
        
        # Show sample
        print(f"First 400 chars:\n{data_str[:400]}\n...")
        
        try:
            # Parse the JSON
            data = json.loads(data_str)
            print(f"\n[SUCCESS] Parsed JSON!")
            print(f"Data type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"Keys found: {list(data.keys())}")
                
                # Look for word lists
                for key in data.keys():
                    if 'kelime' in key.lower() or 'word' in key.lower():
                        print(f"\n[***] Potential word list key: '{key}'")
                        item = data[key]
                        if isinstance(item, list):
                            print(f"      Contains {len(item)} items")
                            if item:
                                print(f"      Sample: {item[:2]}")
                
                # Save to file
                with open("extracted_data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("\n[OK] Saved to extracted_data.json")
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse failed: {e}")
            print(f"Trying alternative parsing...\n")
            
    else:
        print("[NOT FOUND] window.data pattern not found")
        
except Exception as e:
    print(f"[ERROR] {e}")
