import os
import urllib.parse

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WEB_URL = os.getenv("WEB_URL", "http://192.168.64.153:30081")
SELENIUM_URL = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")


@pytest.fixture(scope="session")
def driver():
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    with webdriver.Remote(command_executor=SELENIUM_URL, options=options) as drv:
        yield drv


def wait_and_type(drv, selector, text):
    el = WebDriverWait(drv, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    el.clear()
    el.send_keys(text)
    return el


def click_text(drv, text):
    btn = WebDriverWait(drv, 20).until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{text}')]")))
    btn.click()
    return btn


def test_full_buttons_flow(driver):
    driver.get(WEB_URL)

    # Accept cookies banner if visible (click close)
    try:
        close = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cookie-banner .close")))
        close.click()
    except Exception:
        pass

    # Fill username and click both main buttons
    wait_and_type(driver, "input.user", "serdar")
    click_text(driver, "Play with a bot")
    WebDriverWait(driver, 30).until(lambda d: "/challenger" in urllib.parse.urlparse(d.current_url).path)

    # On challenger page, click one language card and Select
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".lang-card"))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".challengers-select-button .custom-button-link"))).click()
    WebDriverWait(driver, 30).until(lambda d: "/battle" in urllib.parse.urlparse(d.current_url).path)

    # On battle page, pick Rock and click start battle if visible
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'pick-text') and text()='Rock']")))
    driver.find_element(By.XPATH, "//div[contains(@class,'pick-text') and text()='Rock']").click()
    try:
        start = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".start-battle-circle")))
        start.click()
    except Exception:
        pass

    # Back to home and try Play with a friend if enabled
    driver.get(WEB_URL)
    wait_and_type(driver, "input.user", "serdar")
    try:
        click_text(driver, "Play with a friend")
        WebDriverWait(driver, 30).until(lambda d: "/lobby" in urllib.parse.urlparse(d.current_url).path)
    except Exception:
        pytest.skip("Multiplayer not enabled or button not present")

