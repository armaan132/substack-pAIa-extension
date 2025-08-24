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
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
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
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
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
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
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
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
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

    def create_index_html(self) -> None:
        """Create an index.html file from the data in index.json."""
        # Load data from index.json
        json_path = self.base_dir / "index.json"
        if not json_path.exists():
            raise FileNotFoundError(f"index.json not found at {json_path}. Generate it first with create_json_index().")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        content = """
        <!--h1>Recent Newsletter Posts</h-->
        
        <!-- Main Category Selection and Visibility Controls -->
        <div class="main-category-section" style="margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px;">
            <!--h3 style="margin-top: 0;">Select Main Category:</h3-->
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="All" checked onclick="filterByMainCategory('All')"> All
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="Science" onclick="filterByMainCategory('Science')"> Science
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="radio" name="main-category" value="News and Opinion" onclick="filterByMainCategory('News and Opinion')"> News and Opinion
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="checkbox" id="show-hidden" onclick="toggleHiddenPosts()"> Hidden Posts
            </label>
            <label style="margin-right: 20px; cursor: pointer;">
                <input type="checkbox" id="show-liked" onclick="toggleLikedPosts()"> Liked Posts
            </label>
        </div>
        
        <!-- Search Bar -->
        <div class="search-bar" style="margin: 20px 0; padding: 15px; background: #e8f5e8; border-radius: 5px;">
            <input type="text" id="search-input" placeholder="Search posts by title, newsletter, or content..." 
                   style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                   oninput="searchPosts(this.value)">
        </div>
        

        
        <style>
            .post-line { margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
            .post-line a { margin-right: 15px; text-decoration: none; }
            .post-line a.local { color: #0066cc; }
            .post-line a.original { color: #666; font-size: 0.9em; }
            .newsletter-name { color: #333; font-weight: bold; margin-right: 10px; }
            .date { color: #888; font-size: 0.8em; margin-left: 10px; }
            .category { color: #666; font-size: 0.8em; margin-left: 10px; }
            .action-btn { 
                background: #f5f5f5; 
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
                background: #4caf50; 
                color: white; 
                border-color: #4caf50;
            }
            
            /* Individual button colors when marked */
            .action-btn.read-btn.marked { background: #2196f3; border-color: #2196f3; }
            .action-btn.not-interesting-btn.marked { background: #ff6b6b; border-color: #ff6b6b; }
            .action-btn.like-btn.marked { background: #4caf50; border-color: #4caf50; color: white; }
            .action-btn.hide-btn.marked { background: #9c27b0; border-color: #9c27b0; }
            
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

        # Collect all posts from the JSON data and organize by subcategory
        posts_by_subcategory = {}
        all_posts = []

        for newsletter_name, newsletter_data in index_data["newsletters"].items():
            for post in newsletter_data["posts"]:
                # Add newsletter info to each post
                post['newsletter_name'] = newsletter_data['name']
                
                # Group by subcategory (which is more specific than category)
                subcategory = post.get('subcategory', 'Uncategorized')
                posts_by_subcategory.setdefault(subcategory, []).append(post)
                all_posts.append(post)

        # Sort all posts by date for date view
        all_posts.sort(
            key=lambda x: x.get('published_at', '') or '',
            reverse=True
        )

        # Generate subcategory view
        category_content = ""
        for subcategory in sorted(posts_by_subcategory.keys()):
            # Get the main category from the first post in this subcategory
            main_category = posts_by_subcategory[subcategory][0].get('main_category', 'Uncategorized') if posts_by_subcategory[subcategory] else 'Uncategorized'
            category_content += f'<h2 class="subcategory-header" data-main-category="{main_category}">{subcategory}</h2>\n'
            category_posts = sorted(
                posts_by_subcategory[subcategory],
                key=lambda x: x.get('published_at', '') or '',
                reverse=True
            )

            for post in category_posts:
                title = post['title']
                date = post.get('published_at') or 'No date'
                display_date = self._format_date(date)
                newsletter_name = post['newsletter_name']
                
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
                
                category_content += f"""
                <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}" 
                     data-post-id="{post_id}" 
                     data-main-category="{post.get('main_category', 'Uncategorized')}"
                     data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                    <span class="newsletter-name">{newsletter_name}</span>
                    <a href="{content_path}" class="local">{title}</a>
                    <a href="{post['url']}" class="original" target="_blank">🔗 Original</a>
                    <span class="date">{display_date}</span>
                    {f'<span class="subcategory" style="color: #666; font-size: 0.8em; margin-left: 10px;">({post.get("subcategory", "Uncategorized")})</span>' if post.get('subcategory') != post.get('main_category') else ''}
                    <button class="action-btn read-btn {'' if not read else 'marked'}" 
                            onclick="toggleRead('{post_id}', this)"
                            data-tooltip="Mark as Read">
                        {'' if not read else '✓ '}👁️
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
                        {'' if not hide else '✓ '}🚫
                    </button>
                </div>
                """

        # Generate date view
        date_content = ""
        for post in all_posts:
            title = post['title']
            date = post.get('published_at') or 'No date'
            display_date = self._format_date(date)
            newsletter_name = post['newsletter_name']
            category = post['category']
            
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
            
            date_content += f"""
            <div class="post-line {'' if not not_interesting else 'hidden-post'} {'' if not read else 'read-post'} {liked_post_class} {'' if not hide else 'hide-post'}" 
                 data-post-id="{post_id}"
                 data-main-category="{post.get('main_category', 'Uncategorized')}"
                 data-subcategory="{post.get('subcategory', 'Uncategorized')}">
                <span class="newsletter-name">{newsletter_name}</span>
                <a href="{content_path}" class="local">{title}</a>
                <a href="{post['url']}" class="original" target="_blank">🔗 Original</a>
                <span class="date">{display_date}</span>
                <span class="category">({post.get('main_category', 'Uncategorized')}{f' > {post.get("subcategory", "Uncategorized")}' if post.get('subcategory') != post.get('main_category') else ''})</span>
                <button class="action-btn read-btn {'' if not read else 'marked'}" 
                        onclick="toggleRead('{post_id}', this)"
                        data-tooltip="Mark as Read">
                    {'' if not read else '✓ '}👁️
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
                    {'' if not hide else '✓ '}🚫
                </button>
            </div>
            """

        # Add both views to content
        content += f"""
        <div id="category-view" class="view-section">
            {category_content}
        </div>
        
        <div id="date-view" class="view-section show">
            {date_content}
        </div>
        """

        # Add JavaScript for view switching, main category filtering, and not_interesting functionality
        content += """
        <script>
            let currentMainCategory = 'All';
            let currentSubcategory = null;
            
            // Hide posts marked as hidden, read, or hide on page load (liked posts stay visible)
            document.addEventListener('DOMContentLoaded', function() {
                hideNotInterestingPosts();
                hideReadPosts();
                hideHidePosts();
                
                // Initialize subcategory links based on current category selection
                showSubcategoryLinks();
                
                // Apply category filtering based on the selected radio button
                const selectedCategory = document.querySelector('input[name="main-category"]:checked').value;
                currentMainCategory = selectedCategory;
                updateCategoryView();
            });
            
            function hideNotInterestingPosts() {
                const hiddenPosts = document.querySelectorAll('.hidden-post');
                hiddenPosts.forEach(post => {
                    post.style.display = 'none';
                });
            }
            
            function hideReadPosts() {
                const readPosts = document.querySelectorAll('.read-post');
                readPosts.forEach(post => {
                    post.style.display = 'none';
                });
            }



            function hideHidePosts() {
                const hidePosts = document.querySelectorAll('.hide-post');
                hidePosts.forEach(post => {
                    post.style.display = 'none';
                });
            }
            
            function filterByMainCategory(mainCategory) {
                currentMainCategory = mainCategory;
                currentSubcategory = null; // Clear subcategory filter when switching main categories
                
                // Update the display based on current category
                updateCategoryView();
                
                // Always show subcategory links when a specific category is selected
                showSubcategoryLinks();
            }
            

            
            function showSubcategoryLinks() {
                // Get the current main category
                const selectedCategory = document.querySelector('input[name="main-category"]:checked').value;
                
                // Don't show subcategories when "All" is selected
                if (selectedCategory === 'All') {
                    const linksContainer = document.getElementById('subcategory-links');
                    if (linksContainer) {
                        linksContainer.style.display = 'none';
                    }
                    return;
                }
                
                // Find or create the subcategory links container
                let linksContainer = document.getElementById('subcategory-links');
                if (!linksContainer) {
                    linksContainer = document.createElement('div');
                    linksContainer.id = 'subcategory-links';
                    linksContainer.style.cssText = 'margin: 20px 0; padding: 15px; background: #fff3cd; border-radius: 5px; border: 1px solid #ffeaa7;';
                    
                    // Insert after the main category section (back to original placement)
                    const mainCategorySection = document.querySelector('.main-category-section');
                    mainCategorySection.parentNode.insertBefore(linksContainer, mainCategorySection.nextSibling);
                }
                
                // Make sure the container is visible
                linksContainer.style.display = 'block';
                
                // Clear existing links
                linksContainer.innerHTML = '';
                
                // Show only subcategories for the selected main category
                const subcategories = new Set();
                document.querySelectorAll('.subcategory-header').forEach(header => {
                    const headerMainCategory = header.getAttribute('data-main-category');
                    if (headerMainCategory === selectedCategory) {
                        const subcategory = header.textContent.trim();
                        // Only add if subcategory is different from main category
                        if (subcategory !== selectedCategory) {
                            subcategories.add(subcategory);
                        }
                    }
                });
                
                if (subcategories.size > 0) {
                    linksContainer.innerHTML = '<h4 style="margin-top: 0; color: #856404;">Subcategories for ' + selectedCategory + ':</h4>';
                    Array.from(subcategories).sort().forEach(subcategory => {
                        const link = document.createElement('a');
                        link.href = '#';
                        link.textContent = subcategory;
                        link.style.cssText = 'display: inline-block; margin: 5px 10px 5px 0; padding: 5px 10px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px; text-decoration: none; color: #495057; cursor: pointer;';
                        link.onclick = function(e) {
                            e.preventDefault();
                            scrollToSubcategory(subcategory);
                        };
                        linksContainer.appendChild(link);
                    });
                    linksContainer.style.display = 'block';
                } else {
                    // Hide the container when no subcategories exist
                    linksContainer.style.display = 'none';
                }
            }
            
            function scrollToSubcategory(subcategoryName) {
                currentSubcategory = subcategoryName;
                
                // Filter posts to show only those in the selected subcategory
                filterPostsBySubcategory(subcategoryName);
                
                // Scroll to top of page to show filtered results
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            
            function filterPostsBySubcategory(subcategoryName) {
                const allPosts = document.querySelectorAll('.post-line');
                
                allPosts.forEach(post => {
                    const postSubcategory = post.getAttribute('data-subcategory');
                    const postMainCategory = post.getAttribute('data-main-category');
                    
                    // Show post if it matches both main category and subcategory
                    const mainCategoryMatches = currentMainCategory === 'All' || postMainCategory === currentMainCategory;
                    const subcategoryMatches = postSubcategory === subcategoryName;
                    
                    if (mainCategoryMatches && subcategoryMatches) {
                        // Only show if not marked as hidden, read, hide, or liked
                        if (post.classList.contains('hidden-post') || post.classList.contains('read-post') || 
                            post.classList.contains('hide-post') || post.classList.contains('liked-post')) {
                            post.style.display = 'none';
                        } else {
                            post.style.display = 'block';
                        }
                    } else {
                        post.style.display = 'none';
                    }
                });
                
                // Hide all subcategory headers when filtering by subcategory
                const subcategoryHeaders = document.querySelectorAll('.subcategory-header');
                subcategoryHeaders.forEach(header => {
                    header.style.display = 'none';
                });
                
                // Highlight the active subcategory button
                const subcategoryLinks = document.querySelectorAll('#subcategory-links a');
                subcategoryLinks.forEach(link => {
                    if (link.textContent.trim() === subcategoryName) {
                        link.style.background = '#007bff';
                        link.style.color = 'white';
                        link.style.borderColor = '#007bff';
                    } else {
                        link.style.background = '#f8f9fa';
                        link.style.color = '#495057';
                        link.style.borderColor = '#dee2e6';
                    }
                });
            }
            
            function updateCategoryView() {
                // Clear any subcategory filter
                currentSubcategory = null;
                
                // Filter posts by main category and update the display
                const allPosts = document.querySelectorAll('.post-line');
                
                allPosts.forEach(post => {
                    const postMainCategory = post.getAttribute('data-main-category');
                    const categoryMatches = currentMainCategory === 'All' || postMainCategory === currentMainCategory;
                    
                    if (categoryMatches) {
                        // Only show if not marked as hidden, read, hide, or liked (liked posts are hidden by default)
                        if (post.classList.contains('hidden-post') || post.classList.contains('read-post') || 
                            post.classList.contains('hide-post') || post.classList.contains('liked-post')) {
                            post.style.display = 'none';
                        } else {
                            post.style.display = 'block';
                        }
                    } else {
                        post.style.display = 'none';
                    }
                });
                
                // Always hide subcategory headers for a clean view
                const subcategoryHeaders = document.querySelectorAll('.subcategory-header');
                subcategoryHeaders.forEach(header => {
                    header.style.display = 'none';
                });
                
                // Sort visible posts by date (most recent first) for all views
                const visiblePosts = Array.from(allPosts).filter(post => {
                    return post.style.display !== 'none';
                });
                
                // Sort by date (posts have date info in their text content)
                visiblePosts.sort((a, b) => {
                    const dateA = a.querySelector('.date')?.textContent || '';
                    const dateB = b.querySelector('.date')?.textContent || '';
                    
                    // Parse dates properly for sorting
                    const parseDate = (dateStr) => {
                        // Handle formats like "Sep 4, 2023", "Jul 9, 2025"
                        const match = dateStr.match(/(\w{3})\s+(\d{1,2}),?\s+(\d{4})/);
                        if (match) {
                            const month = match[1];
                            const day = parseInt(match[2]);
                            const year = parseInt(match[3]);
                            
                            // Convert month abbreviation to number
                            const monthMap = {
                                'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                                'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
                            };
                            
                            const monthNum = monthMap[month] || 0;
                            return new Date(year, monthNum, day);
                        }
                        return new Date(0); // Invalid date
                    };
                    
                    const parsedDateA = parseDate(dateA);
                    const parsedDateB = parseDate(dateB);
                    
                                    // Sort by actual date (most recent first)
                return parsedDateB - parsedDateA;
            });
                
            // Reorder posts in the DOM
            const container = visiblePosts[0]?.parentNode;
            if (container) {
                visiblePosts.forEach(post => {
                    container.appendChild(post);
                });
            }
                
                // Reset subcategory button highlighting
                const subcategoryLinks = document.querySelectorAll('#subcategory-links a');
                subcategoryLinks.forEach(link => {
                    link.style.background = '#f8f9fa';
                    link.style.color = '#495057';
                    link.style.borderColor = '#dee2e6';
                });
            }
            

            
            function toggleNotInteresting(postId, button) {
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
                        console.log(`✅ Post ${postId} updated successfully`);
                    } else {
                        console.error(`❌ Failed to update post ${postId}:`, result.error);
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
                    console.error('❌ Error updating post:', error);
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
            }
            
            async function updatePostRead(postId, read) {
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

            async function updatePostHide(postId, hide) {
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
                        postLine.classList.remove('hide-post');
                        postLine.style.display = 'block'; // Show the post
                    } else {
                        button.classList.add('marked');
                        button.innerHTML = '✓ Hide';
                        postLine.classList.add('hide-post');
                        postLine.style.display = 'none'; // Hide the post
                    }
                }
            }
            
            function toggleHiddenPosts() {
                const showHidden = document.getElementById('show-hidden').checked;
                const allPosts = document.querySelectorAll('.post-line');
                
                allPosts.forEach(post => {
                    const isHidden = post.classList.contains('hidden-post') || 
                                   post.classList.contains('read-post') || 
                                   post.classList.contains('hide-post') || 
                                   post.classList.contains('liked-post');
                    
                    if (showHidden) {
                        // Show ALL posts (including hidden ones)
                        post.style.display = 'block';
                    } else {
                        // Hide posts that are marked as hidden, but respect current category filter
                        const postMainCategory = post.getAttribute('data-main-category');
                        const categoryMatches = currentMainCategory === 'All' || postMainCategory === currentMainCategory;
                        if (categoryMatches && !isHidden) {
                            post.style.display = 'block';
                        } else {
                            post.style.display = 'none';
                        }
                    }
                });
                
                // Update subcategory links if in category view
                if (document.getElementById('category-view').classList.contains('show') && document.getElementById('subcategory-links')) {
                    showSubcategoryLinks();
                }
            }
            
            function toggleLikedPosts() {
                const showLiked = document.getElementById('show-liked').checked;
                const allPosts = document.querySelectorAll('.post-line');
                
                allPosts.forEach(post => {
                    const isLiked = post.classList.contains('liked-post');
                    
                    if (showLiked) {
                        // Show ONLY liked posts (filter to just liked content)
                        if (isLiked) {
                            post.style.display = 'block';
                        } else {
                            post.style.display = 'none';
                        }
                    } else {
                        // Show all posts (respecting other hiding rules and category filter)
                        const isHidden = post.classList.contains('hidden-post') || 
                                       post.classList.contains('read-post') || 
                                       post.classList.contains('hide-post') || 
                                       post.classList.contains('liked-post');
                        
                        const postMainCategory = post.getAttribute('data-main-category');
                        const categoryMatches = currentMainCategory === 'All' || postMainCategory === currentMainCategory;
                        if (categoryMatches && !isHidden) {
                            post.style.display = 'block';
                        } else {
                            post.style.display = 'none';
                        }
                    }
                });
                
                // Update subcategory links if in category view
                if (document.getElementById('category-view').classList.contains('show') && document.getElementById('subcategory-links')) {
                    showSubcategoryLinks();
                }
            }
            
            function searchPosts(query) {
                const searchTerm = query.toLowerCase().trim();
                const allPosts = document.querySelectorAll('.post-line');
                
                if (searchTerm === '') {
                    // Remove search mode styling from body
                    document.body.classList.remove('search-mode');
                    
                    // Restore the default "All" selection when search is cleared
                    const allRadio = document.querySelector('input[name="main-category"][value="All"]');
                    if (allRadio) allRadio.checked = true;
                    currentMainCategory = 'All';
                    
                    // Show all posts and respect current view settings
                    allPosts.forEach(post => {
                        const isHidden = post.classList.contains('hidden-post') || 
                                       post.classList.contains('read-post') || 
                                       post.classList.contains('hide-post') || 
                                       post.classList.contains('liked-post');
                        
                        // Check checkbox states
                        const showHidden = document.getElementById('show-hidden').checked;
                        const showLiked = document.getElementById('show-liked').checked;
                        
                        let shouldShow = false;
                        
                        if (showLiked) {
                            // Show ONLY liked posts
                            shouldShow = post.classList.contains('liked-post');
                        } else if (showHidden) {
                            // Show ALL posts (including hidden ones)
                            shouldShow = true;
                        } else {
                            // Normal mode: respect hiding rules and category filter
                            const postMainCategory = post.getAttribute('data-main-category');
                            shouldShow = postMainCategory === currentMainCategory && !isHidden;
                        }
                        
                        post.style.display = shouldShow ? 'block' : 'none';
                        
                        // Remove search result styling
                        post.classList.remove('search-result-hidden');
                    });
                    
                    // Update subcategory links if in category view
                    if (document.getElementById('category-view').classList.contains('show') && document.getElementById('subcategory-links')) {
                        showSubcategoryLinks();
                    }
                    return;
                }
                
                // Search through posts - show matching posts from the currently selected category
                // Ensure "By Date" view is selected for chronological search results
                const dateRadio = document.querySelector('input[name="view"][value="date"]');
                if (dateRadio) dateRadio.checked = true;
                showView('date');
                
                // Add search mode styling to body
                document.body.classList.add('search-mode');
                
                allPosts.forEach(post => {
                    const title = post.querySelector('a.local').textContent.toLowerCase();
                    const newsletter = post.querySelector('.newsletter-name').textContent.toLowerCase();
                    const category = post.querySelector('.category, .subcategory')?.textContent.toLowerCase() || '';
                    
                    const matches = title.includes(searchTerm) || 
                                  newsletter.includes(searchTerm) || 
                                  category.includes(searchTerm);
                    
                    // Only show posts that match both search term AND current category selection
                    const postMainCategory = post.getAttribute('data-main-category');
                    const categoryMatches = currentMainCategory === 'All' || postMainCategory === currentMainCategory;
                    
                    if (matches && categoryMatches) {
                        // Show the post regardless of hiding state when searching
                        post.style.display = 'block';
                        
                        // Add visual indicator if post is hidden
                        const isHidden = post.classList.contains('hidden-post') || 
                                       post.classList.contains('read-post') || 
                                       post.classList.contains('hide-post') || 
                                       post.classList.contains('liked-post');
                        
                        if (isHidden) {
                            post.classList.add('search-result-hidden');
                        } else {
                            post.classList.remove('search-result-hidden');
                        }
                    } else {
                        post.style.display = 'none';
                        post.classList.remove('search-result-hidden');
                    }
                });
            }
        </script>
        """

        html = HTML_TEMPLATE.format(
            title="Stored Newsletter Posts",
            css_path=self._get_css_path(1),
            content=content
        )
        index_path = self.base_dir / "index.html"
        index_path.write_text(html, encoding='utf-8')
        print(f"✅ Created index.html from index.json at {index_path}")

    def create_json_index(self) -> None:
        """Create a JSON index file for programmatic access."""
        # Load existing index.json to preserve personalization field values
        existing_not_interesting = {}
        existing_read = {}
        existing_like = {}
        existing_hide = {}
        json_path = self.base_dir / "index.json"
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
        # newsletter_configs is a dict, so we need to handle it differently
        url_to_name = {config['url']: config['name'] for config in newsletter_configs.values()}
        url_to_main_category = {config['url']: config['main_category'] for config in newsletter_configs.values()}
        url_to_subcategory = {config['url']: config['subcategory'] for config in newsletter_configs.values()}
        url_to_tags = {config['url']: config['tags'] for config in newsletter_configs.values()}
        
        # Create normalized URL mappings (remove trailing slashes for comparison)
        normalized_url_to_name = {url.rstrip('/'): name for url, name in url_to_name.items()}
        normalized_url_to_main_category = {url.rstrip('/'): cat for url, cat in url_to_main_category.items()}
        normalized_url_to_subcategory = {url.rstrip('/'): subcat for url, subcat in url_to_subcategory.items()}
        normalized_url_to_tags = {url.rstrip('/'): tags for url, tags in url_to_tags.items()}
        
        newsletters = self.list_newsletters()
        for newsletter in sorted(newsletters):
            posts = self.list_posts(f"https://{newsletter}.substack.com")
            if posts:
                newsletter_url = posts[0]['newsletter_url']
                # Normalize the URL for comparison
                normalized_url = newsletter_url.rstrip('/')
                display_name = normalized_url_to_name.get(normalized_url, newsletter.title())
                main_category = normalized_url_to_main_category.get(normalized_url, 'Uncategorized')
                subcategory = normalized_url_to_subcategory.get(normalized_url, 'Uncategorized')
                tags = normalized_url_to_tags.get(normalized_url, [])
            else:
                newsletter_url = f"https://{newsletter}.substack.com"
                display_name = newsletter.title()
                main_category = 'Uncategorized'
                subcategory = 'Uncategorized'
                tags = []
            
            # Ensure each post has all personalization fields and category info
            for post in posts:
                # Preserve existing values or default to False
                post_url = post.get('url', '')
                post['not_interesting'] = existing_not_interesting.get(post_url, False)
                post['read'] = existing_read.get(post_url, False)
                post['like'] = existing_like.get(post_url, False)
                post['hide'] = existing_hide.get(post_url, False)
                post['main_category'] = main_category
                post['subcategory'] = subcategory
                post['category'] = f"{main_category} > {subcategory}"  # For backward compatibility
                post['tags'] = tags
            
            index_data["newsletters"][newsletter] = {
                "name": display_name,
                "url": newsletter_url,
                "main_category": main_category,
                "subcategory": subcategory,
                "category": f"{main_category} > {subcategory}",  # For backward compatibility
                "tags": tags,
                "post_count": len(posts),
                "posts": posts
            }
            index_data["total_posts"] += len(posts)
        
        json_path = self.base_dir / "index.json"
        json_path.write_text(json.dumps(index_data, indent=2), encoding='utf-8')
        print(f"Created index.json with personalization fields and categories at {json_path}")

    def create_rss_feed(self) -> None:
        """Create an RSS feed of all posts."""
        # This could be implemented later if needed
        pass 