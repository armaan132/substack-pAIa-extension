"""
Database connection and management module.
"""
from typing import List
from .models import Newsletter

class DatabaseManager:
    def __init__(self):
        self.newsletters: List[Newsletter] = []

    def add_newsletter(self, newsletter: Newsletter) -> None:
        self.newsletters.append(newsletter)

    def get_newsletter(self, url: str) -> Newsletter:
        for newsletter in self.newsletters:
            if newsletter.url == url:
                return newsletter
        return None
