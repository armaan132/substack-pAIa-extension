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
project_root = Path(__file__).parent.parent.parent
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
    
    def fetch_new_posts_from_source_rss(self, newsletter_data: Dict, existing_post_urls: Set[str]) -> List[Dict]:
        """Fetch new posts using RSS feed (faster method)."""
        url = newsletter_data['url']
        name = newsletter_data.get('name', url)
        
        print(f"📡 Trying RSS for: {name}")
        
        try:
            import feedparser
            import requests
            
            # Convert to RSS URL
            rss_url = f"{url.rstrip('/')}/feed"
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
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
                post_url = entry.get('link', '')
                if not post_url:
                    continue
                    
                if post_url in existing_post_urls:
                    print(f"  ⏭️ Skipped (already in JSON): {entry.get('title', 'Unknown Title')}")
                    continue
                
                try:
                    print(f"  📝 Adding to JSON: {entry.get('title', 'Unknown Title')}")
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
                        'title': entry.get('title', 'Unknown Title'),
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
                post_url = post.url
                
                # Skip if we already have this post
                if post_url in existing_post_urls:
                    print(f"  ⏭️ Skipped (already downloaded): {post.title}")
                    continue
                
                try:
                    print(f"  📥 Downloading: {post.title}")
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
                        
                        # Store content hash for future change detection
                        import hashlib
                        content = post.get_content()
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        post_data['content_hash'] = content_hash
                        post_data['last_downloaded'] = datetime.now(timezone.utc).isoformat()
                        
                        new_posts.append(post_data)
                        print(f"  ➕ New post: {post_data['title']} (hash: {content_hash[:8]}...)")
                    else:
                        print(f"  ⏭️ Skipped (already exists): {metadata.get('title', 'Unknown')}")
                        
                except Exception as e:
                    print(f"  ❌ Error processing post: {e}")
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
                # Log other errors normally
                print(f"  ❌ Error fetching from {name}: {e}")
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
        
        # Check existing sources for new posts
        print("\n📥 Checking existing sources for new posts...")
        for newsletter_data in current_newsletters.values():
            try:
                existing_post_urls = self.get_existing_post_urls(newsletter_data["url"], existing_data)
                new_posts = self.fetch_new_posts_from_source_rss(newsletter_data, existing_post_urls)
                
                if new_posts:
                    existing_data = self.update_newsletter_data(newsletter_data, new_posts, existing_data)
            except Exception as e:
                print(f"❌ Error processing newsletter {newsletter_data.get('name', 'Unknown')}: {e}")
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
