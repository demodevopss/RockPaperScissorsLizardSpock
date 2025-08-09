#!/usr/bin/env python3
"""
Debug script to check UI behavior
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

WEB_URL = "http://192.168.64.153:30081"
SELENIUM_URL = "http://192.168.64.153:4444/wd/hub"

def debug_ui():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=chrome_options
    )
    
    try:
        print(f"Navigating to {WEB_URL}")
        driver.get(WEB_URL)
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Take screenshot of main page
        driver.save_screenshot("debug_main_page.png")
        print("Main page screenshot saved")
        
        # Enter username
        print("Looking for username input...")
        user_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.user"))
        )
        user_input.clear()
        user_input.send_keys("serdar")
        print("Username entered")
        
        # Take screenshot after username entry
        driver.save_screenshot("debug_after_username.png")
        print("After username screenshot saved")
        
        # Click "Play with a bot"
        print("Looking for Play with bot button...")
        play_bot = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Play with a bot')]"))
        )
        play_bot.click()
        print("Play with bot clicked")
        
        # Wait for navigation
        print("Waiting for navigation to challenger page...")
        WebDriverWait(driver, 30).until(lambda d: "/challenger" in d.current_url)
        print(f"Navigated to: {driver.current_url}")
        
        # Take screenshot of challenger page
        driver.save_screenshot("debug_challenger_page.png")
        print("Challenger page screenshot saved")
        
        # Check page source
        print("Page source (first 1000 chars):")
        print(driver.page_source[:1000])
        
        # Look for .lang-card elements
        print("Looking for .lang-card elements...")
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, ".lang-card")
            print(f"Found {len(cards)} .lang-card elements")
            
            if len(cards) == 0:
                # Try other selectors
                print("Trying alternative selectors...")
                all_divs = driver.find_elements(By.TAG_NAME, "div")
                print(f"Found {len(all_divs)} div elements")
                
                # Look for any elements with "card" in class name
                card_like = driver.find_elements(By.CSS_SELECTOR, "[class*='card']")
                print(f"Found {len(card_like)} elements with 'card' in class name")
                
                for elem in card_like[:5]:  # Show first 5
                    print(f"Card-like element: {elem.get_attribute('class')}")
                    
        except Exception as e:
            print(f"Error finding .lang-card: {e}")
            
        # Wait a bit more and try again
        print("Waiting 5 seconds and trying again...")
        time.sleep(5)
        
        try:
            cards = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".lang-card"))
            )
            print(f"After wait: Found {len(cards)} .lang-card elements")
        except Exception as e:
            print(f"Still no .lang-card elements after wait: {e}")
            
        # Final screenshot
        driver.save_screenshot("debug_final.png")
        print("Final screenshot saved")
        
    except Exception as e:
        print(f"Error during debug: {e}")
        driver.save_screenshot("debug_error.png")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_ui()

