#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sayfanın HTML yapısını incelemek - hangi selectorlarda video ID'leri?
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Sayfaya gidiyor...")
        await page.goto("https://tidsozluk.aile.gov.tr/tr/Alfabetik/Arama/A", wait_until="networkidle")
        await asyncio.sleep(1)
        
        # HTML'yi kaydet inceleme için
        html = await page.content()
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✓ HTML kaydedildi: page_source.html")
        
        # Paginasyon öğelerini incelemek
        print("\n🔍 İnceleme:")
        
        # Video'ları arama
        print("\n1. 'degiske' içeren elementler:")
        degiske_count = len(await page.query_selector_all("[onclick*='degiske'], [href*='degiske'], [data-video*='degiske']"))
        print(f"   Bulundu: {degiske_count}")
        
        # Link'leri incelemek
        links = await page.query_selector_all("li a")
        print(f"\n2. LI → A bağlantılar: {len(links)}")
        
        if links:
            print("\n   İlk 5 link:")
            for i, link in enumerate(links[:5]):
                onclick = await link.get_attribute("onclick")
                href = await link.get_attribute("href")
                text = await link.text_content()
                print(f"   {i+1}. text='{text.strip()[:30]}' | onclick={bool(onclick)} | href={bool(href)}")
                if onclick:
                    print(f"      onclick={onclick[:60]}...")
        
        # Tüm LI'leri incelemek
        print(f"\n3. Toplam LI öğeleri: {len(await page.query_selector_all('li'))}")
        
        # Video kontrol ikonları (play button gibi)
        icons = await page.query_selector_all("button, .play, [class*='video']")
        print(f"   Video ikonları (buttons/videos): {len(icons)}")
        
        await browser.close()
        print("\n✓ Devam etmek için page_source.html'i inceleyebilirsiniz")

if __name__ == "__main__":
    asyncio.run(main())
