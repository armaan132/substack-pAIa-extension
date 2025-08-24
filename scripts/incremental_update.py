#!/usr/bin/env python3
"""
Incremental Update Script for Daily Briefing pAIa

This script performs incremental updates to the newsletter data:
1. Detects new sources from newsletter.md changes
2. Fetches new posts from existing sources
3. Preserves all existing data and personalization
4. Maintains an append-only log structure

Usage: python scripts/incremental_update.py
"""

import json
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
import requests
from urllib.parse import urlparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.web.index_generator import IndexGenerator

class IncrementalUpdater:
    """Handles incremental updates while preserving existing data."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = project_root / "data"
        else:
            self.base_dir = Path(base_dir)
        
        self.metadata_dir = self.base_dir / "metadata"
        self.content_dir = self.base_dir / "content"
        self.index_path = self.base_dir / "index.json"
        self.newsletter_md_path = project_root / "config" / "newsletters.md"
        
        # Ensure directories exist
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_author_safely(self, metadata: Dict) -> str:
        """Safely extract author information from post metadata."""
        try:
            published_bylines = metadata.get('publishedBylines')
            if published_bylines and isinstance(published_bylines, list) and len(published_bylines) > 0:
                first_byline = published_bylines[0]
                if isinstance(first_byline, dict) and 'name' in first_byline:
                    return first_byline['name']
            return 'Unknown Author'
        except Exception as e:
            print(f"    🔍 Debug: Author extraction error: {e}")
            return 'Unknown Author'
    
    def get_newsletter_md_hash(self) -> str:
        """Get hash of newsletter.md to detect changes."""
        if not self.newsletter_md_path.exists():
            return ""
        
        content = self.newsletter_md_path.read_text(encoding='utf-8')
        return hashlib.md5(content.encode()).hexdigest()
    
    def load_existing_data(self) -> Dict:
        """Load existing index.json data."""
        if not self.index_path.exists():
            return {"newsletters": {}, "last_update": None, "newsletter_md_hash": None}
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading existing data: {e}")
            return {"newsletters": {}, "last_update": None, "newsletter_md_hash": None}
    
    def save_data(self, data: Dict) -> bool:
        """Save data to index.json."""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False
    
    def get_existing_urls(self, data: Dict) -> Set[str]:
        """Get set of existing newsletter URLs."""
        urls = set()
        for newsletter_data in data.get("newsletters", {}).values():
            if "url" in newsletter_data:
                urls.add(newsletter_data["url"])
        return urls
    
    def get_existing_post_urls(self, newsletter_url: str, data: Dict) -> Set[str]:
        """Get set of existing post URLs for a newsletter."""
        urls = set()
        for newsletter_data in data.get("newsletters", {}).values():
            if newsletter_data.get("url") == newsletter_url:
                for post in newsletter_data.get("posts", []):
                    if "url" in post:
                        urls.add(post["url"])
        return urls
    
    def detect_new_sources(self, current_newsletters: Dict, existing_urls: Set[str]) -> List[Dict]:
        """Detect new newsletter sources."""
        new_sources = []
        
        for url, newsletter_data in current_newsletters.items():
            if url not in existing_urls:
                new_sources.append(newsletter_data)
                print(f"🆕 New source detected: {newsletter_data['name']} ({url})")
        
        return new_sources
    
    def fetch_new_posts_from_source(self, newsletter_data: Dict, existing_post_urls: Set[str]) -> List[Dict]:
        """Fetch new posts from a source that aren't already stored."""
        url = newsletter_data['url']
        name = newsletter_data.get('name', url)
        
        print(f"📥 Checking for new posts from: {name}")
        
        try:
            # Import here to avoid circular imports
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            print(f"  🔍 Python path: {sys.path[-1]}")
            print(f"  🔍 Current working directory: {Path.cwd()}")
            
            try:
                from substack_api import Newsletter
                print(f"  ✅ Successfully imported substack_api.Newsletter")
            except ImportError as e:
                print(f"  ❌ Failed to import substack_api.Newsletter: {e}")
                raise
                
            try:
                from src.database.filesystem_store import NewsletterStore
                print(f"  ✅ Successfully imported NewsletterStore")
            except ImportError as e:
                print(f"  ❌ Failed to import NewsletterStore: {e}")
                raise
            
            newsletter = Newsletter(url)
            store = NewsletterStore(self.base_dir)
            
            # Get recent posts (limit to avoid overwhelming)
            recent_posts = newsletter.get_posts(limit=10)
            print(f"  Found {len(recent_posts)} recent posts")
            
            new_posts = []
            for post in recent_posts:
                post_url = post.url
                
                # Skip if we already have this post
                if post_url in existing_post_urls:
                    continue
                
                try:
                    # Get post metadata
                    metadata = post.get_metadata()
                    
                    # Save the post using the existing store
                    was_saved = store.save_post(url, post)
                    
                    if was_saved:
                        # Create post data structure compatible with our index
                        post_data = {
                            'url': post_url,
                            'newsletter_url': url,
                            'title': metadata.get('title', 'Unknown Title'),
                            'author': self._extract_author_safely(metadata),
                            'published_at': metadata.get('post_date'),
                            'word_count': metadata.get('wordcount', 0),
                            'content_path': str(self.content_dir / store._get_safe_name(url) / f"{post_url.split('/')[-1]}.html"),
                            'saved_at': datetime.now(timezone.utc).isoformat(),
                            'main_category': newsletter_data.get('main_category', 'Uncategorized'),
                            'subcategory': newsletter_data.get('subcategory', 'Uncategorized'),
                            'category': f"{newsletter_data.get('main_category', 'Uncategorized')} > {newsletter_data.get('subcategory', 'Uncategorized')}",
                            # Initialize personalization fields
                            'read': False,
                            'like': False,
                            'hide': False,
                            'not_interesting': False
                        }
                        
                        new_posts.append(post_data)
                        print(f"  ➕ New post: {post_data['title']}")
                    else:
                        print(f"  ⏭️ Skipped (already exists): {metadata.get('title', 'Unknown')}")
                        
                except Exception as e:
                    print(f"  ❌ Error processing post: {e}")
                    continue
            
            print(f"  ✅ Added {len(new_posts)} new posts")
            return new_posts
            
        except ImportError:
            print(f"  ⚠️ substack_api not available, skipping {name}")
            return []
        except Exception as e:
            # Handle network-related errors gracefully
            error_str = str(e).lower()
            if any(error_type in error_str for error_type in 
                   ['connection', 'timeout', 'dns', 'name resolution', 'nodename', 'servname', 'max retries']):
                print(f"  🌐 Network error (newsletter may be down): {e}")
                print(f"  ⏭️ Skipping {name} - will retry next time")
                return []
            else:
                # Log other errors normally
                print(f"  ❌ Error fetching from {name}: {e}")
                return []
    
    def update_newsletter_data(self, newsletter_data: Dict, new_posts: List[Dict], existing_data: Dict) -> Dict:
        """Update newsletter data with new posts, preserving existing data."""
        newsletter_url = newsletter_data["url"]
        
        # Find existing newsletter data or create new
        if newsletter_url in existing_data.get("newsletters", {}):
            # Update existing newsletter
            existing_newsletter = existing_data["newsletters"][newsletter_url]
            existing_posts = existing_newsletter.get("posts", [])
            
            # Add new posts (avoiding duplicates)
            existing_post_urls = {post.get("url") for post in existing_posts if post.get("url")}
            
            for post in new_posts:
                if post.get("url") not in existing_post_urls:
                    existing_posts.append(post)
                    print(f"  ➕ Added new post: {post.get('title', 'Unknown')}")
            
            # Update metadata
            existing_newsletter.update({
                "name": newsletter_data["name"],
                "main_category": newsletter_data["main_category"],
                "subcategory": newsletter_data["subcategory"],
                "tags": newsletter_data.get("tags", []),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
            
            return existing_data
        else:
            # Create new newsletter entry
            if "newsletters" not in existing_data:
                existing_data["newsletters"] = {}
            
            existing_data["newsletters"][newsletter_url] = {
                "name": newsletter_data["name"],
                "url": newsletter_url,
                "main_category": newsletter_data["main_category"],
                "subcategory": newsletter_data["subcategory"],
                "tags": newsletter_data.get("tags", []),
                "posts": new_posts,
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return existing_data
    
    def run_incremental_update(self) -> bool:
        """Run the complete incremental update process."""
        print("🚀 Starting incremental update...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
        
        # Check if newsletter.md has changed
        current_hash = self.get_newsletter_md_hash()
        last_hash = existing_data.get("newsletter_md_hash")
        
        if current_hash == last_hash:
            print("📝 newsletter.md unchanged, checking for new posts from existing sources...")
        else:
            print("📝 newsletter.md changed, scanning for new sources...")
        
        # Load current newsletter configuration
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        print(f"📋 Current configuration: {len(current_newsletters)} newsletters")
        
        # Detect new sources
        existing_urls = self.get_existing_urls(existing_data)
        new_sources = self.detect_new_sources(current_newsletters, existing_urls)
        
        if new_sources:
            print(f"🆕 Found {len(new_sources)} new sources")
        else:
            print("✅ No new sources detected")
        
        # Process new sources
        for newsletter_data in new_sources:
            new_posts = self.fetch_new_posts_from_source(newsletter_data, set())
            existing_data = self.update_newsletter_data(newsletter_data, new_posts, existing_data)
        
        # Check existing sources for new posts
        print("\n📥 Checking existing sources for new posts...")
        for newsletter_data in current_newsletters.values():
            try:
                existing_post_urls = self.get_existing_post_urls(newsletter_data["url"], existing_data)
                new_posts = self.fetch_new_posts_from_source(newsletter_data, existing_post_urls)
                
                if new_posts:
                    existing_data = self.update_newsletter_data(newsletter_data, new_posts, existing_data)
            except Exception as e:
                print(f"❌ Error processing newsletter {newsletter_data.get('name', 'Unknown')}: {e}")
                # Continue with next newsletter instead of crashing
                continue
        
        # Update metadata
        existing_data["last_update"] = datetime.now(timezone.utc).isoformat()
        existing_data["newsletter_md_hash"] = current_hash
        
        # Save updated data
        if self.save_data(existing_data):
            print(f"💾 Data saved successfully")
            
            # Regenerate HTML
            print("🔄 Regenerating HTML...")
            index_generator.create_index_html()
            print("✅ HTML regenerated")
            
            return True
        else:
            print("❌ Failed to save data")
            return False

def main():
    """Main function."""
    updater = IncrementalUpdater()
    
    try:
        success = updater.run_incremental_update()
        if success:
            print("\n🎉 Incremental update completed successfully!")
        else:
            print("\n❌ Incremental update failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
