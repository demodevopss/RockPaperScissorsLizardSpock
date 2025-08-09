import os
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WEB_URL = os.getenv("WEB_URL", "http://192.168.64.153:30081")
SELENIUM_URL = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")

class CrossBrowserTests:
    
    @pytest.fixture(params=['chrome', 'firefox', 'edge'])
    def driver(self, request):
        """Multi-browser fixture"""
        browser = request.param
        
        if browser == 'chrome':
            options = ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            driver = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
            
        elif browser == 'firefox':
            options = FirefoxOptions()
            options.add_argument("--headless")
            driver = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
            
        elif browser == 'edge':
            options = EdgeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
            
        driver.set_window_size(1920, 1080)
        yield driver
        driver.quit()

    @pytest.mark.cross_browser
    def test_homepage_loads_all_browsers(self, driver):
        """Test homepage loads correctly across browsers"""
        driver.get(WEB_URL)
        
        # Wait for Blazor app to initialize
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        # Check page title
        assert "Rock" in driver.title or "Spock" in driver.title
        
        # Check app container exists
        app_element = driver.find_element(By.ID, "app")
        assert app_element.is_displayed()

    @pytest.mark.cross_browser
    def test_responsive_design(self, driver):
        """Test responsive design across different screen sizes"""
        driver.get(WEB_URL)
        
        # Test different viewport sizes
        viewports = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in viewports:
            driver.set_window_size(width, height)
            time.sleep(2)  # Allow layout to adjust
            
            # Check app is still visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "app"))
            )
            
            app_element = driver.find_element(By.ID, "app")
            assert app_element.is_displayed()
            
            # Check no horizontal scroll for mobile
            if width <= 768:
                body_width = driver.execute_script("return document.body.scrollWidth")
                assert body_width <= width + 50  # Allow small tolerance

    @pytest.mark.cross_browser
    def test_game_flow_all_browsers(self, driver):
        """Test complete game flow across browsers"""
        driver.get(WEB_URL)
        
        # Wait for page load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        try:
            # Enter username
            user_input = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.user"))
            )
            user_input.clear()
            user_input.send_keys("cross_browser_test")
            
            # Click Play with bot
            play_bot = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Play with a bot')]"))
            )
            play_bot.click()
            
            # Check navigation to challenger page
            WebDriverWait(driver, 30).until(
                lambda d: "/challenger" in d.current_url
            )
            
            # This test passes if we can navigate through the basic flow
            assert "/challenger" in driver.current_url
            
        except Exception as e:
            # Log browser-specific information
            browser_name = driver.capabilities.get('browserName', 'unknown')
            print(f"Test failed on {browser_name}: {str(e)}")
            raise

    @pytest.mark.cross_browser
    def test_javascript_functionality(self, driver):
        """Test JavaScript functionality across browsers"""
        driver.get(WEB_URL)
        
        # Wait for Blazor to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        # Test JavaScript execution
        js_result = driver.execute_script("return navigator.userAgent;")
        assert js_result is not None
        
        # Test Blazor framework is loaded
        blazor_check = driver.execute_script("""
            return window.Blazor !== undefined || 
                   document.querySelector('[src*="blazor"]') !== null;
        """)
        assert blazor_check

    @pytest.mark.cross_browser
    def test_css_rendering(self, driver):
        """Test CSS rendering across browsers"""
        driver.get(WEB_URL)
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "app"))
        )
        
        # Check if main app container has proper styling
        app_element = driver.find_element(By.ID, "app")
        
        # Verify element is visible and has dimensions
        assert app_element.is_displayed()
        assert app_element.size['width'] > 0
        assert app_element.size['height'] > 0

    @pytest.mark.cross_browser
    def test_browser_compatibility_features(self, driver):
        """Test browser-specific compatibility features"""
        driver.get(WEB_URL)
        
        # Get browser info
        browser_name = driver.capabilities.get('browserName', 'unknown')
        browser_version = driver.capabilities.get('browserVersion', 'unknown')
        
        print(f"Testing on {browser_name} {browser_version}")
        
        # Test localStorage (if used by Blazor)
        local_storage_test = driver.execute_script("""
            try {
                localStorage.setItem('test', 'value');
                const result = localStorage.getItem('test');
                localStorage.removeItem('test');
                return result === 'value';
            } catch(e) {
                return false;
            }
        """)
        assert local_storage_test, f"localStorage not working in {browser_name}"
        
        # Test fetch API (used by Blazor for HTTP calls)
        fetch_test = driver.execute_script("return typeof fetch === 'function';")
        assert fetch_test, f"Fetch API not available in {browser_name}"

# Performance comparison across browsers
class BrowserPerformanceTests:
    
    @pytest.mark.performance
    @pytest.mark.parametrize("browser", ['chrome', 'firefox', 'edge'])
    def test_page_load_performance(self, browser):
        """Compare page load performance across browsers"""
        
        # Configure browser
        if browser == 'chrome':
            options = ChromeOptions()
            options.add_argument("--headless=new")
        elif browser == 'firefox':
            options = FirefoxOptions()
            options.add_argument("--headless")
        elif browser == 'edge':
            options = EdgeOptions()
            options.add_argument("--headless")
            
        driver = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
        
        try:
            # Measure page load time
            start_time = time.time()
            driver.get(WEB_URL)
            
            # Wait for app to be ready
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "app"))
            )
            
            load_time = time.time() - start_time
            
            print(f"{browser} load time: {load_time:.2f}s")
            
            # Performance assertion (adjust threshold as needed)
            assert load_time < 15.0, f"{browser} took too long to load: {load_time:.2f}s"
            
        finally:
            driver.quit()

if __name__ == "__main__":
    # Run cross-browser tests
    pytest.main([
        __file__,
        "-v",
        "-m", "cross_browser",
        "--tb=short",
        "--html=reports/cross-platform/browser-test-report.html",
        "--self-contained-html"
    ])
