#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rename all downloaded videos from video IDs to their corresponding word names
Example: 22-01.mp4 → Hakkında.mp4
"""

import json
import os
from pathlib import Path
import sys
import re

# Configuration
DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

def sanitize_filename(filename):
    """Remove illegal filename characters"""
    # Replace forward/backslash and other illegal characters
    illegal_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(illegal_chars, '-', filename)
    # Remove trailing spaces/dots (Windows restriction)
    sanitized = sanitized.rstrip('. ')
    return sanitized

def load_mapping():
    """Load the word-to-video mapping from JSON"""
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_existing_videos():
    """Get all existing MP4 files in tid_dataset"""
    return {f.stem: f for f in DATASET_DIR.glob("*.mp4")}

def main():
    print("=" * 70)
    print("🎯 VIDEO RENAMING TOOL: Video IDs → Word Names")
    print("=" * 70)
    
    # Load existing mapping
    mapping = load_mapping()
    print(f"\n📊 Loaded mapping with {len(mapping)} entries from {MAPPING_FILE}")
    
    # Get existing videos
    existing = get_existing_videos()
    print(f"📁 Found {len(existing)} MP4 files in {DATASET_DIR}")
    
    # Create reverse mapping: vid_id → word
    vid_id_to_word = {}
    for word, info in mapping.items():
        vid_id = info['vid_id']
        # Sanitize word for use as filename
        clean_word = sanitize_filename(word)
        if vid_id in vid_id_to_word:
            print(f"⚠️  WARNING: Video ID {vid_id} mapped to both '{vid_id_to_word[vid_id]}' and '{clean_word}'")
            print(f"   Keeping first mapping: '{vid_id_to_word[vid_id]}'")
        else:
            vid_id_to_word[vid_id] = clean_word
    
    print(f"\n🔍 Created reverse mapping with {len(vid_id_to_word)} unique video IDs")
    
    # Find videos that can be renamed
    renamed_count = 0
    not_found = []
    duplicates = {}
    
    for vid_id, old_file in existing.items():
        if vid_id in vid_id_to_word:
            word = vid_id_to_word[vid_id]
            
            # Check for duplicate word names
            if word in duplicates:
                duplicates[word].append(vid_id)
            else:
                duplicates[word] = [vid_id]
            
            new_filename = f"{word}.mp4"
            new_file = DATASET_DIR / new_filename
            
            # Check if new filename already exists
            if new_file.exists() and new_file != old_file:
                print(f"⚠️  SKIP: {new_filename} already exists (from {vid_id})")
                continue
            
            # Rename the file
            try:
                old_file.rename(new_file)
                print(f"✓ {vid_id}.mp4 → {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"✗ ERROR renaming {old_file}: {e}")
        else:
            not_found.append(vid_id)
    
    # Report duplicates (same word for multiple videos)
    print(f"\n📋 RENAME SUMMARY")
    print(f"  ✓ Successfully renamed: {renamed_count} files")
    if not_found:
        print(f"  ✗ Not in mapping (orphaned): {len(not_found)} files")
        if not_found:
            print(f"    IDs: {', '.join(not_found[:5])}" + (" ..." if len(not_found) > 5 else ""))
    
    # List duplicate mappings
    duplicate_words = {w: ids for w, ids in duplicates.items() if len(ids) > 1}
    if duplicate_words:
        print(f"\n⚠️  WARNING: {len(duplicate_words)} word names map to multiple videos:")
        for word, vid_ids in sorted(duplicate_words.items()):
            print(f"   • '{word}': {', '.join(vid_ids)}")
    
    # Create new mapping with word keys and check consistency
    print(f"\n🔄 Creating new mapping file with word names as keys...")
    new_mapping = {}
    for word, info in mapping.items():
        vid_id = info['vid_id']
        if vid_id in get_existing_videos():
            new_mapping[word] = info
    
    # Verify no duplicate words in final mapping
    if len(new_mapping) == len(set(new_mapping.keys())):
        # Save new mapping
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_mapping, f, ensure_ascii=False, indent=2)
        print(f"✓ Updated mapping saved with {len(new_mapping)} entries (word keys)")
    else:
        print(f"⚠️  WARNING: Duplicate word keys in mapping, NOT overwriting {MAPPING_FILE}")
    
    # Final verification
    print(f"\n✅ VERIFICATION")
    final_videos = get_existing_videos()
    print(f"   Final video count: {len(final_videos)}")
    print(f"   Videos in mapping: {len(new_mapping)}")
    if len(final_videos) == len(new_mapping):
        print(f"   ✓ All videos are in mapping!")
    else:
        print(f"   ⚠️  Mismatch: {abs(len(final_videos) - len(new_mapping))} difference")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
