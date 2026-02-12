"""
Create clean mapping with unique video names
"""
import json
import re

# Load current mapping
with open('kelime_mapping.json', 'r', encoding='utf-8') as f:
    old_data = json.load(f)

# Create new clean mapping - key: video ID, value: all info
new_mapping = {}
seen_ids = set()

for word, info in old_data.items():
    vid_id = info['vid_id']
    folder_id = info['folder_id']
    
    # Skip duplicates
    if vid_id not in seen_ids:
        new_mapping[vid_id] = {
            "vid_id": vid_id,
            "folder_id": folder_id,
            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
        }
        seen_ids.add(vid_id)

print(f"Old mapping: {len(old_data)} entries")
print(f"New mapping: {len(new_mapping)} unique video IDs")

# Save new clean mapping
with open('kelime_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(new_mapping, f, ensure_ascii=False, indent=2)

print(f"\n✓ Saved clean mapping to kelime_mapping.json")
print(f"\nSample:")
for vid_id, info in list(new_mapping.items())[:5]:
    print(f"  {vid_id}: {info['url']}")
