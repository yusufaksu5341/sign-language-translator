#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore all MP4 files to video ID naming (e.g., 22-01.mp4)
Parses current filename to extract video ID where possible
"""

import json
from pathlib import Path
import re

DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

def extract_vid_id(filename):
    """Try to extract video ID from various naming formats"""
    # Format: DD-DD (e.g., 22-01)
    match = re.search(r'(\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def main():
    """Rename all files back to video ID format"""
    mapping = {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Build vid_id to info mapping
    vid_id_to_info = {}
    for word, info in mapping.items():
        vid_id = info['vid_id']
        vid_id_to_info[vid_id] = info
    
    print(f"Restoring {len(vid_id_to_info)} file names to video ID format...")
    renamed = 0
    
    for old_file in sorted(DATASET_DIR.glob("*.mp4")):
        vid_id = extract_vid_id(old_file.stem)
        
        if vid_id and vid_id in vid_id_to_info:
            new_file = DATASET_DIR / f"{vid_id}.mp4"
            if new_file != old_file:
                try:
                    old_file.rename(new_file)
                    print(f"  {old_file.name} → {new_file.name}")
                    renamed += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
        else:
            print(f"  SKIP: {old_file.name} (no ID found or not in mapping)")
    
    print(f"\n✓ Restored {renamed} files to video ID naming")
    print(f"Final count: {len(list(DATASET_DIR.glob('*.mp4')))} MP4 files")

if __name__ == "__main__":
    main()
