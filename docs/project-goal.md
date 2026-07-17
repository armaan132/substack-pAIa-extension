# Project Goal

## One-Sentence Goal

Build a browser-based Substack reading assistant that helps a user understand, organize, and personalize newsletter content by analyzing posts, author cross-references, sentiment, and user feedback signals.

## Long-Term Vision

The long-term goal is to turn the existing Substack pAIa system into a standalone browser extension that runs while the user is reading Substack. Instead of requiring a local offline archive first, the assistant should analyze the currently open post, explain useful metadata, identify references to other writers, estimate the author's stance toward those references, and learn from the user's reading preferences.

The project should become a personal recommendation layer for long-form writing:

- It helps the user decide whether a post is worth reading.
- It surfaces how authors reference and evaluate each other.
- It remembers what the user marks as read, liked, hidden, or not interesting.
- It builds recommendation signals from both content analysis and personal feedback.
- It keeps the user in control of their reading data.

## Why This Project Matters

Substack and newsletter ecosystems are difficult to navigate because discovery is scattered across individual writers, recommendations, citations, and social links. A reader may want to know not only what an article says, but also how it connects to other writers and whether those connections are supportive, critical, or neutral.

This project focuses on that problem. It treats newsletters as a network of authors, posts, citations, and reader preferences.

## Target User

The target user is someone who reads a lot of Substack/newsletter content and wants a smarter reading workflow:

- students tracking technical, scientific, or policy writing
- researchers following public intellectual networks
- readers who want personalized recommendations without relying only on platform algorithms
- users who prefer local or user-controlled reading data

## First Extension Milestone

The first production direction should be a Chrome extension MVP with this workflow:

1. User opens a Substack post.
2. Extension detects the post title, author, newsletter, URL, and article text.
3. Extension extracts links to other Substack posts or newsletters.
4. Extension analyzes surrounding text to estimate author sentiment toward those references.
5. Extension shows a compact reading-assistant panel.
6. User can mark the post as read, liked, hidden, or not interesting.
7. Extension stores those signals locally for future recommendations.

## Out of Scope for the First Extension Version

The first extension version should avoid trying to rebuild every current backend feature. These can come later:

- full historical scraping of thousands of newsletters
- account systems
- cloud sync
- public recommendation sharing
- large model inference inside the extension
- automated crawling beyond the currently viewed page

The first priority is a reliable on-page assistant.

## Success Criteria

The project is moving in the right direction when it can:

- run as a browser extension without requiring `localhost`
- analyze the currently viewed Substack post
- extract citation/cross-reference context accurately
- show sentiment and recommendation metadata in the browser
- persist user feedback between sessions
- document architecture changes as the system evolves
