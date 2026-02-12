#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otomatik inceleme: Her video'yu tıkla ve gerçek kelime adını öğren
Websitede video'ya tıklandığında açılan modal/sayfada kelime adını bul
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

# Harfler (A-Z + Türkçe)
LETTERS = ["A", "B", "C", "Ç", "D", "E", "F", "G", "Ğ", "H", "I", "İ", "J", 
           "K", "L", "M", "N", "O", "Ö", "P", "R", "S", "Ş", "T", "U", "Ü", "V", "Y", "Z"]

MAPPING_FILE = Path("kelime_mapping.json")
BASE_URL = "https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama"

async def scrape_letter(page, letter):
    """
    Bir harfin sayfasını ziyaret et ve doğru kelime-video eşleştirmelerini bul
    """
    print(f"\n[{letter}] Sayfaya gidiyor...")
    url = f"{BASE_URL}/{letter}"
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
    except:
        print(f"  ✗ Sayfa yüklenemedi")
        return {}
    
    # Sayfadaki tüm LI elemanlarını incelemek (burada video'lar listeleniyor)
    lis = await page.query_selector_all("li")
    print(f"  ► Bulundu {len(lis)} liste öğesi")
    
    word_to_vid = {}
    
    for idx, li in enumerate(lis):
        try:
            # LI'nin içindeki metni al
            full_text = await li.text_content()
            if not full_text:
                continue
            
            full_text = full_text.strip()
            if not full_text or len(full_text) < 2:
                continue
            
            # Bu LI'de video bağlantısı var mı?
            link = await li.query_selector("a")
            if not link:
                continue
            
            # Link'in onclick, href, data attributlerini kontrol et
            onclick = await link.get_attribute("onclick") or ""
            href = await link.get_attribute("href") or ""
            data_id = await link.get_attribute("data-id") or ""
            
            # Video ID'sini çıkar (formato: DD-DD)
            video_id = None
            for attr in [onclick, href, data_id]:
                match = re.search(r'(\d{2}-\d{2})', attr)
                if match:
                    video_id = match.group(1)
                    break
            
            if not video_id:
                continue
            
            # Link'in text'ini al (kelime adı)
            link_text = await link.text_content()
            word = link_text.strip() if link_text else None
            
            # Kelime adı yoksa LI'nin başındaki metni kullan
            if not word or word == video_id:
                # LI'nin ilk satırını kelime adı olarak al
                lines = full_text.split('\n')
                word = lines[0].strip() if lines else None
            
            if word and word != video_id and len(word) > 1:
                word_to_vid[word] = video_id
                print(f"    ✓ {video_id:6} ← {word[:50]}")
        except Exception as e:
            continue
    
    return word_to_vid

async def main():
    print("=" * 70)
    print("🔍 OTOMATİK KONTROL: Gerçek kelime-video eşleştirmelerini bul")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1280, "height": 720})
        
        all_mappings = {}
        
        for letter in LETTERS:
            mappings = await scrape_letter(page, letter)
            all_mappings.update(mappings)
            await asyncio.sleep(0.3)
        
        await browser.close()
    
    print(f"\n{'=' * 70}")
    print(f"✓ Toplam yeni mapping: {len(all_mappings)}")
    
    # Mevcut mapping'i yükle
    old_mapping = {}
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            old_mapping = json.load(f)
        print(f"  Eski mapping: {len(old_mapping)} entry")
    
    # Yeni mapping'i oluştur
    # Tüm video_id'leri mevcut mapping'den al, kelimeleri yenisinden al
    new_mapping = {}
    
    # Yeni bulunan kelimelerle başla
    for word, vid_id in all_mappings.items():
        folder_id = int(vid_id.split('-')[0])
        new_mapping[word] = {
            "vid_id": vid_id,
            "folder_id": str(folder_id).zfill(4),
            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{str(folder_id).zfill(4)}/degiske/{vid_id}_cr_0.1.mp4"
        }
    
    # Kaydedilmiş video'ları kontrol et (indirilmiş dosyalar)
    tid_dataset = Path("tid_dataset")
    downloaded_vids = set()
    if tid_dataset.exists():
        # Dosya adlarından video ID çıkar
        for f in tid_dataset.glob("*.mp4"):
            # Dosya adında video ID var mı kontrol et
            match = re.search(r'(\d{2}-\d{2})', f.stem)
            if match:
                downloaded_vids.add(match.group(1))
    
    print(f"  İndirilmiş videolar: {len(downloaded_vids)}")
    
    # Sadece indirilmiş videoları koru
    filtered_mapping = {}
    for word, entry in new_mapping.items():
        if entry['vid_id'] in downloaded_vids:
            filtered_mapping[word] = entry
    
    print(f"  Doğrulanmış mapping: {len(filtered_mapping)}")
    
    # Kaydet
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Güncellenen mapping: {MAPPING_FILE}")
    
    # Örnek göster
    print(f"\n📌 Örnekler (ilk 10):")
    for i, (word, entry) in enumerate(list(filtered_mapping.items())[:10]):
        print(f"  {i+1}. {entry['vid_id']:6} ← {word[:45]}")
    
    print(f"\n{'=' * 70}")

if __name__ == "__main__":
    asyncio.run(main())
