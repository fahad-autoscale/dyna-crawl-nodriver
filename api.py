from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import nodriver as uc
import asyncio
import socket
import re
from urllib.parse import urlsplit
import random
import tempfile
import os

app = FastAPI()


PROXIES = [
    'http://p103.dynaprox.com:8899',
    'http://p103.dynaprox.com:8900',
    'http://p103.dynaprox.com:8901',
    'http://p103.dynaprox.com:8902',
]

class UrlRequest(BaseModel):
    url: str

@app.post("/fetch-details")
async def fetch_details(req: UrlRequest):
    url = req.url
    proxy = random.choice(PROXIES)
    username = "3"
    password = "fahad123"

    browser = None
    browser_args = [
        "--no-sandbox", 
        "--disable-dev-shm-usage",
        "--ignore-certificate-errors", 
        "--ignore-ssl-errors", 
        "--disable-gpu", 
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", 
        f"--proxy-server={proxy}"
    ]
    try:
        browser = await uc.start(
            headless=True,
            # user_data_dir="/root/.config/google-chrome", 
            # user_data_dir="/home/dyna-crawl-nodriver/profiles/1", 
            # browser_executable_path="/usr/bin/google-chrome-stable", 
            no_sandbox=True,
            browser_args=browser_args,
            lang="en-US"
        )

        final_url = ''
        http_protocol = ''
        http_status = ''
        content_type = ''
        is_indexable = ''
        page_title = ''
        is_offline = ''
        is_online = ''
        is_blocked = ''
        ip_address = ''
        is_offline = ''
        is_blocked = ''
        is_parked = ''
        classification = ''
        
        page = await browser.get(url)
        await page.sleep(3)
        html_content = await page.get_content()
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            screenshot_path = tmp.name
        await page.save_screenshot(filename=screenshot_path)
        print(f"Screenshot saved temporarily at: {screenshot_path}")
        
        text = html_content.lower()
        await page.sleep(1)
        page_title = await page.evaluate("document.title", await_promise=True, return_by_value=True)
        await page.sleep(1)
        final_url = await page.evaluate("window.location.href", await_promise=True, return_by_value=True)
        
        is_indexable = not re.search(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', html_content, re.I)

        parked_phrases = ["domain is for sale", "is parked", "parking page", "this domain is for sale",
                            "buy this domain", "is under construction", "coming soon", "future home of", "this website is currently unavailable", "it looks like you're a little early"]
        is_parked = any(p in text for p in parked_phrases)
        await page.sleep(1)

        block_indicators = [
            'data-dd-captcha-container',
            'data-dd-captcha-passed="false"',
            'data-dd-captcha-human-title',
            'captcha__contact_support_request_id',
            'slide right to complete the puzzle',
            'We detected unusual activity from your device or network.',
            'Automated (bot, activity on your network',
            'please verify you are human',
            'verify you are human',
            'g-recaptcha',
            'captcha__human__title',
            'captcha__robot__warning',
            'captcha__contact_form',
            'cf-challenge',
            'cf-ray'
        ]
        is_blocked = any(b in text for b in block_indicators)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            screenshot_path = tmp.name
        await page.save_screenshot(filename=screenshot_path)
        print(f"Screenshot saved temporarily at: {screenshot_path}")

        is_offline = None
        is_online = True if is_blocked else None
        # http_status = main_response_info.get("status", 0)
        # http_protocol = main_response_info.get("protocol", "")
        # content_type = main_response_info.get("content_type", "")
        # if http_status == 0:
        #     is_offline = True
        #     is_online = False

        classification = "Non-Dealer"
        car_brands = [
            "ford", "chevrolet", "gmc", "dodge", "ram", "cadillac", "lincoln", "tesla", "buick", "chrysler", "hummer",
            "jeep", "pontiac", "saturn", "oldsmobile",
            "audi", "bmw", "mercedes", "volkswagen", "porsche", "opel", "maybach",
            "toyota", "honda", "nissan", "mazda", "subaru", "mitsubishi", "suzuki", "lexus", "acura", "infiniti",
            "daihatsu", "isuzu",
            "hyundai", "kia", "genesis", "ssangyong",
            "land rover", "jaguar", "aston martin", "rolls-royce", "bentley", "mini", "lotus", "vauxhall",
            "mclaren",
            "ferrari", "lamborghini", "maserati", "fiat", "alfa romeo", "lancia", "pagani",
            "peugeot", "citroën", "renault", "bugatti",
            "volvo", "polestar", "saab", "koenigsegg",
            "byd", "geely", "nio", "chery", "great wall", "haval", "lynk & co", "roewe", "wuling", "hongqi",
            "aiways", "leapmotor",
            "tata", "mahindra", "maruti suzuki", "force motors",
            "dacia",
            "vinfast",
            "proton", "perodua"
        ]
        listing_terms = ["view new vehicles", "view all new vehicles", "view used vehicles", "view all used vehicles", "car inventory", "car sale", "pre-owned", "used car", "new car", "schedule test drive", "Find your next car", "Cars for sale", "Featured Vehicles", "auto sales", "SUV", "SUVs", "pickup trucks", "Sedan", "Car Dealer in", "Used Cars for sale", "Used Trucks and SUVs"]
        x=[]
        y=[]
        for b in car_brands:
            if b in text:
                x.append(b)
            if b in page_title:
                x.append(b)
        for term in listing_terms:
            if term in text:
                y.append(term)
            if term in page_title:
                y.append(term)
            
        print(x)
        print(y)
        has_brand = any(b in text for b in car_brands) or any(b in page_title for b in car_brands)
        print(f"Has Brand: {has_brand}")
        has_vin = "vin" in text
        print(f"Has VIN: {has_vin}")
        has_stock = "stock#" in text or "stock number" in text or "stockno" in text
        print(f"Has Stock: {has_stock}")
        has_listing_terms = any(term in text for term in listing_terms) or any(term in page_title for term in listing_terms)
        print(f"Has Listing Terms: {has_listing_terms}")
        if (has_vin and has_stock) or (has_brand and has_listing_terms):
            classification = "Dealer"
            is_online = True
        if (is_parked or is_offline) and not is_blocked:
            classification = "Offline"
        await page.close()

        ip_address = ""
        try:
            ip_address = socket.gethostbyname(urlsplit(url).hostname)
        except Exception:
            pass

        result = {
            "url": url,
            "finalUrl": final_url,
            "httpVersion": http_protocol,
            "httpStatusCode": http_status,
            "contentType": content_type,
            "isUrlIndexable": is_indexable,
            "pageTitle": page_title or "",
            "isOffline": is_offline,
            "isOnline": is_online,
            "isBlocked": is_blocked,
            "getIp": ip_address,
            "message": "Page is offline or unreachable" if is_offline else (
                "Blocked by CAPTCHA or other protection" if is_blocked else (
                    "Parked or placeholder page detected" if is_parked else "OK"
                )
            ),
            "classification": classification
        }
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if browser:
            try:
                await browser.stop()
            except:
                pass
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=False)
