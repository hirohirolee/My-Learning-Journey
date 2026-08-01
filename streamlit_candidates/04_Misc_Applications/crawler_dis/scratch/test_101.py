import streamlit as st
st.title('test_101.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    u = 'https://www.google.com/maps/place/%E5%8f%B0%E5%8c%97101/'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW', user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = await context.new_page()
        await page.goto(u)
        await page.wait_for_timeout(5000)
        
        els = await page.evaluate("""() => {
            const res = [];
            const tabs = document.querySelectorAll('button, div[role="tab"], a, [role="tab"]');
            for (let e of tabs) {
                if (e.innerText && (e.innerText.includes('評論') || e.innerText.includes('Reviews') || e.innerText.includes('總覽') || e.innerText.includes('簡介'))) {
                    res.push({tag: e.tagName, role: e.getAttribute('role'), text: e.innerText.replace(/\\n/g, ' ')});
                }
            }
            return res;
        }""")
        for item in els:
            st.write(item)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
