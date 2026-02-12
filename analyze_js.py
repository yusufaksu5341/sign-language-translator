import requests
import re

response = requests.get('https://tidsozluk.aile.gov.tr/jsS/siteIncs_v3.js', timeout=10)
content = response.text

# Save full file
with open('site_full.js', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"File size: {len(content)} chars")
print("\nSearching for patterns...\n")

# Look for variables
if "var " in content:
    lines = content.split('\n')
    for i, line in enumerate(lines[:50]):
        if 'var' in line or 'function' in line or '[' in line:
            print(f"{i}: {line[:120]}")
