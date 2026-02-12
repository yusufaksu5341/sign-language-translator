#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doğru yaklaşım: Her LI'deki video URL'sini ve kelime adını javascript ile çek
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

LETTERS = ["A", "B", "C", "Ç", "D", "E", "F", "G", "Ğ", "H", "I", "İ", "J", 
           "K", "L", "M", "N", "O", "Ö", "P", "R", "S", "Ş", "T", "U", "Ü", "V", "Y", "Z"]

BASE_URL = "https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama"

async def scrape_letter_correct(page, letter):
    """
    Her LI'den video ID ve kelime adını birlikte çıkar
    """
    print(f"\n[{letter}] Sayfaya gidiyor...")
    url = f"{BASE_URL}/{letter}"
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
    except:
        print(f"  ✗ Hata")
        return {}
    
    # JavaScript ile LI'leri işlemek
    # Her LI'de: link text, onclick attribute, data attribute vs var
    li_data = await page.evaluate("""
    () => {
        const lis = document.querySelectorAll('li');
        const results = [];
        
        lis.forEach((li) => {
            const link = li.querySelector('a');
            if (!link) return;
            
            const text = link. textContent.trim();
            const onclick = link.getAttribute('onclick') || '';
            const href = link.getAttribute('href') || '';
            const dataAttrs = {};
            
            // Tüm data-* attributes'leri al
            for (let attr of link.attributes) {
                if (attr.name.startsWith('data-')) {
                    dataAttrs[attr.name] = attr.value;
                }
            }
            
            if (text && text.length > 2) {
                results.push({
                    text: text,
                    onclick: onclick,
                    href: href,
                    dataAttrs: dataAttrs,
                    html: link.outerHTML.substring(0, 100)
                });
            }
        });
        
        return results;
    }
    """)
    
    print(f"  ► LI'lerden veriler çekildi: {len(li_data)}")
    
    # Şimdi sayfadaki tüm video URL'lerini al
    html = await page.content()
    video_urls = re.findall(r'https://[^"\'<>]*degiske/[^"\'<>]*\.mp4', html)
    video_urls = list(dict.fromkeys(video_urls))
    
    print(f"  ► Video URL'leri (HTML'den): {len(video_urls)}")
    
    # Video ID'lerini çıkar
    video_ids = []
    for url_str in video_urls:
        match = re.search(r'/degiske/(\d{2}-\d{2})_', url_str)
        if match:
            video_ids.append(match.group(1))
    
    video_ids = list(dict.fromkeys(video_ids))
    print(f"  ► Benzersiz video ID'leri: {video_ids}")
    
    # Kelime adlarını LI'lerden al (sadece text olanlar)
    words = []
    for li_info in li_data:
        text = li_info['text']
        # Filtrele: "EN", "1 (current)" gibi değerleri hariç tut
        if text and text not in ['EN', '1 (current)', 'Sözcük', 'İşaret', 'Alfabetik'] and len(text) > 3:
            words.append(text)
    
    # İlk benzersiz kelime adlarını al
    words = list(dict.fromkeys(words))[:len(video_ids)]
    
    print(f"  ► İlk {len(words)} kelime: {words[:3]}")
    
    # Eşleştir
    mappings = {}
    for i, vid_id in enumerate(video_ids):
        if i < len(words):
            mappings[words[i]] = vid_id
            print(f"    ✓ {vid_id} ← {words[i][:40]}")
    
    return mappings

async def main():
    print("=" * 70)
    print("🔍 CORRECT MAPPING: Video URL ↔ Word Name")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        all_mappings = {}
        
        # Test: A harfini
        mappings_a = await scrape_letter_correct(page, "A")
        all_mappings.update(mappings_a)
        
        await browser.close()
    
    print(f"\n{'=' * 70}")
    print(f"A harfinden: {len(all_mappings)} mapping")
    for word, vid_id in list(all_mappings.items())[:10]:
        print(f"  • {vid_id:6} ← {word}")

if __name__ == "__main__":
    asyncio.run(main())
