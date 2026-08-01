import streamlit as st
st.title('test_msedge.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb'
    async with async_playwright() as p:
        st.write('=== Testing msedge with headless=False ===')
        browser = await p.chromium.launch(
            channel='msedge',
            headless=False,
            args=['--window-size=1920,1080']
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(8000)
        
        txt = await page.evaluate('document.body.innerText')
        st.write('Partial content warning?', '只顯示部分內容' in txt)
        st.write('Contains 中興奶茶 in body?', '中興奶茶' in txt)
        tabs = await page.locator("button, div[role='tab']").all()
        st.write('Total tabs:', len(tabs))
        for t in tabs:
            t_txt = await t.evaluate("node => node.innerText")
            if t_txt and ('評論' in t_txt or 'Reviews' in t_txt) and '撰寫' not in t_txt:
                st.write('Found review tab:', t_txt.replace('\n', ' '))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
