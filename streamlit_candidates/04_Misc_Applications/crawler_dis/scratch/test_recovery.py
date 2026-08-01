import streamlit as st

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"
    async with async_playwright() as p:
        st.write("Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080",
            ]
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(6000)
        
        txt = await page.evaluate("document.body.innerText")
        st.write("Partial content warning?:", "只顯示部分內容" in txt)
        tabs = await page.locator("button, div[role='tab']").all()
        st.write("Total buttons/tabs:", len(tabs))
        for t in tabs:
            try:
                t_txt = await t.evaluate("node => node.innerText")
                if t_txt and ("評論" in t_txt or "Reviews" in t_txt) and "撰寫" not in t_txt:
                    st.write("FOUND REVIEW TAB:", t_txt.replace("\n", " "))
            except Exception:
                pass
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
