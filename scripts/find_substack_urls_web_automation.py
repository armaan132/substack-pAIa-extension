#!/usr/bin/env python3
"""
Human-like script to find Substack URLs using browser automation.
Uses Selenium to control a real browser, making it behave like a human user.
"""

import time
import random
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import chromedriver_autoinstaller
except ImportError:
    print("Selenium not installed. Install with: pip install selenium chromedriver-autoinstaller")
    sys.exit(1)

def setup_browser():
    """
    Set up Chrome browser with human-like settings.
    """
    # Auto-install the correct ChromeDriver version
    print("Installing/updating ChromeDriver...")
    chromedriver_autoinstaller.install()
    
    chrome_options = Options()
    
    # Run Chrome in headless mode (no visible window)
    chrome_options.add_argument("--headless=new")
    
    # Make it look like a real browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set a realistic window size
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add realistic user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Disable images to speed up loading
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        print("    Starting Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Wait a moment for browser to fully load
        time.sleep(2)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("    Browser started successfully")
        return driver
    except Exception as e:
        print(f"Error setting up browser: {e}")
        print("    This might be due to:")
        print("    - Chrome security popup (check for popups)")
        print("    - Permission issues (check System Settings > Privacy & Security)")
        print("    - ChromeDriver version mismatch")
        return None

def human_like_delay(min_seconds=1, max_seconds=3):
    """
    Add random delays to simulate human behavior.
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def human_like_typing(driver, element, text):
    """
    Type text like a human with random delays between characters.
    """
    for char in text:
        element.send_keys(char)
        # Random delay between characters (0.05 to 0.15 seconds)
        time.sleep(random.uniform(0.05, 0.15))

def search_duckduckgo_human(driver, query):
    """
    Search DuckDuckGo like a human would.
    """
    try:
        # Check if driver is still valid
        try:
            driver.current_url
        except:
            print(f"    ❌ Browser window was closed")
            return None
        
        # Go to DuckDuckGo homepage
        print(f"    Navigating to DuckDuckGo...")
        driver.get("https://duckduckgo.com")
        human_like_delay(2, 4)
        
        # Check if we're on the right page
        if "duckduckgo.com" not in driver.current_url:
            print(f"    ❌ Failed to load DuckDuckGo (current URL: {driver.current_url})")
            return None
        
        # Find and click the search box
        print(f"    Looking for search box...")
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchbox_input"))
            )
        except TimeoutException:
            print(f"    ❌ Could not find search box. Trying alternative selectors...")
            # Try alternative selectors
            selectors = [
                (By.NAME, "q"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[name='q']")
            ]
            search_box = None
            for selector_type, selector in selectors:
                try:
                    search_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    print(f"    Found search box with selector: {selector_type}={selector}")
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                print(f"    ❌ Could not find search box with any selector")
                return None
        
        # Clear the search box
        search_box.clear()
        human_like_delay(0.5, 1)
        
        # Type the query like a human
        print(f"    Typing search query...")
        human_like_typing(driver, search_box, query)
        human_like_delay(0.5, 1.5)
        
        # Press Enter
        search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load
        print(f"    Waiting for search results...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result"))
            )
        except TimeoutException:
            print(f"    ❌ Timeout waiting for search results")
            # Try to get page source anyway
            return driver.page_source
        
        human_like_delay(2, 4)
        
        # Get the page source
        page_source = driver.page_source
        
        print(f"    Search completed successfully")
        return page_source
        
    except Exception as e:
        print(f"    ❌ Error during search: {e}")
        return None

def extract_substack_urls_from_html(html_content):
    """
    Extract Substack URLs from HTML content.
    """
    if not html_content:
        return []
    
    # Look for Substack URLs in the HTML
    patterns = [
        r'https://[^"\s]+\.substack\.com[^"\s]*',
        r'https://[^"\s]+\.substack\.com',
        r'https://[^"\s]+\.substack\.com/',
    ]
    
    all_urls = []
    for pattern in patterns:
        urls = re.findall(pattern, html_content)
        all_urls.extend(urls)
    
    # Clean and deduplicate URLs
    clean_urls = []
    for url in all_urls:
        # Remove any trailing characters that aren't part of the URL
        clean_url = re.sub(r'[^\w\-\./:]', '', url)
        # Ensure it ends with .com or .com/
        if clean_url.endswith('.com') or clean_url.endswith('.com/'):
            if clean_url not in clean_urls:
                clean_urls.append(clean_url)
    
    return clean_urls

def find_best_substack_url(author_name, urls):
    """
    Find the best Substack URL from a list of URLs.
    """
    if not urls:
        return None
    
    # Clean author name for matching
    clean_author = re.sub(r'[^\w\s]', '', author_name).lower()
    author_words = clean_author.split()
    
    # Score each URL
    scored_urls = []
    for url in urls:
        score = 0
        url_lower = url.lower()
        
        # Check if author name appears in URL
        for word in author_words:
            if word in url_lower:
                score += 1
        
        # Bonus for exact matches
        if clean_author.replace(' ', '') in url_lower:
            score += 5
        
        # Bonus for author name at start of subdomain
        domain = urlparse(url).netloc
        if domain.startswith(clean_author.replace(' ', '')):
            score += 3
        
        scored_urls.append((url, score))
    
    # Sort by score and return the best match
    scored_urls.sort(key=lambda x: x[1], reverse=True)
    
    if scored_urls and scored_urls[0][1] > 0:
        return scored_urls[0][0]
    
    return urls[0] if urls else None

def search_substack_url_human(driver, author_name):
    """
    Search for Substack URL using human-like browser automation.
    """
    print(f"  Searching for: '{author_name} substack'")
    
    # Search query
    query = f'"{author_name}" substack'
    
    # Perform the search
    html_content = search_duckduckgo_human(driver, query)
    if not html_content:
        print(f"  ❌ Search failed")
        return None
    
    # Extract Substack URLs
    urls = extract_substack_urls_from_html(html_content)
    print(f"    Found {len(urls)} potential URLs: {urls[:3]}...")
    
    if not urls:
        print(f"  ❌ No Substack URLs found in search results")
        return None
    
    # Find the best match
    best_url = find_best_substack_url(author_name, urls)
    
    if best_url:
        print(f"  ✅ Best match: {best_url}")
    else:
        print(f"  ❌ No suitable URL found")
    
    return best_url

def main():
    """Main function to process newsletters.txt using human-like automation"""
    
    # Read newsletters.txt
    newsletters_file = project_root / "config" / "newsletters.txt"
    output_file = project_root / "data" / "newsletters.url.generated.md"
    
    if not newsletters_file.exists():
        print(f"Error: {newsletters_file} not found")
        return
    
    print("Reading newsletters.txt...")
    with open(newsletters_file, 'r') as f:
        authors = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(authors)} authors to process")
    print("\nStarting human-like web search for Substack URLs...")
    print("=" * 60)
    
    # Set up browser
    print("Setting up browser...")
    driver = setup_browser()
    if not driver:
        print("Failed to set up browser. Exiting.")
        return
    
    try:
        results = []
        
        for i, author in enumerate(authors, 1):
            print(f"\n[{i}/{len(authors)}] Processing: {author}")
            
            # Search for the URL
            url = search_substack_url_human(driver, author)
            
            if url:
                results.append(f"{author}\t{url}\t✓")
            else:
                # Fallback to pattern-based generation
                clean_name = re.sub(r'[^\w\s]', '', author).lower()
                clean_name = re.sub(r'\s+', '', clean_name)
                fallback_url = f"https://{clean_name}.substack.com"
                results.append(f"{author}\t{fallback_url}\t?")
                print(f"  ⚠️  Using fallback URL: {fallback_url}")
            
            # Human-like delay between searches
            if i < len(authors):  # Don't delay after the last one
                delay = random.uniform(5, 10)
                print(f"  Taking a break for {delay:.1f}s...")
                time.sleep(delay)
        
        # Write results
        print(f"\nWriting results to {output_file}...")
        with open(output_file, 'w') as f:
            f.write("# Author\tSubstack URL\tVerified\n")
            for result in results:
                f.write(f"{result}\n")
        
        print(f"Done! Results saved to {output_file}")
        print("\nNote: URLs marked with '✓' were found via web search.")
        print("URLs marked with '?' are fallback URLs and need manual verification.")
        
    finally:
        # Always close the browser
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    main() 