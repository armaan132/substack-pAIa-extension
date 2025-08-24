#!/usr/bin/env python3
"""
RSS-based content updater for Daily Briefing pAIa.
Uses RSS feeds for faster content discovery than the substack_api.
"""

import sys
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.filesystem_store import NewsletterStore


class RSSUpdater:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or project_root / "data"
        self.config_dir = project_root / "config"
        self.content_dir = self.base_dir / "content"
        self.index_path = self.base_dir / "index.json"
        self.newsletters_md_path = self.config_dir / "newsletters.md"
        
    def get_newsletter_md_hash(self) -> str:
        """Get hash of newsletters.md to detect changes."""
        if not self.newsletters_md_path.exists():
            return ""
        
        with open(self.newsletters_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def parse_newsletters_md(self) -> Dict[str, Dict]:
        """Parse newsletters.md file to get newsletter configurations."""
        newsletters = {}
        
        if not self.newsletters_md_path.exists():
            print(f"❌ newsletters.md not found at {self.newsletters_md_path}")
            return newsletters
        
        with open(self.newsletters_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        current_category = "Uncategorized"
        current_subcategory = "Uncategorized"
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('## '):
                current_category = line[3:].strip()
                current_subcategory = current_category
            elif line.startswith('### '):
                current_subcategory = line[4:].strip()
            elif line and not line.startswith('#'):
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    name = parts[0]
                    url_and_rest = parts[1].split(' ')
                    if url_and_rest:
                        url = url_and_rest[0]
                        if url.startswith('http'):
                            newsletters[url] = {
                                'name': name,
                                'url': url,
                                'main_category': current_category,
                                'subcategory': current_subcategory,
                                'tags': url_and_rest[1:] if len(url_and_rest) > 1 else []
                            }
        
        return newsletters
    
    def get_rss_url(self, newsletter_url: str) -> str:
        """Convert newsletter URL to RSS feed URL."""
        if newsletter_url.endswith('/'):
            newsletter_url = newsletter_url[:-1]
        
        # For Substack newsletters
        if '.substack.com' in newsletter_url:
            return f"{newsletter_url}/feed"
        
        # For other newsletters, try common RSS patterns
        possible_rss_urls = [
            f"{newsletter_url}/feed",
            f"{newsletter_url}/rss",
            f"{newsletter_url}/feed.xml",
            f"{newsletter_url}/rss.xml"
        ]
        
        return possible_rss_urls[0]  # Start with /feed
    
    def fetch_rss_posts(self, newsletter_url: str, newsletter_data: Dict) -> List[Dict]:
        """Fetch posts from RSS feed."""
        rss_url = self.get_rss_url(newsletter_url)
        newsletter_name = newsletter_data.get('name', newsletter_url)
        
        print(f"📡 Fetching RSS from: {newsletter_name}")
        print(f"  🔗 RSS URL: {rss_url}")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print(f"  ⚠️ No entries found in RSS feed")
                return []
            
            print(f"  📰 Found {len(feed.entries)} entries in RSS feed")
            
            posts = []
            for entry in feed.entries:
                try:
                    # Extract post data from RSS entry
                    post_data = {
                        'url': entry.get('link', ''),
                        'title': entry.get('title', 'Unknown Title'),
                        'author': entry.get('author', newsletter_name),
                        'published_at': self._parse_date(entry.get('published', '')),
                        'summary': entry.get('summary', ''),
                        'newsletter_url': newsletter_url,
                        'newsletter_name': newsletter_name,
                        'main_category': newsletter_data.get('main_category', 'Uncategorized'),
                        'subcategory': newsletter_data.get('subcategory', 'Uncategorized'),
                        'category': f"{newsletter_data.get('main_category', 'Uncategorized')} > {newsletter_data.get('subcategory', 'Uncategorized')}",
                        # Initialize personalization fields
                        'read': False,
                        'like': False,
                        'hide': False,
                        'not_interesting': False
                    }
                    
                    if post_data['url']:  # Only add posts with valid URLs
                        posts.append(post_data)
                    
                except Exception as e:
                    print(f"  ❌ Error processing RSS entry: {e}")
                    continue
            
            print(f"  ✅ Processed {len(posts)} valid posts from RSS")
            return posts
            
        except Exception as e:
            print(f"  ❌ Error fetching RSS from {newsletter_name}: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats from RSS feeds."""
        if not date_str:
            return None
        
        try:
            # feedparser usually handles date parsing automatically
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception:
            # Fallback: return as-is
            return date_str
    
    def download_post_content(self, post_url: str, newsletter_url: str, post_title: str) -> Optional[str]:
        """Download and save post content."""
        try:
            store = NewsletterStore(self.base_dir)
            
            # Create a minimal post object for the store
            class MockPost:
                def __init__(self, url, title):
                    self.url = url
                    self.title = title
                    self._content = None
                    
                def get_content(self):
                    if self._content is None:
                        # Download content
                        try:
                            response = requests.get(self.url, timeout=30)
                            response.raise_for_status()
                            self._content = response.text
                        except Exception as e:
                            print(f"    ⚠️ Could not download content: {e}")
                            self._content = f"<p>Content not available. <a href='{self.url}'>Read online</a></p>"
                    return self._content
                
                def get_metadata(self):
                    """Return metadata compatible with NewsletterStore."""
                    return {
                        'title': self.title,
                        'post_date': datetime.now(timezone.utc).isoformat(),
                        'wordcount': 0,
                        'publishedBylines': []  # Empty to avoid author extraction issues
                    }
                
                @property
                def content(self):
                    return self.get_content()
            
            mock_post = MockPost(post_url, post_title)
            was_saved = store.save_post(newsletter_url, mock_post)
            
            if was_saved:
                # Return the relative path to the saved content
                safe_name = store._get_safe_name(newsletter_url)
                filename = f"{post_url.split('/')[-1]}.html"
                return f"content/{safe_name}/{filename}"
            
        except Exception as e:
            print(f"    ❌ Error downloading content: {e}")
        
        return None
    
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
    
    def get_existing_post_urls(self, data: Dict) -> Set[str]:
        """Get set of all existing post URLs."""
        urls = set()
        for newsletter_data in data.get("newsletters", {}).values():
            for post in newsletter_data.get("posts", []):
                if "url" in post:
                    urls.add(post["url"])
        return urls
    
    def run_rss_update(self) -> bool:
        """Run the RSS-based update process."""
        print("🚀 Starting RSS-based update...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        existing_post_urls = self.get_existing_post_urls(existing_data)
        print(f"📊 Found {len(existing_post_urls)} existing posts")
        
        # Parse newsletters configuration
        newsletters = self.parse_newsletters_md()
        print(f"📝 Found {len(newsletters)} configured newsletters")
        
        total_new_posts = 0
        
        # Process each newsletter
        for newsletter_url, newsletter_data in newsletters.items():
            newsletter_name = newsletter_data['name']
            
            # Fetch posts from RSS
            rss_posts = self.fetch_rss_posts(newsletter_url, newsletter_data)
            
            if not rss_posts:
                continue
            
            # Filter out existing posts
            new_posts = []
            for post in rss_posts:
                if post['url'] not in existing_post_urls:
                    # Download content for new posts
                    print(f"  💾 Downloading content for: {post['title']}")
                    content_path = self.download_post_content(post['url'], newsletter_url, post['title'])
                    if content_path:
                        post['content_path'] = content_path
                        post['saved_at'] = datetime.now(timezone.utc).isoformat()
                        new_posts.append(post)
                        print(f"  ✅ Added: {post['title']}")
                    else:
                        print(f"  ⏭️ Skipped (download failed): {post['title']}")
                else:
                    print(f"  ⏭️ Skipped (already exists): {post['title']}")
            
            if new_posts:
                # Update existing data
                if newsletter_url not in existing_data.get("newsletters", {}):
                    existing_data.setdefault("newsletters", {})[newsletter_url] = {
                        "name": newsletter_name,
                        "url": newsletter_url,
                        "main_category": newsletter_data["main_category"],
                        "subcategory": newsletter_data["subcategory"],
                        "category": f"{newsletter_data['main_category']} > {newsletter_data['subcategory']}",
                        "tags": newsletter_data.get("tags", []),
                        "posts": [],
                        "first_seen": datetime.now(timezone.utc).isoformat()
                    }
                
                # Add new posts
                existing_data["newsletters"][newsletter_url]["posts"].extend(new_posts)
                existing_data["newsletters"][newsletter_url]["last_updated"] = datetime.now(timezone.utc).isoformat()
                
                total_new_posts += len(new_posts)
                print(f"  📈 Added {len(new_posts)} new posts for {newsletter_name}")
        
        # Update metadata
        existing_data["last_update"] = datetime.now(timezone.utc).isoformat()
        existing_data["newsletter_md_hash"] = self.get_newsletter_md_hash()
        
        # Save updated data
        if self.save_data(existing_data):
            print(f"✅ RSS update completed! Added {total_new_posts} new posts total")
            return True
        else:
            print("❌ Failed to save updated data")
            return False


if __name__ == "__main__":
    updater = RSSUpdater()
    success = updater.run_rss_update()
    sys.exit(0 if success else 1)
