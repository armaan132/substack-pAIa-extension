import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class NewsletterStore:
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

    def save_post(self, newsletter_url: str, post) -> None:
        """Save a post's content and metadata."""
        newsletter_name = self._get_safe_name(newsletter_url)
        post_id = post.url.split('/')[-1]
        
        # Get metadata and content
        metadata = post.get_metadata()
        content = post.get_content()
        
        # Save HTML content
        content_path = self.content_dir / newsletter_name / f"{post_id}.html"
        content_path.parent.mkdir(exist_ok=True)
        content_path.write_text(content, encoding='utf-8')
        
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
        """Create an index.html file that links to all stored posts."""
        index_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Science Newsletter Archive</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .newsletter { margin-bottom: 30px; }
                .date { color: #666; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>Science Newsletter Archive</h1>
        """
        
        # Group posts by newsletter
        newsletters = self.list_newsletters()
        for newsletter in sorted(newsletters):
            index_content += f"\n<div class='newsletter'>\n"
            index_content += f"<h2>{newsletter}</h2>\n"
            posts = self.list_posts(f"https://{newsletter}.substack.com")
            
            for post in posts:
                title = post['title']
                date = post.get('published_at', 'No date')
                # Convert content path to relative path
                content_path = Path(post['content_path']).relative_to(self.base_dir)
                index_content += f"""
                <p>
                    <a href="{content_path}">{title}</a>
                    <span class="date">{date}</span>
                </p>
                """
            
            index_content += "</div>\n"
        
        index_content += "</body></html>"
        
        index_path = self.base_dir / "index.html"
        index_path.write_text(index_content, encoding='utf-8') 