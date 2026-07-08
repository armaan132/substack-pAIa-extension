# Data Model Specification

## Overview
JSON-based data model supporting newsletter personalization with hierarchical categorization and user preferences.

## Core Data Structure

### Root Level (`index.json`)
```json
{
  "generated_at": "2025-08-28T06:35:24",
  "total_posts": 1251,
  "categories": {
    "Science": ["Economics", "Philosophy", "Psychology", "History"],
    "News and Opinion": ["None"],
    "Tech": ["None"]
  },
  "newsletters": { ... }
}
```

### Newsletter Structure
```json
"newsletters": {
  "newsletter_url": {
    "name": "Display Name",
    "url": "https://newsletter.substack.com",
    "main_category": "Science",
    "subcategory": "Economics",
    "tags": ["economics", "finance"],
    "posts": [ ... ]
  }
}
```

### Post Structure
```json
"posts": [
  {
    "title": "Post Title",
    "url": "https://newsletter.substack.com/p/post-slug",
    "date": "2025-08-28T06:35:24",
    "main_category": "Science",
    "subcategory": "Economics",
    "local_path": "data/content/newsletter_substack_com/post-slug.html",
    "not_interesting": false,
    "read": false,
    "like": false,
    "hide": false,
    "citation_sentiment": [
      {
        "target_url": "https://other-newsletter.substack.com/p/linked-post",
        "target_newsletter_url": "https://other-newsletter.substack.com",
        "anchor_text": "linked post",
        "context": "Sentence window around the citation link.",
        "sentiment": "supportive",
        "polarity": 0.32,
        "confidence": 0.41,
        "reliability": "medium",
        "evidence": ["supportive: recommend (recommend)"],
        "recommendation_signal": 0.13,
        "is_known_newsletter": true
      }
    ],
    "citation_sentiment_summary": {
      "total": 1,
      "supportive": 1,
      "critical": 0,
      "neutral": 0,
      "average_polarity": 0.32,
      "average_recommendation_signal": 0.13
    }
  }
]
```

## Data Relationships

### Category Hierarchy
- **Main Categories**: Top-level classification (Science, News and Opinion, Tech)
- **Subcategories**: Detailed classification within main categories
- **Post Assignment**: Each post belongs to one main category + subcategory

### Newsletter Organization
- **URL-based Keys**: Newsletter URLs serve as unique identifiers
- **Metadata**: Name, category, tags, and post collection
- **Content Discovery**: RSS feeds and API endpoints for each newsletter

### Post Management
- **Content Storage**: HTML files stored in organized directory structure
- **Personalization**: User preferences stored as boolean flags
- **Status Tracking**: Download status and content availability
- **Citation Sentiment**: Links to other Substack posts/newsletters are analyzed from saved HTML to capture author feedback toward cited sources
- **Recommendation Signals**: `citation_sentiment_summary.average_recommendation_signal` provides a numeric feature for future ranking
- **Reliability Labels**: Citation sentiment includes `low`, `medium`, or `high` reliability so recommendation code can ignore weak or ambiguous evidence

## Data Persistence

### File Storage
- **`index.json`**: Central database with all metadata and personalization
- **`newsletters.md`**: User-curated configuration (source of truth)
- **`data/content/`**: Organized HTML content storage
- **`index.html`**: Generated web interface

### Update Mechanisms
- **Configuration Changes**: `newsletters.md` → `index.json` → `index.html`
- **Content Discovery**: RSS feeds → post metadata → content download
- **Personalization**: User actions → `index.json` → immediate UI update
- **Citation Analysis**: saved HTML content → `citation_sentiment` fields → recommendation features + `index.html` badges

## Data Validation

### Required Fields
- **Newsletters**: name, url, main_category, subcategory
- **Posts**: title, url, date, main_category, subcategory
- **Categories**: Valid main_category and subcategory combinations

### Data Integrity
- **Category Consistency**: All posts have valid category assignments
- **URL Validation**: Newsletter and post URLs are accessible
- **Personalization Preservation**: User preferences maintained across updates

## Performance Characteristics

### Data Volume
- **Newsletters**: 70+ newsletters efficiently managed
- **Posts**: 1000+ posts with responsive filtering
- **Categories**: 3 main categories with 16+ subcategories

### Update Performance
- **Configuration**: 20-200ms for structure changes
- **Structure**: 1-5 seconds for metadata sync
- **Content**: Variable time for discovery and downloads

### Storage Efficiency
- **JSON Compression**: Efficient serialization and parsing
- **Content Organization**: Logical directory structure
- **Incremental Updates**: Only changed data processed
