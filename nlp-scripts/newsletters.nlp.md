# Newsletter Configuration NLP Instructions

## Overview
This document contains rules and instructions for an AI agent to construct `data/newsletters.yaml` from `config/newsletters.md`. The AI-agent should use these patterns to identify authors, assign appropriate metadata, and generate a complete YAML configuration.

## General Instructions

### Input Format
The input file `config/newsletters.md` contains one newsletter per line with some but not necessarily all of the following information:
- Author names (e.g., "Jared Bernstein")
- Publication names (e.g., "Astral Codex Ten")
- URL
- Topics and tags

### Output Format
Generate a YAML file with the following structure:
```yaml
# Configuration file for newsletters to download
# All fields except 'url' are optional and have sensible defaults

# Global settings (applied to all newsletters unless overridden)
settings:
  default_limit: 3
  download_metadata: true
  create_index: true
  retry_failed: true

# Newsletter configurations
newsletters:
  - name: "Publication Name"
    url: "https://subdomain.substack.com"
    author: "Author Name"
    wikipedia: "https://en.wikipedia.org/wiki/Author_Name"
    description: "Brief description of content focus"
    role: "professional-role"
    credibility: "credibility-level"
    categories: ["category1", "category2"]
    tags: ["tag1", "tag2", "tag3"]
    limit: 3
    enabled: true
```

### Required Keys

- **name**: Newsletter name (not author name)
- **url**: Substack URL (e.g., "https://author.substack.com")

### Desired Keys

- **author**: Real author name (when known)
- **wikipedia**: Wikipedia URL for real names or newsletters (eg https://en.wikipedia.org/wiki/Slate_Star_Codex )
- **affiliations**: Current and former nstitutions and date information (when known)
- **description**: Brief description of content focus of the newsletter
- **content_type**: "academic" and/or "commentary" (news/opinion)
- **role**: Professional roles (eg, academic-economist, political-commentator, etc.)
- **topics**: Array of content topics (eg economics, current affairs, etc)
- **tags**: Array of relevant tags
- **limit**: Number of posts to download (3 or 5)
- **enabled**: Whether to download this newsletter (true/false)

## Processing Instructions

1. **Parse Input**: Read each line from `newsletters.txt`
2. **Identify Author**: Extract author name and publication name
3. **Classify Role**: Apply role recognition rules
4. **Generate URL**: Find Substack URL using standard format
5. **Find Wikipedia**: Generate Wikipedia URL for real names
6. **Assign Categories**: Apply category assignment rules
7. **Generate Tags**: Apply tag assignment rules
8. **Write Description**: Generate appropriate description
9. **Set Limits**: Apply limit assignment rules
10. **Format Output**: Generate properly formatted YAML

