import streamlit as st

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-TW',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(4000)
        
        # Test JS click
        res = await page.evaluate("""() => {
            const tabs = document.querySelectorAll('button, div[role="tab"], [role="tab"], a');
            let allTexts = [];
            for (let t of tabs) {
                if (t.innerText && t.innerText.trim()) {
                    allTexts.push(t.tagName + ' | ' + t.getAttribute('role') + ' | ' + t.innerText.trim());
                }
                if (t.innerText && !t.innerText.includes('撰寫') && !t.innerText.includes('Write') && (t.innerText.includes('評論') || t.innerText.includes('Reviews') || t.innerText.includes('則評論'))) {
                    t.click();
                    return 'Clicked JS tab: ' + t.innerText;
                }
            }
            return allTexts.join(' \\n ');
        }""")
        st.write(res)
        await page.wait_for_timeout(3000)
        st.write('jJc9Ad count after JS click:', len(await page.locator('.jJc9Ad').all()))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
