#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

m = json.load(open('kelime_mapping.json'))
print(f'Mapping entries: {len(m)}')
print('\nÖrnekler (ilk 15):')
for i, (k, v) in enumerate(list(m.items())[:15]):
    print(f'{i+1:2}. {v.get("vid_id"):6} ← {k[:45]}')
