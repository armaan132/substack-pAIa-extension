<div align="center">

# Substack pAIa Extension

An in-progress Substack reading assistant that provides smarter recommendations.

[![Status](https://img.shields.io/badge/status-extension%20prototype%20planning-blue)](#project-status)
[![Python](https://img.shields.io/badge/python-data%20pipeline-3776AB)](#current-system)
[![Chrome Extension](https://img.shields.io/badge/chrome%20extension-planned-4285F4)](#extension-goal)
[![Docs](https://img.shields.io/badge/docs-maintained-brightgreen)](docs/README.md)

</div>

> Extension fork note: this repository was cloned from the original `alexhkurz/substack-pAIa` project as a test copy for reshaping the system into a standalone Substack browser extension.

## What This Project Is

Substack pAIa is becoming a browser-based assistant for people who read a lot of Substack/newsletter content. The goal is to help a reader understand a post faster by showing useful metadata, detecting references to other writers, estimating whether the author is supportive or critical of those references, and learning from the user's reading feedback.

Think of it as a personal reading intelligence layer for Substack: part content discovery tool, part citation/sentiment analyzer, part recommendation system.

## Extension Goal

The long-term product goal is a standalone browser extension that works directly on Substack pages:

```text
Open a Substack post
    -> extract post metadata, article text, and links
    -> detect references to other Substack writers/posts
    -> score author sentiment toward those references
    -> show recommendation and reading metadata in the browser
    -> save read/liked/not-interesting feedback locally
```

The first extension milestone is intentionally focused: analyze the currently viewed Substack post and show citation sentiment plus basic recommendation signals.

## Current System

The current implementation is a Python-based local prototype that already supports several core pieces of the future extension:

| Area | Current functionality |
| --- | --- |
| Content discovery | Finds and downloads newsletter posts using RSS/Substack API logic |
| Local storage | Saves post HTML and JSON metadata under `data/` |
| Offline reading | Generates a local `index.html` reading interface |
| Personalization | Tracks read, liked, hidden, and not-interesting feedback |
| Citation sentiment | Scores surrounding text around Substack links as supportive, neutral, or critical |
| Recommendation signals | Stores author-feedback signals that can later feed ranking logic |

## Architecture Snapshot

```text
config/newsletters.md
    -> scripts and src/web/updaters/
    -> data/content/ + data/metadata/
    -> data/index.json
    -> src/analysis/citation_sentiment.py
    -> src/web/index_generator.py
    -> local Flask reading interface
```

The extension version will replace the local-only reading flow with browser-side page extraction, browser storage, and an extension popup or side panel.

## Project Status

This repository is currently in the transition stage:

- Existing: Python data pipeline, local Flask server, generated reading interface, citation sentiment analysis.
- In progress: project documentation and extension architecture planning.
- Next: Chrome extension shell, current-page Substack extraction, JavaScript sentiment scoring, and browser-local feedback storage.

## Quick Start

Install the existing Python dependency:

```bash
pip install substack-api
```

Download configured newsletter posts:

```bash
python scripts/test_substack_api.py
```

Run the local reading server:

```bash
python scripts/run_server.py
```

Then open:

```text
http://localhost:8000/data/index.html
```

Run citation sentiment analysis:

```bash
python scripts/update_citation_sentiment.py
```

## Key Files

| File | Purpose |
| --- | --- |
| `src/analysis/citation_sentiment.py` | Analyzes author stance toward cited Substack links |
| `src/web/server.py` | Local Flask API and reading server |
| `src/web/index_generator.py` | Builds the local HTML/JSON reading interface |
| `src/web/updaters/` | RSS/API update and discovery logic |
| `config/newsletters.md` | User-maintained newsletter source list |
| `docs/` | Project goal, architecture, production readiness, and implementation specs |

## Documentation

- [Documentation Hub](docs/README.md)
- [Project Goal](docs/project-goal.md)
- [Production Readiness](docs/production-readiness.md)
- [Architecture](docs/spec-architecture.md)
- [Data Model](docs/spec-data-model.md)
- [Changelog](docs/CHANGELOG.md)

## Production Direction

To become production-ready as an extension, the project needs:

- a Manifest V3 Chrome extension shell
- content scripts for Substack page extraction
- browser-side citation sentiment scoring
- local browser storage for user feedback
- a compact popup or side panel UI
- tests for extraction, sentiment scoring, and recommendation logic
- clear privacy documentation around stored reading data

See [Production Readiness](docs/production-readiness.md) for the full roadmap.

## Contributing

This project is evolving from a local research prototype into a browser extension. Documentation should be updated whenever changes affect architecture, setup, behavior, data models, or the extension direction.
