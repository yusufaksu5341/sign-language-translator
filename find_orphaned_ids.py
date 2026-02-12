#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find video IDs for word-named files by checking the mapping
"""

import json
from pathlib import Path

DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

# Target words (these are our orphaned word-named files)
orphaned_words = {
    "Alfabetik", "Ağız çevresi", "Baş", "Burun", "Göz", 
    "Hakkında", "Omuz", "Proje Ekibi", "Sözcük", 
    "Sözlük Kullanımı", "Vücut önü", "Vücut", "Yanak",
    "Ön yüz", "İletişim", "İşaret"
}

mapping = {}
with open(MAPPING_FILE, 'r', encoding='utf-16') as f:
    mapping = json.load(f)

print("VIDEO ID → WORD MAPPING FOR ORPHANED FILES:")
print("=" * 50)
word_to_ids = {}
for word, info in mapping.items():
    if word in orphaned_words:
        vid_id = info['vid_id']
        if word not in word_to_ids:
            word_to_ids[word] = []
        word_to_ids[word].append(vid_id)

for word in sorted(orphaned_words):
    if word in word_to_ids:
        ids = sorted(word_to_ids[word])
        primary_id = ids[0]  # First one is primary
        print(f"  {word:30} → {primary_id}" + (f" (+{len(ids)-1} more)" if len(ids) > 1 else ""))
    else:
        print(f"  {word:30} → NOT FOUND in mapping")
