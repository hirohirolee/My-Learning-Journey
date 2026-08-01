import streamlit as st
st.title('inspect_lite.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--window-size=1920,1080', '--no-sandbox'])
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        info = await page.evaluate("""() => {
            const all = document.querySelectorAll('a, button, div');
            for (let e of all) {
                if (e.innerText && (e.innerText.includes('只顯示部分內容') || e.innerText.includes('充分運用') || e.innerText.includes('瞭解詳情'))) {
                    return {
                        tag: e.tagName,
                        html: e.outerHTML.substring(0, 500),
                        href: e.getAttribute('href'),
                        parentHtml: e.parentElement ? e.parentElement.outerHTML.substring(0, 500) : null
                    };
                }
            }
            return null;
        }""")
        st.write('Partial content element info:', info)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
