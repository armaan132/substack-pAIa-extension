# https://github.com/NHagar/substack_api
import sys
import os
import yaml
from pathlib import Path
import re

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.filesystem_store import NewsletterStore
from substack_api import Newsletter
from src.web.index_generator import IndexGenerator

def load_newsletter_md(md_path: str = "config/newsletters.md"):
    """Parse newsletters.md to extract newsletter names and URLs."""
    newsletters = []
    try:
        with open(md_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines, comments, and section headers
                if not line or line.startswith('#') or line.startswith('##'):
                    continue
                # Try to extract name and URL (assume URL is the first http(s) in the line)
                match = re.search(r'(https?://\S+)', line)
                if match:
                    url = match.group(1)
                    # Name is everything before the URL
                    name = line[:match.start()].strip()
                    newsletters.append({'name': name, 'url': url})
    except Exception as e:
        print(f"Error loading {md_path}: {e}")
    return newsletters

def store_newsletter_posts(newsletter_config: dict):
    """Store posts for a single newsletter based on configuration."""
    url = newsletter_config['url']
    name = newsletter_config.get('name', url)
    limit = newsletter_config.get('limit', 3)
    
    print(f"\nProcessing Newsletter: {name} ({url})")
    try:
        newsletter = Newsletter(url)
        store = NewsletterStore()  # Will now use project_root/data by default
        
        recent_posts = newsletter.get_posts(limit=limit)
        print(f"Found {len(recent_posts)} posts")
        
        for post in recent_posts:
            try:
                metadata = post.get_metadata()
                was_saved = store.save_post(url, post)
                if was_saved:
                    print(f"  Storing: {metadata['title']}")
                else:
                    print(f"  Skipping: {metadata['title']} (already exists)")
            except Exception as e:
                print(f"  Error storing post: {e}")
            
        # Show what we've stored
        try:
            print("\n  Stored posts:")
            for post_meta in store.list_posts(url):
                print(f"    - {post_meta['title']} ({post_meta.get('published_at', 'No date')})")
        except Exception as e:
            print(f"  Error listing posts: {e}")
            
    except Exception as e:
        print(f"Error processing {url}: {e}")

def main():
    """Main function to process all configured newsletters from newsletters.md."""
    newsletters = load_newsletter_md()
    if not newsletters:
        print("No newsletters found in config/newsletters.md")
        return
    print(f"Found {len(newsletters)} newsletter(s) to process")
    for newsletter_config in newsletters:
        store_newsletter_posts(newsletter_config)
    
    # Create index files after processing all newsletters
    try:
        index_gen = IndexGenerator()
        # Create test files instead of overwriting main files
        index_gen.create_index_html(output_file="index_test.html")
        index_gen.create_json_index(output_file="index_test.json")
        print("✅ Test files created: index_test.html and index_test.json")
        print("⚠️  Main index.json was NOT overwritten")
    except Exception as e:
        print(f"Error creating test index files: {e}")

if __name__ == "__main__":
    main()
