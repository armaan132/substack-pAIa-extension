# Changelog

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
- Modified server to serve static files from project root

### Fixed
- CSS loading issues. Layout works now with the minimal and the cleaned CSS.

### Known Issues
- Original Substack CSS (`substack-original.css`) doesn't work and browser console shows errors
