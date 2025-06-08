from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
from itertools import product
import string
from selenium.webdriver.chrome.service import Service


app = Flask(__name__)

def generate_combinations(start, end, total_length=6):
    start, end = start.upper(), end.upper()
    middle_len = total_length - len(start) - len(end)
    if middle_len < 0:
        return []
    chars = string.ascii_uppercase + string.digits
    if middle_len == 0:
        return [start + end]
    return [start + ''.join(c) + end for c in product(chars, repeat=middle_len)]

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time, json

def is_plate_available_selenium(plate):
    ts = int(time.time())
    api_url = (
        "https://vplates.com.au/vplatesapi/checkcombo"
        f"?vehicleType=car&combination={plate}&_={ts}"
    )
    print(f"[Selenium] Navigating to API URL for {plate}")
    
    # Setup Chrome options
    opts = Options()
    opts.binary_location = "/usr/bin/chromium"  # IMPORTANT for Render
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # Explicit path to chromedriver
  
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get(api_url)
        time.sleep(1)
        raw = driver.find_element(By.TAG_NAME, 'body').text
        print(f"[Selenium] Raw API response for {plate}:\n{raw}")
        data = json.loads(raw)
        return data.get("status", "").lower() == "available"
    except Exception as e:
        print(f"[Selenium] Error loading API JSON for {plate}: {e}")
        return False
    finally:
        driver.quit()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_plates():
    start = request.form.get('start', '').strip()
    end   = request.form.get('end',   '').strip()
    if not start and not end:
        return jsonify(error="Please provide at least a start or end pattern.",
                       checked=0, total=0, available=[])
    
    plates  = generate_combinations(start, end)
    total   = len(plates)
    checked = 0
    available = []

    print(f"Checking {total} combinations for start='{start}' end='{end}'")

    for plate in plates:
        checked += 1
        ok = is_plate_available_selenium(plate)
        print(f"→ {plate} is {'AVAILABLE' if ok else 'TAKEN'}")
        if ok:
            available.append(plate)
        time.sleep(0.2)

    resp = dict(checked=checked, total=total, available=available)
    print("Final response JSON:", json.dumps(resp, indent=2))
    return jsonify(resp)

if __name__ == '__main__':
    app.run(debug=True)

  #Update