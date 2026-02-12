"""
Complete Turkish Sign Language Database Scraper
Finds ALL video IDs and maps them to words
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_all_videos_complete():
    """
    Visit all 29 Turkish letter pages, extract ALL video IDs and word names
    """
    
    letters = ['A', 'B', 'C', 'Ç', 'D', 'E', 'F', 'G', 'Ğ', 'H', 'I', 'İ', 'J', 'K', 
               'L', 'M', 'N', 'O', 'Ö', 'P', 'R', 'S', 'Ş', 'T', 'U', 'Ü', 'V', 'Y', 'Z']
    
    all_mappings = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
        
        try:
            for idx, letter in enumerate(letters, 1):
                print(f"\n[{idx}/29] Harfi: {letter}")
                
                page = await browser.new_page()
                page.set_default_timeout(30000)
                
                try:
                    url = f"https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/{letter}"
                    print(f"  → {url}")
                    
                    await page.goto(url, wait_until="networkidle")
                    await asyncio.sleep(1)
                    
                    # Get HTML
                    html = await page.content()
                    
                    # Extract ALL video IDs from HTML - pattern: /degiske/XX-YY_cr
                    video_ids = re.findall(r'/degiske/(\d{2}-\d{2})_cr', html)
                    video_ids = sorted(list(set(video_ids)))  # Unique + sorted
                    
                    # Extract word names from LI elements (actual words, not nav items)
                    # Get all LI text content
                    li_elements = await page.query_selector_all("li")
                    
                    words = []
                    for li in li_elements:
                        try:
                            text = await li.text_content()
                            text = text.strip() if text else ""
                            # Filter: real words are usually 2-50 chars, no numbers-only
                            if text and 2 < len(text) < 50:
                                words.append(text)
                        except:
                            pass
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    words_unique = []
                    for w in words:
                        if w not in seen:
                            seen.add(w)
                            words_unique.append(w)
                    
                    print(f"  ✓ Video IDs found: {len(video_ids)}")
                    print(f"  ✓ Words found: {len(words_unique)}")
                    
                    # Map: if more videos than words, use video IDs as identifiers
                    # if more words than videos, only map available videos
                    for i, vid_id in enumerate(video_ids):
                        folder_id = vid_id.split('-')[0].zfill(4)
                        
                        # Use word name if available, otherwise use video ID  
                        if i < len(words_unique):
                            word_key = words_unique[i]
                        else:
                            word_key = f"{letter}_{vid_id}"
                        
                        # Ensure unique key
                        if word_key in all_mappings:
                            word_key = f"{word_key}_{vid_id}"
                        
                        all_mappings[word_key] = {
                            "vid_id": vid_id,
                            "folder_id": folder_id,
                            "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
                        }
                    
                    print(f"  ◆ Mapped: {len(video_ids)} videos")
                    
                except Exception as e:
                    print(f"  ✗ Error: {str(e)[:60]}")
                
                finally:
                    await page.close()
        
        finally:
            await browser.close()
    
    return all_mappings

async def main():
    print("=" * 70)
    print("🎯 Turkish Sign Language - COMPLETE Database Scraper")
    print("=" * 70)
    
    mappings = await scrape_all_videos_complete()
    
    print(f"\n" + "=" * 70)
    print(f"✓ SCRAPING COMPLETE")
    print("=" * 70)
    print(f"Total videos found: {len(mappings)}")
    
    # Show samples
    if mappings:
        samples = list(mappings.items())[:5]
        print(f"\nSample entries:")
        for word, info in samples:
            print(f"  • {word[:40]:40} → {info['vid_id']}")
    
    # Save
    output_file = "kelime_mapping.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved {len(mappings)} entries to: {output_file}")
    print("=" * 70)
    
    return mappings

if __name__ == "__main__":
    asyncio.run(main())
