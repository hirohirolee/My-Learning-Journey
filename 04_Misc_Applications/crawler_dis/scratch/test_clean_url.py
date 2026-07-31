import asyncio
import sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    u = 'https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--window-size=1920,1080', '--no-sandbox'])
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-TW')
        page = await context.new_page()
        await page.goto(u)
        await page.wait_for_timeout(5000)
        
        els = await page.evaluate("""() => {
            const res = [];
            const tabs = document.querySelectorAll('button, div[role="tab"], a, [role="tab"]');
            for (let e of tabs) {
                if (e.innerText) {
                    res.push({tag: e.tagName, role: e.getAttribute('role'), text: e.innerText.replace(/\\n/g, ' ')});
                }
            }
            return res;
        }""")
        for item in els:
            if len(item['text']) < 25:
                print(item)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
