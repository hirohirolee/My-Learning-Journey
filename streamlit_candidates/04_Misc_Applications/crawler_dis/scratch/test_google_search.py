import streamlit as st
st.title('test_google_search.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://www.google.com/search?q=%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6+%E8%A9%95%E8%AB%96&hl=zh-TW"
    async with async_playwright() as p:
        st.write("Launching browser for Google Search...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--window-size=1920,1080", "--no-sandbox"]
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(4000)
        
        # Check if there is a review link or button in the knowledge graph / local block
        links = await page.locator("a, button, span, div").all()
        st.write("Checking elements...")
        rev_els = []
        for el in links:
            try:
                txt = await el.evaluate("node => node.innerText")
                if txt and ("則 Google 評論" in txt or "則評論" in txt or "評論" in txt):
                    if len(txt) < 30 and "撰寫" not in txt:
                        rev_els.append((await el.evaluate("node => node.tagName"), txt.replace("\n", " ")))
            except Exception:
                pass
        st.write("Review elements found on Google Search:", set(rev_els))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
