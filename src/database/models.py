"""
Database models for the application.
"""
from datetime import datetime
from typing import List

class Newsletter:
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title
        self.created_at = datetime.now()
        self.categories: List[str] = []
        self.last_updated = datetime.now()

    def __repr__(self) -> str:
        return f"<Newsletter {self.title}>"
