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
│   └── newsletters.md              # Newsletter URLs and metadata (user maintained)
├── data/                           
│   ├── content/                    # HTML content of posts
│   ├── metadata/                   # JSON metadata of posts
│   ├── index.html                  # Auto-generated HTML index
│   └── index.json                  # Auto-generated JSON index
│   └── newsletters.yaml            # Newsletter configuration (generated via NLP)
├── docs/                       
│   ├── CHANGELOG.md                # Project changelog
│   ├── user-stories.md             # User stories
│   ├── product-backlog.md          # Todo list
│   └── learning-backlog.md         # Learning outcomes
├── nlp-scripts/
│   └── newsletters.nlp.md          # Generate `newsletters.yaml` from `newsletters.md`
├── scripts/                    
│   ├── serve.py                    # Local server for reading newsletters
│   ├── test_substack_api.py        # Download and store newsletters
│   └── sentiment_analysis.py       # Analyze sentiment of newsletter citations
├── src/                
│   ├── database/       
│   │   └── filesystem_store.py     # Data storage and retrieval
│   ├── web/                        
│   │   ├── index_generator.py      # HTML/JSON index generation
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

[`serve.py`](scripts/serve.py) (not needed for basic functionality)
- Usage: `python scripts/serve.py`
- Starts a simple HTTP server on port 8000
- Access your newsletters at `http://localhost:8000/data/index.html`

[`sentiment_analysis.py`](scripts/sentiment_analysis.py) (not needed for basic functionality)
- Usage: `python scripts/sentiment_analysis.py <source_url> <html_file>`
- Performs sentiment analysis on newsletter links and citations
- Extracts context around references to other Substack posts
- Outputs YAML format with sentiment scores and confidence levels

### Architecture

**Data Storage** (`src/database/filesystem_store.py`)
- Handles saving and retrieving newsletter posts
- Stores HTML content and JSON metadata separately
- Creates organized directory structure by newsletter
- Prevents duplicate downloads by checking existing posts 

**Index Generation** (`src/web/index_generator.py`)
- Generates HTML and JSON indexes of stored posts
- Creates chronological timeline view (latest posts first)
- Reads newsletter configuration from markdown
- Formats dates in human-readable format

**NLP Configuration** (`nlp-scripts/newsletters.nlp.md`)
- AI instructions for generating rich YAML configuration
- Extracts author names, Wikipedia links, professional roles
- Assigns topics, tags, and content classifications
- Converts simple markdown to structured metadata

**Note:** The system uses manual configuration via `config/newsletters.md` with optional AI-powered YAML generation for enhanced metadata.

## Features

**Implemented**:

- Download and store Substack newsletters locally
- Auto-generated index page for browsing
- Built-in local server for reading indexed posts
- Sentiment analysis of newsletter citations and references
- AI-powered YAML configuration generation from markdown
- Metadata extraction (authors, roles, topics, tags)

**Currently Working On**:

- Content Organization:
  - Improving the layout of locally stored newsletters. Adding functionality (hiding, summarizing, liking, featured newsletters, etc). 
  - Finding Substack URLs from author names.
- Crawling the substack link graph.

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

    start the local server with `python scripts/serve.py` and open  http://localhost:8000/data/index.html in your browser

## Development Status

See [`docs/product-backlog.md`](docs/product-backlog.md) for completed and planned features.

## Contributing

Get in touch.
