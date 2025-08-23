import os
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_normal_driver(headless=False, max_retries=3):
    try:
        options = webdriver.ChromeOptions()
        path = rf'{BASE_DIR}\chrome-dir'
        options.add_argument(f'--user-data-dir={path}')
        options.add_argument("--log-level=3")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if not headless:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        time.sleep(1)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        return driver
    except Exception as e:
        print(f"Error: {e}")
        if max_retries > 0:
            time.sleep(2)
            return get_normal_driver(headless=headless, max_retries=max_retries - 1)
        print("Max retries exceeded. Could not create the driver.")
        return None

def _with_retries(driver, locator, attr='text', timeout=5, attempts=3):
    for i in range(attempts):
        try:
            el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
            if attr == 'text':
                return el.text.strip()
            if attr == 'href':
                return (el.get_attribute("href") or "").strip()
            return ''
        except StaleElementReferenceException:
            if i == attempts - 1:
                return ''
            time.sleep(0.2)
        except Exception:
            return ''
    return ''

def check_element_visibility_and_return_text(driver, by_locator):
    return _with_retries(driver, by_locator, 'text')

def check_element_visibility_and_return_href(driver, by_locator):
    return _with_retries(driver, by_locator, 'href')

def check_element_visibility(driver, by_locator):
    try:
        WebDriverWait(driver, 3).until(EC.visibility_of_element_located(by_locator))
        return True
    except Exception:
        return False

def create_xpath_1(a):
    return f"(//span[@id= '{a}'])[1]"


def click_element(driver, by_locator):
    try:
        el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(by_locator))
        el.click()
        return True
    except Exception as e:
        print(f"Error clicking element: {e}")
        return False

def check_element_clickable(driver, by_locator):
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable(by_locator))
        return True
    except Exception:
        return False
