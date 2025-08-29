# Content Discovery Specification

## Overview

The content discovery system is responsible for finding and retrieving newsletter posts from external sources (primarily Substack newsletters) and making them available in the local system. The system implements a multi-strategy approach with RSS feeds as the primary method and Substack API as a fallback, ensuring reliable content discovery across different newsletter configurations.

## Content Discovery Strategies

### **Primary Strategy: RSS Feed Discovery**

#### **RSS Endpoint Detection**
The system automatically tests multiple RSS endpoint patterns for each newsletter:

```
Primary: https://newsletter.substack.com/feed
Fallback 1: https://newsletter.substack.com/rss
Fallback 2: https://newsletter.substack.com/feed.xml
Fallback 3: https://newsletter.substack.com/rss.xml
```

#### **RSS Feed Processing**
1. **Feed Validation**: Verify RSS feed is valid and accessible
2. **Content Parsing**: Extract post metadata (title, date, URL, description)
3. **Date Normalization**: Convert various date formats to ISO 8601
4. **URL Validation**: Ensure post URLs are accessible and valid
5. **Content Filtering**: Filter out non-post content (e.g., newsletter announcements)

#### **RSS Feed Advantages**
- **Fast Discovery**: RSS feeds provide immediate access to recent posts
- **Standardized Format**: Consistent structure across different newsletters
- **Real-time Updates**: Feeds update automatically when new posts are published
- **Efficient Processing**: Lightweight XML parsing with minimal bandwidth usage

### **Fallback Strategy: Substack API Discovery**

#### **API Integration**
When RSS feeds fail or are unavailable, the system falls back to Substack's API:

1. **API Endpoint Discovery**: Find the appropriate API endpoint for each newsletter
2. **Authentication Handling**: Manage API keys and rate limiting
3. **Post Retrieval**: Fetch post metadata through API calls
4. **Error Handling**: Graceful fallback when API calls fail

#### **API Fallback Benefits**
- **Reliability**: More consistent than RSS feeds
- **Rich Metadata**: Additional post information available through API
- **Rate Limiting**: Built-in protection against overwhelming external services
- **Error Reporting**: Better error information for debugging

### **Advanced Strategy: Recommendation Discovery**

#### **Content Discovery Network**
The system can discover new newsletters by scraping recommendation pages from existing newsletters:

1. **Recommendation Page Scraping**: Parse `/recommendations` URLs from known newsletters
2. **Newsletter Link Extraction**: Identify Substack URLs and newsletter names
3. **Source Validation**: Check if recommended newsletters are active and accessible
4. **Discovery Queue**: Queue new newsletters for RSS/API content discovery
5. **Configuration Updates**: Optionally suggest additions to `newsletters.md`

#### **Recommendation Page Structure**
```html
<!-- Example from https://johnplaice.substack.com/recommendations -->
<div class="newsletter-recommendation">
  <h3>Fields & Energy</h3>
  <p>By Hans G. Schantz</p>
  <a href="https://hansschantz.substack.com">Subscribe</a>
  <p>How Electromagnetism & Quantum Mechanics Work, And Where Physics Went Wrong</p>
</div>
```

#### **Network Effect Benefits**
- **Content Discovery**: Find newsletters you might not know about
- **Quality Curation**: Leverage existing newsletter curators' recommendations
- **Network Expansion**: Build connections between related newsletters
- **Automatic Growth**: Grow your reading list without manual research

## Content Processing Pipeline

### **Discovery Phase**

#### **1. Source Identification**
- **Newsletter URL**: Extract base URL from `newsletters.md`
- **RSS Detection**: Test multiple RSS endpoint patterns
- **API Fallback**: Identify appropriate API endpoints
- **Recommendation Discovery**: Find related newsletters

#### **2. Content Fetching**
- **RSS Parsing**: Parse RSS feeds using `feedparser` library
- **API Calls**: Make authenticated API requests
- **Error Handling**: Implement retry logic and fallback strategies
- **Rate Limiting**: Respect external service limits

#### **3. Metadata Extraction**
- **Post Information**: Extract title, date, URL, description
- **Newsletter Context**: Associate posts with newsletter and categories
- **Content Validation**: Verify post metadata integrity
- **Duplicate Detection**: Identify and handle duplicate posts

### **Processing Phase**

#### **1. Content Download**
- **HTML Retrieval**: Download full post HTML content
- **Content Cleaning**: Remove navigation, ads, and unnecessary elements
- **Format Standardization**: Normalize HTML structure and formatting
- **Local Storage**: Save content to local file system

#### **2. Metadata Enhancement**
- **Category Assignment**: Inherit categories from newsletter configuration
- **Tag Generation**: Extract or generate relevant tags
- **Content Analysis**: Analyze post content for additional metadata
- **Relationship Mapping**: Build connections between related posts

#### **3. Quality Assurance**
- **Content Validation**: Verify downloaded content integrity
- **Link Validation**: Check all internal and external links
- **Image Processing**: Handle embedded images and media
- **Error Reporting**: Log and report any processing failures

### **Storage Phase**

#### **1. File Organization**
```
data/
├── content/
│   └── newsletter_id/
│       ├── post_id_1.html
│       ├── post_id_2.html
│       └── post_id_3.html
├── metadata/
│   └── newsletter_id/
│       ├── post_id_1.json
│       ├── post_id_2.json
│       └── post_id_3.json
└── index.json
```

#### **2. Database Integration**
- **Post Records**: Add new posts to `index.json`
- **Status Tracking**: Track download and processing status
- **Personalization**: Initialize personalization fields
- **Index Updates**: Update category and newsletter indices

## Performance Optimization

### **Efficient Discovery**

#### **Parallel Processing**
- **Concurrent RSS Checks**: Multiple newsletters processed simultaneously
- **Batch API Calls**: Group API requests for efficiency
- **Connection Pooling**: Reuse HTTP connections when possible
- **Caching**: Cache RSS feed data to reduce redundant requests

#### **Smart Scheduling**
- **Update Frequency**: Adjust discovery frequency based on newsletter activity
- **Priority Queuing**: Process high-priority newsletters first
- **Background Processing**: Run discovery operations in background
- **User Experience**: Ensure discovery doesn't block user interactions

### **Resource Management**

#### **Bandwidth Optimization**
- **Incremental Updates**: Only fetch new or changed content
- **Compression**: Use gzip compression for HTTP requests
- **Conditional Requests**: Use ETags and If-Modified-Since headers
- **Content Filtering**: Download only essential content

#### **Storage Efficiency**
- **Content Deduplication**: Avoid storing duplicate content
- **Compression**: Compress stored HTML content
- **Cleanup**: Remove outdated or unused content
- **Backup Strategy**: Efficient backup and archiving

## Error Handling and Recovery

### **Discovery Failures**

#### **RSS Feed Issues**
- **Invalid Feeds**: Handle malformed RSS XML
- **Access Errors**: Manage network timeouts and connection failures
- **Content Changes**: Adapt to changes in feed structure
- **Fallback Strategies**: Switch to API when RSS fails

#### **API Integration Issues**
- **Authentication Failures**: Handle expired or invalid API keys
- **Rate Limiting**: Implement exponential backoff and retry logic
- **Service Unavailability**: Graceful degradation when services are down
- **Data Inconsistencies**: Validate and clean API responses

### **Content Processing Issues**

#### **Download Failures**
- **Network Errors**: Retry failed downloads with exponential backoff
- **Content Corruption**: Validate downloaded content integrity
- **Storage Issues**: Handle disk space and permission problems
- **Partial Failures**: Continue processing other content when some fails

#### **Processing Errors**
- **HTML Parsing**: Handle malformed HTML gracefully
- **Metadata Extraction**: Provide fallback values for missing data
- **Content Cleaning**: Maintain content quality even with processing errors
- **Error Logging**: Comprehensive logging for debugging and monitoring

## Configuration and Customization

### **Discovery Settings**

#### **Timing Configuration**
- **Update Intervals**: Configurable discovery frequency
- **Retry Delays**: Adjustable retry timing for failed operations
- **Timeout Values**: Configurable network and processing timeouts
- **Batch Sizes**: Adjustable batch processing for large operations

#### **Content Preferences**
- **Download Limits**: Maximum content size and count limits
- **Content Types**: Filter specific types of content
- **Quality Thresholds**: Minimum quality requirements for content
- **Storage Policies**: Content retention and cleanup rules

### **Advanced Configuration**

#### **Newsletter-Specific Settings**
- **Custom RSS Endpoints**: Override default RSS patterns
- **API Configuration**: Newsletter-specific API settings
- **Update Frequency**: Individual newsletter update schedules
- **Content Filters**: Newsletter-specific content filtering rules

#### **Network Configuration**
- **Proxy Settings**: Configure proxy servers for external access
- **Rate Limiting**: Adjust request rates for different services
- **Timeout Configuration**: Service-specific timeout values
- **Retry Policies**: Custom retry logic for different failure types

## Monitoring and Analytics

### **Discovery Metrics**

#### **Performance Tracking**
- **Discovery Success Rate**: Percentage of successful content discoveries
- **Processing Time**: Time required for different discovery operations
- **Error Rates**: Frequency and types of discovery failures
- **Resource Usage**: Bandwidth, storage, and processing resource consumption

#### **Content Analytics**
- **Content Volume**: Number of posts discovered over time
- **Source Distribution**: Distribution of content across different sources
- **Quality Metrics**: Content quality and completeness measures
- **User Engagement**: How discovered content is used by users

### **Health Monitoring**

#### **System Health**
- **Service Availability**: Monitor external service availability
- **Error Tracking**: Track and categorize different types of errors
- **Performance Alerts**: Notify when performance degrades
- **Resource Monitoring**: Monitor system resource usage

#### **Content Health**
- **Content Freshness**: Track how current discovered content is
- **Link Validity**: Monitor broken or invalid links
- **Content Quality**: Assess overall content quality and completeness
- **Storage Health**: Monitor storage usage and efficiency

## Future Enhancements

### **Advanced Discovery Features**

#### **Intelligent Discovery**
- **Machine Learning**: Use ML to predict content relevance and quality
- **Content Recommendations**: Suggest content based on user preferences
- **Trend Analysis**: Identify trending topics and content
- **Quality Scoring**: Automatically score content quality

#### **Enhanced Integration**
- **Multiple Platforms**: Support for platforms beyond Substack
- **Social Media Integration**: Discover content from social media sources
- **News Aggregation**: Integrate with news aggregation services
- **Academic Sources**: Include academic and research content sources

### **Performance Improvements**

#### **Scalability Enhancements**
- **Distributed Processing**: Scale discovery across multiple machines
- **Cloud Integration**: Use cloud services for heavy processing
- **Advanced Caching**: Implement sophisticated caching strategies
- **Load Balancing**: Distribute discovery load across resources

#### **User Experience**
- **Real-time Updates**: Push notifications for new content
- **Smart Scheduling**: Intelligent update timing based on user behavior
- **Content Previews**: Show content previews before full download
- **Offline Synchronization**: Sync content across multiple devices

