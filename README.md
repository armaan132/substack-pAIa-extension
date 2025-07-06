# Substack pAIa

## Mission Statement

A personal AI assistant that helps you discover, collect, and annotate science blogs from Substack - your intelligent companion for staying on top of scientific discussions and breakthroughs.

substack-pAIa is part of pAIa, an initiative to return control of the internet to its users. While today's internet is dominated by platforms that monetize user attention and data, pAIa tools help you interact with online content on your own terms. By enabling local storage and personal curation of Substack science blogs, this assistant lets you build your own knowledge base without sacrificing privacy or autonomy to platform algorithms.

In the future, pAIa will expand into a data science project on federated learning applied to the monitoring of centralized social media platforms. By decentralizing both the data collection and analysis processes, we aim to shift power away from platforms controlled by private financial interests that currently monopolize user data and control information flow. This federated approach will enable users to collectively understand platform dynamics while maintaining individual data sovereignty - a crucial step towards a more democratic and user-controlled internet ecosystem.

## Documentation
- [Changelog](docs/CHANGELOG.md)
- [User Stories](docs/user-stories.md)
- [Product Backlog](docs/product-backlog.md)
- [Learning Backlog](docs/learning-backlog.md)

## Project Structure 

```
project_root/
├── config/
│   └── newsletters.yaml            # Newsletter configuration
├── data/                           # Downloaded newsletters
│   ├── content/                    # HTML content of posts
│   ├── metadata/                   # JSON metadata of posts
│   └── index.html                  # Auto-generated index
├── docs/                       
│   ├── user-stories.md             # User stories
│   ├── product-backlog.md          # Todo list
│   └── learning-backlog.md         # Learning outcomes
├── scripts/                    
│   ├── serve.py                    # Local server for reading newsletters
│   ├── test_substack_api.py        # Download and store newsletters
│   └── sentiment_analysis.py       # Analyze sentiment of newsletter citations
├── src/                
│   └── database/       
│       └── filesystem_store.py     # Core storage functionality
│   └── web/                        
|       └── static/                 
|           └── css/                # CSS files    
```

## Scripts

**`test_substack_api.py`** - Download and store newsletters ([source](scripts/test_substack_api.py))
- Main script for fetching Substack newsletters
- Downloads HTML content and metadata
- Stores files in organized directory structure
- Usage: `python scripts/test_substack_api.py`
- Downloads posts from newsletters configured in `config/newsletters.yaml`
- Supports per-newsletter limits and metadata

**`serve.py`** - Local web server for reading newsletters ([source](scripts/serve.py))
- Starts a simple HTTP server on port 8000
- Serves files from the project root directory
- Usage: `python scripts/serve.py`
- Access your newsletters at `http://localhost:8000/data/index.html`

**`sentiment_analysis.py`** - Analyze newsletter citations and references ([source](scripts/sentiment_analysis.py))
- Performs sentiment analysis on newsletter links and citations
- Extracts context around references to other Substack posts
- Outputs YAML format with sentiment scores and confidence levels
- Usage: `python scripts/sentiment_analysis.py <source_url> <html_file>`

## Features

**Implemented**:

- Download and store Substack newsletters locally
- Separate storage of content (HTML) and metadata (JSON)
- Auto-generated index page for browsing
- Built-in local server for reading indexed posts
- Sentiment analysis of newsletter citations and references

**Currently Working On**:

- Improving the layout of locally stored newsletters

**Next Steps**:

- Content Organization and Discovery

## Getting Started

1. Install dependencies:

    ```bash
    pip install substack-api
    ```

2. Configure newsletters to download (optional):
    Edit `config/newsletters.yaml` to add your preferred newsletters

3. Download some newsletters:
    ```bash
    python scripts/test_substack_api.py
    ```

1. Read a newsletter:

    open `data/index.html` in your browser 

    or 

    start the local server with `python scripts/serve.py` and open  http://localhost:8000/data/index.html in your browser

## Development Status

See [`docs/product-backlog.md`](docs/product-backlog.md) for completed and planned features.

## Contributing

Get in touch.
