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
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration - these paths work on Render's Ubuntu environment
CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver')
CHROME_BINARY_PATH = os.environ.get('CHROME_BINARY_PATH', '/usr/bin/google-chrome')

def verify_chrome_installation():
    """Verify Chrome/Chromium and ChromeDriver are properly installed"""
    try:
        # Check Chrome/Chromium
        chrome_version = subprocess.check_output([CHROME_BINARY_PATH, '--version'], stderr=subprocess.STDOUT)
        logger.info(f"Chrome version: {chrome_version.decode().strip()}")
        
        # Check ChromeDriver
        driver_version = subprocess.check_output([CHROME_DRIVER_PATH, '--version'], stderr=subprocess.STDOUT)
        logger.info(f"ChromeDriver version: {driver_version.decode().strip()}")
        
        return True
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False

def create_driver():
    """Create and configure a Chrome WebDriver instance"""
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
    return webdriver.Chrome(service=service, options=chrome_options)

# Verify installations when starting up
if not verify_chrome_installation():
    logger.error("Chrome/Chromium or ChromeDriver not properly installed!")
    # Continue anyway - Render's health check will fail if this is critical

def generate_combinations(start, end, total_length=6):
    start, end = start.upper(), end.upper()
    middle_len = total_length - len(start) - len(end)
    if middle_len < 0:
        return []
    chars = string.ascii_uppercase + string.digits
    if middle_len == 0:
        return [start + end]
    return [start + ''.join(c) + end for c in product(chars, repeat=middle_len)]

def check_plate_availability(plate):
    """Check if a single plate is available"""
    ts = int(time.time())
    api_url = (
        "https://vplates.com.au/vplatesapi/checkcombo"
        f"?vehicleType=car&combination={plate}&_={ts}"
    )
    
    try:
        driver = create_driver()
        try:
            driver.get(api_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            raw = driver.find_element(By.TAG_NAME, 'body').text
            data = json.loads(raw)
            return data.get("status", "").lower() == "available"
        finally:
            driver.quit()
    except Exception as e:
        logger.error(f"Error checking plate {plate}: {str(e)}")
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
    
    logger.info(f"Checking {total} combinations for start='{start}' end='{end}'")
    
    available = []
    for plate in plates:
        if check_plate_availability(plate):
            available.append(plate)
    
    return jsonify(
        checked=len(plates),
        total=total,
        available=available
    )

if __name__ == '__main__':
    app.run(debug=True)