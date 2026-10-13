<div align="center">

# Substack pAIa Extension

A personalized Substack reading assistant, implemented as the Daily Briefing pAIa Chrome extension.

[![Status](https://img.shields.io/badge/status-functional%20extension-brightgreen)](#project-status)
[![Python](https://img.shields.io/badge/python-research%20pipeline-3776AB)](#current-system)
[![Chrome Extension](https://img.shields.io/badge/chrome%20extension-v1.0.7-4285F4)](#extension-goal)
[![Docs](https://img.shields.io/badge/docs-project%20documentation-blue)](docs/README.md)

</div>

> Extension fork note: this repository originated from `alexhkurz/substack-pAIa` and has evolved into a standalone Substack browser extension. The original Python research prototype remains available alongside the extension.

## What This Project Is

Substack pAIa helps readers personalize their Substack feed using their own reading feedback. Its browser extension, **Daily Briefing pAIa**, re-ranks feed posts based on publication affinity, author affinity, freshness, and explicit user preferences.

Readers can like posts, mark them read, hide them, or mark them not interesting. The extension uses these signals to adjust rankings and explain why posts appear where they do.

All extension ranking and storage run locally in the browser. No separate account, backend, or Python server is required.

## Extension Goal

The extension provides a single-user recommendation layer directly on supported Substack feeds:

```text
Open a Substack inbox or publication archive
    -> extract metadata from recognized post cards
    -> load locally saved feedback and settings
    -> calculate publication and author affinity
    -> rank posts and explain their scores
    -> display feedback controls and reorder the feed
    -> save updated feedback locally
```

The current implementation focuses on feed ranking. Article-text analysis, semantic similarity, and citation sentiment are not part of the extension's current ranking engine.

## Current System

The repository now contains a standalone Chrome extension and the original Python research prototype:

| Area | Current functionality |
| --- | --- |
| Browser extension | Manifest V3 extension under `extension/`, currently version 1.0.7 |
| Feed extraction | Recognizes post cards in Substack reader inbox and publication archive layouts |
| Personalization | Stores read, liked, hidden, and not-interesting feedback |
| Ranking | Combines publication affinity, author affinity, freshness, and direct post feedback |
| Feed controls | Recommended/original sorting, optional mark-read-on-open, hide, and restore |
| Dashboard | Popup showing feedback counts, publication affinity, and ranked posts |
| Settings | Configurable feedback weights and JSON export/import |
| Local storage | Uses `chrome.storage.local` for feedback, settings, and a feed snapshot |
| Python prototype | Retains newsletter discovery, offline reading, and citation sentiment analysis |

The ranking engine uses transparent rules rather than a trained model. Affinity is calculated from the current feed's extracted posts and saved feedback.

## Architecture Snapshot

```text
Substack feed
    -> extension/content.js: extract recognized post cards
    -> extension/store.js: load feedback and settings
    -> extension/engine.js: calculate affinities and rankings
    -> extension/content.js: annotate and reorder cards
    -> chrome.storage.local: persist feedback and feed snapshot
    -> extension/popup.js: display dashboard
```

The options page controls ranking preferences and data export/import. The service worker initializes settings and updates the toolbar badge.

The Python system under `src/` and `scripts/` remains independent of the browser extension.

## Project Status

The project has progressed beyond extension planning:

- **Current version:** 1.0.7, including the updated orange extension icon.
- **Implemented:** Manifest V3 shell, feed extraction, local ranking, feedback controls, ranking explanations, dashboard, options page, and export/import.
- **Reliability:** Storage migration, write-failure notices, feed deduplication, and cleanup of injected controls when navigating into a post.
- **Testing:** 30 automated tests covering the ranking engine, storage adapter, and feed integration, plus syntax and remote-code checks.
- **Store preparation:** Listing copy, screenshots, privacy policy, and a packaging script are present. Chrome Web Store publication is not confirmed in the repository.
- **Remaining work:** Broader surface support, date parsing improvements, formal performance and theme QA, and full extension end-to-end testing.

The extension currently targets recognized feed cards. Custom-domain publications are outside its host permissions, and Notes/activity feeds are not comprehensively supported.

## Quick Start

Load the extension in Chrome:

1. Download or clone this repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the repository's `extension/` folder.
6. Open your Substack inbox or a publication archive on a Substack domain.

The feed controls activate when at least three recognized post cards are present.

No build step, Python server, or runtime dependency installation is required.

For automated development checks, run from the repository root with Node.js and npm installed:

```bash
cd extension
npm install
npm test
npm run lint
```

To build the distribution package, run from `extension/`:

```bash
bash scripts/build-zip.sh
```

The package is generated at `extension/store/daily-briefing-paia.zip`.

## Key Files

| File | Purpose |
| --- | --- |
| `extension/manifest.json` | Extension version, permissions, and Manifest V3 configuration |
| `extension/content.js` | Extracts feed cards, injects controls, and reorders posts |
| `extension/engine.js` | Calculates feedback weights, affinities, rankings, and explanations |
| `extension/store.js` | Handles local storage, schema migration, and export/import |
| `extension/background.js` | Initializes settings and updates the toolbar badge |
| `extension/popup.js` | Displays feedback counts, affinity, and ranked posts |
| `extension/options.js` | Manages settings, configurable weights, and data controls |
| `extension/tests/` | Ranking, storage, and DOM integration tests |
| `extension/store/` | Store listing, privacy policy, and screenshots |
| `src/analysis/citation_sentiment.py` | Citation sentiment analysis in the Python prototype |
| `src/web/` | Original local reading interface and newsletter update logic |
| `docs/` | Research documentation, specifications, and earlier project plans |

## Documentation

- [Extension Guide](extension/README.md)
- [Extension Roadmap](extension/ROADMAP.md)
- [Store Submission Guide](extension/store/STORE-SUBMISSION.md)
- [Privacy Policy](extension/store/privacy.html)
- [Documentation Hub](docs/README.md)
- [Project Goal](docs/project-goal.md)
- [Production Readiness](docs/production-readiness.md)
- [Architecture](docs/spec-architecture.md)
- [Data Model](docs/spec-data-model.md)
- [Changelog](docs/CHANGELOG.md)

Some supporting documents describe earlier milestones and research plans. This README reflects the current extension implementation.

## Production Direction

The core extension is implemented. The next priorities are:

- submission!

Feedback persists locally, but affinity currently uses the current feed snapshot rather than a complete historical post catalog.

Permissions are limited to `storage` and access to `*.substack.com`. The extension makes no network requests of its own. Cross-device sync and browser-side citation sentiment remain future work.

## Contributing

This project combines a standalone browser extension with its original Python research tools. Update documentation whenever changes affect setup, behavior, ranking, storage, permissions, or project status.

For extension changes, run `npm test` and `npm run lint` from `extension/`, and verify the affected workflow on a supported Substack feed.
