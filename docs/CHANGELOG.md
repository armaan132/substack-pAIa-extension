# Changelog

## [2025-05-25] CSS and Display Improvements

### Added
- Three CSS styling options:
  - `substack-minimal.css`: Simple, clean styling
  - `substack-cleaned.css`: Original Substack CSS simplified
  - `substack-original.css`: Original Substack CSS (reference)

### Changed
- Moved CSS files to `src/web/static/css/`
- Created an HTML template in [`src/database/filesystem_store.py`](../src/database/filesystem_store.py) to use CSS
- Modified server to serve static files from project root

### Fixed
- CSS loading issues

### Known Issues
- Original Substack CSS (`substack-original.css`) doesn't work and browser console shows errors
