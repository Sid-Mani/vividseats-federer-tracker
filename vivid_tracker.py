import os
import re
import time
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Configuration
MY_BUDGET = 250
MAX_DISPLAY_PRICE = 350
DISCORD_WEBHOOK_URL = "" 

VIVID_URL = "https://www.vividseats.com/us-open-roger-federer---an-icon-returns-to-ny-tickets-arthur-ashe-stadium-8-25-2026--sports-tennis/production/7134771?quantity=2"

verified_tickets = []

def parse_any_json(response):
    """Deep searches EVERY background network packet for valid seat structures."""
    try:
        # Check if the packet is actual JSON data
        if "json" in response.headers.get("content-type", "").lower() and response.status == 200:
            payload = response.json()
            
            # Stringify everything to look for lists of data
            payload_str = str(payload)
            
            # If the response contains pricing data, hunt for listings inside it
            if "price" in payload_str and ("section" in payload_str or "sec" in payload_str):
                
                # Recursively dig through the JSON objects to find list blocks
                find_listings_deep(payload)
                
    except Exception:
        pass

def find_listings_deep(obj):
    """Recursively walks any JSON structure looking for dictionaries that resemble ticket items."""
    if isinstance(obj, dict):
        # Does this specific dictionary look like a ticket?
        if "price" in obj and ("section" in obj or "row" in obj):
            try:
                # Extract values flexibly, checking for variations in keys
                price_val = obj.get("price") or obj.get("currentPrice") or obj.get("value")
                section_val = obj.get("section") or obj.get("sectionName") or obj.get("sec")
                row_val = obj.get("row") or obj.get("rowName") or ""
                
                if price_val and section_val:
                    # Strip any currency symbols or commas, cast to integer
                    price = int(float(re.sub(r'[^\d.]', '', str(price_val))))
                    section = str(section_val).strip()
                    row = str(row_val).strip().upper()
                    
                    # Target upper bowl bounds (100-400 sections)
                    if section.isdigit() and 100 <= int(section) <= 499:
                        if price <= MAX_DISPLAY_PRICE:
                            ticket_id = f"{section}-{row}-{price}"
                            # Prevent duplicates from firing multiple times
                            if ticket_id not in [f"{t['section']}-{t['row']}-{t['price']}" for t in verified_tickets]:
                                verified_tickets.append({
                                    "section": section,
                                    "row": row,
                                    "price": price
                              })
            except:
                pass
        else:
            for key, value in obj.items():
                find_listings_deep(value)
                
    elif isinstance(obj, list):
        for item in obj:
            find_listings_deep(item)

def fire_discord_report():
    print(f"\n📊 [VividSeats Scan Summary] Total unique listings caught: {len(verified_tickets)}")
    if not verified_tickets:
        print("❌ Net caught data packets, but zero fit within your specific criteria rules.")
        return
        
    # Sort by price ascending
    verified_tickets.sort(key=lambda x: x['price'])
    
    report = "🔬 **VIVIDSEATS DEEP PACKET SUMMARY** 🔬\n====================================\n"
    for t in verified_tickets[:30]: 
        report += f"• Sec {t['section']}, Row {t['row']} ➔ **${t['price']}**\n"
        
    print(report) # Print to GitHub Actions log terminal
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": report})

def main():
    print("📡 Launching Deep Network-Packet Sniffer Matrix...")
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
        
        # Attach the universal JSON detector
        page.on("response", parse_any_json)
        
        try:
            # Let it load fully
            page.goto(VIVID_URL, wait_until="load", timeout=60000)
            print("⏳ Page hit. Standing by for background web traffic assets...")
            time.sleep(20) # Give the page extra time to query the inventory backend
        except Exception as e:
            print(f"⚠️ Page navigation break: {str(e)}")
            
        browser.close()
        
    fire_discord_report()

if __name__ == "__main__":
    main()
