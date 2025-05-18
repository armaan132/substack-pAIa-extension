# https://github.com/NHagar/substack_api
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.filesystem_store import NewsletterStore
from substack_api import Newsletter

# List of science-focused Substacks
science_substacks = [
    "https://econjared.substack.com",
]

def store_newsletter_posts(url: str, limit: int = 3):
    print(f"\nProcessing Newsletter: {url}")
    try:
        newsletter = Newsletter(url)
        store = NewsletterStore()  # Will now use project_root/data by default
        
        recent_posts = newsletter.get_posts(limit=limit)
        print(f"Found {len(recent_posts)} posts")
        
        for post in recent_posts:
            try:
                metadata = post.get_metadata()
                print(f"Storing: {metadata['title']}")
                store.save_post(url, post)
            except Exception as e:
                print(f"Error storing post: {e}")
            
        # Show what we've stored
        try:
            print("\nStored posts:")
            for post_meta in store.list_posts(url):
                print(f"- {post_meta['title']} ({post_meta.get('published_at', 'No date')})")
        except Exception as e:
            print(f"Error listing posts: {e}")
            
        # Create index.html after storing posts
        try:
            store.create_index_html()
            print("\nCreated index.html in data directory")
        except Exception as e:
            print(f"Error creating index: {e}")
            
    except Exception as e:
        print(f"Error processing {url}: {e}")

# Monitor all newsletters
for substack_url in science_substacks:
    store_newsletter_posts(substack_url)
