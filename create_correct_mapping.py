#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapping'i dosya adlarından oluştur (video ID'sini de tut)
Format: "Alfabetik_13-01.mp4" → {"Alfabetik_13-01": {"vid_id": "13-01"}}
"""

import json
import re
from pathlib import Path

DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

def create_mapping_from_files_enhanced():
    """
    Dosya adlarından mapping oluştur - her dosya unique olacak şekilde
    """
    print("İncelenen video dosyaları:")
    print("=" * 70)
    
    mapping = {}
    file_groups = {}  # word → [vid_id'ler]
    
    for mp4_file in sorted(DATASET_DIR.glob("*.mp4")):
        filename = mp4_file.stem
        
        # Video ID'yi çıkar
        match = re.search(r'(\d{2}-\d{2})', filename)
        if not match:
            print(f"  ✗ ID bulunamadı: {filename}")
            continue
        
        vid_id = match.group(1)
        
        # Kelime adını çıkar
        word = re.sub(r'_.*', '', filename).replace(f"_{vid_id}", "").strip()
        if not word:
            word = filename
        
        folder_id = int(vid_id.split('-')[0])
        
        # Tracking
        if word not in file_groups:
            file_groups[word] = []
        file_groups[word].append(vid_id)
        
        # Mapping'e ekle - her video unique key olarak ekle
        # Eğer bir kelimenin tek video'su varsa, sadece kelime adını kullan
        # Birden fazla varsa, ID de ekle
        
        # Şimdilik hepsin ID'sini ekleyelim
        unique_key = f"{word}_{vid_id}" if filename.endswith(f"_{vid_id}.mp4") else word
        
        # Dosya adında ID varsa, onu kullan
        if f"_{vid_id}" in filename:
            unique_key = filename  # Dosya adı zaten unique
        else:
            unique_key = word
        
        mapping[unique_key] = {
            "vid_id": vid_id,
            "folder_id": str(folder_id).zfill(4),
            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{str(folder_id).zfill(4)}/degiske/{vid_id}_cr_0.1.mp4",
            "display_name": word  # Kullanıcı için görünen ad
        }
    
    print(f"\n📊 ÖZET:")
    print(f"  Total unique keys: {len(mapping)}")
    print(f"  Total files: {len(list(DATASET_DIR.glob('*.mp4')))}")
    
    # Kelime'ye göre gruplamayı göster
    print(f"\n🔤 Kelimeler (kaç video var?):")
    for word in sorted(file_groups.keys()):
        count = len(file_groups[word])
        ids = file_groups[word]
        if count > 1:
            print(f"  • {word:45} ({count:2} video) → {', '.join(ids[:3])}")
        else:
            print(f"  • {word:45} ({count:2} video) → {ids[0]}")
    
    return mapping

def main():
    print("=" * 70)
    print("✅ DOĞRU MAPPING: Her Video Unique Key'le")
    print("=" * 70 + "\n")
    
    mapping = create_mapping_from_files_enhanced()
    
    # Kaydet
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Mapping kaydedildi: {MAPPING_FILE}")
    print(f"  Toplam entries: {len(mapping)}")
    
    # Örnek göster
    print(f"\n📌 Mapping örnekleri:")
    for i, (key, info) in enumerate(list(mapping.items())[:30]):
        display = info.get('display_name', key)
        print(f"  {i+1:2}. {key:50} → {info['vid_id']}")

if __name__ == "__main__":
    main()
