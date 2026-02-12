"""
Remove failed videos from mapping file
Keep only successfully downloaded videos
"""
import json
import os

# Get list of successfully downloaded files
vid_folder = "tid_dataset"
downloaded_files = set()

for filename in os.listdir(vid_folder):
    if filename.endswith('.mp4'):
        # Extract video ID (e.g., "22-01" from "22-01.mp4")
        vid_id = filename.replace('.mp4', '')
        downloaded_files.add(vid_id)

print(f"Downloaded files: {len(downloaded_files)}")

# Load mapping
with open('kelime_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

print(f"Total in mapping: {len(mapping)}")

# Filter to keep only downloaded videos
new_mapping = {}
for vid_id, info in mapping.items():
    if vid_id in downloaded_files:
        new_mapping[vid_id] = info

print(f"After filtering: {len(new_mapping)}")

# Save filtered mapping
with open('kelime_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(new_mapping, f, ensure_ascii=False, indent=2)

print(f"\n✓ Saved mapping with {len(new_mapping)} working videos")
print(f"  Removed {len(mapping) - len(new_mapping)} failed videos")

# Show stats
print(f"\nSample working videos:")
for vid_id in list(new_mapping.keys())[:5]:
    print(f"  ✓ {vid_id}.mp4")
