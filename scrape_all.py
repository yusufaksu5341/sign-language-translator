"""
Turkish Sign Language Dictionary - Complete Video Scraper
使用 Playwright 来渲染 JavaScript 并提取所有视频 ID
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_all_videos():
    """
    访问网站并为所有 Turkish 字母提取所有视频 ID 和单词
    """
    
    # Turkish alphabet
    letters = ['A', 'B', 'C', 'Ç', 'D', 'E', 'F', 'G', 'Ğ', 'H', 'I', 'İ', 'J', 'K', 
               'L', 'M', 'N', 'O', 'Ö', 'P', 'R', 'S', 'Ş', 'T', 'U', 'Ü', 'V', 'Y', 'Z']
    
    all_mappings = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            for idx, letter in enumerate(letters, 1):
                print(f"\n[{idx}/{len(letters)}] Scraping letter: {letter}")
                
                page = await browser.new_page()
                page.set_default_timeout(30000)
                
                try:
                    # Navigate to alphabetic page
                    url = f"https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/{letter}"
                    print(f"  → Opening: {url}")
                    
                    await page.goto(url, wait_until="networkidle")
                    await asyncio.sleep(2)  # Wait for JS to render
                    
                    # Get page content
                    content = await page.content()
                    
                    # Extract all video IDs and words from onclick attributes
                    # Pattern: onclick="vid('XX-YY')" or similar
                    video_pattern = r"onclick=['\"]vid\('(\d{2}-\d{2})'\)['\"]"
                    word_pattern = r"<[^>]*onclick=['\"]vid\('[^']*'\)['\"][^>]*>([^<]+)<"
                    
                    videos = re.findall(video_pattern, content)
                    
                    # Get elements with onclick and extract text
                    elements = await page.query_selector_all('[onclick*="vid"]')
                    
                    words_found = 0
                    for elem_idx, elem in enumerate(elements):
                        try:
                            # Get text content
                            text = await elem.text_content()
                            text = text.strip() if text else f"Word_{elem_idx}"
                            
                            # Get onclick attribute
                            onclick = await elem.get_attribute("onclick")
                            
                            # Extract video ID from onclick
                            match = re.search(r"vid\('(\d{2}-\d{2})'\)", onclick)
                            if match:
                                vid_id = match.group(1)
                                folder_id = vid_id.split('-')[0].zfill(4)
                                
                                all_mappings[text] = {
                                    "vid_id": vid_id,
                                    "folder_id": folder_id,
                                    "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                                }
                                words_found += 1
                        except Exception as e:
                            pass
                    
                    print(f"  ✓ Found {words_found} videos for letter '{letter}'")
                    
                except Exception as e:
                    print(f"  ✗ Error scraping {letter}: {str(e)[:50]}")
                
                finally:
                    await page.close()
                
                print(f"  Total: {len(all_mappings)} videos")
        
        finally:
            await browser.close()
    
    return all_mappings

async def main():
    print("=" * 70)
    print("🎯 Turkish Sign Language Video Scraper - Full Database")
    print("=" * 70)
    
    mappings = await scrape_all_videos()
    
    print(f"\n" + "=" * 70)
    print(f"📊 COMPLETE Database Created")
    print("=" * 70)
    print(f"Total unique words: {len(mappings)}")
    
    # Show sample
    if mappings:
        samples = list(mappings.items())[:3]
        print(f"\nSample entries:")
        for word, info in samples:
            print(f"  - {word}: {info['url']}")
    
    # Save to JSON
    output_file = "kelime_mapping.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to: {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
