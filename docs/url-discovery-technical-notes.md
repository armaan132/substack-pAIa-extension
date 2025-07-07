# Substack URL Discovery - Technical Notes

## Overview

This document details the work done on automating Substack URL discovery for newsletter authors. The goal is to automatically find the correct Substack URL for a given author name, reducing manual effort in building the newsletter database.

## Current Status

**Work Completed:** Pattern-based URL generation with fallback mechanisms  
**Work Attempted:** Web scraping approaches (blocked by search engines)  
**Next Steps:** Student needs to implement a robust solution

## Implemented Solutions

### 1. Pattern-Based URL Generation Approach

**Files:**
- `scripts/find_substack_urls.py` - Basic implementation

**How it works:**
- Takes author names from `config/newsletters.txt`
- Applies common URL patterns (no spaces, hyphens, underscores)
- Handles special cases (parentheses, special characters)
- Generates likely Substack URLs based on author name patterns

**Strengths:**
- Fast and reliable
- No external dependencies
- Handles edge cases well
- Good for known authors

**Limitations:**
- Only generates educated guesses
- Requires manual verification
- May not work for authors with unusual URL patterns

### 2. Web Scraping Approache

**Attempted approaches:**

#### A. HTTP Requests (`scripts/find_substack_urls_scraper.py`)
- **Method:** Direct HTTP requests to DuckDuckGo search
- **Technology:** `requests` library
- **Issues:** 403 Forbidden errors, connection timeouts
- **Root cause:** Search engines block automated HTTP requests

#### B. Browser Automation (`scripts/find_substack_urls_web_automation.py`)
- **Method:** Real browser automation with ChromeDriver
- **Technology:** Selenium WebDriver
- **Issues:** ChromeDriver compatibility, window closing, timeouts
- **Root cause:** Complex setup, search engine detection

**Why keep both scripts?**
- **Different failure modes:** They fail in different ways, which is valuable for debugging
- **Different approaches:** If one approach gets fixed, the other might work
- **Educational value:** Shows different web scraping techniques
- **Future potential:** Search engines might change their blocking strategies

### 3. Web Automation Approach

**What is web automation?**
Web automation uses tools like Selenium to control a real web browser programmatically. Instead of sending HTTP requests, it actually opens a browser window and interacts with web pages like a human would.

**How Selenium works:**
- **ChromeDriver:** A separate program that controls Chrome browser
- **Selenium WebDriver:** Python library that communicates with ChromeDriver
- **Browser Control:** Can click buttons, type text, navigate pages, extract content

**Key concepts:**
- **Headless mode:** Browser runs without visible window (faster, less resource-intensive)
- **Element selectors:** Ways to find elements on a page (ID, class, CSS selectors)
- **Wait conditions:** Pause until elements appear or conditions are met
- **User agents:** Browser identification strings that can be customized

**Example workflow:**
1. Open Chrome browser
2. Navigate to DuckDuckGo homepage
3. Find search box element
4. Type search query
5. Press Enter
6. Wait for results to load
7. Extract URLs from page content

**Advantages over HTTP requests:**
- Can handle JavaScript-heavy websites
- More human-like behavior
- Can solve CAPTCHAs (with additional tools)
- Harder to detect as automation

**Disadvantages:**
- Much slower than HTTP requests
- Requires more system resources
- Complex setup and maintenance
- Still can be detected by sophisticated anti-bot systems

## Technical Issues

### 1. Pattern-Based URL Generation 
- **Limited accuracy:** Only generates educated guesses, requires manual verification
- **Special cases:** Authors with unusual naming patterns may not be handled correctly
- **No validation:** Cannot verify if generated URLs actually exist
- **Maintenance burden:** Requires manual updates for new special cases

### 2. Web Scraping 
- **Connection timeouts:** Network issues when making rapid requests
  - ```Error searching DuckDuckGo: HTTPSConnectionPool(host='html.duckduckgo.com', port=443): Max retries exceeded with url: /html/?q=%22Jared+Bernstein%22+substack&kl=us-en (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x1025f3500>, 'Connection to html.duckduckgo.com timed out. (connect timeout=15)'))```

### 3. Web Automation 
- **ChromeDriver compatibility:** Version mismatch between Chrome and ChromeDriver
- **Browser window closing:** Chrome opens but immediately closes or crashes
- **Element selector changes:** Website structure changes break the automation
- **Complex setup:** Requires ChromeDriver installation and configuration
- **Resource intensive:** Uses significant CPU and memory resources
- **Detection:** Sophisticated anti-bot systems can still detect automation

## Configuration Files

### Input Files
- `config/newsletters.txt` - Simple list of author names

### Output Files
- `data/newsletters.url.generated.md` - Generated URLs

## Dependencies

**Required packages:**
```bash
pip install selenium chromedriver-autoinstaller
```

**System requirements:**
- Chrome browser installed
- ChromeDriver (auto-installed by chromedriver-autoinstaller)

## Recommended Next Steps

...

## Testing and Validation

### Current Test Data
- `config/newsletters.txt` contains test authors
- Generated URLs saved to `data/newsletters.url.generated.md`

### Validation Process
1. Run URL generation script
2. Manually verify generated URLs
3. Update special cases database
4. Measure accuracy rates


## Resources

- [ChromeDriver Documentation](https://chromedriver.chromium.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [DuckDuckGo Search API](https://duckduckgo.com/api)
- [Substack URL Patterns](https://substack.com) (analyze existing newsletters) 