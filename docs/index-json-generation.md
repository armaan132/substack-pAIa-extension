# Index.json Generation Architecture

## Overview

This document explains the new architecture for generating `index.json` using RSS feeds and the Substack API. The system uses a two-source approach: `newsletters.md` for structure and content discovery for post data.


## Server Startup Process

When you start the Flask server (`python src/web/server.py`), the following sequence occurs:

1. **Server starts** → `main()` function calls `server.generate_files()`
2. **`generate_files()` checks for `index.json`:**
   ```python
   json_path = Path("data/index.json")
   if not json_path.exists():
       print("⚠️ index.json missing, regenerating from newsletters.md...")
       self.generator.create_json_index()
   ```
3. **`create_json_index()` is called** (if missing)
4. **Safety check**: see below.

## Safety Mechanisms

The system has built-in safety checks to prevent accidental overwriting:

```python
# SAFETY CHECK: Allow regeneration only when index.json is missing
if output_file == "index.json" and input_file == "index.json":
    json_path = self.base_dir / "index.json"
    if json_path.exists():
        print("❌ SAFETY CHECK: Cannot overwrite existing index.json!")
        print("❌ This would overwrite your manual curation decisions.")
        raise RuntimeError("JSON regeneration blocked for safety - JSON is source of truth")
    else:
        print("✅ index.json missing, allowing regeneration from newsletters.md")
```

**Key Point**: You cannot regenerate `index.json` if it already exists. You must delete it first.

## How `index.json` is Created

### Source 1: `newsletters.md` (Primary Structure)

- **File**: `config/newsletters.md`
- **Purpose**: Defines newsletter structure, categories, and metadata
- **Extracts**: Newsletter names, URLs, categories, subcategories, tags
- **Creates**: Basic newsletter structure with empty post lists

**Example `newsletters.md` structure:**
```markdown
# Science
## Philosophy
### Ethics
https://philosophy-blog.com Blog Name, philosophy, ethics
### Logic
https://logic-blog.com Logic Blog, philosophy, logic

# News and Opinion
## Politics
https://politics-news.com Politics News, news, politics
```

### Source 2: Multi-Layer Content Discovery

- **RSS Feeds (A)**: Fast post detection and discovery
- **Substack API (B)**: Download content and extract rich metadata
- **HTML Content (C)**: Local storage of downloaded posts.

**Content Discovery Flow:**
```
RSS Feed → Fast post detection
     ↓
Substack API → Download content + extract metadata
     ↓
Store in index.json → Complete post data
```

**What Gets Extracted:**
- Post titles, URLs, publication dates
- Author information and content
- Categories and tags from newsletters.md
- Content paths for local storage

## Data Flow and Priorities

### Priority Order:

1. **`newsletters.md`** (Highest Priority)
   - Defines what newsletters should exist
   - Sets categories and subcategories
   - Provides display names and tags

2. **Content Discovery** (Medium Priority)
   - RSS feeds provide fast post detection
   - Substack API downloads complete content
   - Generates fresh metadata for all posts

3. **Local Storage** (Important for Offline Access)
   - HTML files stored for offline reading
   - One local copy of each post
   - Required for complete offline functionality

### What Gets Preserved:

- **Personalization fields**: `read`, `like`, `hide`, `not_interesting`
- **Post metadata**: titles, URLs, dates, authors
- **Content paths**: references to local HTML files

### What Gets Regenerated:

- **Newsletter structure**: from `newsletters.md`
- **Categories**: from `newsletters.md`
- **Post counts**: recalculated from metadata
- **Timestamps**: `generated_at` field

## Important Notes

### 1. `newsletters.md` is User Curated

- Adding a newsletter to `newsletters.md` → appears in regenerated JSON
- Removing a newsletter from `newsletters.md` → disappears from regenerated JSON
- Categories are user defined. Changing categories in `newsletters.md` → updates in regenerated JSON

### 2. Content Files are Optional

- JSON can exist without corresponding content files
- Content files can be downloaded later via the update process
- Missing content files don't prevent JSON generation

### 3. Personalization is Preserved

- If metadata files exist, personalization fields are preserved
- If no metadata exists, default values (false) are used
- Personalization data is never lost during regeneration

## Normal Operation vs. Testing

### Normal Operation (Recommended):

**Adding New Content:**
- Use "Update Content" button in web interface
- System automatically discovers new posts via RSS
- Downloads content via Substack API
- Updates `index.json` incrementally
- Preserves all personalization data

**Modifying Configuration:**
- Edit `config/newsletters.md` for structure changes
- Use web interface for personalization changes
- System maintains data consistency automatically

### Testing Scenarios (Development Only):

**Testing Regeneration Logic:**
1. Delete `index.json` (for testing only)
2. Start server → `index.json` regenerates from scratch
3. All data comes from `newsletters.md` + content discovery
4. **Note**: This is only for testing the system architecture

**Why Not Delete in Production:**
- Loses all personalization data
- Requires re-downloading all content
- Disrupts user experience
- Only use for debugging system logic

## Summary

The new `index.json` regeneration process is designed to:

- **Use `newsletters.md` as structure source** - defines what newsletters exist
- **Use RSS + API for content discovery** - fast detection + complete data
- **Generate fresh data every time** - no stale metadata to merge
- **Preserve personalization** - stored directly in `index.json`
- **Maintain data consistency** - single source of truth for all post data

### Key Benefits:

1. **Simpler Architecture**: No separate metadata files to manage
2. **Faster Updates**: RSS provides quick post detection
3. **Complete Data**: API downloads full content + metadata
4. **Fresh Content**: Every regeneration gets current data
5. **Easier Maintenance**: No complex merging of multiple data sources

This approach ensures that `newsletters.md` remains the single source of truth for newsletter configuration while the content discovery system provides fresh, complete data for all posts.
