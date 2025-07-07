#!/usr/bin/env python3
"""
Script to find Substack URLs by web scraping search results
Searches for author names + "substack" and extracts actual URLs
"""

import requests
import re
import time
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote
import random

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def search_duckduckgo(query, session=None):
    """
    Search DuckDuckGo for the query and return results.
    DuckDuckGo doesn't require API keys and is more permissive.
    """
    if session is None:
        session = requests.Session()
    
    # Better headers to look more like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session.headers.update(headers)
    
    try:
        # Use DuckDuckGo's HTML search
        search_url = "https://html.duckduckgo.com/html/"
        params = {
            'q': query,
            'kl': 'us-en'
        }
        
        # Add a small random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = session.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        print(f"    Search response status: {response.status_code}")
        print(f"    Response length: {len(response.text)}")
        
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"    ❌ Access forbidden (403) - DuckDuckGo blocked the request")
            print(f"    💡 This usually means they detected automated access")
        else:
            print(f"    ❌ HTTP error: {e}")
        return None
    except Exception as e:
        print(f"    ❌ Error searching DuckDuckGo: {e}")
        return None

def extract_top_search_result(html_content):
    """
    Extract the top search result from DuckDuckGo HTML.
    """
    if not html_content:
        return "No HTML content"
    
    # Look for the first result link
    # DuckDuckGo typically has results in <a> tags with href attributes
    result_pattern = r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result__a[^"]*"[^>]*>'
    matches = re.findall(result_pattern, html_content)
    
    if matches:
        return matches[0]
    
    # Fallback: look for any link that might be a result
    link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>'
    matches = re.findall(link_pattern, html_content)
    
    if matches:
        return matches[0]
    
    return "No links found"

def extract_substack_urls(html_content):
    """
    Extract Substack URLs from HTML search results.
    """
    if not html_content:
        return []
    
    # Multiple patterns to catch different URL formats
    patterns = [
        r'https://[^"\s]+\.substack\.com[^"\s]*',  # Standard pattern
        r'https://[^"\s]+\.substack\.com',         # Without trailing chars
        r'https://[^"\s]+\.substack\.com/',        # With trailing slash
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
    
    # Debug: print what we found
    print(f"    Raw HTML length: {len(html_content)}")
    print(f"    Found {len(clean_urls)} clean URLs: {clean_urls}")
    
    return clean_urls

def find_best_substack_url(author_name, search_results):
    """
    Find the best Substack URL from search results.
    Prioritizes URLs that match the author name.
    """
    if not search_results:
        return None
    
    # Clean author name for matching
    clean_author = re.sub(r'[^\w\s]', '', author_name).lower()
    author_words = clean_author.split()
    
    # Score each URL based on how well it matches the author name
    scored_urls = []
    
    for url in search_results:
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
    
    # If no good match, return the first result
    return search_results[0] if search_results else None

def search_substack_url(author_name, session=None):
    """
    Search for Substack URL for a given author name.
    """
    print(f"  Searching for: '{author_name} substack'")
    
    # Search query
    query = f'"{author_name}" substack'
    
    # Try up to 3 times with increasing delays
    for attempt in range(3):
        if attempt > 0:
            delay = 5 * attempt  # 5s, 10s delays
            print(f"    Retry {attempt + 1}/3, waiting {delay}s...")
            time.sleep(delay)
        
        # Get search results
        html_content = search_duckduckgo(query, session)
        if html_content:
            break
    else:
        print(f"  ❌ All attempts failed")
        return None
    
    # Extract and log the top search result
    top_result = extract_top_search_result(html_content)
    log_file = project_root / "data" / "search_debug.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{author_name}\n")
        f.write(f"Query: {query}\n")
        f.write(f"Top result: {top_result}\n")
        f.write(f"{'-'*50}\n")
    
    print(f"    Top result logged: {top_result[:100]}...")
    
    # Extract Substack URLs
    urls = extract_substack_urls(html_content)
    if not urls:
        print(f"  ❌ No Substack URLs found in search results")
        return None
    
    print(f"  Found {len(urls)} potential URLs: {urls[:3]}...")
    
    # Find the best match
    best_url = find_best_substack_url(author_name, urls)
    
    if best_url:
        print(f"  ✅ Best match: {best_url}")
    else:
        print(f"  ❌ No suitable URL found")
    
    return best_url

def main():
    """Main function to process newsletters.txt and generate URLs"""
    
    # Read newsletters.txt
    newsletters_file = project_root / "config" / "newsletters.txt"
    output_file = project_root / "data" / "newsletters.url.generated.md"
    
    # Clear the debug log file
    log_file = project_root / "data" / "search_debug.log"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Search Debug Log\n")
        f.write("=" * 50 + "\n")
    
    print(f"Debug log will be saved to: {log_file}")
    
    if not newsletters_file.exists():
        print(f"Error: {newsletters_file} not found")
        return
    
    print("Reading newsletters.txt...")
    with open(newsletters_file, 'r') as f:
        authors = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(authors)} authors to process")
    print("\nStarting web search for Substack URLs...")
    print("=" * 50)
    
    results = []
    
    # Create a session to maintain cookies and headers
    session = requests.Session()
    
    for i, author in enumerate(authors, 1):
        print(f"\n[{i}/{len(authors)}] Processing: {author}")
        
        # Search for the URL
        url = search_substack_url(author, session)
        
        if url:
            results.append(f"{author}\t{url}\t✓")
        else:
            # Fallback to pattern-based generation
            clean_name = re.sub(r'[^\w\s]', '', author).lower()
            clean_name = re.sub(r'\s+', '', clean_name)
            fallback_url = f"https://{clean_name}.substack.com"
            results.append(f"{author}\t{fallback_url}\t?")
            print(f"  ⚠️  Using fallback URL: {fallback_url}")
        
        # Random delay to be respectful
        delay = random.uniform(3, 7)
        print(f"  Waiting {delay:.1f}s...")
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

if __name__ == "__main__":
    main() 