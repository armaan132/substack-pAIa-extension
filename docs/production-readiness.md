# Production Readiness Plan

This document describes what must improve before the project can be considered production ready as a standalone browser extension.

## Current State

The project currently works mostly as a local Python system:

- newsletter URLs are configured in `config/newsletters.md`
- RSS/API scripts discover and download posts
- HTML and metadata are stored locally under `data/`
- `data/index.json` acts as the central data file
- Flask serves a local reading interface
- citation sentiment analysis runs in Python
- user feedback is stored in local JSON fields

This is useful for prototyping, analysis, and resume demonstration. It is not yet production-ready as a browser extension.

## Production Target

The production target is a browser extension that can work on Substack pages without requiring the user to run a local Python server.

Expected behavior:

- detect when the active tab is a Substack post
- extract post metadata and readable article text
- identify links to other Substack posts/newsletters
- score author stance toward each referenced source
- show a clean extension panel or page overlay
- store user feedback using browser storage
- keep private reading data under user control

## Required Improvements

### 1. Browser Extension Shell

Add an extension directory with:

- `manifest.json`
- content script for Substack page extraction
- popup or side panel UI
- background service worker
- local storage wrapper
- extension icons and packaging instructions

### 2. Page Extraction Layer

Create browser-side extraction logic that can read the current page:

- title
- author
- newsletter name
- canonical URL
- publication date when available
- main article body
- outbound links
- context around each cited link

This should become the extension equivalent of the current Python HTML parsing flow.

### 3. JavaScript Sentiment Analyzer

The current sentiment analyzer is in Python. A standalone extension needs browser-runnable logic.

The first version should port the rule-based citation stance logic from Python to JavaScript:

- supportive phrase detection
- critical phrase detection
- neutral citation detection
- negation handling
- confidence scoring
- recommendation signal scoring

### 4. Browser Storage Model

Replace extension-time dependence on `data/index.json` with browser storage.

Suggested browser-side records:

```json
{
  "url": "https://example.substack.com/p/post",
  "title": "Post title",
  "author": "Author name",
  "newsletter": "Newsletter name",
  "analyzed_at": "ISO timestamp",
  "citations": [],
  "citation_summary": {},
  "user_feedback": {
    "read": false,
    "liked": false,
    "hidden": false,
    "not_interesting": false
  }
}
```

### 5. Recommendation Scoring

Build an explainable first recommendation score before adding more complex ML.

Initial signals:

- user liked similar authors or newsletters
- user marked similar posts not interesting
- post has supportive links from trusted sources
- post belongs to a preferred topic/category
- cited links have high-confidence author-stance signals

### 6. UX and Reliability

The extension should handle:

- non-Substack pages
- Substack home pages vs. post pages
- missing metadata
- dynamic page loads
- duplicate analysis of the same URL
- private/error pages
- no detected citations

### 7. Testing

Add tests for:

- extraction from sample Substack HTML
- sentiment scoring examples
- storage read/write behavior
- recommendation scoring
- extension UI rendering

The current Python tests should stay, but extension-specific JavaScript tests should be added when the extension code exists.

### 8. Privacy and Security

Before production:

- document what data is stored locally
- avoid collecting unnecessary page data
- avoid remote requests unless clearly disclosed
- keep permissions narrow in `manifest.json`
- do not request access to all sites unless needed

## Production-Ready Definition

The project can be considered production ready when:

- it installs as an unpacked or packaged Chrome extension
- it works without running Flask locally
- it analyzes real Substack posts reliably
- it stores feedback persistently
- it has tests for extraction, sentiment, and recommendation scoring
- it has clear setup and usage documentation
- the README and docs match the actual implementation

## Recommended Build Order

1. Add extension shell.
2. Implement current-page extraction.
3. Port citation sentiment scoring to JavaScript.
4. Add popup or side panel UI.
5. Add browser storage for feedback.
6. Add simple recommendation scoring.
7. Add tests and sample fixtures.
8. Package and document installation.
