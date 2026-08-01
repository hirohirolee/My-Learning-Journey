import streamlit as st

import asyncio
import sys
import time
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--window-size=1920,1080', '--no-sandbox'])
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW', user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        st.write("Navigating...")
        start_t = time.time()
        await page.goto(url)
        
        for i in range(20):
            await page.wait_for_timeout(1000)
            elapsed = int(time.time() - start_t)
            tabs = await page.locator("button, div[role='tab']").all()
            
            # Check if any tab has text '評論'
            rev_found = False
            for t in tabs:
                try:
                    txt = await t.evaluate("node => node.innerText")
                    if txt and "評論" in txt and "撰寫" not in txt:
                        rev_found = True
                        break
                except Exception:
                    pass
                    
            st.write(f"[{elapsed}s] Total tabs/buttons: {len(tabs)} | Review tab present?: {rev_found}")
            if rev_found:
                st.write("SUCCESS! Found review tab after", elapsed, "seconds!")
                break
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
