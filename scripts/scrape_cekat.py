import os
import time
import csv
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

load_dotenv()

CEKAT_EMAIL = os.getenv("CEKAT_EMAIL")
CEKAT_PASSWORD = os.getenv("CEKAT_PASSWORD")
LOGIN_URL = "https://chat.cekat.ai/login"
TRACKER_URL = "https://chat.cekat.ai/crm?board_id=3f155efe-39fc-4c71-bdc1-61592194b22c&view_id=f5404f70-6453-466e-8167-f7d2d0a3840c"


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def login(driver):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_input.send_keys(CEKAT_EMAIL)

    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.send_keys(CEKAT_PASSWORD)

    login_button = driver.find_element(By.XPATH, "//button[contains(., 'Log in')]")
    login_button.click()

    try:
        wait.until(EC.url_changes(LOGIN_URL))
    except Exception as e:
        driver.save_screenshot("login_debug.png")
        print("Login gagal/timeout — screenshot disimpan ke login_debug.png")
        raise e


def scrape_tracker(driver):
    driver.get(TRACKER_URL)
    wait = WebDriverWait(driver, 40)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    time.sleep(3)  # buffer ekstra biar render selesai total

    # Ambil semua data tabel via JavaScript sekaligus (atomic, gak rentan stale)
    script = """
    const table = document.querySelector('table');
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.trim());
    const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr =>
        Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
    );
    return {headers: headers, rows: rows};
    """
    result = driver.execute_script(script)

    headers = result["headers"]
    data = result["rows"]

    return headers, data


def save_raw(headers, data):
    bronze_dir = Path("data/bronze")
    bronze_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    output_path = bronze_dir / f"leads_{timestamp}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)

    print(f"Saved {len(data)} rows to {output_path}")
    return str(output_path)


def main():
    driver = get_driver()
    try:
        login(driver)
        headers, data = scrape_tracker(driver)
        save_raw(headers, data)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()