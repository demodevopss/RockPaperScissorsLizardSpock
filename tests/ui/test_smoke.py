import os
import time
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


def test_homepage_loads(driver):
    driver.get(WEB_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "app")))
    assert "Rock" in driver.title or "Spock" in driver.title


def test_swagger_redirects(driver):
    # Validate API is also reachable via NodePort 30080
    api_url = os.getenv("API_URL", "http://192.168.64.153:30080")
    driver.get(api_url)
    WebDriverWait(driver, 15).until(lambda d: "/swagger" in urllib.parse.urlparse(d.current_url).path)

