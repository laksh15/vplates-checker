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
from concurrent.futures import ThreadPoolExecutor
import threading
import os

app = Flask(__name__)

# Configuration
CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', '/usr/bin/chromedriver')
CHROME_BINARY_PATH = os.environ.get('CHROME_BINARY_PATH', '/usr/bin/chromium')
MAX_WORKERS = 4  # Adjust based on your Render plan

# Global driver instance with thread-local storage
_driver = None
_driver_lock = threading.Lock()

def get_driver():
    global _driver
    if _driver is None:
        with _driver_lock:
            if _driver is None:
                print(f"Initializing ChromeDriver with binary at: {CHROME_BINARY_PATH}")
                chrome_options = Options()
                chrome_options.binary_location = CHROME_BINARY_PATH
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument(
                    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                )
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option("useAutomationExtension", False)

                service = Service(executable_path=CHROME_DRIVER_PATH)
                try:
                    _driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("ChromeDriver initialized successfully")
                except Exception as e:
                    print(f"Failed to initialize ChromeDriver: {str(e)}")
                    raise
    return _driver

def close_driver():
    global _driver
    if _driver is not None:
        with _driver_lock:
            if _driver is not None:
                try:
                    _driver.quit()
                    print("ChromeDriver closed successfully")
                except Exception as e:
                    print(f"Error closing ChromeDriver: {str(e)}")
                finally:
                    _driver = None

def generate_combinations(start, end, total_length=6):
    start, end = start.upper(), end.upper()
    middle_len = total_length - len(start) - len(end)
    if middle_len < 0:
        return []
    chars = string.ascii_uppercase + string.digits
    if middle_len == 0:
        return [start + end]
    return [start + ''.join(c) + end for c in product(chars, repeat=middle_len)]

def check_single_plate(plate):
    ts = int(time.time())
    api_url = (
        "https://vplates.com.au/vplatesapi/checkcombo"
        f"?vehicleType=car&combination={plate}&_={ts}"
    )
    
    try:
        driver = get_driver()
        driver.get(api_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        raw = driver.find_element(By.TAG_NAME, 'body').text
        data = json.loads(raw)
        return data.get("status", "").lower() == "available"
    except Exception as e:
        print(f"Error checking plate {plate}: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_plates():
    start = request.form.get('start', '').strip()
    end = request.form.get('end', '').strip()
    
    if not start and not end:
        return jsonify(
            error="Please provide at least a start or end pattern.",
            checked=0,
            total=0,
            available=[]
        )
    
    plates = generate_combinations(start, end)
    total = len(plates)
    
    if total > 1000:
        return jsonify(
            error="Too many combinations to check (max 1000). Please refine your search.",
            checked=0,
            total=total,
            available=[]
        )
    
    print(f"Checking {total} combinations for start='{start}' end='{end}'")
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(check_single_plate, plates))
        
        available = [plate for plate, ok in zip(plates, results) if ok]
        checked = len(plates)
        
        return jsonify(
            checked=checked,
            total=total,
            available=available
        )
    except Exception as e:
        return jsonify(
            error=f"An error occurred: {str(e)}",
            checked=0,
            total=total,
            available=[]
        )

@app.teardown_appcontext
def teardown(exception=None):
    close_driver()

if __name__ == '__main__':
    app.run(debug=True)