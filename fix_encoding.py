#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix encoding of kelime_mapping.json: Try multiple encodings
"""

import json

encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']

data = None
used_encoding = None

for enc in encodings_to_try:
    try:
        with open('kelime_mapping.json', 'r', encoding=enc) as f:
            data = json.load(f)
        used_encoding = enc
        print(f"✓ Successfully read with encoding: {enc}")
        break
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        continue

if data is None:
    print("✗ Could not read file with any encoding")
    exit(1)

# Write as UTF-8
with open('kelime_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✓ Converted kelime_mapping.json to UTF-8")
print(f"  Original encoding: {used_encoding}")
print(f"  Entries: {len(data)}")
