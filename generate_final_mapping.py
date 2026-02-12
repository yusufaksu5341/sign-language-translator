#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mapping'i dosya adlarından oluştur
Dosyalar: "Alfabetik_13-01.mp4" formatında
Mapping: {"Alfabetik": {"vid_id": "13-01", ...}}
"""

import json
import re
from pathlib import Path

DATASET_DIR = Path("tid_dataset")
MAPPING_FILE = Path("kelime_mapping.json")

def create_mapping_from_files():
    """
    Dosya adlarından mapping oluştur
    """
    print("Dosyalardan mapping oluşturuluyor...")
    
    mapping = {}
    total_files = 0
    
    for mp4_file in sorted(DATASET_DIR.glob("*.mp4")):
        filename = mp4_file.stem  # Dosya adı (extension olmadan)
        
        # Dosya adından video ID'yi çıkar (dd-dd formatı)
        match = re.search(r'(\d{2}-\d{2})', filename)
        if not match:
            print(f"  ✗ Video ID bulunamadı: {filename}")
            continue
        
        vid_id = match.group(1)
        
        # Kelime adını çıkar (video ID'den önceki kısım)
        word = filename.replace(f"_{vid_id}", "").replace(f"-{vid_id}", "").strip()
        
        if not word:
            word = filename
        
        # Video ID'sinden klasör ID'yi oluştur
        folder_id = int(vid_id.split('-')[0])
        
        if word not in mapping:
            mapping[word] = {
                "vid_id": vid_id,
                "folder_id": str(folder_id).zfill(4),
                "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{str(folder_id).zfill(4)}/degiske/{vid_id}_cr_0.1.mp4"
            }
            print(f"  ✓ {vid_id:6} ← {word[:45]}")
            total_files += 1
        else:
            # Aynı kelime adı multiple times
            print(f"  ⚠️  {word} zaten var ({vid_id})")
    
    return mapping

def main():
    print("=" * 70)
    print("📝 MAPPING İNCELEMESİ VE GÜNCELLEME")
    print("=" * 70)
    
    # Dosyalardan mapping oluştur
    mapping = create_mapping_from_files()
    
    print(f"\n📊 SONUÇ:")
    print(f"  Total mapping entries: {len(mapping)}")
    print(f"  Total files: {len(list(DATASET_DIR.glob('*.mp4')))}")
    
    # Dosyaları kontrol et
    file_count = sum(1 for _ in DATASET_DIR.glob("*.mp4"))
    print(f"\n✓ Her dosya eşleştirildi: {len(mapping) == file_count}")
    
    # Mapping'i kaydet
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Mapping kaydedildi: {MAPPING_FILE}")
    
    # Özet
    print(f"\n📌 İlk 20 mapping:")
    for i, (word, info) in enumerate(list(mapping.items())[:20]):
        print(f"  {i+1:2}. {info['vid_id']:6} ← {word[:50]}")
    
    print(f"\n{'=' * 70}")

if __name__ == "__main__":
    main()
