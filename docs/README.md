# Documentation Hub

This folder is the source of truth for the Substack pAIa extension project. It explains what the project is trying to become, how the current system works, what functionality already exists, and what needs to change before the project is production ready.

The project is currently transitioning from an offline Python newsletter discovery system into a browser-based Substack reading assistant.

## Start Here

- [Project Goal](project-goal.md): long-term product direction and why the project exists.
- [Current Architecture](spec-architecture.md): how the current Python, Flask, storage, and analysis pieces fit together.
- [Production Readiness](production-readiness.md): what has to be improved before this can become a reliable extension product.
- [Documentation Maintenance](documentation-maintenance.md): what documentation must be updated whenever code changes.
- [Changelog](CHANGELOG.md): notable project changes over time.

## Current System

The current system is an offline-first content discovery and personalization pipeline:

```text
config/newsletters.md
    -> RSS/Substack API discovery
    -> saved HTML and metadata
    -> data/index.json
    -> Flask web server and generated HTML index
    -> user feedback and citation sentiment analysis
```

It can collect Substack/newsletter content, store HTML and JSON metadata locally, generate an offline reading interface, track user feedback such as read/not interesting/like/hide, and analyze author sentiment toward linked Substack posts.

## Extension Direction

The intended extension version should analyze the Substack post a user is currently reading:

```text
Open Substack post in browser
    -> content script extracts page metadata and links
    -> sentiment analyzer scores author stance toward cited posts
    -> recommender combines citation signals and user feedback
    -> extension panel shows metadata and actions on the page
    -> browser storage persists reading preferences
```

The first extension milestone should not convert the entire scraper. It should prove one focused workflow: while reading a Substack post, the assistant can detect the post, extract cross-references, estimate sentiment, and let the user save feedback.

## Existing Specs

- [Data Model](spec-data-model.md): `index.json`, post fields, newsletter fields, and personalization data.
- [Server](spec-server.md): Flask routes and local API behavior.
- [Web Interface](spec-web-interface.md): generated HTML interface and user interactions.
- [Update System](spec-update-system.md): configuration, structure, and content update tiers.
- [Content Discovery](spec-content-discovery.md): RSS/API discovery and content download behavior.
- [Recommender](spec-recommender.md): newsletter recommendation discovery concepts.
- [Sentiment Analysis](sentiment-analysis.md): notes on citation and author-stance analysis.
- [User Stories](user-stories.md): user-facing needs and workflows.
- [Product Backlog](product-backlog.md): planned features.
- [Learning Backlog](learning-backlog.md): learning goals and implementation topics.

## Documentation Rule

Every meaningful repository change should update documentation when it changes behavior, architecture, data shape, setup steps, dependencies, user workflows, or the long-term extension direction.

Use [Documentation Maintenance](documentation-maintenance.md) as the checklist before committing changes.
