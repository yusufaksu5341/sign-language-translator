#!/usr/bin/env python3
"""
Tüm Turkish Sign Language Kelimelerini Scrape Eder
Harf harf sayfaları ziyaret eder ve kelime-video mappingini çıkartır
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re

print("\n" + "="*70)
print("[*] Turkish Sign Language Video Scraper - FULL MODE")
print("="*70 + "\n")

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    alphabet = "ABCÇDEFGĞHIIJKLMNOÖPRSŞTUÜVYZ"
    all_words = {}
    
    print("[PHASE 1] Extracting words from alphabetic pages\n")
    
    for idx, letter in enumerate(alphabet, 1):
        print(f"  [{idx:2d}/{len(alphabet)}] Harfi: {letter} - Sayfa yükleniyor...", end="")
        
        try:
            url = f"https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/{letter}"
            driver.get(url)
            time.sleep(1.5)
            
            # Scroll to trigger loading
            for _ in range(2):
                driver.execute_script("window.scrollBy(0, 2000);")
                time.sleep(0.3)
            
            # Extract words from this page
            html = driver.page_source
            word_links = re.findall(r'href="(/tr/([^/"?#]+))"', html)
            
            new_words = 0
            for _, word in word_links:
                if word not in all_words and word not in ['Alfabetik', 'Arama', 'sozluk', 'proje', 'hakkinda', 'ekibi', 'iletisim', 'kullanimi', 'tr']:
                    if len(word) > 1 and not word.endswith('.html'):
                        all_words[word] = None
                        new_words += 1
            
            print(f" +{new_words:3d} yeni kelime (Toplam: {len(all_words)})")
            
        except Exception as e:
            print(f" [HATA]: {str(e)[:40]}")
    
    print(f"\n[PHASE 2] Total kelime sayısı: {len(all_words)}\n")
    
    if len(all_words) == 0:
        print("[-] Hiç kelime bulunamadı!")
    else:
        # Get video URLs
        print(f"[PHASE 3] Her kelime için video URL'si alınıyor ({len(all_words)} kelime)\n")
        print("  UYARI: Bu işlem 10-30 dakika sürebilir. Lütfen bekleyin...\n")
        
        word_mapping = {}
        success = 0
        failed = 0
        
        for idx, word in enumerate(sorted(all_words.keys()), 1):
            try:
                url = f"https://tidsozluk.aile.gov.tr/tr/{word}"
                driver.get(url)
                time.sleep(0.5)
                
                html = driver.page_source
                
                # Extract video ID
                match = re.search(r'/vidz_proc/(\d{4})/degiske/(\d{2}-\d{2})_cr_', html)
                
                if match:
                    folder_id = match.group(1)
                    vid_id = match.group(2)
                    
                    word_mapping[word] = {
                        "vid_id": vid_id,
                        "folder_id": folder_id,
                        "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                    }
                    success += 1
                    
                    if idx % 50 == 0:
                        print(f"  [{idx:4d}/{len(all_words)}] {word:25s} -> {vid_id} (folder: {folder_id})")
                else:
                    failed += 1
                
            except:
                failed += 1
        
        print(f"\n[PHASE 4] Tamamlandı!")
        print(f"  Başarılı: {success} kelime")
        print(f"  Başarısız: {failed} kelime\n")
        
        # Save
        with open("kelime_mapping.json", "w", encoding="utf-8") as f:
            json.dump(word_mapping, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] {len(word_mapping)} kelime mapping 'kelime_mapping.json'a kaydedildi!\n")
        print(f"[NEXT STEP] Videoları indirmek için çalıştırın:")
        print(f"  >>> python main.py\n")
        
        # Sample
        print("Örnek kelimeler:")
        for word in list(word_mapping.keys())[:3]:
            info = word_mapping[word]
            print(f"  - {word}: {info['url']}")

finally:
    driver.quit()
    print("\n[OK] İşlem tamamlandı.\n")
