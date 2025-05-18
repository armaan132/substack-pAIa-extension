# Substack pAIa

A personal AI assistant to help retrieve, manage and discover science blogs on Substack.

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

3. Start the local server:
```bash
python scripts/serve.py
```

4. Open http://localhost:8000/index.html in your browser

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
