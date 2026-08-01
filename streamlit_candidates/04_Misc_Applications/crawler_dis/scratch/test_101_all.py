import streamlit as st
st.title('test_101_all.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    u = 'https://www.google.com/maps/place/%E5%8f%B0%E5%8c%97101/'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(u)
        await page.wait_for_timeout(6000)
        
        els = await page.evaluate("""() => {
            const res = [];
            const tabs = document.querySelectorAll('button, div[role="tab"], a, [role="tab"]');
            for (let e of tabs) {
                if (e.innerText && e.innerText.trim().length > 0 && e.innerText.trim().length < 15) {
                    res.push(e.innerText.trim().replace(/\\n/g, ' '));
                }
            }
            return res;
        }""")
        st.write('Taipei 101 short buttons/tabs:', els)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
