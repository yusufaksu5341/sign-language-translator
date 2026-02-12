"""
Check what the actual page structure looks like
"""
import asyncio
from playwright.async_api import async_playwright
import re

async def check_page_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Go to A letter page
        await page.goto("https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/A", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Get all elements with specific attributes
        print("=" * 70)
        print("Checking for onclick elements...")
        print("=" * 70)
        
        # Try different selectors
        selectors = [
            "[onclick]",
            "[onclick*='vid']",
            "button[onclick]",
            "a[onclick]",
            "div[onclick]",
            ".word",
            ".words",
            "li",
            "span"
        ]
        
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                print(f"[{selector:25}] {count:4} elements")
                
                if count > 0 and count < 20:
                    elements = await page.query_selector_all(selector)
                    for i, elem in enumerate(elements[:3]):
                        text = await elem.text_content()
                        html = await elem.get_attribute("onclick")
                        print(f"  [{i}] Text: {text[:40]}, onclick: {html[:60] if html else 'None'}")
            except:
                pass
        
        # Get full HTML first 10000 chars to see structure
        print("\n" + "=" * 70)
        print("First 3000 characters of page HTML:")
        print("=" * 70)
        
        html = await page.content()
        # Find video references
        videos = re.findall(r'(\d{2}-\d{2})', html)
        print(f"Found {len(set(videos))} unique video ID patterns: {set(videos)}")
        
        # Look for onclick patterns
        onclicks = re.findall(r"onclick=['\"]([^'\"]+)['\"]", html)
        print(f"\nFound {len(onclicks)} onclick attributes:")
        for onclick in onclicks[:5]:
            print(f"  - {onclick[:70]}")
        
        # Check if network requests capture videos
        print("\n" + "=" * 70)
        print("Monitoring network requests for MP4 files...")
        print("=" * 70)
        
        # Listen for network events
        async def handle_response(response):
            if '.mp4' in response.url.lower():
                print(f"[MP4] {response.status} {response.url}")
        
        page.on("response", handle_response)
        
        # Click first few items to trigger network requests
        await page.click("[onclick]", timeout=5000).catch(lambda: None)
        await asyncio.sleep(2)
        
        await browser.close()

asyncio.run(check_page_structure())
