# Update System Specification

## Overview
The newsletter personalization system uses a **4-button update architecture** that provides both structured tiered updates and advanced discovery capabilities.

## Update Button Architecture

### **Core 3-Tier System**
```
[⚡ Update Config] [🔧 Update Structure] [🔍 Discover & Download]
```

**Tier 1: ⚡ Update Config (Gray)**
- **Purpose**: Fast configuration updates only
- **Scope**: Newsletter structure, categories, metadata
- **Speed**: Very fast (seconds)
- **Use Case**: When `newsletters.md` is modified
- **API Endpoint**: `/api/update_metadata`

**Tier 2: 🔧 Update Structure (Blue)**
- **Purpose**: Configuration + post metadata + HTML structure
- **Scope**: Tier 1 + post metadata synchronization + HTML regeneration
- **Speed**: Medium (seconds to minutes)
- **Use Case**: When post metadata needs updating or HTML structure changes
- **API Endpoint**: `/api/update_structure`

**Tier 3: 🔍 Discover & Download (Green)**
- **Purpose**: Full content discovery and download
- **Scope**: Tier 2 + new post discovery + content download
- **Speed**: Slow (minutes to hours)
- **Use Case**: When new posts need to be found and downloaded
- **API Endpoints**: `/api/discover_links` + `/api/download_pending_content`

### **Advanced Discovery: 🚀 Deep Discovery (Orange)**
- **Purpose**: Maximum coverage discovery using both RSS and Substack API
- **Scope**: Enhanced discovery beyond standard RSS feeds
- **Speed**: Medium to slow (minutes)
- **Use Case**: When standard discovery misses recent posts
- **API Endpoint**: `/api/aggressive_discovery`
- **Benefits**: Finds posts that RSS feeds don't show (e.g., older posts pushed out of RSS)

## Update Workflow

### **Automatic Updates**
1. **Server Startup**: Tier 1 update runs automatically
2. **Page Load**: Metadata status check every 5 minutes
3. **Background**: Pending download count updates every 30 seconds

### **Manual Updates**
1. **User clicks button** → Button disabled, loading state shown
2. **API call made** → Progress updates displayed
3. **Operation completes** → Success/error message shown
4. **Page reloads** → New content visible immediately

## Implementation Details

### **Tier 1: Configuration Update**
```python
def run_pure_config_update(self) -> bool:
    """Run pure configuration update (newsletter structure only)."""
    # Load newsletters.md and update structure
    # No post content processing
    # Very fast execution
```

### **Tier 2: Structure Update**
```python
def run_structure_update(self) -> bool:
    """Run structure updates including post metadata and HTML (medium tier)."""
    # First run Tier 1
    # Then update post metadata for category changes
    # Finally regenerate HTML
```

### **Tier 3: Content Discovery & Download**
```python
def triggerContentUpdate():
    """Tier 3: Discover new posts + download content."""
    # Step 1: Discover new links (Tier 3a)
    # Step 2: Download pending content (Tier 3b)
    # Both steps with progress feedback
```

### **Advanced: Deep Discovery**
```python
def run_aggressive_link_discovery(self) -> bool:
    """Run aggressive link discovery using both RSS and substack API."""
    # Method 1: Check RSS feeds (last 15 entries)
    # Method 2: Check Substack API (last 20 posts)
    # Combine results for maximum coverage
```

## Button States and Feedback

### **Loading States**
- **Button disabled** during operation
- **Text changes** to indicate progress (e.g., "⏳ Processing...")
- **Color changes** to show status (gray = loading, green = success, red = error)

### **Status Updates**
- **Real-time progress** shown in status area
- **Success messages** with operation results
- **Error handling** with clear error messages
- **Auto-reload** after successful operations

## Error Handling

### **Network Issues**
- **Timeout handling** with 10-second limits
- **Retry logic** for failed operations
- **Graceful degradation** when services unavailable

### **User Recovery**
- **Buttons re-enable** after errors
- **Clear error messages** explain what went wrong
- **Suggestions** for resolving common issues

## Performance Characteristics

### **Speed Comparison**
- **Tier 1**: ~1-5 seconds (configuration only)
- **Tier 2**: ~5-30 seconds (structure + metadata)
- **Tier 3**: ~1-10 minutes (discovery + download)
- **Deep Discovery**: ~2-15 minutes (enhanced discovery)

### **Resource Usage**
- **Tier 1**: Minimal (file I/O only)
- **Tier 2**: Low (metadata processing)
- **Tier 3**: Medium (network + content processing)
- **Deep Discovery**: Medium-High (dual discovery methods)

## Use Case Scenarios

### **Daily Operations**
- **Morning**: Use 🚀 Deep Discovery to find overnight posts
- **Throughout Day**: Use 🔍 Discover & Download for new content
- **Evening**: Use 🔧 Update Structure to sync metadata

### **Configuration Changes**
- **Add Newsletter**: Use ⚡ Update Config
- **Change Categories**: Use 🔧 Update Structure
- **Major Restructure**: Use 🔧 Update Structure

### **Content Discovery**
- **Standard Discovery**: Use 🔍 Discover & Download
- **Missed Posts**: Use 🚀 Deep Discovery
- **RSS Issues**: Use 🚀 Deep Discovery as fallback

## Future Enhancements

### **Planned Improvements**
- **Scheduled Updates**: Automatic tiered updates at set intervals
- **Smart Discovery**: AI-powered content discovery
- **Batch Operations**: Process multiple newsletters simultaneously
- **Progress Tracking**: Detailed progress bars for long operations

### **Advanced Features**
- **Incremental Updates**: Only process changed content
- **Parallel Processing**: Multiple operations running simultaneously
- **User Preferences**: Customizable update schedules
- **Notification System**: Alerts for completed operations

