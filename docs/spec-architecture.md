# Newsletter Personalization System - Architecture Specification

## Overview
A Flask-based web application that provides offline access to Substack newsletters with intelligent content discovery and personalization features.

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

## Data Flow
1. **Configuration**: `newsletters.md` → Newsletter structure and categories
2. **Discovery**: RSS feeds → New post detection
3. **Download**: Substack API → Content retrieval and storage
4. **Interface**: JSON data → Dynamic HTML generation
5. **Personalization**: User interactions → Persistent preferences

## Key Design Principles
- **3-Tier Updates**: Configuration → Structure → Content
- **Background Processing**: Non-blocking content downloads
- **Incremental Updates**: Only process what's changed
- **Offline First**: Content available without internet connection
