"""
Extract video IDs and words from page HTML using regex and element content
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_all_videos_v2():
    """
    Using regex and LI elements to extract video IDs and word names
    """
    
    letters = ['A', 'B', 'C', 'Ç', 'D', 'E', 'F', 'G', 'Ğ', 'H', 'I', 'İ', 'J', 'K', 
               'L', 'M', 'N', 'O', 'Ö', 'P', 'R', 'S', 'Ş', 'T', 'U', 'Ü', 'V', 'Y', 'Z']
    
    all_mappings = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
        
        try:
            for idx, letter in enumerate(letters, 1):
                print(f"\n[{idx}/{len(letters)}] Harfi: {letter}")
                
                page = await browser.new_page()
                page.set_default_timeout(30000)
                
                try:
                    url = f"https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/{letter}"
                    print(f"  ► {url}")
                    
                    await page.goto(url, wait_until="networkidle")
                    await asyncio.sleep(2)
                    
                    # Get page HTML
                    html = await page.content()
                    
                    # Extract all video ID patterns: XX-YY
                    video_ids = re.findall(r'/vidz_proc/\d{4}/degiske/(\d{2}-\d{2})_cr', html)
                    video_ids = list(set(video_ids))  # Remove duplicates
                    
                    print(f"  → Found {len(video_ids)} videos in HTML")
                    
                    # Get all LI elements (usually word names)
                    li_elements = await page.query_selector_all("li")
                    
                    words = []
                    for li in li_elements:
                        try:
                            text = await li.text_content()
                            text = text.strip() if text else ""
                            if len(text) > 0 and len(text) < 50:  # Filter out garbage
                                words.append(text)
                        except:
                            pass
                    
                    print(f"  → Found {len(words)} words in LI elements")
                    
                    # Try to match videos with words - simple 1:1 mapping by order
                    matched_count = 0
                    for i in range(min(len(video_ids), len(words))):
                        vid_id = video_ids[i]
                        word = words[i]
                        
                        folder_id = vid_id.split('-')[0].zfill(4)
                        
                        all_mappings[word] = {
                            "vid_id": vid_id,
                            "folder_id": folder_id,
                            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                        }
                        matched_count += 1
                    
                    print(f"  ✓ Mapped {matched_count} words to videos")
                    print(f"  ◆ Total collected: {len(all_mappings)}")
                    
                except Exception as e:
                    print(f"  ✗ Error: {str(e)[:60]}")
                
                finally:
                    await page.close()
        
        finally:
            await browser.close()
    
    return all_mappings

async def main():
    print("=" * 70)
    print("🎯 Turkish Sign Language - Complete Video Database Scraper V2")
    print("=" * 70)
    
    mappings = await scrape_all_videos_v2()
    
    print(f"\n" + "=" * 70)
    print(f"✓ DATABASE COMPLETE")
    print("=" * 70)
    print(f"Total unique words: {len(mappings)}")
    
    # Show samples
    if mappings:
        samples = list(mappings.items())[:3]
        print(f"\nSample entries:")
        for word, info in samples:
            print(f"  • {word:20} → {info['vid_id']}")
    
    # Save
    output_file = "kelime_mapping.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to: {output_file}")
    print("=" * 70)
    
    return mappings

if __name__ == "__main__":
    asyncio.run(main())
