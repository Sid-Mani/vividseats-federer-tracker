import os
import re
import time
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Configuration
MY_BUDGET = 250
MAX_DISPLAY_PRICE = 350
DISCORD_WEBHOOK_URL = "" # Add your webhook if you want alerts

VIVID_URL = "https://www.vividseats.com/us-open-roger-federer---an-icon-returns-to-ny-tickets-arthur-ashe-stadium-8-25-2026--sports-tennis/production/7134771?quantity=2"

verified_tickets = []

def parse_vivid_json(response):
    """Intercepts network traffic and targets the hidden production API data payload."""
    try:
        # We target their specific server data route
        if "production" in response.url and "vividseats.com" in response.url and response.status == 200:
            payload = response.json()
            
            # Navigate Vivid's native JSON dictionary path
            listings = payload.get("global_listings", []) or payload.get("listings", [])
            
            for item in listings:
                # Safely extract their native data keys
                section = str(item.get("section", ""))
                row = str(item.get("row", "")).upper()
                price = int(item.get("price", 0))
                
                # Check bounds (Arthur Ashe 100-400 upper bowl levels)
                if section.isdigit() and 100 <= int(section) <= 499:
                    if MY_BUDGET <= price <= MAX_DISPLAY_PRICE:
                        verified_tickets.append({
                            "section": section,
                            "row": row,
                            "price": price
                        })
    except Exception as e:
        pass # Ignore assets or non-JSON payloads tripping the interceptor

def fire_discord_report():
    if not verified_tickets:
        print("📊 [VividSeats] No listings found within the price boundaries.")
        return
        
    # Sort by price ascending
    verified_tickets.sort(key=lambda x: x['price'])
    
    report = "🔬 **VIVIDSEATS EXPERIMENTAL SANDBOX FEED** 🔬\n====================================\n"
    for t in verified_tickets[:30]: # Limit to top 30 rows to prevent spam
        report += f"• Sec {t['section']}, Row {t['row']} ➔ **${t['price']}**\n"
        
    print(report) # Print to GitHub logs
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": report})

def main():
    print("📡 Booting Live Packet Sniffer Matrix for VividSeats...")
    stealth = Stealth()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US"
        )
        
        stealth.apply_stealth_sync(context)
        page = context.new_page()
        
        # Attach our custom network packet sniffer to the page layout
        page.on("response", parse_vivid_json)
        
        try:
            # Open link and wait for all background API calls to clear complete
            page.goto(VIVID_URL, wait_until="networkidle", timeout=60000)
            time.sleep(15) # Give scripts extra breathing room to populate the data cards
        except Exception as e:
            print(f"⚠️ Page loading timeout occurred: {str(e)}")
            
        browser.close()
        
    fire_discord_report()
    print("🏁 Sandbox Evaluation Complete.")

if __name__ == "__main__":
    main()
