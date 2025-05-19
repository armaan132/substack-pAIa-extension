# Substack pAIa

## Mission Statement

A personal AI assistant that helps you discover, collect, and annotate science blogs from Substack - your intelligent companion for staying on top of scientific discussions and breakthroughs.

substack-pAIa is part of pAIa, an initiative to return control of the internet to its users. While today's internet is dominated by platforms that monetize user attention and data, pAIa tools help you interact with online content on your own terms. By enabling local storage and personal curation of Substack science blogs, this assistant lets you build your own knowledge base without sacrificing privacy or autonomy to platform algorithms.

In the future, pAIa will expand into a data science project on federated learning applied to the monitoring of centralized social media platforms. By decentralizing both the data collection and analysis processes, we aim to shift power away from platforms controlled by private financial interests that currently monopolize user data and control information flow. This federated approach will enable users to collectively understand platform dynamics while maintaining individual data sovereignty - a crucial step towards a more democratic and user-controlled internet ecosystem.

## Project Structure 

```
project_root/
└── data/                           # Downloaded newsletters
    ├── content/                    # HTML content of posts
    ├── metadata/                   # JSON metadata of posts
    └── index.html                  # Auto-generated index
├── docs/                       
│   ├── user-stories.md             # User stories
│   └── product-backlog.md          # Product backlog
├── scripts/                    
│   ├── serve.py                    # start server to read newsletters
│   └── test_substack_api.py        # download and store recent newsletters
├── src/                
│   └── api/                        # (not used currently)
│   └── database/                   # (not used currently)
│   └── scraper/                    # (not used currently)
│       └── newsletter_scraper.py   # download and store newsletters
│   └── search/                     # (not used currently)
│   └── weg/                        # (not used currently)
```

## Features

- Download and store Substack newsletters locally
- Separate storage of content (HTML) and metadata (JSON)
- Auto-generated index page for browsing
- Built-in local server for easy reading

## Getting Started

1. Install dependencies:

    ```bash
    pip install substack-api
    ```

2. Download some newsletters:
    ```bash
    python scripts/test_substack_api.py
    ```

1. Read a newsletter:

    open `data/index.html` in your browser 

    or 

    start the local server with `python scripts/serve.py` and open  http://localhost:8000/index.html in your browser

## Current Limitations

- Can only download from known Substack URLs
- Cannot access subscriber-only content
- Basic browsing interface

## Development Status

Current focus:
- Basic newsletter archiving functionality
- Simple browsing interface
- Local storage system

See `docs/product-backlog.md` for planned features.

## Contributing

Get in touch.
