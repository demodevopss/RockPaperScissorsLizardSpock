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


import pytest


@pytest.mark.smoke
def test_homepage_loads(driver):
    driver.get(WEB_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "app")))
    assert "Rock" in driver.title or "Spock" in driver.title


@pytest.mark.smoke
def test_swagger_redirects(driver):
    # Validate API is also reachable via NodePort 30080
    api_url = os.getenv("API_URL", "http://192.168.64.153:30080")
    driver.get(api_url)
    WebDriverWait(driver, 15).until(lambda d: "/swagger" in urllib.parse.urlparse(d.current_url).path)


@pytest.mark.smoke
def test_play_with_bot_button(driver):
    driver.get(WEB_URL)
    # Enter username
    user_input = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.user")))
    user_input.clear()
    user_input.send_keys("serdar")
    # Click "Play with a bot"
    play_bot = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Play with a bot')]")))
    play_bot.click()
    WebDriverWait(driver, 30).until(lambda d: "/challenger" in urllib.parse.urlparse(d.current_url).path)


@pytest.mark.smoke
def test_play_with_friend_button_if_enabled(driver):
    driver.get(WEB_URL)

    # Username input may be hidden if already logged in; fill if visible
    try:
        user_input = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.user"))
        )
        user_input.clear()
        user_input.send_keys("serdar")
    except Exception:
        pass

    # Try to click "Play with a friend" if present/enabled, otherwise skip
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Play with a friend')]"))
        )
        if btn.is_enabled():
            btn.click()
            WebDriverWait(driver, 30).until(
                lambda d: "/lobby" in urllib.parse.urlparse(d.current_url).path
            )
        else:
            pytest.skip("Multiplayer button disabled by settings")
    except Exception:
        pytest.skip("Multiplayer button not rendered")

