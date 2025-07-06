# https://github.com/NHagar/substack_api
import sys
import os
import yaml
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.filesystem_store import NewsletterStore
from substack_api import Newsletter

def load_newsletter_config(config_path: str = "config/newsletters.yaml"):
    """Load newsletter configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('newsletters', [])
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found. Using default newsletter.")
        return [{"name": "EconJared", "url": "https://econjared.substack.com", "limit": 3}]
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return []

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

def main():
    """Main function to process all configured newsletters."""
    newsletters = load_newsletter_config()
    
    if not newsletters:
        print("No newsletters configured. Please check config/newsletters.yaml")
        return
    
    print(f"Found {len(newsletters)} newsletter(s) to process")
    
    for newsletter_config in newsletters:
        store_newsletter_posts(newsletter_config)

if __name__ == "__main__":
    main()
