# Server Specification

## Overview
The newsletter personalization server is a Flask-based web application that serves as the backend for the newsletter personalization interface. It provides a unified architecture that handles both static file serving and dynamic API operations for user personalization data, implementing the three-tier update system architecture.

## Architecture Overview

### Core Components
- **Flask Web Server**: Main application server handling HTTP requests
- **Index Generator**: Python class responsible for generating HTML and JSON data files
- **File System Store**: Data persistence layer for newsletter metadata and user preferences
- **Static File Server**: Serves HTML, CSS, and JavaScript files to clients

### Data Flow Architecture
- **JSON-First Approach**: `index.json` serves as the central database containing all newsletter metadata and user personalization data
- **HTML Generation**: `index.html` is dynamically generated from the JSON data, ensuring consistency
- **Real-time Updates**: HTML is regenerated after each successful API operation to maintain data integrity

## Server Configuration

### Network Configuration
- **Port**: 8000 (configurable)
- **Bind Address**: All interfaces (0.0.0.0)
- **Protocol**: HTTP
- **Environment**: Development server with production warnings

### File Serving Configuration
- **Base Directory**: Project root directory
- **Static Files**: CSS, JavaScript, and other assets served from `src/web/static/`
- **Data Files**: HTML and JSON files served from `data/` directory
- **Content Files**: Newsletter HTML content served from `data/content/`

## API Endpoints

### **Three-Tier Update System Endpoints**

#### **Tier 1: Configuration Updates**
- **`/api/update_metadata`** (POST) - Trigger pure configuration update (20-200ms)
- **`/api/check_metadata_status`** (GET) - Check if newsletters.md has changed

#### **Tier 2: Structure Updates**
- **`/api/update_structure`** (POST) - Configuration + post metadata + HTML structure (1-5 seconds)

#### **Tier 3: Content Updates**
- **`/api/discover_links`** (POST) - Fast discovery of new posts (10 seconds - 2 minutes)
- **`/api/download_pending_content`** (POST) - Background content download (background process)
- **`/api/pending_downloads_count`** (GET) - Get count of posts waiting for download

### **Legacy Endpoints**

#### **Personalization Data Management**

#### Update Not Interesting Status
- **Endpoint**: `/api/update_not_interesting`
- **Method**: POST
- **Purpose**: Marks a post as not interesting or removes the mark
- **Data Flow**: 
  1. Receives POST request with post ID and boolean status
  2. Updates the corresponding post in `index.json`
  3. Regenerates `index.html` to reflect changes
  4. Returns success/error response

#### Update Read Status
- **Endpoint**: `/api/update_read`
- **Method**: POST
- **Purpose**: Marks a post as read or removes the mark
- **Data Flow**: 
  1. Receives POST request with post ID and boolean status
  2. Updates the corresponding post in `index.json`
  3. Regenerates `index.html` to reflect changes
  4. Returns success/error response

#### Update Like Status
- **Endpoint**: `/api/update_like`
- **Method**: POST
- **Purpose**: Marks a post as liked or removes the like
- **Data Flow**: 
  1. Receives POST request with post ID and boolean status
  2. Updates the corresponding post in `index.json`
  3. Regenerates `index.html` to reflect changes
  4. Returns success/error response

#### Update Hide Status
- **Endpoint**: `/api/update_hide`
- **Method**: POST
- **Purpose**: Marks a post as hidden or removes the hide mark
- **Data Flow**: 
  1. Receives POST request with post ID and boolean status
  2. Updates the corresponding post in `index.json`
  3. Regenerates `index.html` to reflect changes
  4. Returns success/error response

### Data Generation Endpoints

#### Generate Index Files
- **Endpoint**: `/generate`
- **Method**: GET
- **Purpose**: Triggers regeneration of both `index.json` and `index.html`
- **Data Flow**: 
  1. Processes newsletter configuration from `config/newsletters.md`
  2. Scrapes metadata from `data/metadata/` directory
  3. Generates hierarchical category structure
  4. Creates `index.json` with all data and personalization fields
  5. Generates `index.html` from the JSON data

## Data Management

### Data Sources
- **Configuration**: `config/newsletters.md` - Manual newsletter categorization and metadata
- **Metadata**: `data/metadata/` - Scraped post metadata including titles, dates, URLs
- **Content**: `data/content/` - Scraped HTML content for each newsletter post
- **Personalization**: Stored within `index.json` for each post

### Data Structure
- **Newsletter Posts**: Array of post objects with metadata and personalization fields
- **Categories**: Hierarchical structure with main categories and subcategories
- **Personalization Fields**: Boolean flags for user preferences (not_interesting, read, like, hide)
- **Metadata Fields**: Title, URL, newsletter name, publication date, content path

### Data Persistence
- **Primary Storage**: `index.json` file containing all system data
- **Backup Strategy**: Personalization data preserved during regeneration
- **Data Integrity**: HTML always reflects current JSON state
- **Atomic Updates**: Changes are applied atomically to prevent data corruption

## File Generation System

### Index Generator Class
- **Responsibility**: Generates both HTML and JSON output files
- **Input Processing**: Parses markdown configuration and metadata files
- **Category Logic**: Implements hierarchical categorization based on markdown headers
- **HTML Generation**: Creates dynamic HTML with JavaScript for interactivity
- **JSON Generation**: Creates structured data file with all metadata and personalization data

### HTML Generation Process
1. **Template Assembly**: Combines static HTML structure with dynamic content
2. **JavaScript Integration**: Embeds all necessary JavaScript functions and event handlers
3. **CSS Integration**: Includes styling for all UI elements and states
4. **Data Attributes**: Adds data attributes for JavaScript filtering and personalization
5. **Accessibility**: Ensures proper HTML structure and ARIA attributes

### JSON Generation Process
1. **Data Aggregation**: Combines configuration, metadata, and personalization data
2. **Category Processing**: Creates hierarchical category structure from markdown
3. **Field Initialization**: Ensures all posts have required personalization fields
4. **Data Validation**: Validates data integrity and completeness
5. **File Output**: Writes structured JSON to `index.json`

## Error Handling and Logging

### Error Categories
- **API Errors**: Invalid requests, missing data, server errors
- **File System Errors**: Permission issues, disk space, file corruption
- **Data Processing Errors**: Invalid metadata, parsing failures, category errors
- **Generation Errors**: HTML/JSON generation failures

### Error Responses
- **HTTP Status Codes**: Appropriate status codes for different error types
- **Error Messages**: Descriptive error messages for debugging
- **Client Feedback**: User-friendly error messages in the interface
- **Logging**: Server-side logging of all errors and operations

### Recovery Mechanisms
- **Data Validation**: Prevents invalid data from corrupting the system
- **Fallback Values**: Default values for missing or invalid data
- **Error Recovery**: Automatic retry mechanisms for transient failures
- **Data Backup**: Preservation of user data during regeneration

## Performance and Scalability

### Caching Strategy
- **Static File Caching**: Browser caching for CSS, JavaScript, and images
- **HTML Caching**: Limited caching for generated HTML to ensure data freshness
- **JSON Caching**: No caching for JSON data to maintain real-time updates

### Resource Management
- **Memory Usage**: Efficient data structures for large numbers of posts
- **File I/O**: Optimized file reading and writing operations
- **CPU Usage**: Efficient HTML generation and data processing

### Scalability Considerations
- **Post Volume**: System designed to handle hundreds of newsletter posts
- **User Load**: Single-user system with potential for multi-user expansion
- **Data Growth**: Efficient storage and retrieval as data volume increases

## Security Considerations

### Input Validation
- **API Input**: Validation of all incoming API requests
- **Data Sanitization**: Prevention of XSS and injection attacks
- **File Path Security**: Prevention of directory traversal attacks

### Access Control
- **Local Access**: Server designed for local network access
- **Authentication**: No authentication required (single-user system)
- **Authorization**: All users have full access to all functionality

### Data Protection
- **User Privacy**: Personalization data stored locally
- **Data Integrity**: Validation and sanitization of all stored data
- **Backup Security**: Secure handling of backup and recovery operations

## Monitoring and Maintenance

### Health Checks
- **Server Status**: Monitoring of server availability and responsiveness
- **File Generation**: Verification of successful HTML and JSON generation
- **Data Integrity**: Validation of data consistency and completeness

### Maintenance Operations
- **Data Regeneration**: Periodic regeneration of index files
- **Cleanup Operations**: Removal of obsolete or corrupted data
- **Performance Optimization**: Monitoring and optimization of generation processes

### Logging and Debugging
- **Operation Logs**: Recording of all major operations and errors
- **Performance Metrics**: Tracking of generation times and resource usage
- **Debug Information**: Detailed logging for troubleshooting and development
