import json
with open('kelime_mapping.json') as f:
    data = json.load(f)
    
# Get first 5 URLs and their IDs
for i, (word, info) in enumerate(list(data.items())[:5]):
    print(f'{i+1}. {word}:')
    print(f'   URL: {info["url"]}')
    print(f'   VID: {info["vid_id"]}')
    print()
