# Daily Briefing pAIa

> Extension fork note: this repository was cloned from the original `alexhkurz/substack-pAIa` project as a test copy for reshaping the system into a standalone Substack browser extension.

## Mission Statement

A personal AI assistant that helps you discover, collect, and curate content from newsletters, blogs, and RSS feeds - your intelligent companion for staying on top of discussions and breakthroughs across your areas of interest.

Daily Briefing pAIa is part of pAIa, an initiative to return control of the internet to its users. While today's internet is dominated by platforms that monetize user attention and data, pAIa tools help you interact with online content on your own terms. By enabling local storage and personal curation of newsletters, blogs, and RSS feeds, this assistant lets you build your own knowledge base without sacrificing privacy or autonomy to platform algorithms.

In the future, pAIa will expand into a data science project on federated learning applied to the monitoring of centralized social media platforms. By decentralizing both the data collection and analysis processes, we aim to shift power away from platforms controlled by private financial interests that currently monopolize user data and control information flow. This federated approach will enable users to collectively understand platform dynamics while maintaining individual data sovereignty - a crucial step towards a more democratic and user-controlled internet ecosystem.

## Documentation
- [Documentation Hub](docs/README.md)
- [Project Goal](docs/project-goal.md)
- [Production Readiness](docs/production-readiness.md)
- [Architecture](docs/spec-architecture.md)
- [Changelog](docs/CHANGELOG.md)
- [User Stories](docs/user-stories.md)
- [Product Backlog](docs/product-backlog.md)
- [Learning Backlog](docs/learning-backlog.md)

## Project Structure 

```
project_root/
├── config/
│   └── newsletters.md              # Newsletter URLs and metadata (user maintained)
├── data/                           
│   ├── content/                    # HTML content of posts
│   ├── metadata/                   # JSON metadata of posts
│   ├── index.html                  # Auto-generated HTML index with personalization
│   └── index.json                  # Auto-generated JSON index with user preferences
│   └── newsletters.yaml            # Newsletter configuration (generated via NLP)
├── docs/                       
│   ├── CHANGELOG.md                # Project changelog
│   ├── user-stories.md             # User stories
│   ├── product-backlog.md          # Todo list
│   ├── learning-backlog.md         # Learning outcomes
│   └── not_interesting_feature.md  # Personalization feature documentation
├── nlp-scripts/
│   └── newsletters.nlp.md          # Generate `newsletters.yaml` from `newsletters.md`
├── scripts/                    
│   ├── run_server.py               # Runner script for the personalization server
│   ├── test_substack_api.py        # Download and store newsletters
│   └── sentiment_analysis.py       # Analyze sentiment of newsletter citations
├── src/                
│   ├── database/       
│   │   └── filesystem_store.py     # Data storage and retrieval
│   ├── web/                        
│   │   ├── index_generator.py      # HTML/JSON index generation with personalization
│   │   ├── server.py               # Main Flask server (core application)
│   │   ├── updaters/               # Content update mechanisms
│   │   │   ├── __init__.py         # Package initialization
│   │   │   ├── incremental_update.py # Incremental updates with RSS fallback
│   │   │   └── rss_updater.py      # RSS-based fast content discovery
│   │   └── static/                 
│   │       └── css/                # CSS styling files
│   ├── scraper/                    # Web scraping 
├── tmp/      
│   ├── scraper_output.jsonl/       
```

## Scripts

[`newsletters.nlp.md`](nlp-scripts/newsletters.nlp.md) (not needed for basic functionality)
- Usage: Prompt AI-agent to execute the script.
- Transforms [`newsletters.md`](config/newsletters.md) to [`data/newsletters.yaml`](data/newsletters.yaml)

[`test_substack_api.py`](scripts/test_substack_api.py) (currently the main script)
- Usage: `python scripts/test_substack_api.py` 
- Downloads posts from newsletters configured in `config/newsletters.md`
- Generates HTML and JSON indexes; open [`index.html`](data/index.html) with your browser

[`run_server.py`](scripts/run_server.py) (personalization server)
- Usage: `python scripts/run_server.py`
- Starts the main Flask server on port 8000 with full personalization features
- Provides interactive "Not Interesting" and "Read/Unread" functionality for posts
- Hierarchical categorization with Science and News & Opinion sections
- Access your newsletters at `http://localhost:8000/data/index.html`
- **Features**: Mark posts as not interesting or read, hide them instantly, persist all preferences

[`sentiment_analysis.py`](scripts/sentiment_analysis.py) (not needed for basic functionality)
- Usage: `python scripts/sentiment_analysis.py <source_url> <html_file>`
- Performs sentiment analysis on newsletter links and citations
- Extracts context around references to other Substack posts
- Outputs YAML format with sentiment scores and confidence levels

[`update_citation_sentiment.py`](scripts/update_citation_sentiment.py) (recommendation feature)
- Usage: `python scripts/update_citation_sentiment.py`
- Analyzes locally saved post HTML for links to other Substack posts/newsletters
- Scores the author's surrounding context as supportive, neutral, or critical
- Stores citation-level and per-post summary signals in `data/index.json`
- Regenerates `data/index.html` with citation sentiment badges for recommender debugging

### Architecture

**Data Storage** (`src/database/filesystem_store.py`)
- Handles saving and retrieving newsletter posts
- Stores HTML content and JSON metadata separately
- Creates organized directory structure by newsletter
- Prevents duplicate downloads by checking existing posts 

**Index Generation** (`src/web/index_generator.py`)
- Generates HTML and JSON indexes of stored posts with JSON-first architecture
- Creates chronological timeline view (latest posts first)
- Reads newsletter configuration with hierarchical categorization (## and ### headers)
- Formats dates in human-readable format  
- **Features**: Includes personalization fields (not_interesting, read) with persistent storage

**Main Server** (`src/web/server.py`)
- **Core Flask application** for the newsletter personalization system
- Single clean server architecture (no duplicate server code)
- Provides both static file serving and interactive API functionality  
- Handles user preference updates (not_interesting, read status)
- Runs citation sentiment analysis from the web UI via the "Analyze Citations" button
- Serves the generated HTML interface with hierarchical categorization
- **Future-ready**: Foundation for AI training, user management, advanced filtering

**Content Updates** (`src/web/updaters/`)
- **RSS-first strategy**: Uses RSS feeds for fast content discovery (10x faster than scraping)
- **Smart fallback**: Falls back to `substack_api` when RSS fails
- **Incremental updates**: Only fetches new content, preserves existing data and personalization
- **Web interface integration**: Update button in web UI triggers RSS-based updates
- **Content preservation**: All user preferences (read, like, hide, not_interesting) are maintained

**NLP Configuration** (`nlp-scripts/newsletters.nlp.md`)
- AI instructions for generating rich YAML configuration
- Extracts author names, Wikipedia links, professional roles
- Assigns topics, tags, and content classifications
- Converts simple markdown to structured metadata

**Note:** The system uses manual configuration via `config/newsletters.md` with optional AI-powered YAML generation for enhanced metadata. The new personalization features are built on top of this foundation.

## Features

**Implemented**:

- Download and store Substack newsletters locally
- Auto-generated index page for browsing with hierarchical categorization
- Built-in Flask server for reading indexed posts with personalization
- Interactive "Not Interesting" and "Read/Unread" buttons with instant hiding
- Persistent user preferences (survives server restarts and page refreshes)
- JSON-first architecture with `index.json` as single source of truth
- Sentiment analysis of newsletter citations and references, including stored author feedback signals for recommendation ranking
- AI-powered YAML configuration generation from markdown
- Metadata extraction (authors, roles, topics, tags)

**Currently Working On**:

- Content Discovery and Organization:
  - Finding Substack URLs from author names
  - Crawling the substack link graph
  - Advanced filtering and search capabilities

**Next Steps**:

- Local AI that learns user's personal preferences. 
- Automated computation of a science score: A higher score means that the newsletter brings cutting edge research to the attention of the non-expert reader (in-depth citations add to the score, frivolous citations subtract).
- Automated computation of a strongman-vs-strawman score. High if the article argues against a strongman, low if it argues against a strawman. 
- Content Discovery, Recommender System.

**Future Work**:

- From Local to Global: Federating pAIas.


## Getting Started

1. Install dependencies:

    ```bash
    pip install substack-api
    ```

2. Configure newsletters to download (optional):
    Edit `config/newsletters.md` to add your preferred newsletters

3. Download some newsletters:
    ```bash
    python scripts/test_substack_api.py
    ```

1. Read a newsletter:

    open `data/index.html` in your browser 

    or 

    start the personalization server with `python scripts/run_server.py` and open  http://localhost:8000/data/index.html in your browser

## Development Status

See [`docs/product-backlog.md`](docs/product-backlog.md) for completed and planned features.

## Contributing

Get in touch.
