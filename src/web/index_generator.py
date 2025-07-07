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

    def load_newsletter_md(self, md_path: str = "config/newsletters.md"):
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

    def _format_date(self, date_str):
        """Format ISO date string as 'Jul 7, 2025'."""
        if not date_str or date_str == 'No date':
            return 'No date'
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%b %-d, %Y') if hasattr(dt, 'strftime') else dt.strftime('%b %d, %Y')
        except Exception:
            return date_str

    def create_index_html(self) -> None:
        """Create an index.html file listing all stored posts."""
        content = """
        <h1>Recent Newsletter Posts</h1>
        <style>
            .post-line { margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
            .post-line a { margin-right: 15px; text-decoration: none; }
            .post-line a.local { color: #0066cc; }
            .post-line a.original { color: #666; font-size: 0.9em; }
            .newsletter-name { color: #333; font-weight: bold; margin-right: 10px; }
            .date { color: #888; font-size: 0.8em; margin-left: 10px; }
        </style>
        """
        
        # Load newsletter configuration from markdown
        newsletter_configs = self.load_newsletter_md()
        
        # Create a mapping from URL to display name
        url_to_name = {config['url']: config['name'] for config in newsletter_configs}
        
        # Collect all posts from all newsletters
        all_posts = []
        newsletters = self.list_newsletters()
        for newsletter in sorted(newsletters):
            posts = self.list_posts(f"https://{newsletter}.substack.com")
            if posts:
                newsletter_url = posts[0]['newsletter_url']
                display_name = url_to_name.get(newsletter_url, newsletter.title())
            else:
                newsletter_url = f"https://{newsletter}.substack.com"
                display_name = newsletter.title()
            
            for post in posts:
                post['newsletter_name'] = display_name
                post['newsletter_url'] = newsletter_url
                all_posts.append(post)
        
        # Sort all posts by date (latest first)
        all_posts.sort(
            key=lambda x: x.get('published_at', '') or '',
            reverse=True
        )
        
        # Display all posts in chronological order
        for post in all_posts:
            title = post['title']
            date = post.get('published_at')
            if date is None:
                date = 'No date'
            display_date = self._format_date(date)
            newsletter_name = post['newsletter_name']
            
            # Convert content path to relative path
            content_path = Path(post['content_path']).relative_to(self.base_dir)
            content += f"""
            <div class="post-line">
                <span class="newsletter-name">{newsletter_name}</span>
                <a href="{content_path}" class="local">📄 {title}</a>
                <a href="{post['url']}" class="original" target="_blank">🔗 Original</a>
                <span class="date">{display_date}</span>
            </div>
            """
        
        html = HTML_TEMPLATE.format(
            title="Stored Newsletter Posts",
            css_path=self._get_css_path(1),  # index.html is one level deep
            content=content
        )
        
        index_path = self.base_dir / "index.html"
        index_path.write_text(html, encoding='utf-8')
        print(f"Created index.html at {index_path}")

    def create_json_index(self) -> None:
        """Create a JSON index file for programmatic access."""
        index_data = {
            "generated_at": datetime.now().isoformat(),
            "total_posts": 0,
            "newsletters": {}
        }
        
        # Load newsletter configuration from markdown for proper names
        newsletter_configs = self.load_newsletter_md()
        url_to_name = {config['url']: config['name'] for config in newsletter_configs}
        
        newsletters = self.list_newsletters()
        for newsletter in sorted(newsletters):
            posts = self.list_posts(f"https://{newsletter}.substack.com")
            if posts:
                newsletter_url = posts[0]['newsletter_url']
                display_name = url_to_name.get(newsletter_url, newsletter.title())
            else:
                newsletter_url = f"https://{newsletter}.substack.com"
                display_name = newsletter.title()
            
            index_data["newsletters"][newsletter] = {
                "name": display_name,
                "url": newsletter_url,
                "post_count": len(posts),
                "posts": posts
            }
            index_data["total_posts"] += len(posts)
        
        json_path = self.base_dir / "index.json"
        json_path.write_text(json.dumps(index_data, indent=2), encoding='utf-8')
        print(f"Created index.json at {json_path}")

    def create_rss_feed(self) -> None:
        """Create an RSS feed of all posts."""
        # This could be implemented later if needed
        pass 