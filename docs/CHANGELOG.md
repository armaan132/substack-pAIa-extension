# Changelog

## [2025-07-07] Newsletter Download and Index System Overhaul

### Added
- **NLP Configuration Generator**: AI-powered YAML generation from markdown using `nlp-scripts/newsletters.nlp.md`
- **Newsletter Download System**: Script to download posts from Substack newsletters using `substack_api`
- **Markdown Configuration**: `config/newsletters.md` for managing newsletter URLs and metadata
- **Index Generator**: Separate `src/web/index_generator.py` for creating HTML and JSON indexes
- **Date Formatting**: Human-readable dates (e.g., "Jul 7, 2025") instead of ISO strings
- **Chronological Index**: All posts displayed in single timeline, sorted by date (latest first)
- **Dual Links**: Each post shows both local copy and original Substack link (🔗)
- **Duplicate Prevention**: Skip existing posts to avoid re-downloading
- **Rich Metadata**: Author names, Wikipedia links, professional roles, topics, and tags

### Changed
- **Architecture Refactor**: Separated data storage (`filesystem_store.py`) from presentation (`index_generator.py`)
- **URL Handling**: Fixed `_get_safe_name()` to properly handle custom domains (e.g., `www.astralcodexten.com` → `astralcodexten`)
- **Metadata Storage**: Fixed date extraction using `post_date` field instead of `publishedAt`
- **Index Layout**: Changed from newsletter-grouped view to chronological timeline
- **Post Display**: One line per post showing: Newsletter Name | Title | Links | Date

### Fixed
- **Date Display**: Posts now show proper publication dates instead of "No date"
- **Newsletter Names**: Correct display names from markdown config instead of directory names
- **URL Mapping**: Proper newsletter URLs in index instead of generic substack.com links
- **Verbose Logging**: Removed excessive metadata debugging output

### Technical Improvements
- **Single Responsibility**: Clear separation between data storage and presentation logic
- **Generic Design**: Index generator reads from markdown config, no hardcoded newsletter names
- **Future-Ready**: Easy to switch from markdown to YAML configuration later
- **Error Handling**: Better error handling for missing metadata and failed downloads
- **AI Integration**: NLP instructions for automated YAML generation from markdown
- **Efficient Downloads**: Skip existing posts to reduce bandwidth and processing time

## [2025-05-25] CSS and Display Improvements

### Added
- Three CSS styling options in `src/web/static/css`:
  - `substack-minimal.css`: Simple, clean styling
  - `substack-cleaned.css`: Original Substack CSS simplified
  - `substack-original.css`: Original Substack CSS (reference)

### Changed
- Moved CSS files to `src/web/static/css/`
- Added a constant `CSS_PATH` to `filesystem_store.py`. Change this constant to experiment with different CSS.
- Created an HTML template in [`src/database/filesystem_store.py`](../src/database/filesystem_store.py) which links to `CSS_PATH`
- Modified [the server](../scripts/serve.py) to serve static files from project root

### Fixed
- CSS loading issues. Layout works now with the minimal and the cleaned CSS.

### Known Issues
- Original Substack CSS (`substack-original.css`) doesn't work and browser console shows errors
