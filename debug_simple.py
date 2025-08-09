from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox') 
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Remote('http://192.168.64.153:4444/wd/hub', options=options)

try:
    driver.get('http://192.168.64.153:30081')
    print('Main page loaded:', driver.title)
    
    # Username input
    user_input = driver.find_element(By.CSS_SELECTOR, 'input.user')
    user_input.send_keys('serdar')
    
    # Click bot button using partial text
    bot_button = driver.find_element(By.XPATH, '//button[contains(text(), "Play with a bot")]')
    bot_button.click()
    
    # Wait for page load
    time.sleep(10)
    print('Current URL after click:', driver.current_url)
    
    # Check for cards
    cards = driver.find_elements(By.CSS_SELECTOR, '.lang-card')
    print('lang-card elements found:', len(cards))
    
    # Check other card patterns
    all_cards = driver.find_elements(By.CSS_SELECTOR, '[class*="card"]')
    print('All card elements found:', len(all_cards))
    
    # Check specific challenger page elements
    challenger_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="challenger"]')
    print('Challenger elements found:', len(challenger_elements))
    
    # Check if there are errors 
    if 'error' in driver.page_source.lower():
        print('ERROR TEXT FOUND IN PAGE')
    
    # Show first 500 chars of page
    print('Page preview:', driver.page_source[:500])
    
finally:
    driver.quit()
