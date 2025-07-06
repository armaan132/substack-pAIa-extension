# Newsletter Configuration NLP Instructions

## Overview
This document contains rules and instructions for an AI agent to reconstruct `newsletters.yaml` from `newsletters.txt`. The agent should use these patterns to identify authors, assign appropriate metadata, and generate a complete YAML configuration.

## Input Format
The input file `newsletters.txt` contains one name per line, representing either:
- Author names (e.g., "Jared Bernstein")
- Publication names (e.g., "Astral Codex Ten")
- Combined formats (e.g., "Scott Alexander (Astral Codex Ten)")

## Output Format
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

## Author Recognition Rules

### Academic Economists
**Patterns:** Nobel laureates, university economics professors, published economic researchers
**Examples:**
- Paul Krugman → Nobel Prize winner, Princeton professor
- Jared Bernstein → Chief Economist to VP Biden, Georgetown professor
- Robin Hanson → George Mason University, prediction markets expert

**Metadata:**
- role: "academic-economist"
- credibility: "academic-level"
- categories: ["economics", "politics"] or ["economics", "futurism"]
- tags: Include "nobel" for Nobel laureates

### Academic Philosophers
**Patterns:** Philosophy professors, published philosophers, ethics researchers
**Examples:**
- Michael Huemer → University of Colorado, libertarian philosophy
- Richard Chappell → University of Miami, effective altruism
- Slavoj Žižek → Continental philosophy, critical theory

**Metadata:**
- role: "academic-philosopher"
- credibility: "academic-level"
- categories: ["philosophy", "politics"] or ["philosophy", "ethics"]
- tags: Include specific philosophical traditions

### Academic Physicians
**Patterns:** Medical doctors with research positions, healthcare innovators
**Examples:**
- Eric Topol → Cardiologist, digital health pioneer

**Metadata:**
- role: "academic-physician"
- credibility: "academic-level"
- categories: ["medicine", "science"]
- tags: Include medical specialties

### Political Commentators
**Patterns:** Journalists, policy analysts, economic commentators without academic positions
**Examples:**
- Matt Yglesias → Vox co-founder, policy commentator
- Noah Smith → Bloomberg columnist, economic commentator

**Metadata:**
- role: "political-commentator"
- credibility: "high-quality"
- categories: ["politics", "economics"]
- tags: Include "commentary", "policy"

### Independent Researchers
**Patterns:** High-quality independent publications, pseudonymous authors
**Examples:**
- Scott Alexander (Astral Codex Ten) → Pseudonymous, high-quality analysis

**Metadata:**
- role: "independent-researcher"
- credibility: "academic-level"
- categories: ["science", "medicine", "philosophy", "politics"]
- tags: Include "independent", "pseudonymous" if applicable

## URL Generation Rules

### Standard Format
- Extract author name or publication name
- Convert to lowercase
- Remove spaces and special characters
- Add `.substack.com` suffix

**Examples:**
- "Jared Bernstein" → "econjared.substack.com"
- "Paul Krugman" → "krugman.substack.com"
- "Matt Yglesias" → "mattyglesias.substack.com"

### Special Cases
- "Astral Codex Ten" → "astralcodexten.substack.com"
- "Noah Smith" → "noahpinion.substack.com" (known publication name)

## Wikipedia URL Generation

### Standard Format
- Use author's real name (not pseudonyms)
- Convert to Wikipedia URL format
- Handle special characters (e.g., Žižek → %C5%BDi%C5%BEek)

**Examples:**
- "Jared Bernstein" → "https://en.wikipedia.org/wiki/Jared_Bernstein"
- "Slavoj Žižek" → "https://en.wikipedia.org/wiki/Slavoj_%C5%BDi%C5%BEek"

### Special Cases
- "Richard Chappell" → "https://en.wikipedia.org/wiki/Richard_Chappell_(philosopher)"
- "Noah Smith" → "https://en.wikipedia.org/wiki/Noah_Smith_(economist)"
- Skip for pseudonymous authors (e.g., Scott Alexander)

## Publication Name Rules

### Author-Based Publications
For authors with personal Substacks, use descriptive names:
- "Michael Huemer's Substack"
- "Richard Chappell's Substack"
- "Robin Hanson's Substack"
- "Eric Topol's Substack"
- "Slavoj Žižek's Substack"

### Named Publications
Use actual publication names when known:
- "The Conscience of a Liberal" (Paul Krugman)
- "Slow Boring" (Matt Yglesias)
- "Noahpinion" (Noah Smith)
- "Astral Codex Ten" (Scott Alexander)
- "EconJared" (Jared Bernstein)

## Category Assignment Rules

### Primary Categories
- **economics**: Economic analysis, policy economics
- **politics**: Political commentary, policy analysis
- **philosophy**: Philosophical discussion, ethics
- **science**: Scientific research, medical science
- **medicine**: Healthcare, medical innovation
- **futurism**: Future predictions, forecasting

### Multi-Category Logic
- Academic economists: ["economics", "politics"]
- Political commentators: ["politics", "economics"]
- Philosophers: ["philosophy", "politics"] or ["philosophy", "ethics"]
- Physicians: ["medicine", "science"]
- Independent researchers: ["science", "medicine", "philosophy", "politics"]

## Tag Assignment Rules

### Academic Tags
- "nobel" for Nobel laureates
- "academic" for university professors
- "research" for published researchers

### Content Tags
- "policy" for policy analysis
- "commentary" for opinion pieces
- "analysis" for analytical content
- "forecasting" for prediction content
- "innovation" for technology/healthcare innovation

### Specialized Tags
- "effective-altruism" for EA content
- "libertarianism" for libertarian philosophy
- "critical-theory" for continental philosophy
- "prediction-markets" for forecasting
- "digital-health" for healthcare technology

## Description Generation Rules

### Format
Brief, 3-5 word phrases describing primary content focus

### Examples
- "Economics and policy analysis"
- "Philosophy, political theory, and libertarian thought"
- "Medicine, healthcare, and digital health innovation"
- "Economics, futurism, and prediction markets"

## Limit Assignment Rules

### Default
- Most newsletters: limit: 3

### Special Cases
- High-volume publications: limit: 5
- Independent researchers with longer posts: limit: 5

## Processing Instructions

1. **Parse Input**: Read each line from `newsletters.txt`
2. **Identify Author**: Extract author name and publication name
3. **Classify Role**: Apply role recognition rules
4. **Generate URL**: Create Substack URL using standard format
5. **Find Wikipedia**: Generate Wikipedia URL for real names
6. **Assign Categories**: Apply category assignment rules
7. **Generate Tags**: Apply tag assignment rules
8. **Write Description**: Generate appropriate description
9. **Set Limits**: Apply limit assignment rules
10. **Format Output**: Generate properly formatted YAML

## Quality Checks

### Required Fields
- name: Publication name (not author name)
- url: Valid Substack URL format
- author: Real author name (when known)
- role: Valid role classification
- credibility: Valid credibility level
- categories: Array of valid categories
- tags: Array of relevant tags
- limit: Integer (3 or 5)
- enabled: true

### Validation Rules
- All URLs should follow Substack format
- Wikipedia URLs only for real names
- Categories should be from approved list
- Tags should be relevant to content
- Descriptions should be concise and accurate

## Error Handling

### Unknown Authors
- Use publication name as fallback
- Skip Wikipedia URL
- Assign generic categories based on publication name
- Use "general" role and credibility

### Ambiguous Cases
- Prefer more specific classifications
- Use multiple categories when appropriate
- Include relevant tags for disambiguation

This instruction set should enable an AI agent to accurately reconstruct the complete `newsletters.yaml` configuration from the simple `newsletters.txt` list. 