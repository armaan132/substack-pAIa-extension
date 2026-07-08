import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from html import escape


# Constants
CSS_PATH = 'src/web/static/css/substack-original.css'

# More robust project root detection
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

PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
CONTENT_DIR = DATA_DIR / "content"

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="{css_path}">
    <title>{title}</title>
</head>
<body class="post typography">
    {content}
</body>
</html>
"""

class IndexGenerator:
    """Handles generation of index.html and other presentation files."""

    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = DATA_DIR
        else:
            self.base_dir = Path(base_dir)
        self.metadata_dir = self.base_dir / "metadata"
        self.content_dir = self.base_dir / "content"



    def _get_safe_name(self, url: str) -> str:
        """Convert URL to safe directory name."""
        # Handle URLs like https://www.astralcodexten.com -> astralcodexten
        # and https://astralcodexten.substack.com -> astralcodexten
        domain = url.split("//")[1]
        if domain.startswith("www."):
            domain = domain[4:]  # Remove www.

        # Extract the main part before .substack.com or other TLD
        if ".substack.com" in domain:
            return domain.split(".substack.com")[0]
        else:
            # For custom domains, use the first part
            return domain.split(".")[0]

    def _get_css_path(self, depth: int) -> str:
        """Get the relative path to CSS based on file depth in directory structure."""
        return '../' * depth + CSS_PATH

    def list_newsletters(self) -> List[str]:
        """Get list of all stored newsletters."""
        return [d.name for d in self.metadata_dir.iterdir() if d.is_dir()]

    def list_posts(self, newsletter_url: str) -> List[Dict]:
        """Get all posts for a specific newsletter."""
        newsletter_name = self._get_safe_name(newsletter_url)
        newsletter_dir = self.metadata_dir / newsletter_name

        if not newsletter_dir.exists():
            return []

        posts = []
        for metadata_file in newsletter_dir.glob("*.json"):
            metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            posts.append(metadata)

        # Sort by published date, handling None values
        posts.sort(
            key=lambda x: x.get('published_at', '') or '',  # Use empty string if None
            reverse=True
        )
        return posts

    def load_newsletters_with_categories(self, md_path: str = "config/newsletters.md"):
        """Parse newsletters.md to extract name, url, tags, main categories, and subcategories."""
        newsletters_by_url = {}
        current_main_category = "Uncategorized"
        current_subcategory = "Uncategorized"

        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        if line.startswith('###'):
                            # Subcategory (### headline) - check this first!
                            current_subcategory = line.lstrip('#').strip()
                        elif line.startswith('##'):
                            # Main category (## headline)
                            current_main_category = line.lstrip('#').strip()
                            current_subcategory = "Uncategorized"
                        continue
                    match = re.search(r'(https?://\S+)', line)
                    if match:
                        url = match.group(1).rstrip('/')
                        name = line[:match.start()].strip()
                        tags_part = line[match.end():].strip()
                        tags = [tag.strip() for tag in tags_part.split(',')] if tags_part else []

                        # Only use subcategory if it's actually different from main category
                        if current_subcategory != "Uncategorized" and current_subcategory != current_main_category:
                            effective_subcategory = current_subcategory
                        else:
                            effective_subcategory = None  # No subcategory for this newsletter

                        newsletters_by_url[url] = {
                            'name': name,
                            'url': url,
                            'tags': tags,
                            'main_category': current_main_category,
                            'subcategory': effective_subcategory,
                            'category': f"{current_main_category} > {effective_subcategory}" if effective_subcategory else current_main_category
                        }
        except Exception as e:
            print(f"Error loading {md_path}: {e}")

        return newsletters_by_url

    def _get_web_path(self, file_path):
        """Convert absolute file system path to web-relative path."""
        if not file_path:
            return ""

        # Convert to string if it's a Path object
        file_path_str = str(file_path)

        # Convert absolute path to relative web path
        if file_path_str.startswith('/'):
            # Remove the project root part and keep only the content/... part
            if 'data/content/' in file_path_str:
                # Extract everything from 'content/' onwards (skip the 'data/' part)
                start_idx = file_path_str.find('content/')
                return file_path_str[start_idx:]
            else:
                # Fallback: just use the filename
                return Path(file_path_str).name
        else:
            # Already a relative path
            return file_path_str

    def _format_date(self, date_str):
        """Format ISO date string as 'Jul 7, 2025'."""
        if not date_str or date_str == 'No date':
            return 'No date'
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%b %-d, %Y') if hasattr(dt, 'strftime') else dt.strftime('%b %d, %Y')
        except Exception:
            return date_str

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

    def update_post_not_interesting(self, post_id: str, not_interesting: bool) -> bool:
        """Update the not_interesting field for a specific post in the JSON file."""
        try:
            json_path = self.base_dir / "index.json"
            if not json_path.exists():
                print(f"❌ index.json not found at {json_path}")
                return False

            # Load current JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Find and update the post
            post_found = False
            for newsletter_name, newsletter_data in index_data["newsletters"].items():
                for post in newsletter_data["posts"]:
                    # Extract post ID from URL
                    post_url_id = post.get('url', '').split('/')[-1]
                    if post_url_id == post_id:
                        post['not_interesting'] = not_interesting
                        post_found = True
                        break
                if post_found:
                    break

            if not post_found:
                print(f"❌ Post with ID {post_id} not found")
                return False

            # Write updated JSON back to file
            # Sort data for consistent ordering before saving
            sorted_data = self._sort_json_data(index_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)

            print(f"✅ Updated post {post_id} not_interesting to {not_interesting}")
            return True

        except Exception as e:
            print(f"❌ Error updating post {post_id}: {e}")
            return False

    def update_post_read(self, post_id: str, read: bool) -> bool:
        """Update the read field for a specific post in the JSON file."""
        try:
            json_path = self.base_dir / "index.json"
            if not json_path.exists():
                print(f"❌ index.json not found at {json_path}")
                return False

            # Load current JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Find and update the post
            post_found = False
            for newsletter_name, newsletter_data in index_data["newsletters"].items():
                for post in newsletter_data["posts"]:
                    # Extract post ID from URL
                    post_url_id = post.get('url', '').split('/')[-1]
                    if post_url_id == post_id:
                        post['read'] = read
                        post_found = True
                        break
                if post_found:
                    break

            if not post_found:
                print(f"❌ Post with ID {post_id} not found")
                return False

            # Write updated JSON back to file
            # Sort data for consistent ordering before saving
            sorted_data = self._sort_json_data(index_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)

            print(f"✅ Updated post {post_id} read to {read}")
            return True

        except Exception as e:
            print(f"❌ Error updating post {post_id}: {e}")
            return False

    def update_post_like(self, post_id: str, like: bool) -> bool:
        """Update the like field for a specific post in the JSON file."""
        try:
            json_path = self.base_dir / "index.json"
            if not json_path.exists():
                print(f"❌ index.json not found at {json_path}")
                return False

            # Load current JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Find and update the post
            post_found = False
            for newsletter_name, newsletter_data in index_data["newsletters"].items():
                for post in newsletter_data["posts"]:
                    # Extract post ID from URL
                    post_url_id = post.get('url', '').split('/')[-1]
                    if post_url_id == post_id:
                        post['like'] = like
                        post_found = True
                        break
                if post_found:
                    break

            if not post_found:
                print(f"❌ Post with ID {post_id} not found")
                return False

            # Write updated JSON back to file
            # Sort data for consistent ordering before saving
            sorted_data = self._sort_json_data(index_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)

            print(f"✅ Updated post {post_id} like to {like}")
            return True

        except Exception as e:
            print(f"❌ Error updating post {post_id}: {e}")
            return False

    def update_post_hide(self, post_id: str, hide: bool) -> bool:
        """Update the hide field for a specific post in the JSON file."""
        try:
            json_path = self.base_dir / "index.json"
            if not json_path.exists():
                print(f"❌ index.json not found at {json_path}")
                return False

            # Load current JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Find and update the post
            post_found = False
            for newsletter_name, newsletter_data in index_data["newsletters"].items():
                for post in newsletter_data["posts"]:
                    # Extract post ID from URL
                    post_url_id = post.get('url', '').split('/')[-1]
                    if post_url_id == post_id:
                        post['hide'] = hide
                        post_found = True
                        break
                if post_found:
                    break

            if not post_found:
                print(f"❌ Post with ID {post_id} not found")
                return False

            # Write updated JSON back to file
            # Sort data for consistent ordering before saving
            sorted_data = self._sort_json_data(index_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_data, f, indent=2)

            print(f"✅ Updated post {post_id} hide to {hide}")
            return True

        except Exception as e:
            print(f"❌ Error updating post {post_id}: {e}")
            return False

    def initialize_personalization_fields(self):
        """Initialize all personalization fields for existing posts if they don't exist."""
        try:
            json_path = self.base_dir / "index.json"
            if not json_path.exists():
                print(f"ℹ️ index.json not found, will be created with personalization fields")
                return

            # Load current JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Check if any posts are missing personalization fields
            needs_update = False
            for newsletter_name, newsletter_data in index_data["newsletters"].items():
                for post in newsletter_data["posts"]:
                    if 'not_interesting' not in post:
                        post['not_interesting'] = False
                        needs_update = True
                    if 'read' not in post:
                        post['read'] = False
                        needs_update = True
                    if 'like' not in post:
                        post['like'] = False
                        needs_update = True
                    if 'hide' not in post:
                        post['hide'] = False
                        needs_update = True

            if needs_update:
                # Write updated JSON back to file
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, indent=2)
                print("✅ Initialized personalization fields for existing posts")
            else:
                print("ℹ️ All posts already have personalization fields")

        except Exception as e:
            print(f"❌ Error initializing personalization fields: {e}")

    def _format_citation_sentiment_badge(self, post: Dict) -> str:
        """Return a compact badge summarizing author feedback toward cited posts."""
        summary = post.get("citation_sentiment_summary") or {}
        total = int(summary.get("total", 0) or 0)
        if total == 0:
            return ""

        supportive = int(summary.get("supportive", 0) or 0)
        critical = int(summary.get("critical", 0) or 0)
        neutral = int(summary.get("neutral", 0) or 0)
        average_signal = float(summary.get("average_recommendation_signal", 0.0) or 0.0)
        label = "positive" if average_signal > 0 else "negative" if average_signal < 0 else "neutral"
        badge_color = "#198754" if average_signal > 0 else "#dc3545" if average_signal < 0 else "#6c757d"
        tooltip = (
            f"Author feedback toward cited Substack posts: "
            f"{supportive} supportive, {critical} critical, {neutral} neutral. "
            f"Average recommendation signal: {average_signal:+.3f}"
        )
        return (
            f'<span class="sentiment-badge sentiment-{label}" '
            f'title="{escape(tooltip)}" '
            f'style="color: {badge_color}; font-size: 0.8em; margin-left: 10px;">'
            f'💬 {total} refs ({average_signal:+.2f})'
            f'</span>'
        )

    def create_index_html(self, output_file: str = "index.html") -> None:
        """Create an index.html file from the data in index.json."""
        # Load data from index.json
        json_path = self.base_dir / "index.json"
        if not json_path.exists():
            raise FileNotFoundError(f"index.json not found at {json_path}. Generate it first with create_json_index().")

        with open(json_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        content = """
        <!-- Page Title -->
        <div style="text-align: center; margin: 15px 0; padding: 10px;">
            <h1 style="margin: 0; color: #2c3e50; font-size: 2em; font-weight: 400; letter-spacing: 0.5px;">
                Daily Briefing pAIa
                <span style="color: #7f8c8d; font-size: 0.6em; font-weight: 300; font-style: italic; margin-left: 15px;">
                    Personal Content Curation
                </span>
            </h1>
        </div>

        <!-- Main Category Selection and Visibility Controls -->
        <div class="main-category-section" style="margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px;">
            <!--h3 style="margin-top: 0;">Select Main Category:</h3-->
            <!-- All category radio buttons and filter checkboxes will be generated here -->
            <div id="dynamic-categories"></div>
        </div>

        <!-- Subcategory Selection (hidden by default) -->
        <div id="subcategory-row" class="subcategory-row" style="display: none; margin: 15px 0; padding: 15px; background: #fff3cd; border-radius: 5px; border: 1px solid #ffeaa7;">
            <!--h4 style="margin: 0 0 10px 0; color: #856404; font-size: 1em;">Filter by Subcategory:</h4-->
            <div id="subcategory-buttons" class="subcategory-buttons">
                <!-- Will be populated dynamically -->
            </div>
        </div>

        <!-- Update and Search Section -->
        <div style="display: flex; gap: 20px; margin: 20px 0;">
            <!-- Update Buttons - 3-Tier System -->
            <div style="flex: 0 0 auto; display: flex; gap: 10px; align-items: center; flex-wrap: nowrap;">
                <!-- Tier 1: Configuration Update Button -->
                <button id="metadata-btn" onclick="triggerMetadataUpdate()"
                        style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap;"
                        title="Tier 1: Fast configuration update (newsletter structure, categories)">
                    ⚡ Update Config
                </button>

                <!-- Tier 2: Structure Update Button -->
                <button id="structure-btn" onclick="triggerStructureUpdate()"
                        style="padding: 10px 20px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap;"
                        title="Tier 2: Configuration + post metadata + HTML structure">
                    🔧 Update Structure
                </button>

                <!-- Tier 3: Content Discovery & Download Button -->
                <button id="content-btn" onclick="triggerContentUpdate()"
                        style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap;"
                        title="Tier 3: Discover new posts + download content for offline reading">
                    🔍 Discover & Download
                </button>

                <!-- Advanced: Deep Discovery Button (RSS + API) -->
                <button id="aggressive-btn" onclick="triggerAggressiveDiscovery()"
                        style="padding: 10px 20px; background: #ff5722; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap;"
                        title="Advanced: Deep discovery using both RSS feeds and Substack API for maximum coverage">
                    🚀 Deep Discovery
                </button>

                <!-- Analysis: Citation Sentiment Button -->
                <button id="sentiment-btn" onclick="triggerCitationSentimentUpdate()"
                        style="padding: 10px 20px; background: #6f42c1; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; white-space: nowrap;"
                        title="Analyze author feedback toward linked Substack posts for recommendation signals">
                    💬 Analyze Citations
                </button>
            </div>

            <!-- Update Status (moved outside button container) -->
            <div id="update-status" style="margin-top: 10px; font-size: 12px; color: #666; text-align: center;"></div>



            <!-- Search Bar -->
            <div style="flex: 1;">
                <div class="search-bar" style="padding: 15px; background: #e8f5e8; border-radius: 5px;">
                    <input type="text" id="search-input" placeholder="Search posts by title, newsletter, or content..."
                           style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                           oninput="searchPosts(this.value)"
                           onkeydown="if(event.key === 'Enter') { console.log('🟢 Enter key detected'); searchPosts(this.value); }">
                </div>
            </div>
        </div>



        <style>
            .post-line { margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
            .post-line a { margin-right: 15px; text-decoration: none; }
            .post-line a.local { color: #0066cc; text-decoration: none; }
            .post-line a.local:hover { text-decoration: underline; }
            .post-line a.original { color: #666; font-size: 0.9em; text-decoration: none; }
            .post-line a.original:hover { text-decoration: underline; }
            .newsletter-name { color: #333; font-weight: bold; margin-right: 10px; }
            .date { color: #888; font-size: 0.8em; margin-left: 10px; }
            .category { color: #666; font-size: 0.8em; margin-left: 10px; }
            .action-btn {
                background: #fef7e0;
                color: #666;
                border: 1px solid #ddd;
                padding: 6px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin-left: 8px;
                transition: all 0.2s ease;
                position: relative;
            }
            .action-btn:hover {
                background: #e0e0e0;
                border-color: #bbb;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .action-btn.marked {
                background: #2196f3;
                color: white;
                border-color: #2196f3;
            }

            /* All marked buttons use the same blue color */
            .action-btn.read-btn.marked { background: #2196f3; border-color: #2196f3; }
            .action-btn.not-interesting-btn.marked { background: #2196f3; border-color: #2196f3; }
            .action-btn.like-btn.marked { background: #2196f3; border-color: #2196f3; }
            .action-btn.hide-btn.marked { background: #2196f3; border-color: #2196f3; }

            /* Tooltip styles */
            .action-btn::after {
                content: attr(data-tooltip);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: #333;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.2s ease;
                z-index: 1000;
                margin-bottom: 5px;
            }
            .action-btn:hover::after {
                opacity: 1;
                visibility: visible;
            }

            /* Subcategory button styles */
            .subcategory-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .subcategory-btn {
                background: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.2s ease;
            }

            .subcategory-btn:hover {
                background: #e9ecef;
                border-color: #adb5bd;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .subcategory-btn.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }

            .hidden-post { display: none; }
            .read-post { display: none; }
            .hide-post { display: none; }
            .liked-post { display: none; } /* Hide liked posts by default (they're read) */



            /* Search result styling for hidden posts */
            .search-result-hidden {
                opacity: 0.7;
                border-left: 3px solid #ff9800;
                padding-left: 10px;
            }

            /* Search mode styling */


            .search-mode .search-bar {
                background: #fff3cd !important;
                border-color: #ffc107 !important;
            }
        </style>
        """

        # Collect all posts from the JSON data
        all_posts = []
        for newsletter_url, newsletter_data in index_data.get("newsletters", {}).items():
            newsletter_name = newsletter_data.get("name", "Unknown Newsletter")
            main_category = newsletter_data.get("main_category", "Unknown")
            subcategory = newsletter_data.get("subcategory", "Unknown")
            category = newsletter_data.get("category", "Unknown")

            for post in newsletter_data.get("posts", []):
                post_data = post.copy()
                post_data["newsletter_name"] = newsletter_name
                post_data["newsletter_url"] = newsletter_url
                post_data["main_category"] = main_category
                post_data["subcategory"] = subcategory
                post_data["category"] = category
                all_posts.append(post_data)

        # Sort posts by date (newest first)
        all_posts.sort(key=lambda x: x.get('published_at', '') or '1970-01-01', reverse=True)

        # Add pending downloads indicator if any
        pending_downloads = 0
        for post in all_posts:
            if post.get('status') == 'pending_download':
                pending_downloads += 1

        if pending_downloads > 0:
            content += f"""
            <!-- Pending Downloads Indicator -->
            <div data-pending-downloads style="background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin: 20px 0; text-align: center;">
                <strong>⏳ {pending_downloads} posts are downloading in the background</strong><br>
                <small>New post links are visible above. Content will be available offline once downloads complete.</small>
            </div>
            """

                # Generate posts HTML (chronological order)
        posts_html = ""
        for post in all_posts:
            title = post['title']
            date = post.get('published_at') or 'No date'
            display_date = self._format_date(date)
            newsletter_name = post['newsletter_name']
            category = post.get('category', 'Uncategorized')
            status = post.get('status', 'downloaded')

            # Keep the original content_path for _get_web_path to handle
            content_path = post['content_path']

            not_interesting = post.get('not_interesting', False)
            read = post.get('read', False)
            like = post.get('like', False)
            hide = post.get('hide', False)
            post_id = post.get('url', '').split('/')[-1]
            sentiment_badge = self._format_citation_sentiment_badge(post)

            # Apply liked-post class if post is both read AND liked
            liked_post_class = 'liked-post' if read and like else ''

            # Determine post display based on status
            if status == 'pending_download':
                # Post is discovered but not downloaded yet - show just the link (no icon)
                posts_html += f"""
                <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}"
                     data-post-id="{post_id}"
                     data-main-category="{post.get('main_category', 'Uncategorized')}"
                     data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                    <span class="newsletter-name">{newsletter_name}</span>
                    <a href="{post['url']}" class="original" target="_blank" title="View local post">{title}</a>
                    <span class="date">{display_date}</span>
                    <span class="category">({post.get('main_category', 'Uncategorized')}{f' > {post.get("subcategory", "Uncategorized")}' if post.get('subcategory') and post.get('subcategory') != post.get('main_category') else ''})</span>
                    {sentiment_badge}
                    <span style="color: #ffc107; font-size: 0.8em; margin-left: 10px;">⏳ Downloading...</span>
                </div>
                """
            else:
                # Normal downloaded post
                if post.get('content_path') and Path(post['content_path']).exists():
                    # Local content available
                    posts_html += f"""
                    <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}"
                         data-post-id="{post_id}"
                         data-main-category="{post.get('main_category', 'Uncategorized')}"
                         data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                        <span class="newsletter-name">{newsletter_name}</span>
                        <a href="{post['url']}" class="local" target="_blank" title="View original post">{title}</a>
                        <a href="{self._get_web_path(content_path)}" class="original" title="Read offline">📄</a>
                        <span class="date">{display_date}</span>
                        <span class="category">({post.get('main_category', 'Uncategorized')}{f' > {post.get("subcategory", "Uncategorized")}' if post.get('subcategory') and post.get('subcategory') != post.get('main_category') else ''})</span>
                        {sentiment_badge}
                        <button class="action-btn read-btn {'' if not read else 'marked'}"
                                onclick="toggleRead('{post_id}', this)"
                                data-tooltip="Mark as Read">
                            👁️
                        </button>
                        <button class="action-btn not-interesting-btn {'' if not not_interesting else 'marked'}"
                                onclick="toggleNotInteresting('{post_id}', this)"
                                data-tooltip="Mark as Not Interesting">
                            👎
                        </button>
                        <button class="action-btn like-btn {'' if not like else 'marked'}"
                                onclick="toggleLike('{post_id}', this)"
                                data-tooltip="Like">
                            👍
                        </button>
                        <button class="action-btn hide-btn {'' if not hide else 'marked'}"
                                onclick="toggleHide('{post_id}', this)"
                                data-tooltip="Hide">
                            🚫
                        </button>
                    </div>
                    """
                else:
                    # No local content
                    posts_html += f"""
                    <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}"
                         data-post-id="{post_id}"
                         data-main-category="{post.get('main_category', 'Uncategorized')}"
                         data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                        <span class="newsletter-name">{newsletter_name}</span>
                        <a href="{post['url']}" class="local" target="_blank" title="View original post">{title}</a>
                        <span class="date">{display_date}</span>
                        <span class="category">({post.get('main_category', 'Uncategorized')}{f' > {post.get("subcategory", "Uncategorized")}' if post.get('subcategory') and post.get('subcategory') != post.get('main_category') else ''})</span>
                        {sentiment_badge}
                        <span style="color: #dc3545; font-size: 0.8em; margin-left: 10px;">⚠️ No offline content</span>
                    </div>
                    """

        # Add posts to the page
        content += f"""
        <div id="posts-container">
            {posts_html}
        </div>
        """

        # Add category index data for efficient subcategory generation
        category_index_html = ""
        if "categories" in index_data:
            category_index_html = f"""
            <script>
                // Pre-built category-subcategory index for efficient UI generation
                window.categoryIndex = {json.dumps(index_data["categories"])};
                console.log('📊 Category index loaded:', window.categoryIndex);
            </script>
            """

        # Add JavaScript for view switching, main category filtering, and not_interesting functionality
        content += category_index_html + """
        <script>
            // Simple test to see if JavaScript is working
            console.log('🚀 JavaScript is loading!');

            let currentMainCategory = 'All';
            let currentSubcategory = null;

            // Hide posts marked as hidden, read, or hide on page load (liked posts stay visible)
            document.addEventListener('DOMContentLoaded', function() {
                console.log('🔵 DOMContentLoaded event fired');

                hideNotInterestingPosts();
                hideReadPosts();
                hideHidePosts();

                // Generate dynamic category radio buttons FIRST
                generateCategoryRadioButtons();

                // Restore saved category selection from localStorage
                const savedCategory = localStorage.getItem('selectedMainCategory') || 'All';
                currentMainCategory = savedCategory;

                // Set the radio button to match the saved selection
                const radioButton = document.querySelector(`input[name="main-category"][value="${savedCategory}"]`);
                if (radioButton) {
                    radioButton.checked = true;
                }

                // Show subcategory row if a specific category is selected (not 'All')
                if (savedCategory !== 'All') {
                    showSubcategoryLinks(savedCategory);
                }

                // Apply the saved category filtering to show the correct posts
                updateCategoryView();

                // Add event listener for search input
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.addEventListener('input', function() {
                        console.log(`🟢 Search input detected: "${this.value}"`);
                        searchPosts(this.value);
                    });
                }
            });

            // Generate dynamic category radio buttons
            function generateCategoryRadioButtons() {
                const dynamicCategoriesDiv = document.getElementById('dynamic-categories');
                if (!dynamicCategoriesDiv) return;

                const categoryIndex = window.categoryIndex || {};
                let categoriesHtml = '';

                // Always start with "All" button
                categoriesHtml += `
                    <label style="margin-right: 20px; cursor: pointer;">
                        <input type="radio" name="main-category" value="All" onclick="console.log('🟢 Radio button clicked: All'); filterByMainCategory('All')"> All
                    </label>
                `;

                // Preserve human-curated order from newsletters.md instead of alphabetical sorting
                // The order should be: Science, News and Opinion, Tech (as defined in newsletters.md)
                const humanCuratedOrder = ['Science', 'News and Opinion', 'Tech'];
                const availableCategories = Object.keys(categoryIndex);

                // Use human-curated order for known categories, append any others at the end
                const orderedCategories = [];
                for (const category of humanCuratedOrder) {
                    if (availableCategories.includes(category)) {
                        orderedCategories.push(category);
                    }
                }

                // Add any remaining categories that weren't in the human-curated list
                for (const category of availableCategories) {
                    if (!orderedCategories.includes(category)) {
                        orderedCategories.push(category);
                    }
                }

                for (const category of orderedCategories) {
                    categoriesHtml += `
                        <label style="margin-right: 20px; cursor: pointer;">
                            <input type="radio" name="main-category" value="${category}" onclick="console.log('🟢 Radio button clicked: ${category}'); filterByMainCategory('${category}')"> ${category}
                        </label>
                    `;
                }

                // Add filter checkboxes on the same line
                categoriesHtml += `
                    <label style="margin-right: 20px; cursor: pointer;">
                        <input type="checkbox" id="show-hidden" onclick="console.log('🟢 Hidden posts checkbox clicked'); toggleHiddenPosts()"> <span title="Include Hidden Posts">Hidden Posts</span>
                    </label>
                    <label style="margin-right: 20px; cursor: pointer;">
                        <input type="checkbox" id="show-liked" onclick="console.log('🟢 Liked posts checkbox clicked'); toggleLikedPosts()"> <span title="Only Liked Posts">Liked Posts</span>
                    </label>
                `;

                dynamicCategoriesDiv.innerHTML = categoriesHtml;
                console.log(`🔧 Generated ${orderedCategories.length + 1} dynamic category radio buttons (including All) plus filter checkboxes in human-curated order: All, ${orderedCategories.join(', ')}`);
            }

            // Check for metadata updates on page load
            let metadataCheckSuccessful = false;

            async function checkForMetadataUpdates() {
                console.log('🔵 checkForMetadataUpdates() called');

                try {
                    // Quick check if newsletters.md has changed
                    const response = await fetch('/api/check_metadata_status', {
                        method: 'GET',
                        // Add timeout and better error handling
                        signal: AbortSignal.timeout(10000) // 10 second timeout
                    });

                    if (response.ok) {
                        const result = await response.json();
                        if (result.needs_update) {
                            console.log('📝 newsletters.md has changed - automatically updating metadata...');

                            // Show notification to user
                            const updateStatus = document.getElementById('update-status');
                            updateStatus.innerHTML = `
                                <div style="background: #e8f5e8; border: 1px solid #28a745; padding: 10px; border-radius: 4px; margin-top: 10px;">
                                    <strong>⚡ Updating Configuration...</strong><br>
                                    Your newsletters.md has changed. Applying updates automatically...
                                </div>
                            `;

                            // Automatically run metadata update
                            await triggerMetadataUpdate();

                            // Regenerate category radio buttons after update
                            generateCategoryRadioButtons();
                        } else {
                            console.log('✅ Metadata is up to date');
                            metadataCheckSuccessful = true; // Mark as successful
                        }
                    } else {
                        console.log('⚠️ Server error checking metadata status:', response.statusText);
                        // Keep the UI clean - no error status updates needed
                    }
                } catch (error) {
                    console.log('ℹ️ Could not check metadata status:', error.message);

                    // Better error categorization for console logging
                    if (error.name === 'AbortError') {
                        console.log('⏱️ Request timeout');
                    } else if (error.message.includes('Failed to fetch')) {
                        console.log('🔌 Connection failed');
                    } else {
                        console.log(`❌ Error: ${error.message}`);
                    }
                }
            }

            // Call metadata check after a longer delay to ensure server is ready
            setTimeout(checkForMetadataUpdates, 3000);

            // Retry once more after 5 seconds ONLY if the first attempt failed
            setTimeout(() => {
                if (!metadataCheckSuccessful) {
                    console.log('🔄 Retrying metadata status check...');
                    checkForMetadataUpdates();
                }
            }, 5000);

            // NEW: Background metadata check every 5 minutes
            setInterval(checkForMetadataUpdates, 5 * 60 * 1000);

            // NEW: Update pending downloads count every 30 seconds
            setInterval(updatePendingDownloadsCount, 30 * 1000);

            function hideNotInterestingPosts() {
                console.log('🔵 hideNotInterestingPosts() called');
                const hiddenPosts = document.querySelectorAll('.hidden-post');
                hiddenPosts.forEach(post => {
                    post.style.display = 'none';
                });
            }

            function hideReadPosts() {
                console.log('🔵 hideReadPosts() called');
                const readPosts = document.querySelectorAll('.read-post');
                readPosts.forEach(post => {
                    post.style.display = 'none';
                });
            }

            function hideHidePosts() {
                console.log('🔵 hideHidePosts() called');
                const hidePosts = document.querySelectorAll('.hide-post');
                hidePosts.forEach(post => {
                    post.style.display = 'none';
                });
            }

            function filterByMainCategory(mainCategory) {
                console.log(`🔵 filterByMainCategory('${mainCategory}') called`);
                currentMainCategory = mainCategory;
                currentSubcategory = null; // Clear subcategory filter when switching main categories

                // Save the selection to localStorage for persistence
                localStorage.setItem('selectedMainCategory', mainCategory);

                // Show/hide subcategory row and populate subcategory buttons
                showSubcategoryLinks(mainCategory);

                // Update the display based on current category using unified AND logic
                updateCategoryView();
            }

            function showSubcategoryLinks(mainCategory) {
                console.log(`🔵 showSubcategoryLinks('${mainCategory}') called`);
                const subcategoryRow = document.getElementById('subcategory-row');
                const subcategoryButtons = document.getElementById('subcategory-buttons');

                // Clear any active subcategory filter when switching main categories
                currentSubcategory = null;

                if (mainCategory === 'All') {
                    subcategoryRow.style.display = 'none';
                    return;
                }

                // Use the pre-built category index from index.json for efficiency
                const categoryIndex = window.categoryIndex || {};
                const subcategories = categoryIndex[mainCategory] || [];

                if (subcategories.length === 0) {
                    subcategoryRow.style.display = 'none';
                    return;
                }

                // Populate subcategory buttons
                subcategoryButtons.innerHTML = '';
                const sortedSubcategories = subcategories; // Already sorted from JSON

                sortedSubcategories.forEach(subcategory => {
                    const button = document.createElement('button');
                    button.className = 'subcategory-btn';
                    button.textContent = subcategory;
                    button.onclick = function() {
                        console.log(`🟢 Subcategory button clicked: ${subcategory}`);
                        filterBySubcategory(subcategory);
                    };
                    subcategoryButtons.appendChild(button);
                });

                subcategoryRow.style.display = 'block';
            }

            function filterBySubcategory(subcategory) {
                console.log(`🔵 filterBySubcategory('${subcategory}') called`);

                // Toggle: if clicking the same subcategory, turn it off
                if (currentSubcategory === subcategory) {
                    currentSubcategory = null;
                    console.log('🔄 Toggling off subcategory filter');
                } else {
                    currentSubcategory = subcategory;
                    console.log(`🔄 Setting subcategory filter to: ${subcategory}`);
                }

                // Update button states
                const buttons = document.querySelectorAll('.subcategory-btn');
                buttons.forEach(btn => {
                    if (btn.textContent === subcategory && currentSubcategory === subcategory) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });

                // Update the display
                updateCategoryView();
            }

            function updateCategoryView() {
                console.log(`🔵 updateCategoryView() called`);

                // Get current filter states with safety check
                const checkedRadio = document.querySelector('input[name="main-category"]:checked');
                if (!checkedRadio) {
                    console.log('⚠️ No category radio button checked yet, skipping update');
                    return;
                }

                const selectedCategory = checkedRadio.value;
                const showHidden = document.getElementById('show-hidden').checked;
                const showLiked = document.getElementById('show-liked').checked;

                // Filter posts by applying ALL active filters with AND logic
                const allPosts = document.querySelectorAll('.post-line');

                let visibleCount = 0;
                let hiddenCount = 0;

                allPosts.forEach(post => {
                    // Apply Category Filter
                    const postMainCategory = post.getAttribute('data-main-category');
                    const categoryMatches = selectedCategory === 'All' || postMainCategory === selectedCategory;

                    // Apply Subcategory Filter (if active)
                    let subcategoryMatches = true;
                    if (currentSubcategory && selectedCategory !== 'All') {
                        const postSubcategory = post.getAttribute('data-subcategory');
                        subcategoryMatches = postSubcategory === currentSubcategory;
                    }

                    // Apply Hidden Posts Filter
                    const isHidden = post.classList.contains('hidden-post') ||
                                   post.classList.contains('read-post') ||
                                   post.classList.contains('hide-post') ||
                                   post.classList.contains('liked-post');
                    const hiddenFilterPasses = showHidden || !isHidden;

                    // Apply Liked Posts Filter
                    const isLiked = post.classList.contains('liked-post');
                    const likedFilterPasses = !showLiked || isLiked;

                    // Post must pass ALL active filters (AND logic)
                    const shouldShow = categoryMatches && subcategoryMatches && hiddenFilterPasses && likedFilterPasses;

                    if (shouldShow) {
                        post.style.display = 'block';
                        visibleCount++;
                    } else {
                        post.style.display = 'none';
                        hiddenCount++;
                    }
                });
            }



            function toggleNotInteresting(postId, button) {
                console.log(`🔵 toggleNotInteresting('${postId}') called`);
                const postLine = button.closest('.post-line');
                const isCurrentlyMarked = button.classList.contains('marked');

                // Toggle the button appearance and visibility
                if (isCurrentlyMarked) {
                    button.classList.remove('marked');
                    button.innerHTML = 'Not Interesting';
                    postLine.classList.remove('hidden-post');
                    postLine.style.display = 'block'; // Show the post
                } else {
                    button.classList.add('marked');
                    button.innerHTML = '👎';
                    postLine.classList.add('hidden-post');
                    postLine.style.display = 'none'; // Hide the post immediately
                }

                // Update the JSON data via API
                updatePostNotInteresting(postId, !isCurrentlyMarked);
            }

            function toggleRead(postId, button) {
                console.log(`🔵 toggleRead('${postId}') called`);
                const postLine = button.closest('.post-line');
                const isCurrentlyMarked = button.classList.contains('marked');

                // Toggle the button appearance and visibility
                if (isCurrentlyMarked) {
                    button.classList.remove('marked');
                    button.innerHTML = 'Read';
                    postLine.classList.remove('read-post');
                    postLine.style.display = 'block'; // Show the post
                } else {
                    button.classList.add('marked');
                    button.innerHTML = '✓ Read';
                    postLine.classList.add('read-post');
                    postLine.style.display = 'none'; // Hide the post immediately
                }

                // Update the JSON data via API
                updatePostRead(postId, !isCurrentlyMarked);
            }

            async function updatePostNotInteresting(postId, notInteresting) {
                console.log(`🔵 updatePostNotInteresting('${postId}', ${notInteresting}) called`);
                try {
                    const response = await fetch('/api/update_not_interesting', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            post_id: postId,
                            not_interesting: notInteresting
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        console.log(`✅ Post ${postId} not_interesting updated successfully`);
                    } else {
                        console.error(`❌ Failed to update post ${postId} not_interesting:`, result.error);
                        // Revert the UI change if the update failed
                        const button = document.querySelector(`[onclick*="${postId}"]`);
                        const postLine = button.closest('.post-line');
                        if (notInteresting) {
                            button.classList.remove('marked');
                            button.innerHTML = '👎';
                            postLine.classList.remove('hidden-post');
                            postLine.style.display = 'block'; // Show the post
                        } else {
                            button.classList.add('marked');
                            button.innerHTML = '👎';
                            postLine.classList.add('hidden-post');
                            postLine.style.display = 'none'; // Hide the post
                        }
                    }
                } catch (error) {
                    console.error('❌ Error updating post not_interesting:', error);
                    // Revert the UI change if the update failed
                    const button = document.querySelector(`[onclick*="${postId}"]`);
                    const postLine = button.closest('.post-line');
                    if (notInteresting) {
                        button.classList.remove('marked');
                        button.innerHTML = '👎';
                        postLine.classList.remove('hidden-post');
                        postLine.style.display = 'none'; // Hide the post
                    } else {
                        button.classList.remove('marked');
                        button.innerHTML = '👎';
                        postLine.classList.add('hidden-post');
                        postLine.style.display = 'block'; // Show the post
                    }
                }
            }

            async function updatePostRead(postId, read) {
                console.log(`🔵 updatePostRead('${postId}', ${read}) called`);
                try {
                    const response = await fetch('/api/update_read', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            post_id: postId,
                            read: read
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        console.log(`✅ Post ${postId} read status updated successfully`);
                    } else {
                        console.error(`❌ Failed to update post ${postId} read status:`, result.error);
                        // Revert the UI change if the update failed
                        const button = document.querySelector(`[onclick*="${postId}"]`);
                        const postLine = button.closest('.post-line');
                        if (read) {
                            button.classList.remove('marked');
                            button.innerHTML = 'Read';
                            postLine.classList.remove('read-post');
                            postLine.style.display = 'block'; // Show the post
                        } else {
                            button.classList.add('marked');
                            button.innerHTML = '✓ Read';
                            postLine.classList.add('read-post');
                            postLine.style.display = 'none'; // Hide the post
                        }
                    }
                } catch (error) {
                    console.error('❌ Error updating post read status:', error);
                    // Revert the UI change if the update failed
                    const button = document.querySelector(`[onclick*="${postId}"]`);
                    const postLine = button.closest('.post-line');
                    if (read) {
                        button.classList.remove('marked');
                        button.innerHTML = 'Read';
                        postLine.classList.add('marked');
                        postLine.classList.remove('read-post');
                        postLine.style.display = 'block'; // Show the post
                    } else {
                        button.classList.remove('marked');
                        button.innerHTML = 'Read';
                        postLine.classList.remove('read-post');
                        postLine.style.display = 'none'; // Hide the post
                    }
                }
            }

            function toggleLike(postId, button) {
                console.log(`🔵 toggleLike('${postId}') called`);
                const postLine = button.closest('.post-line');
                const isCurrentlyMarked = button.classList.contains('marked');

                // Toggle the button appearance
                if (isCurrentlyMarked) {
                    button.classList.remove('marked');
                    button.innerHTML = '👍';
                    postLine.classList.remove('liked-post');
                } else {
                    button.classList.add('marked');
                    button.innerHTML = '👍'; // Keep thumbs up, but with colored background
                    postLine.classList.add('liked-post');
                }

                // Check if post should be hidden (if both read AND liked)
                const isRead = postLine.classList.contains('read-post');
                if (isRead && !isCurrentlyMarked) {
                    // Post is now liked and read, so hide it
                    postLine.style.display = 'none';
                } else if (isRead && isCurrentlyMarked) {
                    // Post is no longer liked but still read, so show it
                    postLine.style.display = 'block';
                }
                // If post is not read, visibility depends on other factors

                // Update the JSON data via API
                updatePostLike(postId, !isCurrentlyMarked);
            }

            function toggleHide(postId, button) {
                console.log(`🔵 toggleHide('${postId}') called`);
                const postLine = button.closest('.post-line');
                const isCurrentlyMarked = button.classList.contains('marked');

                // Toggle the button appearance and visibility
                if (isCurrentlyMarked) {
                    button.classList.remove('marked');
                    button.innerHTML = 'Hide';
                    postLine.classList.remove('hide-post');
                    postLine.style.display = 'block'; // Show the post
                } else {
                    button.classList.add('marked');
                    button.innerHTML = '✓ Hide';
                    postLine.classList.add('hide-post');
                    postLine.style.display = 'none'; // Hide the post immediately
                }

                // Update the JSON data via API
                updatePostHide(postId, !isCurrentlyMarked);
            }

            async function updatePostLike(postId, like) {
                console.log(`🔵 updatePostLike('${postId}', ${like}) called`);
                try {
                    const response = await fetch('/api/update_like', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            post_id: postId,
                            like: like
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        console.log(`✅ Post ${postId} like updated successfully`);
                    } else {
                        console.error(`❌ Failed to update post ${postId} like:`, result.error);
                        // Revert the UI change if the update failed
                        const button = document.querySelector(`[onclick*="${postId}"]`);
                        const postLine = button.closest('.post-line');
                        if (like) {
                            button.classList.remove('marked');
                            button.innerHTML = '👍';
                            postLine.classList.remove('liked-post');
                        } else {
                            button.classList.add('marked');
                            button.innerHTML = '👍';
                            postLine.classList.add('liked-post');
                        }
                    }
                } catch (error) {
                    console.error('❌ Error updating post like:', error);
                    // Revert the UI change if the update failed
                        const button = document.querySelector(`[onclick*="${postId}"]`);
                        const postLine = button.closest('.post-line');
                        if (like) {
                            button.classList.remove('marked');
                            button.innerHTML = '👍';
                            postLine.classList.remove('liked-post');
                        } else {
                            button.classList.add('marked');
                            button.innerHTML = '👍';
                            postLine.classList.add('liked-post');
                        }
                }
            }

            async function triggerMetadataUpdate() {
                console.log('🔵 triggerMetadataUpdate() called');

                const metadataBtn = document.getElementById('metadata-btn');
                const updateStatus = document.getElementById('update-status');

                // Disable button and show loading state
                metadataBtn.disabled = true;
                metadataBtn.innerHTML = '⏳ Updating...';
                metadataBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '⚡ Starting Tier 1: Configuration update...';

                try {
                    const response = await fetch('/api/update_metadata', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();

                    if (result.success) {
                        updateStatus.innerHTML = `✅ Tier 1 completed! ${result.message || ''}`;
                        metadataBtn.style.background = '#6c757d';

                        // Reload the page to show new structure
                        setTimeout(() => {
                            updateStatus.innerHTML = '🔄 Reloading page to show new structure...';
                            location.reload();
                        }, 1500);
                    } else {
                        throw new Error(result.error || 'Configuration update failed');
                    }

                } catch (error) {
                    console.error('❌ Configuration update error:', error);
                    updateStatus.innerHTML = `❌ Configuration update failed: ${error.message}`;
                    metadataBtn.style.background = '#dc3545';
                } finally {
                    // Re-enable button
                    metadataBtn.disabled = false;
                    metadataBtn.innerHTML = '⚡ Update Config';
                }
            }

            async function triggerStructureUpdate() {
                console.log('🔵 triggerStructureUpdate() called');

                const structureBtn = document.getElementById('structure-btn');
                const updateStatus = document.getElementById('update-status');

                // Disable button and show loading state
                structureBtn.disabled = true;
                structureBtn.innerHTML = '⏳ Updating...';
                structureBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '🔧 Starting Tier 2: Structure update...';

                try {
                    const response = await fetch('/api/update_structure', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();

                    if (result.success) {
                        updateStatus.innerHTML = `✅ Tier 2 completed! ${result.message || ''}`;
                        structureBtn.style.background = '#17a2b8';

                        // Reload the page to show new structure
                        setTimeout(() => {
                            updateStatus.innerHTML = '🔄 Reloading page to show new structure...';
                            location.reload();
                        }, 1500);
                    } else {
                        throw new Error(result.error || 'Structure update failed');
                    }

                } catch (error) {
                    console.error('❌ Structure update error:', error);
                    updateStatus.innerHTML = `❌ Structure update failed: ${error.message}`;
                    structureBtn.style.background = '#dc3545';
                } finally {
                    // Re-enable button
                    structureBtn.disabled = false;
                    structureBtn.innerHTML = '🔧 Update Structure';
                }
            }

            async function triggerContentUpdate() {
                console.log('🔵 triggerContentUpdate() called');

                const contentBtn = document.getElementById('content-btn');
                const updateStatus = document.getElementById('update-status');

                // Disable button and show loading state
                contentBtn.disabled = true;
                contentBtn.innerHTML = '⏳ Updating...';
                contentBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '🔍 Starting Tier 3: Content discovery and download...';

                try {
                    // First discover new links (Tier 3a)
                    updateStatus.innerHTML = '🔍 Tier 3a: Discovering new posts...';
                    const discoverResponse = await fetch('/api/discover_links', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!discoverResponse.ok) {
                        throw new Error(`Link discovery failed: HTTP ${discoverResponse.status}`);
                    }

                    const discoverResult = await discoverResponse.json();

                    if (discoverResult.success) {
                        updateStatus.innerHTML = `✅ Tier 3a completed! ${discoverResult.message || ''}`;

                        // Then start background downloads (Tier 3b)
                        updateStatus.innerHTML = '📥 Tier 3b: Starting background downloads...';
                        const downloadResponse = await fetch('/api/download_pending_content', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });

                        if (!downloadResponse.ok) {
                            throw new Error(`Download start failed: HTTP ${downloadResponse.status}`);
                        }

                        const downloadResult = await downloadResponse.json();

                        if (downloadResult.success) {
                            updateStatus.innerHTML = `✅ Tier 3 completed! ${downloadResult.message || ''}`;
                            contentBtn.style.background = '#28a745';

                            // Reload the page to show new content
                            setTimeout(() => {
                                updateStatus.innerHTML = '🔄 Reloading page to show new content...';
                                location.reload();
                            }, 1500);
                        } else {
                            throw new Error(downloadResult.error || 'Download start failed');
                        }
                    } else {
                        throw new Error(discoverResult.error || 'Link discovery failed');
                    }

                } catch (error) {
                    console.error('❌ Content update error:', error);
                    updateStatus.innerHTML = `❌ Content update failed: ${error.message}`;
                    contentBtn.style.background = '#dc3545';
                } finally {
                    // Re-enable button
                    contentBtn.disabled = false;
                    contentBtn.innerHTML = '🔍 Discover & Download';
                }
            }

            async function triggerAggressiveDiscovery() {
                console.log('🔵 triggerAggressiveDiscovery() called');

                const aggressiveBtn = document.getElementById('aggressive-btn');
                const updateStatus = document.getElementById('update-status');

                // Disable button and show loading state
                aggressiveBtn.disabled = true;
                aggressiveBtn.innerHTML = '⏳ Deep Discovery...';
                aggressiveBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '🚀 Starting aggressive discovery using RSS + Substack API...';

                try {
                    const response = await fetch('/api/aggressive_discovery', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();

                    if (result.success) {
                        updateStatus.innerHTML = `✅ Aggressive discovery completed! ${result.message || ''}`;
                        aggressiveBtn.style.background = '#ff5722';

                        // Reload the page to show new post links
                        setTimeout(() => {
                            updateStatus.innerHTML = '🔄 Reloading page to show new post links...';
                            location.reload();
                        }, 1500);
                    } else {
                        throw new Error(result.error || 'Aggressive discovery failed');
                    }

                } catch (error) {
                    console.error('❌ Aggressive discovery error:', error);
                    updateStatus.innerHTML = `❌ Aggressive discovery failed: ${error.message}`;
                    aggressiveBtn.style.background = '#dc3545';
                } finally {
                    // Re-enable button
                    aggressiveBtn.disabled = false;
                    aggressiveBtn.innerHTML = '🚀 Deep Discovery';
                }
            }

            async function triggerCitationSentimentUpdate() {
                console.log('🔵 triggerCitationSentimentUpdate() called');

                const sentimentBtn = document.getElementById('sentiment-btn');
                const updateStatus = document.getElementById('update-status');

                sentimentBtn.disabled = true;
                sentimentBtn.innerHTML = '⏳ Analyzing...';
                sentimentBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '💬 Analyzing citation sentiment in saved post HTML...';

                try {
                    const response = await fetch('/api/update_citation_sentiment', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();

                    if (result.success) {
                        updateStatus.innerHTML = `✅ Citation analysis completed: ${result.total_citations} citations across ${result.posts_with_citations} posts.`;
                        sentimentBtn.style.background = '#6f42c1';

                        setTimeout(() => {
                            updateStatus.innerHTML = '🔄 Reloading page to show citation sentiment badges...';
                            location.reload();
                        }, 1500);
                    } else {
                        throw new Error(result.error || 'Citation sentiment analysis failed');
                    }

                } catch (error) {
                    console.error('❌ Citation sentiment update error:', error);
                    updateStatus.innerHTML = `❌ Citation sentiment analysis failed: ${error.message}`;
                    sentimentBtn.style.background = '#dc3545';
                } finally {
                    sentimentBtn.disabled = false;
                    sentimentBtn.innerHTML = '💬 Analyze Citations';
                }
            }



            async function updatePostHide(postId, hide) {
                console.log(`🔵 updatePostHide('${postId}', ${hide}) called`);
                try {
                    const response = await fetch('/api/update_hide', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            post_id: postId,
                            hide: hide
                        })
                    });

                    const result = await response.json();
                    if (result.success) {
                        console.log(`✅ Post ${postId} hide updated successfully`);
                    } else {
                        console.error(`❌ Failed to update post ${postId} hide:`, result.error);
                        // Revert the UI change if the update failed
                        const button = document.querySelector(`[onclick*="${postId}"]`);
                        const postLine = button.closest('.post-line');
                        if (hide) {
                            button.classList.remove('marked');
                            button.innerHTML = 'Hide';
                            postLine.classList.remove('hide-post');
                            postLine.style.display = 'block'; // Show the post
                        } else {
                            button.classList.add('marked');
                            button.innerHTML = '✓ Hide';
                            postLine.classList.add('hide-post');
                            postLine.style.display = 'none'; // Hide the post
                        }
                    }
                } catch (error) {
                    console.error('❌ Error updating post hide:', error);
                    // Revert the UI change if the update failed
                    const button = document.querySelector(`[onclick*="${postId}"]`);
                    const postLine = button.closest('.post-line');
                    if (hide) {
                        button.classList.remove('marked');
                        button.innerHTML = 'Hide';
                        postLine.classList.add('marked');
                        postLine.classList.remove('hide-post');
                        postLine.style.display = 'block'; // Show the post
                    } else {
                        button.classList.remove('marked');
                        button.innerHTML = 'Hide';
                        postLine.classList.add('hide-post');
                        postLine.style.display = 'none'; // Hide the post
                    }
                }
            }

            function toggleHiddenPosts() {
                console.log('🔵 toggleHiddenPosts() called');
                // Simply update the category view to apply all filters with AND logic
                updateCategoryView();
            }

            function toggleLikedPosts() {
                console.log('🔵 toggleLikedPosts() called');
                // Simply update the category view to apply all filters with AND logic
                updateCategoryView();
            }

            function searchPosts(query) {
                console.log(`🔵 searchPosts('${query}') called`);
                const searchTerm = query.toLowerCase().trim();

                console.log(`🔍 Searching for: "${searchTerm}"`);

                if (searchTerm === '') {
                    // Remove search mode styling from body
                    document.body.classList.remove('search-mode');

                    // When search is cleared, restore normal category view
                    updateCategoryView();
                    return;
                }

                // Add search mode styling to body
                document.body.classList.add('search-mode');

                // Get all currently visible posts (based on filter row settings)
                const visiblePosts = document.querySelectorAll('.post-line[style*="block"]');
                console.log(`🔍 Found ${visiblePosts.length} visible posts to search through`);

                let matchCount = 0;
                let hiddenMatchCount = 0;

                visiblePosts.forEach(post => {
                    // Handle different types of posts (local, original, pending download)
                    let titleElement = post.querySelector('a.local') || post.querySelector('a.original');
                    if (!titleElement) {
                        // Skip posts that don't have a title link
                        return;
                    }

                    const title = titleElement.textContent.toLowerCase();
                    const newsletter = post.querySelector('.newsletter-name')?.textContent.toLowerCase() || '';
                    const category = post.querySelector('.category')?.textContent.toLowerCase() || '';

                    // Check if post matches search term
                    const matches = title.includes(searchTerm) ||
                                  newsletter.includes(searchTerm) ||
                                  category.includes(searchTerm);

                    if (matches) {
                        // Keep the post visible
                        post.style.display = 'block';
                        matchCount++;

                        // Add visual indicator if post is hidden
                        const isHidden = post.classList.contains('hidden-post') ||
                                       post.classList.contains('read-post') ||
                                       post.classList.contains('hide-post') ||
                                       post.classList.contains('liked-post');

                        if (isHidden) {
                            post.classList.add('search-result-hidden');
                            hiddenMatchCount++;
                        } else {
                            post.classList.remove('search-result-hidden');
                        }
                    } else {
                        // Hide posts that don't match search term
                        post.style.display = 'none';
                        post.classList.remove('search-result-hidden');
                    }
                });

                // Update subcategory links if they exist
                // showSubcategoryLinks(); // This function is removed

                console.log(`✅ Search completed: ${matchCount} matches found, ${hiddenMatchCount} hidden matches`);
            }



            // NEW: Update pending downloads count
            async function updatePendingDownloadsCount() {
                try {
                    const response = await fetch('/api/pending_downloads_count', {
                        method: 'GET'
                    });

                    if (response.ok) {
                        const result = await response.json();
                        const count = result.pending_downloads;

                        // Update the pending downloads indicator if it exists
                        const indicator = document.querySelector('[data-pending-downloads]');
                        if (indicator && count > 0) {
                            indicator.innerHTML = `
                                <strong>⏳ ${count} posts are downloading in the background</strong><br>
                                <small>New post links are visible above. Content will be available offline once downloads complete.</small>
                            `;
                        } else if (indicator && count === 0) {
                            // Hide the indicator if no pending downloads
                            indicator.style.display = 'none';
                        }
                    }
                } catch (error) {
                    console.log('ℹ️ Could not update pending downloads count:', error.message);
                }
            }



            function hideNotInterestingPosts() {
                console.log('🔵 hideNotInterestingPosts() called');
                const hiddenPosts = document.querySelectorAll('.hidden-post');
                hiddenPosts.forEach(post => {
                    post.style.display = 'none';
                });
            }
        </script>
        """

        html = HTML_TEMPLATE.format(
            title="Stored Newsletter Posts",
            css_path=self._get_css_path(1),
            content=content
        )
        index_path = self.base_dir / output_file
        index_path.write_text(html, encoding='utf-8')
        print(f"✅ Created {output_file} from index.json at {index_path}")

    def create_json_index(self, output_file: str = "index.json", input_file: str = "index.json") -> None:
        """Create a JSON index file using RSS feeds and Substack API for fresh content discovery.

        This method generates a fresh index.json from newsletters.md and current content,
        using RSS for fast post detection and API for complete content download.
        """
        # SAFETY CHECK: Allow regeneration only when index.json is missing
        if output_file == "index.json" and input_file == "index.json":
            json_path = self.base_dir / "index.json"
            if json_path.exists():
                print("❌ SAFETY CHECK: Cannot overwrite existing index.json!")
                print("❌ This would overwrite your manual curation decisions.")
                print("❌ If you really need to regenerate, delete index.json first or use a different output filename.")
                raise RuntimeError("JSON regeneration blocked for safety - JSON is source of truth")
            else:
                print("✅ index.json missing, allowing regeneration from newsletters.md + content discovery")
                print("🔄 This will create a fresh index.json with current content")

        # Load existing index.json to preserve personalization field values
        existing_personalization = {}
        if input_file != "none":
            json_path = self.base_dir / input_file
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    # Extract existing personalization field values by post URL
                    for newsletter_data in existing_data.get("newsletters", {}).values():
                        for post in newsletter_data.get("posts", []):
                            post_url = post.get('url', '')
                            if post_url:
                                existing_personalization[post_url] = {
                                    'not_interesting': post.get('not_interesting', False),
                                    'read': post.get('read', False),
                                    'like': post.get('like', False),
                                    'hide': post.get('hide', False)
                                }
                    print(f"ℹ️ Preserving personalization for {len(existing_personalization)} existing posts")
                except Exception as e:
                    print(f"⚠️ Could not load existing personalization: {e}")
        else:
            print("🔄 Starting fresh regeneration - no existing personalization to preserve")

        index_data = {
            "generated_at": datetime.now().isoformat(),
            "total_posts": 0,
            "categories": {},  # New: maps main_category -> list of subcategories
            "newsletters": {}
        }

        # Load newsletter configuration from markdown for proper names and categories
        newsletter_configs = self.load_newsletters_with_categories()
        print(f"📋 Loaded {len(newsletter_configs)} newsletter configurations from newsletters.md")

        # Build category-subcategory index for efficient UI generation
        category_index = {}
        for url, config in newsletter_configs.items():
            main_category = config['main_category']
            subcategory = config['subcategory']

            # Only add subcategories that are actually different from main category
            if subcategory and subcategory != main_category:
                if main_category not in category_index:
                    category_index[main_category] = set()
                category_index[main_category].add(subcategory)

        # Convert sets to sorted lists for JSON serialization
        for main_category, subcategories in category_index.items():
            index_data["categories"][main_category] = sorted(list(subcategories))

        print(f"📊 Built category index: {len(category_index)} main categories with subcategories")
        for main_category, subcategories in index_data["categories"].items():
            print(f"   {main_category}: {len(subcategories)} subcategories")

        # Create newsletter structure and discover current content
        for url, config in newsletter_configs.items():
            newsletter_url = config['url']
            display_name = config['name']
            main_category = config['main_category']
            subcategory = config['subcategory']
            tags = config['tags']

            print(f"🔍 Discovering content for: {display_name}")

            # Discover current posts via RSS + API
            current_posts = self._discover_newsletter_content(newsletter_url, display_name)

            # Apply personalization from existing data
            for post in current_posts:
                post_url = post.get('url', '')
                if post_url in existing_personalization:
                    post.update(existing_personalization[post_url])
                else:
                    # Set default personalization values
                    post.update({
                        'not_interesting': False,
                        'read': False,
                        'like': False,
                        'hide': False
                    })

                # Add category information
                post['main_category'] = main_category
                post['subcategory'] = subcategory
                # Only show subcategory if it exists and is different from main category
                if subcategory and subcategory != main_category:
                    post['category'] = f"{main_category} > {subcategory}"
                else:
                    post['category'] = main_category
                post['tags'] = tags

            # Sort posts chronologically (newest first)
            current_posts.sort(
                key=lambda x: x.get('published_at', '') or '1970-01-01',
                reverse=True
            )

            index_data["newsletters"][newsletter_url] = {
                "name": display_name,
                "url": newsletter_url,
                "main_category": main_category,
                "subcategory": subcategory,
                "category": f"{main_category} > {subcategory}" if subcategory and subcategory != main_category else main_category,
                "tags": tags,
                "post_count": len(current_posts),
                "posts": current_posts
            }
            index_data["total_posts"] += len(current_posts)

            print(f"📰 {display_name}: {len(current_posts)} posts discovered")

        # Sort the final data for consistency
        sorted_data = self._sort_json_data(index_data)

        json_path = self.base_dir / output_file
        json_path.write_text(json.dumps(sorted_data, indent=2), encoding='utf-8')
        print(f"✅ Created {output_file} with fresh content discovery at {json_path}")

    def _discover_newsletter_content(self, newsletter_url: str, display_name: str) -> List[Dict]:
        """Discover current posts for a newsletter using RSS + API approach.

        Args:
            newsletter_url: The newsletter's URL
            display_name: Human-readable name for logging

        Returns:
            List of post dictionaries with complete metadata
        """
        try:
            print(f"  📡 Checking RSS feed for {display_name}...")

            # Step 1: Try RSS feed first (fast discovery)
            rss_posts = self._get_posts_from_rss(newsletter_url)
            if rss_posts:
                print(f"  ✅ RSS: Found {len(rss_posts)} posts")

                # Step 2: Download content via API for each post
                complete_posts = []
                for rss_post in rss_posts:
                    try:
                        complete_post = self._download_post_via_api(rss_post, newsletter_url)
                        if complete_post:
                            complete_posts.append(complete_post)
                    except Exception as e:
                        print(f"  ⚠️ Failed to download post {rss_post.get('title', 'Unknown')}: {e}")
                        # Add RSS data as fallback
                        complete_posts.append(rss_post)

                return complete_posts
            else:
                print(f"  ⚠️ RSS: No posts found, trying API fallback...")
                # Fallback to direct API discovery
                return self._discover_posts_via_api(newsletter_url)

        except Exception as e:
            print(f"  ❌ Content discovery failed for {display_name}: {e}")
            return []

    def _get_posts_from_rss(self, newsletter_url: str) -> List[Dict]:
        """Get posts from RSS feed for a newsletter."""
        try:
            # Try multiple RSS URL patterns
            rss_patterns = []

            if 'substack.com' in newsletter_url:
                # Substack RSS format: https://newsletter.substack.com/feed
                rss_patterns.append(newsletter_url.rstrip('/') + '/feed')
            else:
                # Try common RSS patterns for non-Substack sites
                base_url = newsletter_url.rstrip('/')
                rss_patterns.extend([
                    base_url + '/feed',
                    base_url + '/rss',
                    base_url + '/feed.xml',
                    base_url + '/rss.xml',
                    base_url + '/atom.xml',
                    base_url + '/blog/feed',
                    base_url + '/blog/rss'
                ])

            # Import feedparser here to avoid dependency issues
            try:
                import feedparser
            except ImportError:
                print("    ⚠️ feedparser not available, skipping RSS")
                return []

            # Try each RSS pattern until one works
            for rss_url in rss_patterns:
                try:
                    print(f"    🔍 Trying RSS: {rss_url}")
                    feed = feedparser.parse(rss_url)

                    if not feed.bozo and feed.entries:
                        print(f"    ✅ RSS found: {len(feed.entries)} entries")
                        posts = []
                        for entry in feed.entries[:20]:  # Limit to recent posts
                            post = {
                                'title': entry.get('title', 'No Title'),
                                'url': entry.get('link', ''),
                                'published_at': self._parse_rss_date(entry.get('published', '')),
                                'author': entry.get('author', 'Unknown'),
                                'summary': entry.get('summary', ''),
                                'content_path': None  # Will be set when downloaded
                            }
                            posts.append(post)
                        return posts
                    else:
                        if feed.bozo:
                            print(f"    ⚠️ RSS malformed: {feed.bozo_exception}")
                        else:
                            print(f"    ⚠️ No entries found")

                except Exception as e:
                    print(f"    ⚠️ RSS failed for {rss_url}: {e}")
                    continue

            print(f"    ❌ All RSS patterns failed for {newsletter_url}")
            return []

        except Exception as e:
            print(f"    ❌ RSS discovery failed: {e}")
            return []

    def _parse_rss_date(self, date_str: str) -> str:
        """Parse RSS date string to ISO format."""
        if not date_str:
            return datetime.now().isoformat()

        try:
            # Try common RSS date formats
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception:
            try:
                # Fallback to datetime parsing
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue
            except Exception:
                pass

        # Final fallback
        print(f"    ⚠️ Could not parse date: {date_str}, using current time")
        return datetime.now().isoformat()

    def _download_post_via_api(self, rss_post: Dict, newsletter_url: str) -> Dict:
        """Download complete post content via Substack API."""
        try:
            # Check if content already exists locally
            post_url = rss_post.get('url', '')
            if not post_url:
                return rss_post

            # Generate safe filename for local storage
            safe_name = self._get_safe_name(newsletter_url)
            post_id = post_url.split('/')[-1] or 'post'
            content_filename = f"{post_id}.html"
            content_path = f"data/content/{safe_name}/{content_filename}"

            # Check if we already have this content
            full_content_path = self.base_dir / content_path
            if full_content_path.exists():
                print(f"    📁 Content already exists: {content_path}")
                rss_post['content_path'] = content_path
                return rss_post

            print(f"    ⬇️ Downloading content for: {rss_post.get('title', 'Unknown')}")

            # Try to download via Substack API
            try:
                import substack_api
                # This would use the substack_api library to download content
                # For now, we'll just mark it as needing download
                rss_post['content_path'] = content_path
                rss_post['needs_download'] = True
                return rss_post
            except ImportError:
                print("    ⚠️ substack_api not available, marking for later download")
                rss_post['content_path'] = content_path
                rss_post['needs_download'] = True
                return rss_post

        except Exception as e:
            print(f"    ❌ API download failed: {e}")
            return rss_post

    def _discover_posts_via_api(self, newsletter_url: str) -> List[Dict]:
        """Fallback method to discover posts via API when RSS fails."""
        try:
            print(f"    🔍 Trying API discovery for {newsletter_url}")

            # Try to use substack_api library for discovery
            try:
                import substack_api
                print(f"    📡 Using Substack API for {newsletter_url}")

                # This would use the substack_api library to discover posts
                # For now, return empty list to indicate no posts found
                # TODO: Implement actual API discovery
                return []

            except ImportError:
                print(f"    ⚠️ substack_api not available for {newsletter_url}")
                return []

        except Exception as e:
            print(f"    ❌ API discovery failed: {e}")
            return []

    def create_rss_feed(self) -> None:
        """Create an RSS feed of all posts."""
        # This could be implemented later if needed
        pass

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate index files for Daily Briefing pAIa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  SAFETY WARNING: JSON regeneration is blocked by default!
JSON is the source of truth - regenerating it will overwrite your curation decisions.

Examples:
  python src/web/index_generator.py                    # Use default index.json (HTML only)
  python src/web/index_generator.py index_test.json    # Use index_test.json (HTML only)
  python src/web/index_generator.py --html-only        # Only generate HTML
  python src/web/index_generator.py --json-only        # Only generate JSON (SAFE: uses different output file)

To regenerate main index.json (DANGEROUS):
  python src/web/index_generator.py --output-json index_new.json  # Creates new file, doesn't overwrite
        """
    )

    parser.add_argument(
        'input_file',
        nargs='?',
        default='index.json',
        help='Input JSON file to generate from (default: index.json)'
    )

    parser.add_argument(
        '--html-only',
        action='store_true',
        help='Only generate HTML file, skip JSON generation'
    )

    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only generate JSON file, skip HTML generation'
    )

    parser.add_argument(
        '--output-html',
        default='index.html',
        help='Output HTML filename (default: index.html)'
    )

    parser.add_argument(
        '--output-json',
        default='index.json',
        help='Output JSON filename (default: index.json)'
    )

    parser.add_argument(
        '--regenerate',
        action='store_true',
        help='Regenerate index.json from newsletters.md using RSS + API (for testing only)'
    )

    args = parser.parse_args()

    try:
        # Create IndexGenerator instance
        ig = IndexGenerator()

        # Check if input file exists (only when not regenerating)
        if not args.regenerate:
            input_path = Path(args.input_file)
            if not input_path.exists():
                # Try in data directory
                input_path = Path("data") / args.input_file
                if not input_path.exists():
                    print(f"❌ Error: Input file '{args.input_file}' not found")
                    print(f"   Available files in current dir: {list(Path('.').glob('*.json'))}")
                    print(f"   Available files in data dir: {list(Path('data').glob('*.json'))}")
                    sys.exit(1)

        if not args.html_only:
            if args.regenerate:
                # Allow regeneration from scratch using new RSS + API approach
                print("🔄 Regenerating index.json from newsletters.md using RSS + API...")
                ig.create_json_index(output_file=args.output_json, input_file="none")
            else:
                # SAFETY CHECK: Allow regeneration only when index.json is missing
                if args.output_json == "index.json":
                    json_path = Path("data/index.json")
                    if json_path.exists():
                        print("❌ SAFETY CHECK: Cannot overwrite existing index.json!")
                        print("❌ Use --output-json with a different filename to create new JSON files.")
                        print("❌ Example: --output-json index_new.json")
                        print("❌ Or use --regenerate to regenerate from newsletters.md")
                        sys.exit(1)
                    else:
                        print("✅ index.json missing, allowing regeneration from newsletters.md + content files")

                print(f"📊 Generating JSON index from {args.input_file}...")
                ig.create_json_index(output_file=args.output_json, input_file=args.input_file)

        if not args.json_only:
            print(f"🌐 Generating HTML from {args.input_file}...")
            ig.create_index_html(output_file=args.output_html)

        print("✅ Index generation completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
