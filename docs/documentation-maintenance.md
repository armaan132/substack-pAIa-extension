# Documentation Maintenance

This repository should keep documentation current as the code changes. The docs are part of the product, not a separate afterthought.

## Rule

Update documentation in the same change whenever code changes affect:

- project goals or scope
- architecture
- setup or installation
- dependencies
- commands or scripts
- API endpoints
- data structures
- browser extension behavior
- user-facing functionality
- known limitations
- production-readiness status

## What To Update

Use this checklist before committing a change:

- README: update if setup, project summary, commands, or major features changed.
- `docs/project-goal.md`: update if the product direction or extension goal changed.
- `docs/spec-architecture.md`: update if components, data flow, or runtime architecture changed.
- `docs/spec-data-model.md`: update if JSON/storage fields changed.
- `docs/spec-server.md`: update if Flask routes or local APIs changed.
- `docs/spec-web-interface.md`: update if the local generated UI changed.
- `docs/production-readiness.md`: update if the extension plan, readiness gaps, or production checklist changed.
- `docs/CHANGELOG.md`: add a short entry for notable user-facing or architectural changes.

## Documentation Standard

Good documentation in this repo should:

- describe what exists now, not only what is planned
- separate current behavior from future goals
- name the files or modules involved
- include example data shapes when useful
- explain why a change matters to the project goal
- avoid outdated claims after implementation changes

## Suggested Change Entry Format

Use this format in `docs/CHANGELOG.md` for notable changes:

```md
## [YYYY-MM-DD] Short Change Title

### Added
- New behavior or documentation.

### Changed
- Existing behavior that was modified.

### Fixed
- Bugs or corrections.

### Notes
- Context, limitations, or follow-up work.
```

## Extension-Specific Documentation

When extension code is added, documentation should include:

- how to load the extension locally
- what browser permissions it requests
- what data is stored
- which Substack pages it supports
- how current-page extraction works
- how recommendation and sentiment scores are calculated
- what still requires the Python/local system, if anything
