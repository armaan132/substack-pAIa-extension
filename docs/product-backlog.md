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
  - [ ] Create simplified version of Substack CSS
  - [ ] Test with different post formats (text, images, etc.)
  - [ ] Style typography (fonts, sizes, line heights)
  - [ ] Adjust spacing and margins
  - [ ] Style images and media content
  - [ ] Implement dark/light mode support

---

(the following items have been sketched out with AI and need careful discussion)

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
- [ ] Implement AI post summaries
  - [ ] Generate concise summaries
    - [ ] Key points extraction
    - [ ] Main findings/arguments
    - [ ] Methodology highlights
  - [ ] Summary management
    - [ ] Store summaries with post metadata
    - [ ] Version control for summaries
    - [ ] User feedback/corrections
  - [ ] Display integration
    - [ ] Show summaries in dashboard
    - [ ] Quick-view summary cards
    - [ ] Expandable detailed summaries

## Content Organization & Discovery
- [ ] Basic Content Collection
  - [ ] Implement web scraper for science Substacks
    - [ ] Scrape Substack's science category pages
    - [ ] Extract newsletter information
    - [ ] Build discovery queue for manual verification
  - [ ] Admin interface for initial processing
    - [ ] Review discovered newsletters
    - [ ] Add to monitored list
    - [ ] Basic categorization

- [ ] Tagging System
  - [ ] Publication-level themes
    - [ ] Broad topic areas (e.g., "Economics", "Climate Science")
    - [ ] Author expertise domains
    - [ ] Publication focus/scope tags
  - [ ] Post-level tags
    - [ ] Specific topics/concepts
    - [ ] Research findings
    - [ ] Type of content (analysis, news, review)
  - [ ] Tag relationships and management
    - [ ] Link publication themes to post tags
    - [ ] Track theme-tag correlations
    - [ ] Theme evolution tracking

- [ ] Content Organization Tools
  - [ ] Create curated collections interface
  - [ ] Implement manual highlight system for breakthrough research
  - [ ] Add "big picture" discussion section
  - [ ] Build content organization admin tools

- [ ] Smart Discovery & Recommendations
  - [ ] Theme-based discovery
    - [ ] Find similar publications using themes
    - [ ] Discover cross-referenced content
    - [ ] Suggest new sources based on themes
  - [ ] Automated tag suggestions
    - [ ] Content analysis (key terms, embeddings)
    - [ ] Tag matching and suggestions
    - [ ] Confidence scoring and feedback

- [ ] Integrated User Interface
  - [ ] Theme browse/explore interface
    - [ ] Multi-tag filtering
    - [ ] Tag intersection views
    - [ ] Related tag suggestions
  - [ ] Personal feed and following
    - [ ] Follow multiple themes
    - [ ] Adjustable theme weights
    - [ ] Multi-theme blended view
    - [ ] Discovery queue with tag suggestions
    - [ ] New content recommendations
    - [ ] Theme gap detection
    - [ ] Cross-theme discoveries

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
  
---

(list of potential further ideas)

## Future Considerations
- Advanced search with NLP
- Automated trend analysis
- Academic credential verification
- Research opportunity matching
