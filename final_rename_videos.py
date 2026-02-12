#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rename all 146 MP4 files to their word names from mapping
Final version with proper handling of Windows filename restrictions
"""

import json
from pathlib import Path
import re

DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

def sanitize_filename(filename):
    """Remove Windows-illegal characters from filename"""
    # Replace illegal characters: / \ : * ? " < > |
    sanitized = re.sub(r'[/\\:*?"<>|]', '-', filename)
    # Remove trailing spaces and dots
    sanitized = re.sub(r'[\s.]+$', '', sanitized)
    return sanitized

def main():
    print("=" * 70)
    print("🎯 FINAL VIDEO RENAMING: All 146 files to word names")
    print("=" * 70)
    
    # Load mapping
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    print(f"\n📊 Loaded {len(mapping)} word entries from mapping")
    
    # Get all existing videos
    existing_files = {f.stem: f for f in DATASET_DIR.glob("*.mp4")}
    print(f"📁 Found {len(existing_files)} MP4 files in {DATASET_DIR}")
    
    # Build reverse mapping: vid_id → (word, sanitized_word)
    vid_to_word = {}
    for word, info in mapping.items():
        vid_id = info['vid_id']
        clean_word = sanitize_filename(word)
        
        # Keep track of first (primary) occurrence
        if vid_id not in vid_to_word:
            vid_to_word[vid_id] = (word, clean_word)
    
    print(f"📖 Created reverse mapping with {len(vid_to_word)} unique video IDs")
    
    # Rename sequence
    renamed_count = 0
    failed_renames = []
    skipped = []
    duplicates_found = {}
    
    for old_stem, old_file in sorted(existing_files.items()):
        if old_stem in vid_to_word:
            word, clean_word = vid_to_word[old_stem]
            new_filename = f"{clean_word}.mp4"
            new_file = DATASET_DIR / new_filename
            
            # Track potential duplicates
            if new_filename in duplicates_found:
                duplicates_found[new_filename].append(old_stem)
            else:
                duplicates_found[new_filename] = [old_stem]
            
            # Try to rename
            try:
                if new_file.exists() and new_file != old_file:
                    print(f"⚠️  SKIP: {new_filename} already exists")
                    skipped.append(old_stem)
                else:
                    old_file.rename(new_file)
                    print(f"✓ {old_stem:6} → {clean_word}")
                    renamed_count += 1
            except Exception as e:
                print(f"✗ ERROR: {old_file.name}: {e}")
                failed_renames.append((old_stem, str(e)))
        else:
            print(f"✗ NOT IN MAPPING: {old_stem}")
            skipped.append(old_stem)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📋 SUMMARY")
    print(f"  ✓ Successfully renamed: {renamed_count}")
    print(f"  ✗ Failed/skipped: {len(skipped) + len(failed_renames)}")
    
    duplicate_words = {f: ids for f, ids in duplicates_found.items() if len(ids) > 1}
    if duplicate_words:
        print(f"\n⚠️  Duplicate target names ({len(duplicate_words)}):")
        for filename, ids in list(duplicate_words.items())[:5]:
            print(f"   • {filename}: {', '.join(ids)}")
        if len(duplicate_words) > 5:
            print(f"   ... and {len(duplicate_words)-5} more")
    
    # Verify final state
    final_files = list(DATASET_DIR.glob("*.mp4"))
    print(f"\n✅ FINAL STATE: {len(final_files)} MP4 files")
    
    # Update mapping to only include successfully converted files
    print(f"\n🔄 Creating filtered mapping with only {len(final_files)} entries...")
    filtered_mapping = {}
    for word, info in mapping.items():
        clean_word = sanitize_filename(word)
        target_file = DATASET_DIR / f"{clean_word}.mp4"
        if target_file.exists():
            filtered_mapping[word] = info
    
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_mapping, f, ensure_ascii=False, indent=2)
    print(f"✓ Updated mapping with {len(filtered_mapping)} verified entries")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
