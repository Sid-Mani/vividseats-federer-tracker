import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

url = "https://www.vividseats.com/us-open-roger-federer---an-icon-returns-to-ny-tickets-arthur-ashe-stadium-8-25-2026--sports-tennis/production/7134771"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
    Stealth().apply_stealth_sync(context)
    page = context.new_page()
    
    page.goto(url, wait_until="load")
    
    # Locate the server-side hydration script tag
    element = page.locator("script#__NEXT_DATA__")
    raw_json_text = element.inner_html()
    
    # Unpack the entire state matrix as a Python dictionary
    data_matrix = json.loads(raw_json_text)
    
    # Drill down into their structure to capture listings
    # Note: Exact JSON key nesting paths fluctuate based on app builds
    props = data_matrix.get("props", {}).get("pageProps", {})
    listings = props.get("initialListings", []) or props.get("listings", [])
    
    print(f"Captured {len(listings)} clean inventory listings straight from the hydration source!")
    browser.close()
