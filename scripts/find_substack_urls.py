#!/usr/bin/env python3
"""
Script to generate Substack URLs for authors in newsletters.txt
Generates likely URLs based on common patterns and saves them to data/newsletters.url.generated.md
Note: Generated URLs need manual verification as they are educated guesses.
"""

import requests
import re
import time
from urllib.parse import urlparse
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def search_substack_url(author_name):
    """
    Generate possible Substack URLs for a given author name.
    Uses common patterns to generate likely URLs.
    """
    # Handle special cases first
    if "(" in author_name and ")" in author_name:
        # Extract publication name from parentheses
        pub_name = author_name.split("(")[1].split(")")[0]
        return f"https://{pub_name.lower().replace(' ', '').replace(' ', '')}.substack.com"
    
    # Clean the author name for URL generation
    clean_name = re.sub(r'[^\w\s]', '', author_name).lower()
    clean_name = re.sub(r'\s+', '', clean_name)
    
    # Generate possible URL patterns
    patterns = [
        f"https://{clean_name}.substack.com",
        f"https://{author_name.lower().replace(' ', '')}.substack.com",
        f"https://{author_name.lower().replace(' ', '-')}.substack.com",
    ]
    
    # Return the most likely pattern (first one)
    return patterns[0]

def verify_substack_url(url):
    """
    Verify if a URL is a valid Substack URL.
    """
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function to process newsletters.txt and generate newsletters.url.txt"""
    
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
    
    results = []
    
    for i, author in enumerate(authors, 1):
        print(f"[{i}/{len(authors)}] Processing: {author}")
        
        # Get the URL
        url = search_substack_url(author)
        
        # Note: URL verification is disabled to avoid rate limiting
        # All URLs are marked as "?" and need manual verification
        status = "?"
        
        results.append(f"{author}\t{url}\t{status}")
        
        # Small delay to be respectful
        time.sleep(0.5)
    
    # Write results
    print(f"\nWriting results to {output_file}...")
    with open(output_file, 'w') as f:
        f.write("# Author\tSubstack URL\tVerified\n")
        for result in results:
            f.write(f"{result}\n")
    
    print(f"Done! Results saved to {output_file}")
    print("\nNote: URLs marked with '?' need manual verification.")
    print("You can edit newsletters.url.txt to correct any URLs.")

if __name__ == "__main__":
    main() 