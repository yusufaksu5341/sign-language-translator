#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit çözüm: HTML'de video'ları bul, kelime adlarını bul, eşleştir
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

LETTERS = ["A", "B", "C", "Ç", "D", "E", "F", "G", "Ğ", "H", "I", "İ", "J", 
           "K", "L", "M", "N", "O", "Ö", "P", "R", "S", "Ş", "T", "U", "Ü", "V", "Y", "Z"]

BASE_URL = "https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama"

async def scrape_letter_v3(page, letter):
    """
    HTML'deki video element'lerini ve kelime adlarını eşleştirmek
    """
    print(f"\n[{letter}] Sayfaya gidiyor...")
    url = f"{BASE_URL}/{letter}"
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
        
        # HTML kaynağını al
        html = await page.content()
        
        # Video URL'lerini çıkar (degiske pattern'ini ara)
        video_ids = re.findall(r'/degiske/(\d{2}-\d{2})_', html)
        video_ids = list(dict.fromkeys(video_ids))  # Benzersiz
        
        print(f"  ► Video ID'leri (HTML'den): {video_ids}")
        
        # LI → A tag'larındaki kelime adlarını çıkar
        lis = await page.query_selector_all("li")
        words = []
        for li in lis:
            link = await li.query_selector("a")
            if link:
                text = await link.text_content()
                if text and len(text.strip()) > 2 and text.strip() != 'EN':
                    words.append(text.strip())
        
        print(f"  ► Kelime adları (LI'lerden): {len(words)} bulundu")
        if words:
            print(f"    İlk 5: {words[:5]}")
        
        # Eşleştir: video_id'leri kelime adlarıyla
        # Sıra: ilk video_id'si ilk kelimeyle, vs.
        mappings = {}
        for i, vid_id in enumerate(video_ids):
            if i < len(words):
                word = words[i]
                mappings[word] = vid_id
                print(f"    ✓ {vid_id:6} ← {word[:40]}")
            else:
                print(f"    ⚠️  {vid_id:6} ← (no word)")
        
        return mappings
    
    except Exception as e:
        print(f"  ✗ Hata: {e}")
        return {}

async def main():
    print("=" * 70)
    print("🔍 TÜM HARFLERİ KONTROL ET: Doğru kelime-video eşleştirmesi")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        all_mappings = {}
        
        # Tüm harfleri kontrol et
        for letter in LETTERS:
            mappings = await scrape_letter_v3(page, letter)
            all_mappings.update(mappings)
            await asyncio.sleep(0.2)
        
        await browser.close()
    
    print(f"\n{'=' * 70}")
    print(f"✓ TOPLAM MAPPING: {len(all_mappings)}")
    
    # İndirilmiş videolarla karşılaştır
    tid_dataset = Path("tid_dataset")
    vid_files = list(tid_dataset.glob("*.mp4"))
    video_vids = set()
    for f in vid_files:
        match = re.search(r'(\d{2}-\d{2})', f.stem)
        if match:
            video_vids.add(match.group(1))
    
    print(f"  İndirilmiş videolar: {len(video_vids)}")
    
    # Mapping'i videolarla filtrele
    final_mapping = {}
    for word, vid_id in all_mappings.items():
        if vid_id in video_vids:
            final_mapping[word] = vid_id
    
    print(f"  Doğrulanmış mapping (indirilmiş): {len(final_mapping)}")
    
    # kelime_mapping.json'ı güncelle
    mapping_data = {}
    for word, vid_id in final_mapping.items():
        folder_id = int(vid_id.split('-')[0])
        mapping_data[word] = {
            "vid_id": vid_id,
            "folder_id": str(folder_id).zfill(4),
            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{str(folder_id).zfill(4)}/degiske/{vid_id}_cr_0.1.mp4"
        }
    
    with open("kelime_mapping.json", 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Güncellenmiş mapping kaydedildi")
    
    print(f"\n📌 Örnekler (ilk 10):")
    for i, (word, vid_id) in enumerate(list(final_mapping.items())[:10]):
        print(f"  {i+1}. {vid_id:6} ← {word}")

if __name__ == "__main__":
    asyncio.run(main())
