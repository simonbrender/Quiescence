"""Test YC page structure to understand how to extract companies"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    p = await async_playwright().start()
    b = await p.chromium.launch(headless=True)
    page = await b.new_page()
    
    await page.goto('https://www.ycombinator.com/companies', wait_until='networkidle', timeout=30000)
    await page.wait_for_timeout(5000)  # Wait for React to render
    
    # Try to extract using JavaScript
    result = await page.evaluate('''() => {
        const links = Array.from(document.querySelectorAll("a[href*='/companies/']"));
        const companies = [];
        for (let link of links.slice(0, 10)) {
            const text = link.textContent.trim();
            const href = link.href;
            // Try to find website link nearby
            let domain = null;
            const card = link.closest('div, article, li');
            if (card) {
                const websiteLink = card.querySelector('a[href^="http"]:not([href*="ycombinator"]):not([href*="twitter"]):not([href*="linkedin"])');
                if (websiteLink) {
                    try {
                        const url = new URL(websiteLink.href);
                        domain = url.hostname.replace('www.', '');
                    } catch(e) {}
                }
            }
            companies.push({name: text, href: href, domain: domain});
        }
        return companies;
    }''')
    
    print("Sample companies from YC page:")
    for i, c in enumerate(result, 1):
        print(f"{i}. Name: {c['name'][:80]}...")
        print(f"   Domain: {c['domain']}")
        print(f"   Link: {c['href']}")
        print()
    
    await b.close()
    await p.stop()

asyncio.run(test())

