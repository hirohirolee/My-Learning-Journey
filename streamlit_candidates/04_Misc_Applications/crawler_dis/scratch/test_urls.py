import streamlit as st

import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

urls = [
    'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb',
    'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/',
    'https://www.google.com/maps/search/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/',
    'https://www.google.com/maps/place/?q=place_id:ChIJsezdaQo9aTQRyRhx-bsuJyY'
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--window-size=1920,1080', '--no-sandbox']
        )
        for idx, u in enumerate(urls):
            st.write(f'=== Testing URL {idx + 1}: {u} ===')
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
            page = await context.new_page()
            try:
                await page.goto(u, timeout=15000)
                await page.wait_for_timeout(4000)
                txt = await page.evaluate('document.body.innerText')
                st.write('Partial content warning present?', '只顯示部分內容' in txt)
                tabs = await page.locator("button, div[role='tab']").all()
                review_tabs = []
                for t in tabs:
                    t_txt = await t.evaluate('node => node.innerText')
                    if t_txt and ('評論' in t_txt or 'Reviews' in t_txt) and '撰寫' not in t_txt and 'Write' not in t_txt:
                        review_tabs.append(t_txt.replace('\n', ' '))
                st.write(f'Found {len(tabs)} tabs. Review tabs:', review_tabs)
            except Exception as e:
                st.write('Error:', e)
            await context.close()
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
