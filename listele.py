from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import re

def extract_vid_id(onclick_str):
    """
    Extracts vid_id from onclick attribute.
    Example: "vid('22-01')" -> "22-01"
    """
    if not onclick_str:
        return None
    
    match = re.search(r"vid\('([^']+)'\)", onclick_str)
    if match:
        return match.group(1)
    return None

def calculate_folder_id(vid_id):
    """
    Calculates folder_id from vid_id.
    Example: "22-01" -> "0022"
    """
    if not vid_id or '-' not in vid_id:
        return None
    
    folder_num = vid_id.split('-')[0]
    return folder_num.zfill(4)

def scroll_and_load_all_items(driver, wait_time=10):
    """
    Scrolls through the page to load all dynamic content.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    items_count = 0
    
    while True:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Calculate new height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    return last_height

# Initialize Chrome driver
options = webdriver.ChromeOptions()
# Uncomment for headless mode:
# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("🔄 Accessing https://tidsozluk.aile.gov.tr/tr/")
    # Changed to Turkish home page
    driver.get("https://tidsozluk.aile.gov.tr/tr/")
    
    # Wait for page body to load first
    wait = WebDriverWait(driver, 30)
    print("⏳ Waiting for page to load...")
    
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        print("⚠️  Body load timeout, continuing anyway...")
    
    # Give more time for JavaScript to execute
    time.sleep(5)
    
    # Reload elements after wait
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Try to find elements with onclick
    print("🔍 Searching for word elements...")
    try:
        items = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@onclick, 'vid')]")),
            timeout=30
        )
        print(f"✓ Found {len(items)} elements with onclick attribute")
    except:
        print("⚠️  Could not find onclick elements, trying alternative selectors...")
        items = driver.find_elements(By.XPATH, "//li | //a | //*[@onclick]")
        print(f"✓ Found {len(items)} alternative elements")
        
        # Debug: Show page source snippet and all onclick attributes
        print("\n🐛 DEBUG - Searching for any onclick attributes...")
        all_with_onclick = driver.find_elements(By.XPATH, "//*[@onclick]")
        if all_with_onclick:
            print(f"   Found {len(all_with_onclick)} elements with onclick")
            for i, elem in enumerate(all_with_onclick[:5]):
                try:
                    print(f"   [{i}] Text: {elem.text[:30] if elem.text else 'N/A'} | onclick: {elem.get_attribute('onclick')[:60]}")
                except:
                    pass
    # Debug: Get page source and check content
    page_source = driver.page_source
    
    # Save HTML for inspection
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(page_source)
    print("   💾 Page source saved as page_source.html")
        
    # Try different search methods
    print("\n📋 Trying alternative search methods...")
    
    # Method 1: Search by 'a' tags
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"   Found {len(links)} <a> tags")
    
    # Method 2: Search by divs
    divs = driver.find_elements(By.TAG_NAME, "div")
    print(f"   Found {len(divs)} <div> tags")
    
    # Method 3: Search by li
    lis = driver.find_elements(By.TAG_NAME, "li")
    print(f"   Found {len(lis)} <li> tags")
    
    # If we found items, show their structure
    if links:
        print("\n   Sample <a> tags:")
        for i, link in enumerate(links[:3]):
            try:
                onclick = link.get_attribute("onclick")
                href = link.get_attribute("href")
                classes = link.get_attribute("class")
                print(f"     [{i}] Text: '{link.text[:30]}' | onclick: {onclick} | href: {href} | class: {classes}")
            except:
                pass
    
    # Scroll to load all dynamic content
    print("📜 Scrolling to load all words...")
    scroll_and_load_all_items(driver)
    
    word_mapping = {}
    
    # Find all word items with onclick containing 'vid'
    print("🔍 Extracting words and IDs...")
    items = driver.find_elements(By.XPATH, "//*[contains(@onclick, 'vid')]")
    
    print(f"Found {len(items)} items")
    
    for idx, item in enumerate(items, 1):
        try:
            name = item.text.strip()
            onclick_attr = item.get_attribute("onclick")
            
            if name and onclick_attr:
                vid_id = extract_vid_id(onclick_attr)
                
                if vid_id:
                    folder_id = calculate_folder_id(vid_id)
                    
                    # Store both raw ID and folder_id for reference
                    word_mapping[name] = {
                        "vid_id": vid_id,
                        "folder_id": folder_id,
                        "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                    }
                    print(f"  [{idx}] ✓ {name:20} -> vid_id: {vid_id}, folder: {folder_id}")
        except Exception as e:
            print(f"  [{idx}] ✗ Error processing item: {str(e)}")
            continue
    
    print(f"\n✅ Total words extracted: {len(word_mapping)}")
    
    # Save to JSON
    output_file = "kelime_mapping.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(word_mapping, f, ensure_ascii=False, indent=4)
    
    print(f"💾 Saved to {output_file}")

except Exception as e:
    import traceback
    print(f"❌ Error: {str(e)}")
    print(f"Traceback: {traceback.format_exc()}")
    
finally:
    try:
        driver.quit()
    except:
        pass
    print("✔ Browser closed")