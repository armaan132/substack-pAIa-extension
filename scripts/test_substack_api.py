# https://github.com/NHagar/substack_api
from substack_api import Newsletter

# List of science-focused Substacks
science_substacks = [
    "https://econjared.substack.com",
]

def get_post_content(url, limit=3):
    print(f"\nNewsletter: {url}\n")
    try:
        newsletter = Newsletter(url)
        recent_posts = newsletter.get_posts(limit=limit)
        for post in recent_posts:
            metadata = post.get_metadata()
            print(f"Title: {metadata['title']}")
            print(f"Author: {metadata['publishedBylines'][0]['name']}")
            print(f"Word Count: {metadata['wordcount']}")
            print(f"URL: {post.url}")
            
            # Try to get full content
            try:
                content = post.get_content()
                print("\nContent Preview (first 200 chars):")
                print(content[:200] + "...\n")
            except Exception as e:
                print(f"\nCouldn't get full content: {e}")
                print("Note: Subscriber-only posts are not accessible\n")
            
            print("-" * 80 + "\n")
    except Exception as e:
        print(f"Error accessing {url}: {e}\n")

# Monitor all newsletters
for substack_url in science_substacks:
    get_post_content(substack_url)
