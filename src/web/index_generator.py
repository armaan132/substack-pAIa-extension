import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime


# Constants
CSS_PATH = 'src/web/static/css/substack-original.css'
PROJECT_ROOT = Path(__file__).parent.parent.parent
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

                        # If no subcategory is set, use the main category as subcategory
                        effective_subcategory = current_subcategory if current_subcategory != "Uncategorized" else current_main_category
                        
                        newsletters_by_url[url] = {
                            'name': name,
                            'url': url,
                            'tags': tags,
                            'main_category': current_main_category,
                            'subcategory': effective_subcategory,
                            'category': f"{current_main_category} > {effective_subcategory}"  # For backward compatibility
                        }
        except Exception as e:
            print(f"Error loading {md_path}: {e}")

        return newsletters_by_url

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
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="All" onclick="console.log('🟢 Radio button clicked: All'); filterByMainCategory('All')"> All
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="Science" onclick="console.log('🟢 Radio button clicked: Science'); filterByMainCategory('Science')"> Science
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="News and Opinion" onclick="console.log('🟢 Radio button clicked: News and Opinion'); filterByMainCategory('News and Opinion')"> News and Opinion
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="checkbox" id="show-hidden" onclick="console.log('🟢 Hidden posts checkbox clicked'); toggleHiddenPosts()"> <span title="Include Hidden Posts">Hidden Posts</span>
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="checkbox" id="show-liked" onclick="console.log('🟢 Liked posts checkbox clicked'); toggleLikedPosts()"> <span title="Only Liked Posts">Liked Posts</span>
            </label>
        </div>
        
        <!-- Subcategory Selection (hidden by default) -->
        <div id="subcategory-row" class="subcategory-row" style="display: none; margin: 15px 0; padding: 15px; background: #fff3cd; border-radius: 5px; border: 1px solid #ffeaa7;">
            <h4 style="margin: 0 0 10px 0; color: #856404; font-size: 1em;">Filter by Subcategory:</h4>
            <div id="subcategory-buttons" class="subcategory-buttons">
                <!-- Will be populated dynamically -->
            </div>
        </div>
        
        <!-- Update and Search Section -->
        <div style="display: flex; gap: 20px; margin: 20px 0;">
            <!-- Update Button -->
            <div style="flex: 0 0 auto;">
                <button id="update-btn" onclick="triggerUpdate()" 
                        style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">
                    🔄 Update Content
                </button>
                <div id="update-status" style="margin-top: 5px; font-size: 12px; color: #666;"></div>
            </div>
            
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

        for newsletter_name, newsletter_data in index_data["newsletters"].items():
            for post in newsletter_data["posts"]:
                # Add newsletter info to each post
                post['newsletter_name'] = newsletter_data['name']
                all_posts.append(post)

        # Sort all posts chronologically (newest first)
        all_posts.sort(
            key=lambda x: x.get('published_at', '') or '',
            reverse=True
        )

        # Generate posts HTML (chronological order)
        posts_html = ""
        for post in all_posts:
            title = post['title']
            date = post.get('published_at') or 'No date'
            display_date = self._format_date(date)
            newsletter_name = post['newsletter_name']
            # Handle missing category field gracefully
            category = post.get('category', 'Uncategorized')
            
            # Handle content path calculation more robustly
            try:
                if Path(post['content_path']).is_absolute():
                    content_path = Path(post['content_path']).relative_to(self.base_dir)
                else:
                    content_path = post['content_path']
            except ValueError:
                # Fallback: use the filename only
                content_path = Path(post['content_path']).name
            
            not_interesting = post.get('not_interesting', False)
            read = post.get('read', False)
            like = post.get('like', False)
            hide = post.get('hide', False)
            post_id = post.get('url', '').split('/')[-1]

            # Apply liked-post class if post is both read AND liked
            liked_post_class = 'liked-post' if read and like else ''
            
            posts_html += f"""
            <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}" 
                 data-post-id="{post_id}"
                 data-main-category="{post.get('main_category', 'Uncategorized')}"
                 data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                <span class="newsletter-name">{newsletter_name}</span>
                <a href="{post['url']}" class="local" target="_blank">{title}</a>
                <a href="{content_path}" class="original" title="">📄</a>
                <span class="date">{display_date}</span>
                <span class="category">({post.get('main_category', 'Uncategorized')}{f' > {post.get("subcategory", "Uncategorized")}' if post.get('subcategory') != post.get('main_category') else ''})</span>
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

        # Add posts to the page
        content += f"""
        <div id="posts-container">
            {posts_html}
        </div>
        """

        # Add JavaScript for view switching, main category filtering, and not_interesting functionality
        content += """
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
                
                // Restore saved category selection from localStorage
                const savedCategory = localStorage.getItem('selectedMainCategory') || 'All';
                currentMainCategory = savedCategory;
                
                // Set the radio button to match the saved selection
                const radioButton = document.querySelector(`input[name="main-category"][value="${savedCategory}"]`);
                if (radioButton) {
                    radioButton.checked = true;
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
                
                // Get unique subcategories for the selected main category
                const subcategories = new Set();
                const posts = document.querySelectorAll('.post-line');
                posts.forEach(post => {
                    const postMainCategory = post.getAttribute('data-main-category');
                    if (postMainCategory === mainCategory) {
                        const subcategory = post.getAttribute('data-subcategory');
                        if (subcategory && subcategory !== 'Uncategorized') {
                            subcategories.add(subcategory);
                        }
                    }
                });
                
                if (subcategories.size === 0) {
                    subcategoryRow.style.display = 'none';
                    return;
                }
                
                // Populate subcategory buttons
                subcategoryButtons.innerHTML = '';
                const sortedSubcategories = Array.from(subcategories).sort();
                
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
                
                // Get current filter states
                const selectedCategory = document.querySelector('input[name="main-category"]:checked').value;
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

            async function triggerUpdate() {
                console.log('🔵 triggerUpdate() called');
                
                const updateBtn = document.getElementById('update-btn');
                const updateStatus = document.getElementById('update-status');
                
                // Disable button and show loading state
                updateBtn.disabled = true;
                updateBtn.innerHTML = '⏳ Updating...';
                updateBtn.style.background = '#6c757d';
                updateStatus.innerHTML = '🔄 Starting incremental update...';
                
                try {
                    const response = await fetch('/api/update_content', {
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
                        updateStatus.innerHTML = `✅ Update completed! ${result.message || ''}`;
                        updateBtn.style.background = '#28a745';
                        
                        // Reload the page to show new content
                        setTimeout(() => {
                            updateStatus.innerHTML = '🔄 Reloading page to show new content...';
                            location.reload();
                        }, 2000);
                    } else {
                        throw new Error(result.error || 'Update failed');
                    }
                    
                } catch (error) {
                    console.error('❌ Update error:', error);
                    updateStatus.innerHTML = `❌ Update failed: ${error.message}`;
                    updateBtn.style.background = '#dc3545';
                } finally {
                    // Re-enable button
                    updateBtn.disabled = false;
                    updateBtn.innerHTML = '🔄 Update Content';
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
                
                let matchCount = 0;
                let hiddenMatchCount = 0;
                
                visiblePosts.forEach(post => {
                    const title = post.querySelector('a.local').textContent.toLowerCase();
                    const newsletter = post.querySelector('.newsletter-name').textContent.toLowerCase();
                    const category = post.querySelector('.category, .subcategory')?.textContent.toLowerCase() || '';
                    
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
        """Create a JSON index file for programmatic access.
        
        ⚠️ WARNING: This method regenerates JSON from content files!
        This will overwrite manual deletions and curation decisions.
        Use with extreme caution or disable entirely.
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
                print("✅ index.json missing, allowing regeneration from newsletters.md")
                print("🔄 This will create a fresh index.json with newsletter structure")
        
        # Load existing index.json to preserve personalization field values
        existing_not_interesting = {}
        existing_read = {}
        existing_like = {}
        existing_hide = {}
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
                            if 'not_interesting' in post:
                                existing_not_interesting[post_url] = post['not_interesting']
                            if 'read' in post:
                                existing_read[post_url] = post['read']
                            if 'like' in post:
                                existing_like[post_url] = post['like']
                            if 'hide' in post:
                                existing_hide[post_url] = post['hide']
                print(f"ℹ️ Preserving {len(existing_not_interesting)} existing not_interesting values, {len(existing_read)} read values, {len(existing_like)} like values, and {len(existing_hide)} hide values")
            except Exception as e:
                print(f"⚠️ Could not load existing values: {e}")
        
        index_data = {
            "generated_at": datetime.now().isoformat(),
            "total_posts": 0,
            "newsletters": {}
        }
        
        # Load newsletter configuration from markdown for proper names and categories
        newsletter_configs = self.load_newsletters_with_categories()
        print(f"📋 Loaded {len(newsletter_configs)} newsletter configurations from newsletters.md")
        
        # Create newsletter structure from newsletters.md (content files are optional)
        for url, config in newsletter_configs.items():
            newsletter_url = config['url']
            display_name = config['name']
            main_category = config['main_category']
            subcategory = config['subcategory']
            tags = config['tags']
            
            # Check if we have existing posts for this newsletter (optional)
            existing_posts = []
            try:
                # Try to load existing posts if they exist, but don't require them
                newsletter_name = self._get_safe_name(newsletter_url)
                metadata_dir = self.base_dir / "metadata" / newsletter_name
                if metadata_dir.exists():
                    for metadata_file in metadata_dir.glob("*.json"):
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                post_data = json.load(f)
                                # Preserve existing personalization values
                                post_url = post_data.get('url', '')
                                if post_url:
                                    post_data['not_interesting'] = existing_not_interesting.get(post_url, False)
                                    post_data['read'] = existing_read.get(post_url, False)
                                    post_data['like'] = existing_like.get(post_url, False)
                                    post_data['hide'] = existing_hide.get(post_url, False)
                                    post_data['main_category'] = main_category
                                    post_data['subcategory'] = subcategory
                                    post_data['category'] = f"{main_category} > {subcategory}"
                                    post_data['tags'] = tags
                                    existing_posts.append(post_data)
                        except Exception as e:
                            print(f"⚠️ Could not load post metadata {metadata_file}: {e}")
                            continue
            except Exception as e:
                print(f"⚠️ Could not check existing posts for {display_name}: {e}")
            
            # Sort posts chronologically (newest first)
            existing_posts.sort(
                key=lambda x: x.get('published_at', '') or '1970-01-01',
                reverse=True
            )
            
            index_data["newsletters"][newsletter_url] = {
                "name": display_name,
                "url": newsletter_url,
                "main_category": main_category,
                "subcategory": subcategory,
                "category": f"{main_category} > {subcategory}",
                "tags": tags,
                "post_count": len(existing_posts),
                "posts": existing_posts
            }
            index_data["total_posts"] += len(existing_posts)
            
            print(f"📰 {display_name}: {len(existing_posts)} existing posts (if any)")
        
        json_path = self.base_dir / output_file
        json_path.write_text(json.dumps(index_data, indent=2), encoding='utf-8')
        print(f"Created {output_file} with personalization fields and categories at {json_path}")

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
    
    args = parser.parse_args()
    
    try:
        # Check if input file exists (try current dir and data dir)
        input_path = Path(args.input_file)
        if not input_path.exists():
            # Try in data directory
            input_path = Path("data") / args.input_file
            if not input_path.exists():
                print(f"❌ Error: Input file '{args.input_file}' not found")
                print(f"   Available files in current dir: {list(Path('.').glob('*.json'))}")
                print(f"   Available files in data dir: {list(Path('data').glob('*.json'))}")
                sys.exit(1)
        
        # Create IndexGenerator instance
        ig = IndexGenerator()
        
        if not args.html_only:
            # SAFETY CHECK: Allow regeneration only when index.json is missing
            if args.output_json == "index.json":
                json_path = Path("data/index.json")
                if json_path.exists():
                    print("❌ SAFETY CHECK: Cannot overwrite existing index.json!")
                    print("❌ Use --output-json with a different filename to create new JSON files.")
                    print("❌ Example: --output-json index_new.json")
                    print("❌ Or delete index.json first to allow regeneration from newsletters.md")
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