import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class NewsletterStore:
    # Add template as a class variable
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="{css_path}">
        <style>
            /* Test style that will be overridden by Substack CSS if it loads */
            body {{
                background-color: pink !important; /* Very obvious color */
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div style="border: 2px solid red; margin: 10px; padding: 10px;">
            If Substack CSS is loading, this box should have different styling
        </div>
        {content}
    </body>
    </html>
    """

    def __init__(self, base_dir=None):
        if base_dir is None:
            # Get the project root (2 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            base_dir = project_root / "data"
        self.base_dir = Path(base_dir)
        self.metadata_dir = self.base_dir / "metadata"
        self.content_dir = self.base_dir / "content"
        
        # Create directories if they don't exist
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def _get_safe_name(self, url: str) -> str:
        """Convert URL to safe directory name."""
        return url.split("//")[1].split(".")[0]

    def _get_css_path(self, depth: int) -> str:
        """Get the relative path to CSS based on file depth in directory structure."""
        return '../' * depth + 'src/web/static/css/substack.css'

    def save_post(self, newsletter_url: str, post) -> None:
        """Save a post's content and metadata."""
        newsletter_name = self._get_safe_name(newsletter_url)
        post_id = post.url.split('/')[-1]
        
        # Get metadata and content
        metadata = post.get_metadata()
        content = post.get_content()
        
        # Save HTML content using our template
        content_path = self.content_dir / newsletter_name / f"{post_id}.html"
        content_path.parent.mkdir(exist_ok=True)
        
        # Generate HTML using template
        html = self.HTML_TEMPLATE.format(
            title=metadata['title'],
            css_path=self._get_css_path(3),  # posts are three levels deep
            content=content
        )
        content_path.write_text(html, encoding='utf-8')
        
        # Save metadata
        metadata_obj = {
            'url': post.url,
            'newsletter_url': newsletter_url,
            'title': metadata['title'],
            'author': metadata['publishedBylines'][0]['name'],
            'published_at': metadata.get('publishedAt'),
            'word_count': metadata.get('wordcount'),
            'content_path': str(content_path),
            'saved_at': datetime.now().isoformat()
        }
        
        metadata_path = self.metadata_dir / newsletter_name / f"{post_id}.json"
        metadata_path.parent.mkdir(exist_ok=True)
        metadata_path.write_text(json.dumps(metadata_obj, indent=2), encoding='utf-8')

    def get_post(self, newsletter_url: str, post_id: str) -> Optional[Dict]:
        """Get a specific post by newsletter URL and post ID."""
        newsletter_name = self._get_safe_name(newsletter_url)
        metadata_path = self.metadata_dir / newsletter_name / f"{post_id}.json"
        
        if not metadata_path.exists():
            return None
            
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        content_path = Path(metadata['content_path'])
        
        if not content_path.exists():
            return None
            
        content = content_path.read_text(encoding='utf-8')
        
        return {
            'metadata': metadata,
            'content': content
        }

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

    def create_index_html(self) -> None:
        """Create an index.html file listing all stored posts."""
        content = "<h1>Stored Newsletter Posts</h1><ul>"
        
        # Group posts by newsletter
        newsletters = self.list_newsletters()
        for newsletter in sorted(newsletters):
            content += f"\n<li><strong>{newsletter}</strong></li>\n"
            posts = self.list_posts(f"https://{newsletter}.substack.com")
            
            for post in posts:
                title = post['title']
                date = post.get('published_at', 'No date')
                # Convert content path to relative path
                content_path = Path(post['content_path']).relative_to(self.base_dir)
                content += f"""
                <li>
                    <a href="{content_path}">{title}</a>
                    <span class="date">{date}</span>
                </li>
                """
            
            content += "</ul>\n"
        
        html = self.HTML_TEMPLATE.format(
            title="Stored Newsletter Posts",
            css_path=self._get_css_path(1),  # index.html is one level deep
            content=content
        )
        
        index_path = self.base_dir / "index.html"
        index_path.write_text(html, encoding='utf-8') 