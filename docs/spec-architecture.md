# Substack pAIa Architecture Specification

## Overview
The current system is a Flask-based local web application that provides offline access to Substack newsletters with content discovery, personalization, and citation sentiment analysis.

The long-term project direction is to evolve this into a standalone browser extension that can analyze the Substack post a user is currently reading without requiring a local server.

## Architecture Status

There are two important architectures to understand:

1. **Current local system**: Python scripts, local JSON/HTML storage, generated web interface, and Flask APIs.
2. **Planned extension system**: browser content script, popup/side panel UI, browser storage, and JavaScript-based page analysis.

The current codebase mainly implements the local system. The extension architecture is the target direction documented here so future changes can move toward it deliberately.

## Core Components

### 1. Web Interface (`src/web/`)
- **Flask Server** (`server.py`): RESTful API endpoints and static file serving
- **HTML Generator** (`index_generator.py`): Dynamic HTML generation with embedded JavaScript
- **Static Assets**: CSS styling for clean, responsive interface

### 2. Update System (`src/web/updaters/`)
- **Incremental Updater** (`incremental_update.py`): Core 3-tier update logic
- **RSS Updater** (`rss_updater.py`): Fast post discovery via RSS feeds
- **Content Downloader**: Background content fetching for offline access

### 3. Data Management (`src/database/`)
- **Filesystem Store** (`filesystem_store.py`): JSON-based data persistence
- **Content Storage**: HTML content stored in organized directory structure

### 4. Content Discovery (`src/scraper/`)
- **RSS Parsing**: Fast detection of new posts
- **Substack API**: Complete content retrieval
- **Metadata Extraction**: Post titles, dates, categories

### 5. Citation Sentiment (`src/analysis/`)
- **Citation analyzer** (`citation_sentiment.py`): extracts Substack post links from saved HTML
- **Context extraction**: captures nearby prose around each linked post
- **Author stance scoring**: labels citation context as supportive, neutral, or critical
- **Recommendation signal**: produces confidence-weighted scores that can feed ranking logic

## Current Data Flow
1. **Configuration**: `newsletters.md` → Newsletter structure and categories
2. **Discovery**: RSS feeds → New post detection
3. **Download**: Substack API → Content retrieval and storage
4. **Interface**: JSON data → Dynamic HTML generation
5. **Personalization**: User interactions → Persistent preferences
6. **Citation Analysis**: Saved post HTML → citation sentiment fields in `data/index.json`

```text
config/newsletters.md
    -> src/web/updaters/
    -> data/content/ and data/metadata/
    -> data/index.json
    -> src/analysis/citation_sentiment.py
    -> src/web/index_generator.py
    -> data/index.html
    -> src/web/server.py
```

## Planned Extension Data Flow

```text
Current Substack browser tab
    -> content script extracts metadata, article text, and links
    -> browser-side citation sentiment analyzer scores author stance
    -> recommendation scorer combines content signals and user feedback
    -> popup or side panel displays reading metadata
    -> chrome.storage.local stores feedback and analysis records
```

The first extension version should focus on the currently viewed post rather than bulk scraping.

## Key Design Principles
- **3-Tier Updates**: Configuration → Structure → Content
- **Background Processing**: Non-blocking content downloads
- **Incremental Updates**: Only process what's changed
- **Offline First**: Content available without internet connection
- **User-Controlled Data**: Personalization and reading feedback should remain transparent and portable
- **Extension First Milestone**: Analyze one active Substack post reliably before rebuilding historical crawling
