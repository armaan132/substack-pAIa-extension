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
def get_project_root():
    """Get the project root directory, with fallback to current working directory."""
    # Try to get from __file__ location first
    file_based_root = Path(__file__).parent.parent.parent
    if (file_based_root / "data").exists():
        return file_based_root
    
    # Fallback to current working directory
    cwd = Path.cwd()
    if (cwd / "data").exists():
        return cwd
    
    # If neither works, use the file-based approach
    return file_based_root

project_root = get_project_root()
sys.path.append(str(project_root))

# Dynamic import to avoid circular import issues
import importlib.util
import sys
from pathlib import Path

# Get the path to index_generator.py
index_generator_path = Path(__file__).parent.parent / "index_generator.py"
spec = importlib.util.spec_from_file_location("index_generator", index_generator_path)
index_generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index_generator_module)
IndexGenerator = index_generator_module.IndexGenerator

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
            # Ensure data is sorted before saving
            sorted_data = self._sort_json_data(data.copy())
            
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2, ensure_ascii=False)
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
    
    def check_rss_timestamp_quick(self, newsletter_data: Dict) -> bool:
        """Quick check if RSS feed has been updated since last check."""
        url = newsletter_data['url']
        name = newsletter_data.get('name', url)
        
        try:
            import requests
            rss_url = f"{url.rstrip('/')}/feed"
            
            # Quick HEAD request to check if RSS has changed
            response = requests.head(rss_url, timeout=5)
            if response.status_code != 200:
                return False
                
            # Check last-modified header if available
            last_modified = response.headers.get('last-modified')
            if last_modified:
                # Parse the date and compare with last known update
                try:
                    from email.utils import parsedate_to_datetime
                    rss_date = parsedate_to_datetime(last_modified)
                    last_known = newsletter_data.get('last_rss_check')
                    if last_known:
                        from datetime import datetime
                        last_known_dt = datetime.fromisoformat(last_known.replace('Z', '+00:00'))
                        if rss_date <= last_known_dt:
                            return False  # RSS hasn't changed
                except Exception:
                    pass  # If date parsing fails, assume it might have changed
            
            return True  # RSS might have new content
            
        except Exception:
            return True  # If we can't check, assume it might have changed
    
    def batch_check_rss_timestamps(self, current_newsletters: Dict) -> Dict[str, bool]:
        """Batch check RSS timestamps for all newsletters to identify which ones need processing."""
        print("🔍 Quick RSS timestamp check for all newsletters...")
        
        results = {}
        active_count = 0
        
        for url, newsletter_data in current_newsletters.items():
            name = newsletter_data.get('name', url)
            is_active = self.check_rss_timestamp_quick(newsletter_data)
            results[url] = is_active
            if is_active:
                active_count += 1
        
        print(f"📊 RSS check complete: {active_count}/{len(current_newsletters)} newsletters may have new content")
        return results
    
    def fetch_new_posts_from_source_rss(self, newsletter_data: Dict, existing_post_urls: Set[str]) -> List[Dict]:
        """Fetch new posts using RSS feed (faster method with quick timestamp check)."""
        url = newsletter_data['url']
        name = newsletter_data.get('name', url)
        
        # Quick timestamp check first
        if not self.check_rss_timestamp_quick(newsletter_data):
            print(f"📡 RSS unchanged for: {name} - skipping")
            return []
        
        print(f"📡 Trying RSS for: {name}")
        
        try:
            import feedparser
            import requests
            
            # Convert to RSS URL
            rss_url = f"{url.rstrip('/')}/feed"
            
            # Parse RSS feed with timeout protection
            try:
                # Use requests with timeout to fetch RSS
                response = requests.get(rss_url, timeout=15)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
            except requests.exceptions.Timeout:
                print(f"  ⏰ RSS request timed out for {name}")
                return []
            except requests.exceptions.RequestException as e:
                print(f"  🌐 RSS request failed for {name}: {e}")
                return []
            
            if not feed.entries:
                print(f"  ⚠️ No RSS entries found, will try substack_api fallback")
                return self.fetch_new_posts_from_source_api(newsletter_data, existing_post_urls)
            
            print(f"  📰 Found {len(feed.entries)} RSS entries")
            
            # Debug: Show sample RSS entry structure
            if feed.entries:
                    sample = feed.entries[0]
                    print(f"    🔍 Sample RSS entry keys: {list(sample.keys())}")
                    print(f"    🔍 Sample published date: '{sample.get('published', 'NO_DATE')}'")
                    print(f"    🔍 Sample title: '{sample.get('title', 'NO_TITLE')}'")
                    
                    # Show all date-related fields for debugging
                    date_fields = ['published', 'pubDate', 'date', 'updated', 'lastBuildDate']
                    for field in date_fields:
                        if field in sample:
                            print(f"    🔍 {field}: '{sample[field]}'")
                    
                    # Show a few more entries to see date patterns
                    print(f"    🔍 Date samples from first 3 entries:")
                    for i, entry in enumerate(feed.entries[:3]):
                        date_val = entry.get('published', entry.get('pubDate', 'NO_DATE'))
                        print(f"      Entry {i+1}: '{date_val}' → {entry.get('title', 'NO_TITLE')[:50]}...")
            
            # Phase 1: Update JSON with RSS metadata (fast)
            new_posts = []
            for entry in feed.entries:
                try:
                    post_url = entry.get('link', '')
                    if not post_url:
                        print(f"  ⚠️ RSS entry missing link, skipping")
                        continue
                        
                    if post_url in existing_post_urls:
                        entry_title = entry.get('title', 'Unknown Title')
                        print(f"  ⏭️ Skipped (already in JSON): {entry_title}")
                        continue
                    
                    entry_title = entry.get('title', 'Unknown Title')
                    print(f"  📝 Adding to JSON: {entry_title}")
                    
                    # Create post data from RSS (metadata only)
                    raw_date = entry.get('published', '')
                    parsed_date = self._parse_rss_date(raw_date)
                    
                    # Robust author handling: use RSS author if available and meaningful, otherwise use newsletter name
                    rss_author = entry.get('author', '').strip()
                    if rss_author and rss_author.lower() not in ['', 'unknown', 'anonymous', 'none']:
                        author = rss_author
                        print(f"    👤 Using RSS author: '{rss_author}'")
                    else:
                        author = name
                        print(f"    👤 Using newsletter name: '{name}' (RSS author: '{rss_author}')")
                    
                    post_data = {
                        'url': post_url,
                        'newsletter_url': url,
                        'title': entry_title,
                        'author': author,
                        'published_at': parsed_date,
                        'word_count': 0,  # Not available from RSS
                        'content_path': '',  # Will be set after content check
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
                    print(f"  ✅ Added metadata to JSON: {post_data['title']}")
                    
                except Exception as e:
                    print(f"  ❌ Error processing RSS entry: {e}")
                    # Continue with next entry instead of crashing
                    continue
            
            # Phase 2: Check and download missing content (smart)
            if new_posts:
                print(f"  🔍 Checking local content for {len(new_posts)} new posts...")
                from src.database.filesystem_store import NewsletterStore
                store = NewsletterStore(self.base_dir)
                
                for post_data in new_posts:
                    try:
                        # Check if content already exists locally
                        safe_name = store._get_safe_name(url)
                        filename = f"{post_data['url'].split('/')[-1]}.html"
                        local_content_path = self.content_dir / safe_name / filename
                        
                        if local_content_path.exists():
                            print(f"    ⏭️ Content exists locally: {post_data['title']}")
                            post_data['content_path'] = str(local_content_path)
                        else:
                            print(f"    📥 Downloading missing content: {post_data['title']}")
                            # Download content using the existing store
                            class MockPost:
                                def __init__(self, url, title):
                                    self.url = url
                                    self.title = title
                                    self._content = None
                                    
                                def get_content(self):
                                    if self._content is None:
                                        try:
                                            response = requests.get(self.url, timeout=30)
                                            response.raise_for_status()
                                            self._content = response.text
                                        except Exception as e:
                                            print(f"      ⚠️ Could not download content: {e}")
                                            self._content = f"<p>Content not available. <a href='{self.url}'>Read online</a></p>"
                                    return self._content
                                
                                def get_metadata(self):
                                    return {
                                        'title': self.title,
                                        'post_date': post_data['published_at'],
                                        'wordcount': 0,
                                        'publishedBylines': []
                                    }
                                
                                @property
                                def content(self):
                                    return self.get_content()
                            
                            mock_post = MockPost(post_data['url'], post_data['title'])
                            was_saved = store.save_post(url, mock_post)
                            
                            if was_saved:
                                post_data['content_path'] = str(local_content_path)
                                
                                # Store content hash for future change detection
                                import hashlib
                                content = mock_post.get_content()
                                content_hash = hashlib.md5(content.encode()).hexdigest()
                                post_data['content_hash'] = content_hash
                                post_data['last_downloaded'] = datetime.now(timezone.utc).isoformat()
                                
                                print(f"    ✅ Content downloaded: {post_data['title']} (hash: {content_hash[:8]}...)")
                            else:
                                print(f"    ❌ Failed to save content: {post_data['title']}")
                    
                    except Exception as e:
                        print(f"    ❌ Error processing content for {post_data['title']}: {e}")
                        continue
            
            skipped_count = len(feed.entries) - len(new_posts)
            print(f"  📈 RSS: Added {len(new_posts)} posts to JSON, skipped {skipped_count} existing posts")
            return new_posts
            
        except ImportError:
            print(f"  ⚠️ feedparser not available, using substack_api fallback")
            return self.fetch_new_posts_from_source_api(newsletter_data, existing_post_urls)
        except Exception as e:
            print(f"  ❌ RSS failed for {name}: {e}")
            print(f"  🔄 Falling back to substack_api...")
            return self.fetch_new_posts_from_source_api(newsletter_data, existing_post_urls)
    
    def _parse_rss_date(self, date_str: str) -> str:
        """Parse RSS date format."""
        if not date_str:
            print(f"    ⚠️ No RSS date provided, using current date")
            return datetime.now(timezone.utc).isoformat()
        
        # Try multiple date parsing strategies
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            parsed_date = dt.isoformat()
            print(f"    📅 Parsed RSS date: {date_str} → {parsed_date}")
            return parsed_date
        except Exception as e:
            print(f"    ⚠️ email.utils parsing failed: '{date_str}' → {e}")
            
            # Try datetime.strptime with common RSS formats
            try:
                from datetime import datetime
                # Common RSS date formats
                formats = [
                    '%a, %d %b %Y %H:%M:%S %z',  # RFC 822
                    '%a, %d %b %Y %H:%M:%S %Z',  # RFC 822 with timezone name
                    '%d %b %Y %H:%M:%S %z',      # Without day name
                    '%d %b %Y %H:%M:%S %Z',      # Without day name, timezone name
                    '%Y-%m-%dT%H:%M:%S%z',      # ISO format with timezone
                    '%Y-%m-%dT%H:%M:%S',        # ISO format without timezone
                    '%Y-%m-%d %H:%M:%S',        # Space-separated ISO
                    '%Y-%m-%d',                 # Date only
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        parsed_date = dt.isoformat()
                        print(f"    📅 Parsed with format '{fmt}': {date_str} → {parsed_date}")
                        return parsed_date
                    except ValueError:
                        continue
                
                print(f"    ⚠️ All date formats failed for: '{date_str}'")
                
            except Exception as e2:
                print(f"    ⚠️ strptime parsing also failed: {e2}")
            
            print(f"    ⚠️ Using current date as fallback")
            return datetime.now(timezone.utc).isoformat()
    
    def fetch_new_posts_from_source_api(self, newsletter_data: Dict, existing_post_urls: Set[str]) -> List[Dict]:
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
                try:
                    # Robust post URL extraction with fallback
                    post_url = getattr(post, 'url', None)
                    if not post_url:
                        print(f"  ⚠️ Post missing URL, skipping")
                        continue
                    
                    # Robust title extraction with fallback
                    post_title = getattr(post, 'title', None)
                    if not post_title:
                        # Try to get title from metadata if available
                        try:
                            metadata = post.get_metadata()
                            post_title = metadata.get('title', 'Unknown Title')
                        except Exception:
                            post_title = 'Unknown Title'
                    
                    # Skip if we already have this post
                    if post_url in existing_post_urls:
                        print(f"  ⏭️ Skipped (already downloaded): {post_title}")
                        continue
                    
                    print(f"  📥 Downloading: {post_title}")
                    
                    # Get post metadata with error handling
                    try:
                        metadata = post.get_metadata()
                    except Exception as e:
                        print(f"  ⚠️ Could not get metadata for {post_title}: {e}")
                        metadata = {'title': post_title, 'post_date': None, 'wordcount': 0}
                    
                    # Save the post using the existing store
                    try:
                        was_saved = store.save_post(url, post)
                    except Exception as e:
                        print(f"  ❌ Failed to save post {post_title}: {e}")
                        continue
                    
                    if was_saved:
                        # Create post data structure compatible with our index
                        post_data = {
                            'url': post_url,
                            'newsletter_url': url,
                            'title': metadata.get('title', post_title),
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
                        
                        # Store content hash for future change detection
                        try:
                            import hashlib
                            content = post.get_content()
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            post_data['content_hash'] = content_hash
                            post_data['last_downloaded'] = datetime.now(timezone.utc).isoformat()
                            
                            new_posts.append(post_data)
                            print(f"  ➕ New post: {post_data['title']} (hash: {content_hash[:8]}...)")
                        except Exception as e:
                            print(f"  ⚠️ Could not get content hash for {post_title}: {e}")
                            # Still add the post without hash
                            new_posts.append(post_data)
                            print(f"  ➕ New post: {post_data['title']} (no hash)")
                    else:
                        print(f"  ⏭️ Skipped (already exists): {metadata.get('title', post_title)}")
                        
                except Exception as e:
                    print(f"  ❌ Error processing post: {e}")
                    # Continue with next post instead of crashing
                    continue
            
            skipped_count = len(recent_posts) - len(new_posts)
            print(f"  ✅ Downloaded {len(new_posts)} new posts, skipped {skipped_count} existing posts")
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
                # Log other errors normally but don't crash
                print(f"  ❌ Error fetching from {name}: {e}")
                print(f"  ⏭️ Skipping {name} - will retry next time")
                return []
    
    def update_newsletter_data(self, newsletter_data: Dict, new_posts: List[Dict], existing_data: Dict) -> Dict:
        """Update newsletter data with new posts, preserving existing data."""
        newsletter_url = newsletter_data["url"]
        
        # Debug: Check what's in newsletter_data
        print(f"🔍 Debug: newsletter_data keys: {list(newsletter_data.keys())}")
        print(f"🔍 Debug: newsletter_data['name'] = '{newsletter_data.get('name', 'MISSING')}'")
        print(f"🔍 Debug: newsletter_data['url'] = '{newsletter_data.get('url', 'MISSING')}'")
        
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
    
    def update_post_download_status(self, post_url: str, status: str = "downloaded") -> bool:
        """Update the download status of a post."""
        try:
            # Load current data
            existing_data = self.load_existing_data()
            
            # Find and update the post
            for newsletter in existing_data.get("newsletters", {}).values():
                for post in newsletter.get("posts", []):
                    if post.get("url") == post_url:
                        post["status"] = status
                        post["last_updated"] = datetime.now(timezone.utc).isoformat()
                        
                        # Update the pending downloads count
                        total_pending = 0
                        for n in existing_data.get("newsletters", {}).values():
                            for p in n.get("posts", []):
                                if p.get("status") == "pending_download":
                                    total_pending += 1
                        
                        existing_data["pending_downloads"] = total_pending
                        
                        # Save updated data
                        if self.save_data(existing_data):
                            print(f"✅ Updated post status: {post_url} → {status}")
                            return True
                        else:
                            print(f"❌ Failed to save data after status update")
                            return False
            
            print(f"⚠️ Post not found: {post_url}")
            return False
            
        except Exception as e:
            print(f"❌ Error updating post status: {e}")
            return False

    def add_new_newsletters(self, current_newsletters: Dict, existing_data: Dict) -> Dict:
        """Add new newsletters from newsletters.md that don't exist in current data."""
        print("🔄 Adding new newsletters from newsletters.md...")
        
        added_count = 0
        existing_urls = set(existing_data.get("newsletters", {}).keys())
        
        for url, newsletter_config in current_newsletters.items():
            if url not in existing_urls:
                # Create new newsletter entry
                new_newsletter = {
                    "name": newsletter_config["name"],
                    "url": url,
                    "main_category": newsletter_config["main_category"],
                    "subcategory": newsletter_config["subcategory"],
                    "category": newsletter_config["category"],
                    "tags": newsletter_config.get("tags", []),
                    "posts": [],  # No posts yet
                    "added_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                
                existing_data["newsletters"][url] = new_newsletter
                print(f"  ➕ Added new newsletter: {newsletter_config['name']} ({newsletter_config['main_category']})")
                added_count += 1
        
        if added_count > 0:
            print(f"✅ Added {added_count} new newsletters")
        else:
            print("✅ No new newsletters to add")
        
        return existing_data

    def update_existing_newsletter_metadata(self, current_newsletters: Dict, existing_data: Dict) -> Dict:
        """Update existing newsletter metadata when newsletters.md configuration changes."""
        print("🔄 Updating existing newsletter metadata from newsletters.md...")
        
        updated_count = 0
        for url, current_config in current_newsletters.items():
            if url in existing_data.get("newsletters", {}):
                existing_newsletter = existing_data["newsletters"][url]
                
                # Check if metadata has changed
                metadata_changed = False
                changes = []
                
                # Check name
                if existing_newsletter.get("name") != current_config["name"]:
                    old_name = existing_newsletter.get("name", "Unknown")
                    new_name = current_config["name"]
                    existing_newsletter["name"] = new_name
                    changes.append(f"name: '{old_name}' → '{new_name}'")
                    metadata_changed = True
                
                # Check main_category
                if existing_newsletter.get("main_category") != current_config["main_category"]:
                    old_category = existing_newsletter.get("main_category", "Unknown")
                    new_category = current_config["main_category"]
                    existing_newsletter["main_category"] = new_category
                    changes.append(f"main_category: '{old_category}' → '{new_category}'")
                    metadata_changed = True
                
                # Check subcategory
                if existing_newsletter.get("subcategory") != current_config["subcategory"]:
                    old_subcategory = existing_newsletter.get("subcategory", "Unknown")
                    new_subcategory = current_config["subcategory"]
                    existing_newsletter["subcategory"] = new_subcategory
                    changes.append(f"subcategory: '{old_subcategory}' → '{new_subcategory}'")
                    metadata_changed = True
                
                # Check tags
                current_tags = current_config.get("tags", [])
                existing_tags = existing_newsletter.get("tags", [])
                if set(current_tags) != set(existing_tags):
                    existing_newsletter["tags"] = current_tags
                    changes.append(f"tags: {existing_tags} → {current_tags}")
                    metadata_changed = True
                
                # Update category field (combination of main_category + subcategory)
                new_category = f"{current_config['main_category']} > {current_config['subcategory']}"
                if existing_newsletter.get("category") != new_category:
                    old_category = existing_newsletter.get("category", "Unknown")
                    existing_newsletter["category"] = new_category
                    changes.append(f"category: '{old_category}' → '{new_category}'")
                    metadata_changed = True
                
                # Update timestamp
                if metadata_changed:
                    existing_newsletter["last_updated"] = datetime.now(timezone.utc).isoformat()
                    print(f"  🔄 Updated metadata for {current_config['name']}: {', '.join(changes)}")
                    updated_count += 1
        
        if updated_count > 0:
            print(f"✅ Updated metadata for {updated_count} existing newsletters")
        else:
            print("✅ No existing newsletter metadata changes detected")
        
        return existing_data

    def update_post_metadata_for_category_changes(self, existing_data: Dict) -> Dict:
        """Update post metadata when newsletter categories change."""
        print("🔄 Updating post metadata for category changes...")
        
        updated_posts = 0
        for newsletter_url, newsletter_data in existing_data.get("newsletters", {}).items():
            main_category = newsletter_data.get("main_category")
            subcategory = newsletter_data.get("subcategory")
            category = f"{main_category} > {subcategory}"
            
            for post in newsletter_data.get("posts", []):
                post_updated = False
                
                # Update main_category if it changed
                if post.get("main_category") != main_category:
                    post["main_category"] = main_category
                    post_updated = True
                
                # Update subcategory if it changed
                if post.get("subcategory") != subcategory:
                    post["subcategory"] = subcategory
                    post_updated = True
                
                # Update category if it changed
                if post.get("category") != category:
                    post["category"] = category
                    post_updated = True
                
                if post_updated:
                    updated_posts += 1
        
        if updated_posts > 0:
            print(f"✅ Updated metadata for {updated_posts} posts")
        else:
            print("✅ No post metadata updates needed")
        
        return existing_data

    def handle_removed_newsletters(self, current_newsletters: Dict, existing_data: Dict) -> Dict:
        """Remove newsletters that are no longer in newsletters.md."""
        print("🔍 Checking for removed newsletters...")
        
        current_urls = set(current_newsletters.keys())
        existing_urls = set(existing_data.get("newsletters", {}).keys())
        removed_urls = existing_urls - current_urls
        
        if removed_urls:
            print(f"🗑️ Found {len(removed_urls)} newsletters removed from newsletters.md:")
            for url in removed_urls:
                newsletter_name = existing_data["newsletters"][url].get("name", "Unknown")
                print(f"  ❌ Removing: {newsletter_name} ({url})")
                del existing_data["newsletters"][url]
            
            # Also remove any posts from these newsletters from the content directory
            for url in removed_urls:
                try:
                    safe_name = self._get_safe_newsletter_name(url)
                    newsletter_content_dir = self.content_dir / safe_name
                    if newsletter_content_dir.exists():
                        import shutil
                        shutil.rmtree(newsletter_content_dir)
                        print(f"    🗂️ Removed content directory: {newsletter_content_dir}")
                except Exception as e:
                    print(f"    ⚠️ Warning: Could not remove content directory for {url}: {e}")
        else:
            print("✅ No newsletters were removed from newsletters.md")
        
        return existing_data
    
    def detect_url_changes(self, current_newsletters: Dict, existing_data: Dict) -> Dict:
        """Detect if any newsletters have changed URLs (redirects, moves, etc.)."""
        print("🔍 Checking for newsletter URL changes...")
        
        # Create a mapping of newsletter names to URLs for comparison
        current_name_to_url = {}
        for url, config in current_newsletters.items():
            name = config.get("name", "Unknown")
            current_name_to_url[name] = url
        
        existing_name_to_url = {}
        for url, config in existing_data.get("newsletters", {}).items():
            name = config.get("name", "Unknown")
            existing_name_to_url[name] = url
        
        # Find newsletters that might have moved URLs
        moved_newsletters = []
        for name, current_url in current_name_to_url.items():
            if name in existing_name_to_url:
                existing_url = existing_name_to_url[name]
                if current_url != existing_url:
                    moved_newsletters.append({
                        'name': name,
                        'old_url': existing_url,
                        'new_url': current_url
                    })
        
        if moved_newsletters:
            print(f"🔄 Found {len(moved_newsletters)} newsletters with URL changes:")
            for move in moved_newsletters:
                print(f"  🔄 {move['name']}: {move['old_url']} → {move['new_url']}")
                
                # Update the URL in existing data
                old_url = move['old_url']
                new_url = move['new_url']
                
                if old_url in existing_data["newsletters"]:
                    # Move the newsletter data to the new URL
                    existing_data["newsletters"][new_url] = existing_data["newsletters"][old_url]
                    existing_data["newsletters"][new_url]["url"] = new_url
                    existing_data["newsletters"][new_url]["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Remove the old entry
                    del existing_data["newsletters"][old_url]
                    
                    print(f"    ✅ Updated URL for {move['name']}")
        else:
            print("✅ No newsletter URL changes detected")
        
        return existing_data
    
    def _get_safe_newsletter_name(self, url: str) -> str:
        """Get a safe directory name for a newsletter URL."""
        # Extract domain name and clean it for filesystem use
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        return domain

    def regenerate_category_index(self, existing_data: Dict) -> Dict:
        """Regenerate the category-subcategory index from current newsletters.md configuration."""
        print("🔄 Regenerating category-subcategory index from newsletters.md...")
        
        # Build category-subcategory index from current newsletters.md configuration (not existing data)
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        
        category_index = {}
        for newsletter_data in current_newsletters.values():
            main_category = newsletter_data.get('main_category')
            subcategory = newsletter_data.get('subcategory')
            
            if main_category:
                if main_category not in category_index:
                    category_index[main_category] = set()
                
                # Add subcategory if it exists and is different from main category
                if subcategory and subcategory != main_category:
                    category_index[main_category].add(subcategory)
        
        # Convert sets to sorted lists for JSON serialization
        for main_category, subcategories in category_index.items():
            category_index[main_category] = sorted(list(subcategories))
        
        # Update the categories in existing_data
        existing_data["categories"] = category_index
        
        print(f"✅ Category index regenerated: {len(category_index)} main categories")
        for main_cat, subcats in category_index.items():
            print(f"  📂 {main_cat}: {len(subcats)} subcategories")
        
        return existing_data
    
    def _sort_json_data(self, data: Dict) -> Dict:
        """Sort JSON data for consistent ordering: newsletters alphabetically, posts chronologically."""
        if "newsletters" not in data:
            return data
        
        # Sort newsletters alphabetically by URL
        sorted_newsletters = {}
        for url in sorted(data["newsletters"].keys()):
            newsletter_data = data["newsletters"][url].copy()
            
            # Sort posts chronologically (newest first)
            if "posts" in newsletter_data:
                posts = newsletter_data["posts"]
                # Sort by published_at, handling missing dates
                posts.sort(
                    key=lambda x: x.get('published_at', '') or '1970-01-01',
                    reverse=True  # Newest first
                )
                newsletter_data["posts"] = posts
            
            sorted_newsletters[url] = newsletter_data
        
        data["newsletters"] = sorted_newsletters
        return data
    
    def _validate_content_consistency(self, existing_data: Dict) -> List[Dict]:
        """Check for posts in JSON that have missing content files."""
        orphaned_posts = []
        
        for newsletter_url, newsletter_data in existing_data.get("newsletters", {}).items():
            for post in newsletter_data.get("posts", []):
                content_path = post.get('content_path', '')
                if content_path and not Path(content_path).exists():
                    orphaned_posts.append({
                        'post': post,
                        'newsletter_url': newsletter_url,
                        'newsletter_data': newsletter_data
                    })
        
        return orphaned_posts
    
    def _restore_orphaned_content(self, orphaned_posts: List[Dict], existing_data: Dict) -> None:
        """Re-download content for posts with missing content files."""
        from src.database.filesystem_store import NewsletterStore
        store = NewsletterStore(self.base_dir)
        
        for orphan_info in orphaned_posts:
            post = orphan_info['post']
            newsletter_url = orphan_info['newsletter_url']
            
            try:
                print(f"  📥 Re-downloading: {post.get('title', 'Unknown')}")
                
                # Create mock post for download
                class MockPost:
                    def __init__(self, url, title):
                        self.url = url
                        self.title = title
                        self._content = None
                        
                    def get_content(self):
                        if self._content is None:
                            try:
                                response = requests.get(self.url, timeout=30)
                                response.raise_for_status()
                                self._content = response.text
                            except Exception as e:
                                print(f"    ⚠️ Could not download content: {e}")
                                self._content = f"<p>Content not available. <a href='{self.url}'>Read online</a></p>"
                        return self._content
                    
                    def get_metadata(self):
                        return {
                            'title': self.title,
                            'post_date': post.get('published_at', ''),
                            'wordcount': 0,
                            'publishedBylines': []
                        }
                    
                    @property
                    def content(self):
                        return self.get_content()
                
                mock_post = MockPost(post['url'], post.get('title', 'Unknown'))
                was_saved = store.save_post(newsletter_url, mock_post)
                
                if was_saved:
                    # Update the content_path in the existing data
                    safe_name = store._get_safe_name(newsletter_url)
                    filename = f"{post['url'].split('/')[-1]}.html"
                    new_content_path = str(self.content_dir / safe_name / filename)
                    
                    # Store content hash for future change detection
                    import hashlib
                    content = mock_post.get_content()
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Find and update the post in existing_data
                    for existing_newsletter in existing_data.get("newsletters", {}).values():
                        for existing_post in existing_newsletter.get("posts", []):
                            if existing_post.get('url') == post['url']:
                                existing_post['content_path'] = new_content_path
                                existing_post['content_hash'] = content_hash
                                existing_post['last_downloaded'] = datetime.now(timezone.utc).isoformat()
                                break
                    
                    print(f"    ✅ Content restored: {post.get('title', 'Unknown')} (hash: {content_hash[:8]}...)")
                else:
                    print(f"    ❌ Failed to restore content: {post.get('title', 'Unknown')}")
                    
            except Exception as e:
                print(f"    ❌ Error restoring content for {post.get('title', 'Unknown')}: {e}")
                continue
    
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
            new_posts = self.fetch_new_posts_from_source_rss(newsletter_data, set())
            existing_data = self.update_newsletter_data(newsletter_data, new_posts, existing_data)
        
        # If newsletters.md changed, update existing newsletter metadata and regenerate category index
        if current_hash != last_hash:
            print("\n📝 newsletters.md changed - updating existing newsletter metadata...")
            existing_data = self.update_existing_newsletter_metadata(current_newsletters, existing_data)
            existing_data = self.update_post_metadata_for_category_changes(existing_data)
            existing_data = self.handle_removed_newsletters(current_newsletters, existing_data)
            existing_data = self.detect_url_changes(current_newsletters, existing_data) # Added this line
            existing_data = self.regenerate_category_index(existing_data)
            
            # Show summary of changes
            self.summarize_metadata_changes(current_newsletters, existing_data)
            
            # Validate newsletter coverage
            self.validate_newsletter_coverage(current_newsletters, existing_data)
        
        # Check existing sources for new posts
        print("\n📥 Checking existing sources for new posts...")
        
        # Quick batch RSS timestamp check to identify active newsletters
        active_newsletters = self.batch_check_rss_timestamps(current_newsletters)
        
        # Count active newsletters for progress tracking
        active_count = sum(1 for is_active in active_newsletters.values() if is_active)
        processed_count = 0
        
        print(f"🚀 Processing {active_count} active newsletters...")
        
        for newsletter_data in current_newsletters.values():
            newsletter_url = newsletter_data["url"]
            
            # Skip newsletters that haven't updated their RSS
            if not active_newsletters.get(newsletter_url, True):
                print(f"⏭️ Skipping {newsletter_data.get('name', 'Unknown')} - RSS unchanged")
                continue
                
            processed_count += 1
            print(f"📊 Progress: {processed_count}/{active_count} - Processing {newsletter_data.get('name', 'Unknown')}")
                
            try:
                existing_post_urls = self.get_existing_post_urls(newsletter_url, existing_data)
                new_posts = self.fetch_new_posts_from_source_rss(newsletter_data, existing_post_urls)
                
                if new_posts:
                    existing_data = self.update_newsletter_data(newsletter_data, new_posts, existing_data)
                
                # Update RSS check timestamp
                if newsletter_url in existing_data.get("newsletters", {}):
                    existing_data["newsletters"][newsletter_url]["last_rss_check"] = datetime.now(timezone.utc).isoformat()
                    
            except Exception as e:
                print(f"❌ Error processing newsletter {newsletter_data.get('name', 'Unknown')}: {e}")
                print(f"⏭️ Continuing with next newsletter...")
                # Continue with next newsletter instead of crashing
                continue
        
        # Update metadata
        existing_data["last_update"] = datetime.now(timezone.utc).isoformat()
        existing_data["newsletter_md_hash"] = current_hash
        
        # Content validation phase: Check for orphaned JSON entries
        print("\n🔍 Validating content consistency...")
        orphaned_posts = self._validate_content_consistency(existing_data)
        if orphaned_posts:
            print(f"⚠️ Found {len(orphaned_posts)} posts with missing content files")
            print("🔄 Re-downloading orphaned content...")
            self._restore_orphaned_content(orphaned_posts, existing_data)
        
        # Sort JSON data for consistent ordering
        print("\n📊 Sorting JSON data for consistent ordering...")
        existing_data = self._sort_json_data(existing_data)
        
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

    def run_fast_metadata_update(self) -> bool:
        """Run only the fast metadata update operations (no content fetching)."""
        print("⚡ Starting fast metadata update (configuration changes only)...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
        
        # Check if newsletter.md has changed
        current_hash = self.get_newsletter_md_hash()
        last_hash = existing_data.get("newsletter_md_hash")
        
        if current_hash == last_hash:
            print("📝 newsletter.md unchanged - no metadata updates needed")
            return True
        
        print("📝 newsletter.md changed - updating metadata...")
        
        # Load current newsletter configuration
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        print(f"📋 Current configuration: {len(current_newsletters)} newsletters")
        
        # Run all fast metadata operations
        print("\n🔄 Processing metadata changes...")
        
        # 1. Update existing newsletter metadata
        existing_data = self.update_existing_newsletter_metadata(current_newsletters, existing_data)
        
        # 2. Update post metadata for category changes
        existing_data = self.update_post_metadata_for_category_changes(existing_data)
        
        # 3. Handle removed newsletters
        existing_data = self.handle_removed_newsletters(current_newsletters, existing_data)
        
        # 4. Detect URL changes
        existing_data = self.detect_url_changes(current_newsletters, existing_data)
        
        # 5. Regenerate category index
        existing_data = self.regenerate_category_index(existing_data)
        
        # 6. Show summary of changes
        self.summarize_metadata_changes(current_newsletters, existing_data)
        
        # 7. Validate newsletter coverage
        self.validate_newsletter_coverage(current_newsletters, existing_data)
        
        # Update the hash to reflect current state
        existing_data["newsletter_md_hash"] = current_hash
        existing_data["last_metadata_update"] = datetime.now(timezone.utc).isoformat()
        
        # Sort JSON data for consistent ordering
        print("\n📊 Sorting JSON data for consistent ordering...")
        existing_data = self._sort_json_data(existing_data)
        
        # Save updated data
        if self.save_data(existing_data):
            print(f"💾 Data saved successfully")
            
            # Regenerate HTML
            print("🔄 Regenerating HTML...")
            index_generator.create_index_html()
            print("✅ HTML regenerated")
            
            print("\n⚡ Fast metadata update completed successfully!")
            return True
        else:
            print("❌ Failed to save data")
            return False

    def run_pure_config_update(self) -> bool:
        """Run only the pure configuration updates (fastest tier)."""
        print("⚡ Starting pure configuration update (newsletter structure only)...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
        
        # Load current newsletter configuration
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        print(f"📋 Current configuration: {len(current_newsletters)} newsletters")
        
        # Run only pure configuration operations
        print("\n🔄 Processing configuration changes...")
        
        # 1. Add new newsletters from newsletters.md
        existing_data = self.add_new_newsletters(current_newsletters, existing_data)
        
        # 2. Update existing newsletter metadata (structure only)
        existing_data = self.update_existing_newsletter_metadata(current_newsletters, existing_data)
        
        # 3. Handle removed newsletters
        existing_data = self.handle_removed_newsletters(current_newsletters, existing_data)
        
        # 4. Detect URL changes
        existing_data = self.detect_url_changes(current_newsletters, existing_data)
        
        # 5. Regenerate category index
        existing_data = self.regenerate_category_index(existing_data)
        
        # 5. Show summary of changes
        self.summarize_metadata_changes(current_newsletters, existing_data)
        
        # 6. Validate newsletter coverage
        self.validate_newsletter_coverage(current_newsletters, existing_data)
        
        # Update the hash to reflect current state
        current_hash = self.get_newsletter_md_hash()
        existing_data["newsletter_md_hash"] = current_hash
        existing_data["last_config_update"] = datetime.now(timezone.utc).isoformat()
        
        # Sort JSON data for consistent ordering
        print("\n📊 Sorting JSON data for consistent ordering...")
        existing_data = self._sort_json_data(existing_data)
        
        # Save updated data
        if self.save_data(existing_data):
            print(f"💾 Configuration data saved successfully")
            
            # Regenerate HTML to show new categories
            print("🔄 Regenerating HTML to show new categories...")
            index_generator = IndexGenerator(self.base_dir)
            index_generator.create_index_html()
            print("✅ HTML regenerated with new categories")
            
            print("\n⚡ Pure configuration update completed successfully!")
            print("📝 Note: Post metadata will be updated separately")
            return True
        else:
            print("❌ Failed to save configuration data")
            return False

    def run_structure_update(self) -> bool:
        """Run structure updates including post metadata and HTML (medium tier)."""
        print("🔄 Starting structure update (configuration + post metadata + HTML)...")
        
        # First run pure configuration update
        if not self.run_pure_config_update():
            print("❌ Pure configuration update failed - aborting structure update")
            return False
        
        print("\n🔄 Now updating post metadata and HTML structure...")
        
        # Load the updated data
        existing_data = self.load_existing_data()
        
        # Update post metadata for category changes
        existing_data = self.update_post_metadata_for_category_changes(existing_data)
        
        # Update the timestamp
        existing_data["last_structure_update"] = datetime.now(timezone.utc).isoformat()
        
        # Save updated data
        if self.save_data(existing_data):
            print(f"💾 Structure data saved successfully")
            
            # Regenerate HTML
            print("🔄 Regenerating HTML...")
            index_generator = IndexGenerator(self.base_dir)
            index_generator.create_index_html()
            print("✅ HTML regenerated")
            
            print("\n🔄 Structure update completed successfully!")
            print("📝 Note: New content will be fetched separately")
            return True
        else:
            print("❌ Failed to save structure data")
            return False

    def summarize_metadata_changes(self, current_newsletters: Dict, existing_data: Dict) -> None:
        """Summarize all metadata changes made during the update."""
        print("\n📊 Metadata Change Summary:")
        print("=" * 50)
        
        # Count newsletters by category
        category_counts = {}
        for newsletter_data in existing_data.get("newsletters", {}).values():
            main_cat = newsletter_data.get("main_category", "Unknown")
            sub_cat = newsletter_data.get("subcategory", "Unknown")
            
            if main_cat not in category_counts:
                category_counts[main_cat] = {}
            if sub_cat not in category_counts[main_cat]:
                category_counts[main_cat][sub_cat] = 0
            category_counts[main_cat][sub_cat] += 1
        
        # Display summary
        total_newsletters = len(existing_data.get("newsletters", {}))
        total_posts = sum(len(n.get("posts", [])) for n in existing_data.get("newsletters", {}).values())
        
        print(f"📈 Total Newsletters: {total_newsletters}")
        print(f"📄 Total Posts: {total_posts}")
        print(f"📂 Main Categories: {len(category_counts)}")
        
        for main_cat, subcats in sorted(category_counts.items()):
            print(f"  📁 {main_cat}: {len(subcats)} subcategories")
            for sub_cat, count in sorted(subcats.items()):
                print(f"    📄 {sub_cat}: {count} newsletters")
        
        print("=" * 50)

    def validate_newsletter_coverage(self, current_newsletters: Dict, existing_data: Dict) -> None:
        """Validate that all newsletters from newsletters.md are properly represented in existing data."""
        print("🔍 Validating newsletter coverage...")
        
        current_urls = set(current_newsletters.keys())
        existing_urls = set(existing_data.get("newsletters", {}).keys())
        
        missing_urls = current_urls - existing_urls
        extra_urls = existing_urls - current_urls
        
        if missing_urls:
            print(f"⚠️ Warning: {len(missing_urls)} newsletters from newsletters.md are missing from existing data:")
            for url in missing_urls:
                name = current_newsletters[url].get("name", "Unknown")
                print(f"  ❌ Missing: {name} ({url})")
        else:
            print("✅ All newsletters from newsletters.md are present in existing data")
        
        if extra_urls:
            print(f"ℹ️ Info: {len(extra_urls)} newsletters in existing data are not in newsletters.md:")
            for url in extra_urls:
                name = existing_data["newsletters"][url].get("name", "Unknown")
                print(f"  ℹ️ Extra: {name} ({url})")
        
        # Check for any newsletters with missing required fields
        invalid_newsletters = []
        for url, newsletter_data in existing_data.get("newsletters", {}).items():
            required_fields = ["name", "main_category", "subcategory"]
            missing_fields = [field for field in required_fields if not newsletter_data.get(field)]
            
            if missing_fields:
                invalid_newsletters.append({
                    'url': url,
                    'name': newsletter_data.get("name", "Unknown"),
                    'missing_fields': missing_fields
                })
        
        if invalid_newsletters:
            print(f"⚠️ Warning: {len(invalid_newsletters)} newsletters have missing required fields:")
            for invalid in invalid_newsletters:
                print(f"  ⚠️ {invalid['name']} ({invalid['url']}): missing {', '.join(invalid['missing_fields'])}")
        else:
            print("✅ All newsletters have required metadata fields")

    def run_fast_link_discovery(self) -> bool:
        """Run fast link discovery - add new posts immediately without content download."""
        print("🚀 Starting fast link discovery (new posts without content download)...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
        
        # Load current newsletter configuration
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        print(f"📋 Current configuration: {len(current_newsletters)} newsletters")
        
        # Quick RSS check for new post URLs only (no content download)
        print("\n🔍 Checking RSS feeds for new post URLs...")
        
        new_posts_found = 0
        for newsletter_url, newsletter_data in current_newsletters.items():
            try:
                # Get existing post URLs for this newsletter
                existing_posts = []
                for newsletter_entry in existing_data.get("newsletters", {}).values():
                    if newsletter_entry.get("url") == newsletter_url:
                        existing_posts = newsletter_entry.get("posts", [])
                        break
                
                existing_urls = {post.get("url") for post in existing_posts if post.get("url")}
                
                # Quick RSS check for new URLs only
                rss_url = f"{newsletter_url.rstrip('/')}/feed"
                response = requests.get(rss_url, timeout=10)
                
                if response.status_code != 200:
                    print(f"  ⚠️ RSS feed not accessible for {newsletter_data.get('name', 'Unknown')}: {response.status_code}")
                    continue
                
                # Parse RSS for new URLs
                import feedparser
                feed = feedparser.parse(response.content)
                
                new_posts = []
                for entry in feed.entries[:10]:  # Check last 10 entries
                    post_url = entry.get("link")
                    if post_url and post_url not in existing_urls:
                        # Create placeholder post data
                        new_post = {
                            "title": entry.get("title", "Unknown Title"),
                            "url": post_url,
                            "published_at": entry.get("published", ""),
                            "author": newsletter_data.get("name", "Unknown Author"),
                            "content_path": "",  # Will be filled during download
                            "main_category": newsletter_data.get("main_category", "Unknown"),
                            "subcategory": newsletter_data.get("subcategory", "Unknown"),
                            "category": newsletter_data.get("category", "Unknown"),
                            "tags": newsletter_data.get("tags", []),
                            "read": False,
                            "like": False,
                            "hide": False,
                            "not_interesting": False,
                            "status": "pending_download",  # New field
                            "discovered_at": datetime.now(timezone.utc).isoformat()
                        }
                        new_posts.append(new_post)
                
                if new_posts:
                    # Add new posts to existing data immediately
                    existing_data = self.add_new_posts_fast(newsletter_url, new_posts, existing_data)
                    new_posts_found += len(new_posts)
                    print(f"  ➕ Added {len(new_posts)} new posts for {newsletter_data.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"  ⚠️ Error checking {newsletter_data.get('name', 'Unknown')}: {e}")
                continue
        
        if new_posts_found > 0:
            # Update timestamps
            existing_data["last_link_discovery"] = datetime.now(timezone.utc).isoformat()
            
            # Calculate actual pending downloads instead of accumulating
            total_pending = 0
            for newsletter in existing_data.get("newsletters", {}).values():
                for post in newsletter.get("posts", []):
                    if post.get("status") == "pending_download":
                        total_pending += 1
            
            existing_data["pending_downloads"] = total_pending
            
            # Sort and save data
            existing_data = self._sort_json_data(existing_data)
            
            if self.save_data(existing_data):
                print(f"💾 Fast link discovery completed: {new_posts_found} new posts added")
                
                # Regenerate HTML immediately with new post links
                print("🔄 Regenerating HTML with new post links...")
                index_generator.create_index_html()
                print("✅ HTML regenerated - new posts visible immediately")
                
                # Start background download process
                self.start_background_downloads()
                
                return True
            else:
                print("❌ Failed to save data after link discovery")
                return False
        else:
            print("✅ No new posts found - no updates needed")
            return True
    
    def discover_new_post_urls_only(self, newsletter_url: str, newsletter_data: Dict, existing_data: Dict) -> List[Dict]:
        """Discover new post URLs from RSS without downloading content."""
        try:
            # Get existing post URLs for this newsletter
            existing_posts = []
            for newsletter in existing_data.get("newsletters", {}).values():
                if newsletter.get("url") == newsletter_url:
                    existing_posts = newsletter.get("posts", [])
                    break
            
            existing_urls = {post.get("url") for post in existing_posts if post.get("url")}
            
            # Quick RSS check for new URLs only
            rss_url = f"{newsletter_url.rstrip('/')}/feed"
            response = requests.get(rss_url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Parse RSS for new URLs
            import feedparser
            feed = feedparser.parse(response.content)
            
            new_posts = []
            for entry in feed.entries[:10]:  # Check last 10 entries
                post_url = entry.get("link")
                if post_url and post_url not in existing_urls:
                    # Create placeholder post data
                    new_post = {
                        "title": entry.get("title", "Unknown Title"),
                        "url": post_url,
                        "published_at": entry.get("published", ""),
                        "author": newsletter_data.get("name", "Unknown Author"),
                        "content_path": "",  # Will be filled during download
                        "main_category": newsletter_data.get("main_category", "Unknown"),
                        "subcategory": newsletter_data.get("subcategory", "Unknown"),
                        "category": newsletter_data.get("category", "Unknown"),
                        "tags": newsletter_data.get("tags", []),
                        "read": False,
                        "like": False,
                        "hide": False,
                        "not_interesting": False,
                        "status": "pending_download",  # New field
                        "discovered_at": datetime.now(timezone.utc).isoformat()
                    }
                    new_posts.append(new_post)
            
            return new_posts
            
        except Exception as e:
            print(f"    ❌ Error discovering new posts for {newsletter_url}: {e}")
            return []
    
    def add_new_posts_fast(self, newsletter_url: str, new_posts: List[Dict], existing_data: Dict) -> Dict:
        """Add new posts to existing data structure immediately."""
        # Find the newsletter in existing data
        for url, newsletter in existing_data.get("newsletters", {}).items():
            if url == newsletter_url:
                if "posts" not in newsletter:
                    newsletter["posts"] = []
                
                # Add new posts
                newsletter["posts"].extend(new_posts)
                
                # Update post count
                newsletter["post_count"] = len(newsletter["posts"])
                newsletter["last_updated"] = datetime.now(timezone.utc).isoformat()
                
                break
        
        return existing_data
    
    def start_background_downloads(self):
        """Start background content downloads for pending posts."""
        try:
            print("🔄 Starting background content downloads...")
            
            # Load current data
            existing_data = self.load_existing_data()
            
            # Find all posts with pending_download status
            pending_posts = []
            for newsletter_url, newsletter_data in existing_data.get("newsletters", {}).items():
                for post in newsletter_data.get("posts", []):
                    if post.get("status") == "pending_download":
                        pending_posts.append({
                            'newsletter_url': newsletter_url,
                            'post': post,
                            'post_index': existing_data["newsletters"][newsletter_url]["posts"].index(post)
                        })
            
            if not pending_posts:
                print("✅ No pending downloads found")
                return
            
            print(f"📥 Found {len(pending_posts)} posts to download")
            
            # Download content for each pending post
            for item in pending_posts:
                newsletter_url = item['newsletter_url']
                post = item['post']
                post_index = item['post_index']
                
                try:
                    print(f"📥 Downloading: {post.get('title', 'Unknown')}")
                    
                    # Download the post content
                    content_path = self._download_post_content(post['url'], newsletter_url)
                    
                    if content_path:
                        # Update the post status and content path
                        existing_data["newsletters"][newsletter_url]["posts"][post_index]["status"] = "downloaded"
                        existing_data["newsletters"][newsletter_url]["posts"][post_index]["content_path"] = str(content_path)
                        existing_data["newsletters"][newsletter_url]["posts"][post_index]["last_updated"] = datetime.now(timezone.utc).isoformat()
                        
                        print(f"✅ Downloaded: {post.get('title', 'Unknown')} -> {content_path}")
                    else:
                        print(f"❌ Failed to download: {post.get('title', 'Unknown')}")
                        
                except Exception as e:
                    print(f"❌ Error downloading {post.get('title', 'Unknown')}: {e}")
                    continue
            
            # Update the pending downloads count
            total_pending = 0
            for newsletter in existing_data.get("newsletters", {}).values():
                for post in newsletter.get("posts", []):
                    if post.get("status") == "pending_download":
                        total_pending += 1
            
            existing_data["pending_downloads"] = total_pending
            
            # Save updated data
            if self.save_data(existing_data):
                print(f"💾 Updated data saved. {total_pending} posts still pending download")
            else:
                print("❌ Failed to save updated data")
                
        except Exception as e:
            print(f"❌ Error in background downloads: {e}")
    
    def _clean_html_content(self, html_content: str, post_url: str) -> str:
        """Clean HTML content by removing JavaScript, external resources, and problematic elements."""
        try:
            from bs4 import BeautifulSoup
            import re
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove all script tags
            for script in soup.find_all('script'):
                script.decompose()
            
            # Remove all external CSS links (keep only inline styles)
            for link in soup.find_all('link', rel='stylesheet'):
                if link.get('href') and not link.get('href').startswith('#'):
                    link.decompose()
            
            # Remove external image sources that might cause issues
            for img in soup.find_all('img'):
                if img.get('src') and img.get('src').startswith('http'):
                    # Keep the image but make it local-friendly
                    img['src'] = '#'
                    img['alt'] = img.get('alt', 'Image') + ' (external)'
            
            # Remove external iframes
            for iframe in soup.find_all('iframe'):
                iframe.decompose()
            
            # Remove external embeds
            for embed in soup.find_all('embed'):
                embed.decompose()
            
            # Remove external objects
            for obj in soup.find_all('object'):
                obj.decompose()
            
            # Remove external video/audio sources
            for media in soup.find_all(['video', 'audio']):
                media.decompose()
            
            # Remove external fonts
            for font in soup.find_all('link', rel='preload'):
                if 'font' in font.get('as', ''):
                    font.decompose()
            
            # Remove external analytics and tracking
            for tag in soup.find_all(['noscript', 'meta']):
                if tag.get('name') in ['google-site-verification', 'norton-safeweb-site-verification']:
                    tag.decompose()
            
            # Add a simple header to indicate this is a cleaned local copy
            header_div = soup.new_tag('div')
            header_div['style'] = 'background: #f0f0f0; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;'
            header_div.string = f'📖 Local copy of: {post_url}'
            
            # Insert the header at the beginning of the body
            if soup.body:
                soup.body.insert(0, header_div)
            
            # Convert back to string
            return str(soup)
            
        except Exception as e:
            print(f"⚠️ Warning: Could not clean HTML content: {e}")
            # Return original content if cleaning fails
            return html_content
    
    def _download_post_content(self, post_url: str, newsletter_url: str) -> Optional[Path]:
        """Download the content of a single post."""
        try:
            # Create content directory for this newsletter
            newsletter_name = self._get_safe_newsletter_name(newsletter_url)
            content_dir = self.base_dir / "data" / "content" / newsletter_name
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from URL
            post_id = post_url.split('/')[-1]
            if not post_id or post_id == '':
                post_id = hashlib.md5(post_url.encode()).hexdigest()[:8]
            
            content_file = content_dir / f"{post_id}.html"
            
            # Check if already downloaded
            if content_file.exists():
                print(f"ℹ️ Content already exists: {content_file}")
                return content_file
            
            # Download the post content
            print(f"🌐 Fetching: {post_url}")
            
            # Use requests to fetch the content
            import requests
            from urllib.parse import urlparse
            
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(post_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Clean the content by stripping JavaScript and external resources
            cleaned_content = self._clean_html_content(response.text, post_url)
            
            # Save the cleaned content
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"💾 Saved content to: {content_file}")
            return content_file
            
        except Exception as e:
            print(f"❌ Error downloading post content: {e}")
            return None

    def get_accurate_pending_downloads_count(self) -> int:
        """Get the accurate count of posts that are actually pending download."""
        try:
            existing_data = self.load_existing_data()
            
            total_pending = 0
            for newsletter in existing_data.get("newsletters", {}).values():
                for post in newsletter.get("posts", []):
                    if post.get("status") == "pending_download":
                        total_pending += 1
            
            return total_pending
            
        except Exception as e:
            print(f"❌ Error getting pending downloads count: {e}")
            return 0

    def run_aggressive_link_discovery(self) -> bool:
        """Run aggressive link discovery using both RSS and substack API to find more recent posts."""
        print("🚀 Starting aggressive link discovery (RSS + Substack API)...")
        
        # Load existing data
        existing_data = self.load_existing_data()
        print(f"📊 Loaded existing data: {len(existing_data.get('newsletters', {}))} newsletters")
        
        # Load current newsletter configuration
        index_generator = IndexGenerator(self.base_dir)
        current_newsletters = index_generator.load_newsletters_with_categories()
        print(f"📋 Current configuration: {len(current_newsletters)} newsletters")
        
        new_posts_found = 0
        
        for newsletter_url, newsletter_data in current_newsletters.items():
            try:
                newsletter_name = newsletter_data.get('name', 'Unknown')
                print(f"\n🔍 Checking {newsletter_name} ({newsletter_url})...")
                
                # Get existing post URLs for this newsletter
                existing_posts = []
                for newsletter_entry in existing_data.get("newsletters", {}).values():
                    if newsletter_entry.get("url") == newsletter_url:
                        existing_posts = newsletter_entry.get("posts", [])
                        break
                
                existing_urls = {post.get("url") for post in existing_posts if post.get("url")}
                print(f"  📄 Found {len(existing_posts)} existing posts")
                
                # Method 1: Check RSS feed (fast)
                rss_posts = self._check_rss_for_new_posts(newsletter_url, newsletter_data, existing_urls)
                if rss_posts:
                    print(f"  📡 RSS: Found {len(rss_posts)} new posts")
                    existing_data = self.add_new_posts_fast(newsletter_url, rss_posts, existing_data)
                    new_posts_found += len(rss_posts)
                    existing_urls.update(post.get("url") for post in rss_posts)
                
                # Method 2: Check Substack API (more thorough)
                try:
                    api_posts = self._check_substack_api_for_new_posts(newsletter_url, newsletter_data, existing_urls)
                    if api_posts:
                        print(f"  🔌 API: Found {len(api_posts)} new posts")
                        existing_data = self.add_new_posts_fast(newsletter_url, api_posts, existing_data)
                        new_posts_found += len(api_posts)
                        existing_urls.update(post.get("url") for post in api_posts)
                except Exception as e:
                    print(f"  ⚠️ Substack API check failed: {e}")
                
            except Exception as e:
                print(f"  ❌ Error checking {newsletter_data.get('name', 'Unknown')}: {e}")
                continue
        
        if new_posts_found > 0:
            # Update timestamps
            existing_data["last_link_discovery"] = datetime.now(timezone.utc).isoformat()
            
            # Calculate actual pending downloads
            total_pending = 0
            for newsletter in existing_data.get("newsletters", {}).values():
                for post in newsletter.get("posts", []):
                    if post.get("status") == "pending_download":
                        total_pending += 1
            
            existing_data["pending_downloads"] = total_pending
            
            # Sort and save data
            existing_data = self._sort_json_data(existing_data)
            
            if self.save_data(existing_data):
                print(f"\n💾 Aggressive discovery completed: {new_posts_found} new posts found")
                
                # Regenerate HTML immediately
                print("🔄 Regenerating HTML with new post links...")
                index_generator.create_index_html()
                print("✅ HTML regenerated - new posts visible immediately")
                
                return True
            else:
                print("❌ Failed to save data after aggressive discovery")
                return False
        else:
            print("\n✅ No new posts found during aggressive discovery")
            return True
    
    def _check_rss_for_new_posts(self, newsletter_url: str, newsletter_data: Dict, existing_urls: Set[str]) -> List[Dict]:
        """Check RSS feed for new posts."""
        try:
            rss_url = f"{newsletter_url.rstrip('/')}/feed"
            response = requests.get(rss_url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            import feedparser
            feed = feedparser.parse(response.content)
            
            new_posts = []
            for entry in feed.entries[:15]:  # Check last 15 entries instead of 10
                post_url = entry.get("link")
                if post_url and post_url not in existing_urls:
                    new_post = {
                        "title": entry.get("title", "Unknown Title"),
                        "url": post_url,
                        "published_at": entry.get("published", ""),
                        "author": newsletter_data.get("name", "Unknown Author"),
                        "content_path": "",
                        "main_category": newsletter_data.get("main_category", "Unknown"),
                        "subcategory": newsletter_data.get("subcategory", "Unknown"),
                        "category": newsletter_data.get("category", "Unknown"),
                        "tags": newsletter_data.get("tags", []),
                        "read": False,
                        "like": False,
                        "hide": False,
                        "not_interesting": False,
                        "status": "pending_download",
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "source": "rss"
                    }
                    new_posts.append(new_post)
            
            return new_posts
            
        except Exception as e:
            print(f"    ⚠️ RSS check failed: {e}")
            return []
    
    def _check_substack_api_for_new_posts(self, newsletter_url: str, newsletter_data: Dict, existing_urls: Set[str]) -> List[Dict]:
        """Check Substack API for new posts."""
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path
            
            project_root = Path(__file__).parent.parent.parent
            scripts_dir = project_root / "scripts"
            
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            try:
                from substack_api import Newsletter
            except ImportError:
                print(f"    ⚠️ substack_api not available, skipping API check")
                return []
            
            newsletter = Newsletter(newsletter_url)
            
            # Get more posts from API (limit 20 instead of 10)
            recent_posts = newsletter.get_posts(limit=20)
            
            new_posts = []
            for post in recent_posts:
                try:
                    post_url = getattr(post, 'url', None)
                    if not post_url or post_url in existing_urls:
                        continue
                    
                    post_title = getattr(post, 'title', 'Unknown Title')
                    
                    # Get metadata if available
                    try:
                        metadata = post.get_metadata()
                        post_date = metadata.get('post_date', '')
                    except Exception:
                        post_date = ''
                    
                    new_post = {
                        "title": post_title,
                        "url": post_url,
                        "published_at": post_date,
                        "author": newsletter_data.get("name", "Unknown Author"),
                        "content_path": "",
                        "main_category": newsletter_data.get("main_category", "Unknown"),
                        "subcategory": newsletter_data.get("subcategory", "Unknown"),
                        "category": newsletter_data.get("category", "Unknown"),
                        "tags": newsletter_data.get("tags", []),
                        "read": False,
                        "like": False,
                        "hide": False,
                        "not_interesting": False,
                        "status": "pending_download",
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "source": "substack_api"
                    }
                    new_posts.append(new_post)
                    
                except Exception as e:
                    print(f"    ⚠️ Error processing API post: {e}")
                    continue
            
            return new_posts
            
        except Exception as e:
            print(f"    ⚠️ Substack API check failed: {e}")
            return []

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
