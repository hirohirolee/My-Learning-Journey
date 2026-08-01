import streamlit as st

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb'
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--window-size=1920,1080',
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-TW',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-TW', 'zh', 'en-US', 'en']});
            window.chrome = { runtime: {} };
        """)
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        tabs = await page.locator("button, div[role='tab']").all()
        st.write('Total tabs with stealth:', len(tabs))
        for t in tabs:
            txt = await t.evaluate("node => node.innerText")
            if txt and ('評論' in txt or 'Reviews' in txt) and '撰寫' not in txt:
                st.write('Found review tab:', txt.replace('\n', ' '))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
