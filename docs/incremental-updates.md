# Incremental Updates for Daily Briefing pAIa

## Overview

The incremental update system allows you to keep your newsletter data current without losing your personalization (read/like/hide status). It's designed as an **append-only log** that preserves all existing data while adding new content.

## How It Works

### 1. **Source Detection**
- Monitors `config/newsletters.md` for changes
- Detects new newsletter sources added to the configuration
- Automatically adds new sources to your data

### 2. **Post Discovery**
- Checks existing newsletters for new posts
- Only fetches content you don't already have
- Preserves all existing posts and personalization

### 3. **Data Preservation**
- **Never overwrites** existing posts
- **Maintains** your read/like/hide status
- **Appends** new content to existing data
- **Updates** metadata when sources change

## Usage

### Basic Update
```bash
python scripts/incremental_update.py
```

### What Happens During Update
1. **Loads existing data** from `data/index.json`
2. **Checks newsletter.md** for configuration changes
3. **Detects new sources** and adds them to tracking
4. **Fetches new posts** from all sources (new and existing)
5. **Saves updated data** preserving all existing content
6. **Regenerates HTML** for the web interface

### Update Triggers

#### Manual Updates
- Run `python scripts/incremental_update.py` whenever you want
- Useful for checking new posts from your sources

#### Configuration Changes
- Add new newsletters to `config/newsletters.md`
- Run incremental update to discover new sources
- Update automatically detects and processes changes

#### Regular Maintenance
- Run periodically to check for new posts
- Recommended: daily or weekly depending on your sources

## Benefits

✅ **Efficient**: Only fetches new content, not everything  
✅ **Preserves Work**: Keeps all your personalization and curation  
✅ **Smart Detection**: Knows what's new vs. what you already have  
✅ **Append-Only**: Never loses data, only adds to it  
✅ **Automatic**: Handles newsletter.md changes automatically  

## Data Structure

### New Sources
- Added to `data/index.json` with metadata
- Initialized with empty personalization fields
- Ready for post discovery

### New Posts
- Fetched and stored in `data/content/`
- Metadata saved with personalization defaults
- Integrated into existing newsletter structure

### Personalization Fields
All new posts start with:
- `read: false`
- `like: false` 
- `hide: false`
- `not_interesting: false`

## Requirements

### Dependencies
- `substack_api` library for Substack sources
- `requests` for HTTP operations
- Standard Python libraries (pathlib, json, etc.)

### Installation
```bash
pip install substack-api requests
```

## Troubleshooting

### "substack_api not available"
- Install the library: `pip install substack-api`
- This is required for fetching Substack content

### No New Posts Found
- Sources may not have new content since last update
- Check if sources are still active
- Verify newsletter.md configuration

### Update Fails
- Check console output for error messages
- Ensure write permissions to `data/` directory
- Verify `config/newsletters.md` is valid

## Integration

### With Web Interface
- Updates automatically regenerate `data/index.html`
- New posts appear immediately in the interface
- All personalization features work on new content

### With Existing Scripts
- Compatible with current `test_substack_api.py`
- Uses same data storage structure
- Preserves all existing functionality

## Future Enhancements

- **RSS Support**: Add RSS feed parsing for non-Substack sources
- **Scheduled Updates**: Automatic updates via cron/systemd
- **Change Notifications**: Alert when new sources or posts are found
- **Backup System**: Automatic backups before major updates
- **Conflict Resolution**: Handle URL changes and redirects

## Example Workflow

1. **Daily**: Run incremental update to check for new posts
2. **Weekly**: Review newsletter.md for new sources to add
3. **Monthly**: Clean up old/unused sources if desired
4. **Ongoing**: Use web interface to curate and personalize content

The system is designed to be **set-and-forget** - once configured, it maintains your data automatically while preserving all your curation work.
