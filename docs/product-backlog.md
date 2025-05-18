# Product Backlog


## Basic Featurs 
- [x] Implement newsletter data collection using Substack API (using a manually created list of substacks)
  - [x] Fetch recent posts 
  - [x] Extract metadata (title, author, word count) 
  - [x] Store in local `data` folder
- [x] Simple interface for reading stored newsletters
  - [x] `index.html` linking downloaded newsletters
  - [x] `serve.py` serving downloaded files on local host
- [ ] Improve newsletter content display
  - [ ] Extract Substack's CSS using browser dev tools
    - [ ] Save main post content styles
    - [ ] Save typography styles
    - [ ] Save responsive layout styles
  - [ ] Create simplified version of Substack CSS
  - [ ] Test with different post formats (text, images, etc.)
  - [ ] Style typography (fonts, sizes, line heights)
  - [ ] Add proper spacing and margins
  - [ ] Style images and media content
  - [ ] Implement dark/light mode support

---

(the following items need prioratizing and details)

## Newsletter Monitoring System 
- [ ] Set up periodic refresh mechanism
- [ ] Build basic monitoring dashboard
  - [ ] Create dashboard layout and basic UI
  - [ ] Implement system health indicators
    - [ ] Last successful data fetch timestamp
    - [ ] API connection status
    - [ ] Database storage metrics
  - [ ] Add newsletter data displays
    - [ ] Recent posts list with metadata
    - [ ] Post collection statistics
    - [ ] Error logs/alerts section
  - [ ] Set up automatic dashboard refresh

## Annotation System
- [ ] Chrome extension that can annotate / highlight text
  - [ ] Text highlighting functionality
    - [ ] Multiple highlight colors
    - [ ] Save highlights locally
    - [ ] Export highlights
  - [ ] Annotation system
    - [ ] Add notes to highlighted sections
    - [ ] Sidebar for viewing all annotations
    - [ ] Search through annotations
- [ ] Local server for filesystem access
  - [ ] Set up basic Express/FastAPI server
  - [ ] Create API endpoints
    - [ ] Save annotations to filesystem
    - [ ] Load annotations from filesystem
    - [ ] Export/import functionality
  - [ ] Extension-server communication
    - [ ] Establish secure connection protocol
    - [ ] Handle extension requests
    - [ ] Error handling & retry logic
  - [ ] File system operations
    - [ ] Define storage structure
    - [ ] Handle concurrent writes
    - [ ] Backup mechanism
- [ ] Annotation storage system
  - [ ] Design metadata schema
    - [ ] Highlight data (position, color, text content)
    - [ ] Annotation text
    - [ ] Timestamp
    - [ ] Article reference
  - [ ] Storage implementation
    - [ ] Local storage in Chrome extension
    - [ ] Backup to local database
    - [ ] JSON format for easy export/import
  - [ ] Link annotations to newsletter content
    - [ ] Store text position markers
    - [ ] Handle content updates
    - [ ] Version tracking for posts

## Newsletter Discovery System 
- Implement web scraper for finding new science Substacks
  - Scrape Substack's science category pages
  - Extract newsletter information from cross-references
  - Build discovery queue for manual verification
- Create admin interface for:
  - Reviewing discovered newsletters
  - Adding to monitored list
  - Categorizing newsletters

## Theme Following 
- Design and implement tagging system for scientific themes
- Create theme browse/explore interface
- Add ability to follow themes
- Build theme feed view

## Content Organization 
- Create curated collections interface
- Implement manual highlight system for breakthrough research
- Add "big picture" discussion section
- Build content organization admin tools

## Basic Recommendations 
- Implement tag-based recommendation algorithm
- Create personalized feed based on followed themes
- Add "similar content" suggestions
- Build recommendation management interface

## User Engagement 
- Add author contact information display
- Create simple author profile pages
- Implement basic engagement metrics
- Build notification system for new content

## Future Considerations
- Advanced search with NLP
- Automated trend analysis
- Academic credential verification
- Research opportunity matching
