# Science Newsletter Archive

A tool to archive and browse science newsletters from Substack.

## Project Structure 

```
project_root/
├── src/               # Main source code
│   └── database/     # Data storage handling
├── scripts/          # Utility scripts
├── docs/             # Documentation
│   ├── user-stories.md
│   └── product-backlog.md
└── data/             # Downloaded newsletters
    ├── content/      # HTML content
    ├── metadata/     # JSON metadata
    └── index.html    # Auto-generated index
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

This is a student project in development. Current focus:
- Basic newsletter archiving functionality
- Simple browsing interface
- Local storage system

See `docs/product-backlog.md` for planned features.

## Contributing

Get in touch.
