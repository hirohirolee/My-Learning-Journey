import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D'
    Path('scratch/user_data').mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        for attempt in range(1, 4):
            print(f'=== Persistent Context Attempt {attempt} ===')
            context = await p.chromium.launch_persistent_context(
                user_data_dir='scratch/user_data',
                headless=True,
                viewport={'width': 1920, 'height': 1080},
                locale='zh-TW',
                args=['--window-size=1920,1080', '--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            page = await context.new_page()
            await page.goto(url)
            await page.wait_for_timeout(5000)
            
            txt = await page.evaluate('document.body.innerText')
            print('Partial content warning present?', '只顯示部分內容' in txt)
            tabs = await page.locator("button, div[role='tab']").all()
            review_tabs = []
            for t in tabs:
                t_txt = await t.evaluate('node => node.innerText')
                if t_txt and ('評論' in t_txt or 'Reviews' in t_txt) and '撰寫' not in t_txt and 'Write' not in t_txt:
                    review_tabs.append(t_txt.replace('\n', ' '))
            print(f'Found {len(tabs)} tabs. Review tabs:', review_tabs)
            await context.close()

if __name__ == '__main__':
    asyncio.run(main())
