import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188124,120.6739482,17z/data=!3m1!4b1!4m6!3m5!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!16s%2Fg%2F11gx_dwdfb'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(6000)
        
        html = await page.evaluate("""() => {
            const all = document.querySelectorAll('*');
            for (let e of all) {
                if (e.innerText && e.innerText.includes('充分運用')) {
                    return e.outerHTML;
                }
            }
            return null;
        }""")
        print('Banner HTML:', html[:1500] if html else 'None')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
