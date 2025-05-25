# Changelog

## [2024-03-XX] CSS and Display Improvements

### Added
- Three CSS styling options:
  - `substack-minimal.css`: Simple, clean styling
  - `substack-cleaned.css`: Substack-like styling without complexity
  - `substack-original.css`: Original Substack CSS (reference)

### Changed
- Updated HTML template to use Substack classes (`post`, `typography`)
- Modified server to serve static files from project root
- Moved CSS files to `src/web/static/css/`

### Fixed
- CSS loading issues in local server
- Browser console errors from original Substack CSS 