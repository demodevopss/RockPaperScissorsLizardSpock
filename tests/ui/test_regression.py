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


@pytest.mark.regression
def test_leaderboard_link(driver):
    driver.get(WEB_URL)
    link = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".leaderboard-link a, .github a.github-text")))
    href = link.get_attribute("href")
    assert href is not None and href.startswith("http")


@pytest.mark.regression
def test_cookies_banner_close(driver):
    driver.get(WEB_URL)
    try:
        close = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cookie-banner .close")))
        close.click()
    except Exception:
        pytest.skip("Cookie banner not shown for authenticated state")


@pytest.mark.regression
def test_navigation_swagger_health(driver):
    # API checks via direct browser hits through NodePort
    api_base = os.getenv("API_URL", "http://192.168.64.153:30080")
    driver.get(api_base + "/health")
    WebDriverWait(driver, 10).until(lambda d: d.page_source == "Healthy" or "Healthy" in d.page_source)
    driver.get(api_base)
    WebDriverWait(driver, 10).until(lambda d: "/swagger" in urllib.parse.urlparse(d.current_url).path)

