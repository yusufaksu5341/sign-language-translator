"""
Optimize Scraper - Tüm Kelimeleri Harf Harf Çıkartır
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re

print("=" * 70)
print("[*] Turkish Sign Language Dictionary - Complete Word Extractor")
print("=" * 70)

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("\n[1] Opening https://tidsozluk.aile.gov.tr/tr/")
    driver.get("https://tidsozluk.aile.gov.tr/tr/")
    time.sleep(4)
    
    print("[2] Extracting all word links from page...\n")
    
    # Get all links and extract words
    words_set = set()
    
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"    Scanning {len(links)} links...")
    
    for link in links:
        try:
            href = link.get_attribute("href") or ""
            text = link.text.strip()
            
            # Pattern: /tr/WordName (without .html)
            if "/tr/" in href and not ".html" in href and text:
                word = re.search(r'/tr/([^/?#]+)', href)
                if word:
                    word_name = word.group(1)
                    # Filter out navigation words
                    if word_name not in ['Alfabetik', 'Arama', 'sozluk', 'proje'] and len(word_name) > 1:
                        if text == word_name or text[:10] == word_name[:10]:
                            words_set.add(word_name)
        except:
            pass
    
    words_list = sorted(list(words_set))
    print(f"    [OK] Found {len(words_list)} words in homepage\n")
    
    if words_list:
        print("    Sample words:")
        for word in words_list[:10]:
            print(f"      - {word}")
    
    # Now visit each letter page (Alfabetik)
    print("\n[3] Visiting alphabetic pages (A-Z)...")
    print("    This will take a moment...\n")
    
    alphabet = "ABCÇDEFGĞHIIJKLMNOÖPRSŞTUÜVYZ"
    
    for letter in alphabet:
        try:
            url = f"https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/{letter}"
            driver.get(url)
            time.sleep(1.5)
            
            # Scroll to load content
            driver.execute_script("window.scrollBy(0, 3000);")
            time.sleep(0.5)
            
            # Extract from this page
            links = driver.find_elements(By.TAG_NAME, "a")
            page_words = 0
            
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.text.strip()
                    
                    if "/tr/" in href and not ".html" in href and text and len(text) > 1:
                        word = re.search(r'/tr/([^/?#]+)', href)
                        if word:
                            word_name = word.group(1)
                            if word_name not in ['Alfabetik', 'Arama'] and len(word_name) > 1:
                                if word_name not in words_set:
                                    words_set.add(word_name)
                                    page_words += 1
                except:
                    pass
            
            print(f"    [{letter}] Found {page_words} new words (Total: {len(words_set)})")
            
        except Exception as e:
            print(f"    [{letter}] Error: {str(e)[:50]}")
    
    print(f"\n[4] Total words found: {len(words_set)}\n")
    
    # Get header info for mapping
    print("[5] Creating mappings with video URLs...\n")
    
    word_mapping = {}
    
    for i, word in enumerate(sorted(words_set), 1):
        # For each word, visit its page and extract video ID
        try:
            url = f"https://tidsozluk.aile.gov.tr/tr/{word}"
            driver.get(url)
            time.sleep(0.8)
            
            # Look for video source URLs
            page_source = driver.page_source
            
            # Extract video ID from vidz_proc URLs
            # Pattern: /vidz_proc/0012/degiske/12-01_cr_0.1.mp4
            vid_match = re.search(r'/vidz_proc/(\d{4})/degiske/(\d{2}-\d{2})_', page_source)
            
            if vid_match:
                folder_id = vid_match.group(1)
                vid_id = vid_match.group(2)
                
                word_mapping[word] = {
                    "vid_id": vid_id,
                    "folder_id": folder_id,
                    "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                }
                
                if i % 10 == 0:
                    print(f"    [{i}/{len(words_set)}] {word}: {vid_id}")
            else:
                if i % 20 == 0:
                    print(f"    [{i}/{len(words_set)}] {word}: No video found")
                    
        except Exception as e:
            pass
    
    print(f"\n[6] Successfully mapped {len(word_mapping)} words\n")
    
    # Save to file
    with open("kelime_mapping.json", "w", encoding="utf-8") as f:
        json.dump(word_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] Saved {len(word_mapping)} words to kelime_mapping.json")
    print("\n[7] Next step: Run 'python main.py' to download all videos!\n")
    
finally:
    driver.quit()
    print("[OK] Done")
