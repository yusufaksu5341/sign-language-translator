from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("[*] Loading page...")
    driver.get("https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/A")
    time.sleep(6)
    
    print("[*] Checking for global data objects...")
    
    # Check for common data containers
    data_sources = [
        "window.data",
        "window.words",
        "window.kelimeler",
        "window.__data",
        "window.__INITIAL_STATE__",
        "window.__INITIAL_DATA__",
        "document.body.dataset",
        "window.React"
    ]
    
    for source in data_sources:
        try:
            result = driver.execute_script(f"return typeof {source}")
            if result != "undefined":
                print(f"  [FOUND] {source}: {result}")
        except:
            pass
    
    print("\n[*] Trying to extract any visible links...")
    # Get all clickable elements
    all_elements = driver.find_elements(By.CSS_SELECTOR, "span, div, a, li, p")
    
    print(f"[*] Total elements: {len(all_elements)}")
    
    # Get text contents
    texts = []
    for el in all_elements[:200]:
        try:
            text = el.text.strip()
            if text and 2 < len(text) < 50:
                # Check if element is clickable or has data attribute
                onclick = el.get_attribute("onclick")
                classes = el.get_attribute("class")
                data_attrs = el.get_attribute("data-*")
                if onclick or "click" in classes or data_attrs:
                    texts.append((text, onclick, classes))
        except:
            pass
    
    print(f"\n[*] Potentially interactive elements: {len(texts)}")
    if texts:
        print("\nSample:")
        for text, onclick, classes in texts[:15]:
            print(f"  Text: {text[:30]:30} | onclick: {str(onclick)[:40]:40} | class: {str(classes)[:40]}")
    
    # Try navigating to a specific word
    print("\n[*] Testing direct word URL...")
    driver.get("https://tidsozluk.aile.gov.tr/tr/Anne")
    time.sleep(3)
    
    # Save and analyze
    source = driver.page_source
    with open("word_page.html", "w", encoding="utf-8") as f:
        f.write(source)
    
    import re
    # Extract video URL from source
    vid_urls = re.findall(r'/vidz_proc/(\d+)/degiske/([^_]+)_cr_', source)
    if vid_urls:
        print(f"\n[SUCCESS] Found video URLs in word page!")
        print(f"Sample: /vidz_proc/{vid_urls[0][0]}/degiske/{vid_urls[0][1]}_cr_0.1.mp4")
    
    # Extract text that looks like word names
    word_texts = re.findall(r'>([A-Z][a-zçğıöşüÇĞİÖŞÜ]+)<', source)
    print(f"\nFound word in page: {word_texts[:10]}")
            
finally:
    driver.quit()
    print("\n[OK] Done")
