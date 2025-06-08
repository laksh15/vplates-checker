from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from itertools import product
import string

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

def is_plate_available_selenium(plate):
    ts = int(time.time())
    api_url = (
        "https://vplates.com.au/vplatesapi/checkcombo"
        f"?vehicleType=car&combination={plate}&_={ts}"
    )
    print(f"[Selenium] Navigating to API URL for {plate}")
    
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium"  # add if needed
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(api_url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
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
