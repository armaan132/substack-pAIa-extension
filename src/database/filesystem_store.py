import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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

class NewsletterStore:
    # Make HTML_TEMPLATE accessible in the class
    HTML_TEMPLATE = HTML_TEMPLATE

    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = DATA_DIR
        else:
            self.base_dir = Path(base_dir)
        self.metadata_dir = self.base_dir / "metadata"
        self.content_dir = self.base_dir / "content"
        
        # Create directories if they don't exist
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

    def save_post(self, newsletter_url: str, post) -> bool:
        """Save a post's content and metadata. Returns True if saved, False if already exists."""
        newsletter_name = self._get_safe_name(newsletter_url)
        post_id = post.url.split('/')[-1]
        
        # Check if post already exists
        metadata_path = self.metadata_dir / newsletter_name / f"{post_id}.json"
        if metadata_path.exists():
            return False  # Post already exists, skip it
        
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
            'author': self._extract_author_safely(metadata),
            'published_at': metadata.get('post_date'),  # Fix: use 'post_date' instead of 'publishedAt'
            'word_count': metadata.get('wordcount'),
            'content_path': str(content_path),
            'saved_at': datetime.now().isoformat()
        }
        
        metadata_path.parent.mkdir(exist_ok=True)
        metadata_path.write_text(json.dumps(metadata_obj, indent=2), encoding='utf-8')
        return True  # Post was saved successfully

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

 