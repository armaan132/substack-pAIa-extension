# Metadata Store Discussion

## What is the Metadata Store?
- The metadata store is a structured, deduplicated, and cleaned JSON file that contains all relevant metadata about newsletters, posts, and their relationships for the Substack graph project.
- It serves as the authoritative source for downstream analysis, visualization, and further processing.
- The metadata store will be maintained in the file `content/metadata_store.json`.
- The file will be created and updated with the help of a scraper that is a doing breadth-first search through Substack.
- The output of the scraper will be a temporary file `tmp/scraper_output.jsonl`.
- The scraper output will be used to update `metadata_store.json`.

## JSON Example

### Newsletter

```json
[
  {
    "url": "https://newsletter1.substack.com",
    "title": "Newsletter 1",
    "author": "Author One",
    "description": "A sample newsletter for demonstration purposes.",
    "topics": ["topicA", "topicB"],
    "last_updated": "2024-06-01",
    "language": "en"
  }
]
```

### Posts

```json
[
  {
    "url": "https://newsletter1.substack.com/p/post1",
    "newsletter": "https://newsletter1.substack.com",
    "author": "Author One",
    "published_date": "2024-06-01",
    "topics": ["topicA"],
    "links_to_substack_posts": [],
    "links_to_external_resources": []
  }
]
```

