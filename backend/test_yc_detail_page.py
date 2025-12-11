"""Test YC company detail page to extract domain"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    p = await async_playwright().start()
    b = await p.chromium.launch(headless=True)
    page = await b.new_page()
    
    # Test with a known YC company
    await page.goto('https://www.ycombinator.com/companies/airbnb', wait_until='networkidle', timeout=30000)
    await page.wait_for_timeout(3000)
    
    # Try to extract company name and domain
    result = await page.evaluate('''() => {
        const nameElem = document.querySelector('h1, [class*="name"], [class*="title"]');
        const name = nameElem ? nameElem.textContent.trim() : null;
        
        // Look for website link
        const websiteLink = document.querySelector('a[href^="http"]:not([href*="ycombinator"]):not([href*="twitter"]):not([href*="linkedin"]):not([href*="facebook"])');
        let domain = null;
        if (websiteLink) {
            try {
                const url = new URL(websiteLink.href);
                domain = url.hostname.replace('www.', '');
            } catch(e) {}
        }
        
        return {name: name, domain: domain};
    }''')
    
    print(f"Company name: {result['name']}")
    print(f"Domain: {result['domain']}")
    
    await b.close()
    await p.stop()

asyncio.run(test())

