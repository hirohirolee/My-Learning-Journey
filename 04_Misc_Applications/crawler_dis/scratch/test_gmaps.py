import asyncio
import sys
import csv
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188173,120.6713679,17z/data=!4m8!3m7!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!9m1!1b1!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080",
            ]
        )
        tmp_context = await browser.new_context()
        tmp_page = await tmp_context.new_page()
        ua = await tmp_page.evaluate("navigator.userAgent")
        await tmp_context.close()
        real_ua = ua.replace("HeadlessChrome", "Chrome").replace("Headless", "")
        print("Using UA:", real_ua)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-TW',
            user_agent=real_ua
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Navigating to URL...")
        await page.goto(url)
        
        print("Waiting for review tab to render...")
        try:
            review_tab = page.locator("button, div[role='tab']").filter(has_text="評論").filter(has_not_text="撰寫").first
            await review_tab.wait_for(timeout=15000)
            print("Found review tab! Clicking...")
            await review_tab.click()
            clicked = True
        except Exception as e:
            print(f"Could not find review tab within 15s: {e}")
            clicked = False
            
        await page.wait_for_timeout(3000)
        await page.screenshot(path="scratch/step2_after_click.png")
        print("Saved step2_after_click.png")
        
        # Scroll logic
        print("Scrolling...")
        for i in range(5):
            await page.evaluate("""
                let c = document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf') || document.querySelector('.m6QErb');
                if (c) c.scrollTop = c.scrollHeight;
            """)
            await page.wait_for_timeout(1000)
            
        await page.screenshot(path="scratch/step3_after_scroll.png")
        print("Saved step3_after_scroll.png")
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        with open("scratch/page_text.txt", "w", encoding="utf-8") as f:
            f.write(soup.get_text(separator="\n"))
        print("Saved page_text.txt")
        
        review_blocks = soup.find_all("div", class_="jJc9Ad")
        print(f"Found {len(review_blocks)} reviews.")
        
        comments = []
        for idx, block in enumerate(review_blocks):
            author_tag = block.find("div", class_="d4r55")
            author = author_tag.text.strip() if author_tag else f"User_{idx}"
            
            content_tag = block.find("span", class_="wiI7pd")
            content = content_tag.text.strip() if content_tag else ""
            
            if content:
                comments.append({"author": author, "content": content})
                
        output_file = "scratch/google_reviews_test.csv"
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["author", "content"])
            writer.writeheader()
            for c in comments:
                writer.writerow(c)
                
        print(f"Saved {len(comments)} comments to {output_file}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
