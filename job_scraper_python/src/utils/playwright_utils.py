import json
import os
import time
from typing import Optional, List, Dict, Any

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    Page,
    BrowserContext,
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError
)

from utils.project_root import DATA_DIR # Assuming project_root.py is in the same utils directory
from config.settings import Settings # May be needed for browser settings later

# Global variables for Playwright instance, browser, context, and page
_playwright_instance: Optional[Playwright] = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None # Represents the currently active page

DEFAULT_TIMEOUT = 30 * 1000  # 30 seconds in milliseconds for Playwright operations

def init_playwright(
    settings: Optional[Settings] = None,
    headless: bool = False,
    browser_name: str = "chromium"
) -> None:
    global _playwright_instance, _browser, _context, _page
    if _playwright_instance:
        print("Playwright already initialized.")
        return

    try:
        _playwright_instance = sync_playwright().start()
        launch_options = {"headless": headless}

        # Example for proxy settings if they were in Settings dataclass
        # if settings and settings.proxy and settings.proxy.server:
        #     launch_options["proxy"] = {
        #         "server": settings.proxy.server,
        #         "username": settings.proxy.username,
        #         "password": settings.proxy.password
        #     }

        if browser_name == "chromium":
            _browser = _playwright_instance.chromium.launch(**launch_options)
        elif browser_name == "firefox":
            _browser = _playwright_instance.firefox.launch(**launch_options)
        elif browser_name == "webkit":
            _browser = _playwright_instance.webkit.launch(**launch_options)
        else:
            raise ValueError(f"Unsupported browser: {browser_name}")

        _context = _browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/90.0.4430.212 Safari/537.36"
            )
            # Add other context options: viewport, locale, timezone, permissions
        )
        _context.set_default_timeout(DEFAULT_TIMEOUT)
        _page = _context.new_page()
        print(f"{browser_name.capitalize()} browser started. Headless: {headless}")

    except Exception as e:
        print(f"Error initializing Playwright: {e}")
        if _playwright_instance: # Check if playwright started before failing
            _playwright_instance.stop()
        _playwright_instance = None # Reset global
        raise # Re-raise the exception so caller knows init failed

def get_page() -> Optional[Page]:
    global _page
    if not _page:
        # This could also try to initialize or get context/browser if they are also None
        print("Error: Page not initialized. Call init_playwright() first.")
    return _page

def new_page() -> Optional[Page]:
    global _context, _page
    if not _context:
        print("Error: Browser context not initialized. Call init_playwright() first.")
        return None
    _page = _context.new_page() # Assign new page to global _page
    return _page

def close_playwright() -> None:
    global _playwright_instance, _browser, _context, _page
    # Close in reverse order of creation
    if _page and not _page.is_closed(): # Check if page is already closed
        try:
            _page.close()
        except Exception as e:
            print(f"Error closing page: {e}") # Log error but continue cleanup
    _page = None

    if _context:
        try:
            _context.close()
        except Exception as e:
            print(f"Error closing context: {e}")
    _context = None

    if _browser:
        try:
            _browser.close()
        except Exception as e:
            print(f"Error closing browser: {e}")
    _browser = None

    if _playwright_instance:
        try:
            _playwright_instance.stop()
        except Exception as e:
            print(f"Error stopping Playwright: {e}")
    _playwright_instance = None
    print("Playwright resources closed/released.")


def save_cookies(page: Page, site_name: str) -> None:
    cookie_file = os.path.join(DATA_DIR, f"{site_name}_cookies.json")
    try:
        cookies = page.context.cookies()
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
        print(f"Cookies saved for {site_name} to {cookie_file}")
    except Exception as e:
        print(f"Error saving cookies for {site_name}: {e}")

def load_cookies(context: BrowserContext, site_name: str) -> bool:
    cookie_file = os.path.join(DATA_DIR, f"{site_name}_cookies.json")
    if not os.path.exists(cookie_file):
        print(f"Cookie file not found for {site_name}: {cookie_file}")
        return False
    try:
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        if cookies: # Ensure cookies list is not empty
            context.add_cookies(cookies)
            print(f"Cookies loaded for {site_name} from {cookie_file}")
            return True
        else:
            print(f"No cookies found in file for {site_name}: {cookie_file}")
            return False
    except Exception as e:
        print(f"Error loading cookies for {site_name}: {e}")
        return False

def navigate_to_url(page: Page, url: str, timeout: Optional[int] = None) -> bool:
    actual_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        print(f"Navigating to {url}...")
        page.goto(url, timeout=actual_timeout, wait_until="domcontentloaded")
        print(f"Successfully navigated to {url}")
        return True
    except PlaywrightTimeoutError:
        print(f"Timeout navigating to {url}")
        return False
    except Exception as e:
        print(f"Error navigating to {url}: {e}")
        return False

def click_element(page: Page, selector: str, timeout: Optional[int] = None) -> bool:
    actual_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        page.locator(selector).click(timeout=actual_timeout)
        print(f"Clicked element: {selector}")
        return True
    except PlaywrightTimeoutError:
        print(f"Timeout clicking element: {selector}")
        return False
    except Exception as e:
        print(f"Error clicking element {selector}: {e}")
        return False

def fill_input(page: Page, selector: str, text: str, timeout: Optional[int] = None) -> bool:
    actual_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        page.locator(selector).fill(text, timeout=actual_timeout)
        print(f"Filled input {selector} with text.")
        return True
    except PlaywrightTimeoutError:
        print(f"Timeout filling input: {selector}")
        return False
    except Exception as e:
        print(f"Error filling input {selector}: {e}")
        return False

def wait_for_selector(page: Page, selector: str, timeout: Optional[int] = None, state: str = "visible") -> Optional[ElementHandle]:
    actual_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    try:
        # Note: page.wait_for_selector returns ElementHandle, not Locator
        element = page.wait_for_selector(selector, timeout=actual_timeout, state=state) # type: ignore
        print(f"Element {selector} is {state}.")
        return element
    except PlaywrightTimeoutError:
        print(f"Timeout waiting for selector: {selector} with state: {state}")
        return None
    except Exception as e:
        print(f"Error waiting for selector {selector}: {e}")
        return None

def scroll_page_down(page: Page, times: int = 1, delay_sec: float = 0.5):
    try:
        for _ in range(times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(delay_sec)
        print(f"Scrolled page down {times} time(s).")
    except Exception as e:
        print(f"Error scrolling page: {e}")

def take_screenshot(page: Page, file_name_prefix: str = "screenshot") -> Optional[str]:
    screenshots_dir = os.path.join(DATA_DIR, "screenshots") # DATA_DIR from project_root
    os.makedirs(screenshots_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(screenshots_dir, f"{file_name_prefix}_{timestamp}.png")
    try:
        page.screenshot(path=path)
        print(f"Screenshot saved to {path}")
        return path
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

# Example usage for testing this file directly
if __name__ == "__main__":
    print("Testing Playwright utils...")
    # Create a dummy settings object for this direct test
    class DummySettingsForPlaywrightTest:
        pass # Add proxy or other browser relevant settings if needed for direct test

    test_settings_obj = DummySettingsForPlaywrightTest()

    try:
        init_playwright(settings=test_settings_obj, headless=True)

        current_page = get_page()
        if current_page:
            print("Navigating to example.com...")
            if navigate_to_url(current_page, "http://example.com"):
                print("Navigation successful.")
                take_screenshot(current_page, "example_com")

                if _context: # Check if context is available for cookie operations
                    _context.add_cookies([{"name": "test_cookie", "value": "test_value", "domain": "example.com", "path": "/"}])
                    save_cookies(current_page, "example_site")

                    _context.clear_cookies()
                    print("Cookies cleared from context.")
                    if load_cookies(_context, "example_site"):
                        reloaded_cookies = _context.cookies()
                        print(f"Reloaded cookies: {reloaded_cookies}")
                        if any(c['name'] == 'test_cookie' for c in reloaded_cookies):
                            print("Cookie load and check successful.")
                        else:
                            print("Cookie load test failed: test_cookie not found after load.")
                    else:
                        print("Failed to load cookies for example_site.")
            else:
                print("Navigation to example.com failed.")
        else:
            print("Failed to get page for testing after init.")

    except Exception as e:
        print(f"An error occurred during Playwright utils self-test: {e}")
    finally:
        close_playwright() # Ensure cleanup happens

    print("Playwright utils self-test finished.")
