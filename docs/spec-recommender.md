# Recommendation System Specification (spec-recommender.md)

## Overview

The recommendation system is a content discovery engine that automatically finds new newsletters by scraping recommendation pages from existing newsletters. This creates a **content discovery network** where newsletters recommend each other, expanding the user's reading options without manual research.

## Core Concept

### Content Discovery Network

Instead of manually searching for new newsletters, the system leverages existing newsletter curators' recommendations to discover quality content. When Newsletter A recommends Newsletter B, and Newsletter B recommends Newsletter C, the system can build a network of related, high-quality newsletters.

```
Newsletter A (Science) 
    ↓ recommends
Newsletter B (Physics)
    ↓ recommends  
Newsletter C (Quantum Mechanics)
    ↓ recommends
Newsletter D (Philosophy of Science)
```

## How It Works

### 1. **Recommendation Page Discovery**
- **Input**: Known newsletter URLs from `config/newsletters.md`
- **Process**: Append `/recommendations` to each newsletter URL
- **Output**: List of recommendation page URLs to scrape

**Example URLs:**
- `https://johnplaice.substack.com/recommendations`
- `https://astralcodexten.com/recommendations`
- `https://philosophy-blog.com/recommendations`

### 2. **HTML Scraping and Parsing**
- **Tool**: `requests` + `BeautifulSoup` for HTML parsing
- **Target Elements**: Newsletter recommendation blocks
- **Extracted Data**: Newsletter URLs, names, authors, descriptions

**Example HTML Structure:**
```html
<!-- From https://johnplaice.substack.com/recommendations -->
<div class="newsletter-recommendation">
  <h3>Fields & Energy</h3>
  <p>By Hans G. Schantz</p>
  <a href="https://hansschantz.substack.com">Subscribe</a>
  <p>How Electromagnetism & Quantum Mechanics Work, And Where Physics Went Wrong</p>
</div>
```

### 3. **Data Validation and Enrichment**
- **URL Validation**: Check if recommended newsletters are accessible
- **Metadata Extraction**: Newsletter name, author, description
- **Category Inference**: Suggest categories based on description and context
- **Duplicate Detection**: Avoid re-discovering already known newsletters

### 4. **Storage in index.json**
- **Location**: New `recommendations` section in `index.json`
- **Structure**: Organized by source newsletter with discovery metadata
- **Status Tracking**: Track review status (pending, approved, rejected)

## Data Structure

### Recommendations Section in index.json

```json
{
  "recommendations": {
    "discovered_at": "2025-08-24T14:06:18.112401",
    "total_discovered": 15,
    "pending_review": 8,
    "approved": 5,
    "rejected": 2,
    "sources": {
      "https://johnplaice.substack.com": {
        "name": "John Plaice",
        "category": "Science",
        "subcategory": "Philosophy",
        "last_scraped": "2025-08-24T14:06:18.112401",
        "recommendations": [
          {
            "newsletter_url": "https://hansschantz.substack.com",
            "name": "Fields & Energy",
            "author": "Hans G. Schantz",
            "description": "How Electromagnetism & Quantum Mechanics Work, And Where Physics Went Wrong",
            "discovered_via": "https://johnplaice.substack.com/recommendations",
            "discovered_at": "2025-08-24T14:06:18.112401",
            "status": "pending_review",
            "suggested_category": "Science",
            "suggested_subcategory": "Physics",
            "confidence_score": 0.85,
            "source_newsletter_quality": "high"
          }
        ]
      }
    }
  }
}
```

### Recommendation Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `newsletter_url` | string | Substack URL of recommended newsletter |
| `name` | string | Newsletter display name |
| `author` | string | Author/creator name |
| `description` | string | Brief description or tagline |
| `discovered_via` | string | URL of the recommendation page |
| `discovered_at` | string | ISO timestamp of discovery |
| `status` | string | `pending_review`, `approved`, `rejected` |
| `suggested_category` | string | Inferred main category |
| `suggested_subcategory` | string | Inferred subcategory |
| `confidence_score` | float | 0.0-1.0 confidence in categorization |
| `source_newsletter_quality` | string | Quality rating of source newsletter |

## Implementation Architecture

### Core Functions

#### 1. **`discover_recommendations()`** - Main Discovery Function
- **Purpose**: Orchestrates the entire recommendation discovery process
- **Input**: List of known newsletter URLs
- **Output**: Updated recommendations in `index.json`
- **Location**: `src/web/index_generator.py`

#### 2. **`scrape_recommendation_page(url)`** - Page Scraping
- **Purpose**: Scrapes and parses a single recommendation page
- **Input**: Recommendation page URL
- **Output**: List of discovered newsletter objects
- **Error Handling**: Graceful failure for inaccessible pages

#### 3. **`extract_newsletter_data(html)`** - Data Extraction
- **Purpose**: Parses HTML to extract newsletter information
- **Input**: Raw HTML content
- **Output**: Structured newsletter data
- **Patterns**: Multiple HTML patterns for different page structures

#### 4. **`categorize_newsletter(description, context)`** - Auto-Categorization
- **Purpose**: Suggests categories based on description and source context
- **Input**: Newsletter description and source newsletter category
- **Output**: Suggested main_category and subcategory
- **Method**: Keyword matching + context inference

#### 5. **`validate_newsletter_url(url)`** - URL Validation
- **Purpose**: Checks if discovered newsletter is accessible
- **Input**: Newsletter URL
- **Output**: Boolean + metadata (active, post_count, etc.)
- **Method**: HTTP HEAD request + basic validation

### Integration Points

#### With Content Discovery System
```python
def discover_recommendations():
    # 1. Get known newsletters
    known_newsletters = load_newsletters_from_config()
    
    # 2. Scrape recommendation pages
    for newsletter in known_newsletters:
        recommendations_url = f"{newsletter['url']}/recommendations"
        discovered = scrape_recommendation_page(recommendations_url)
        
        # 3. Validate and categorize
        for rec in discovered:
            if validate_newsletter_url(rec['newsletter_url']):
                rec['suggested_category'] = categorize_newsletter(rec['description'])
                add_to_recommendations(rec)
    
    # 4. Update index.json
    update_recommendations_in_json()
```

#### With User Interface
- **Discovery Dashboard**: Show pending recommendations
- **Review Interface**: Approve/reject discovered newsletters
- **Category Suggestions**: Display inferred categories
- **Integration Options**: Add to `newsletters.md` or ignore

## Discovery Strategies

### 1. **Direct Recommendations**
- Scrape `/recommendations` pages from known newsletters
- Most reliable source of quality recommendations
- Direct curator endorsement

### 2. **Cross-Reference Discovery**
- Find newsletters that recommend each other
- Build recommendation networks
- Identify high-quality clusters

### 3. **Category-Based Discovery**
- Focus on newsletters in specific categories
- Discover related content within domains
- Build comprehensive category coverage

### 4. **Quality-Based Discovery**
- Prioritize recommendations from high-quality sources
- Weight recommendations by source reputation
- Filter out low-quality suggestions

## User Workflow

### 1. **Automatic Discovery**
- System runs recommendation discovery periodically
- New newsletters appear in "Pending Review" section
- Users notified of new discoveries

### 2. **Review Process**
- User reviews each discovered newsletter
- Views suggested category and description
- Checks newsletter directly if needed

### 3. **Decision Making**
- **Approve**: Add to `newsletters.md` for content discovery
- **Reject**: Mark as rejected, won't be suggested again
- **Defer**: Keep in pending for later review

### 4. **Integration**
- Approved newsletters added to main system
- Content discovery begins automatically
- Personalization features available immediately

## Benefits

### For Users
- **Content Discovery**: Find newsletters you might not know about
- **Quality Curation**: Leverage existing newsletter curators' expertise
- **Time Saving**: No need to manually research new sources
- **Category Expansion**: Discover content in new domains

### For the System
- **Network Effect**: More newsletters → more recommendations → more discovery
- **Quality Improvement**: Build on trusted sources' curation
- **Automatic Growth**: System expands without manual intervention
- **User Engagement**: New content keeps users engaged

### For Newsletter Ecosystem
- **Cross-Promotion**: Help quality newsletters find readers
- **Community Building**: Connect related newsletters
- **Discovery Network**: Create recommendation networks

## Implementation Considerations

### Technical Challenges

#### 1. **HTML Parsing Robustness**
- Different newsletter themes have different HTML structures
- Need multiple parsing patterns for reliability
- Handle malformed HTML gracefully

#### 2. **Rate Limiting and Ethics**
- Respect Substack's terms of service
- Implement delays between requests
- Don't overwhelm servers

#### 3. **Data Quality**
- Validate discovered newsletters are active
- Filter out spam or low-quality content
- Maintain recommendation quality over time

#### 4. **Categorization Accuracy**
- Improve auto-categorization algorithms
- Learn from user corrections
- Build better category inference

### Privacy and Ethics

#### 1. **Respectful Scraping**
- Follow robots.txt guidelines
- Implement reasonable delays
- Don't scrape private or password-protected content

#### 2. **User Control**
- Users control what gets added to their system
- Clear opt-out mechanisms
- Transparent about discovery process

#### 3. **Data Handling**
- Store only necessary metadata
- Respect newsletter creators' preferences
- Clear data retention policies

## Future Enhancements

### 1. **Machine Learning Integration**
- **Content Analysis**: Analyze newsletter content for better categorization
- **User Preference Learning**: Learn from user approval/rejection patterns
- **Quality Prediction**: Predict newsletter quality before discovery

### 2. **Advanced Discovery**
- **Social Network Analysis**: Find newsletters through social connections
- **Content Similarity**: Discover newsletters with similar content
- **Trend Analysis**: Identify emerging newsletters early

### 3. **User Experience**
- **Discovery Feed**: Show new discoveries in real-time
- **Collaborative Filtering**: Learn from other users' preferences
- **Smart Notifications**: Alert users to highly relevant discoveries

### 4. **Integration Features**
- **Auto-Import**: Automatically add high-confidence discoveries
- **Category Suggestions**: Smart category organization
- **Content Preview**: Show sample posts before adding

## Example Implementation

### Basic Scraping Function
```python
def scrape_recommendation_page(url):
    """Scrape a recommendation page and extract newsletter data."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        recommendations = []
        
        # Look for recommendation blocks
        rec_blocks = soup.find_all(['div', 'article'], class_=re.compile(r'recommendation|newsletter'))
        
        for block in rec_blocks:
            newsletter_data = extract_newsletter_from_block(block)
            if newsletter_data:
                recommendations.append(newsletter_data)
        
        return recommendations
        
    except Exception as e:
        print(f"⚠️ Failed to scrape {url}: {e}")
        return []
```

### Category Inference
```python
def categorize_newsletter(description, source_category=None):
    """Infer newsletter category from description and context."""
    description_lower = description.lower()
    
    # Keyword-based categorization
    if any(word in description_lower for word in ['physics', 'quantum', 'electromagnetism']):
        return 'Science', 'Physics'
    elif any(word in description_lower for word in ['philosophy', 'ethics', 'logic']):
        return 'Science', 'Philosophy'
    elif any(word in description_lower for word in ['economics', 'finance', 'markets']):
        return 'Science', 'Economics'
    
    # Fallback to source category
    if source_category:
        return source_category, 'General'
    
    return 'Science', 'General Science, Science Communication'
```

## Summary

The recommendation system transforms Daily Briefing pAIa from a static content aggregator into a **dynamic content discovery network**. By leveraging existing newsletter curators' recommendations, the system can:

1. **Automatically discover** new, high-quality newsletters
2. **Build recommendation networks** between related newsletters
3. **Expand user reading lists** without manual research
4. **Maintain quality** through curator endorsement
5. **Create network effects** that improve over time

This creates a powerful content discovery ecosystem where quality newsletters help users find more quality content, building a virtuous cycle of discovery and curation.

The system is designed to be **respectful, user-controlled, and quality-focused**, ensuring that automated discovery enhances rather than replaces human curation.

