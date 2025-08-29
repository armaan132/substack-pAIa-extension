# Web Interface Specification

## Overview

The newsletter personalization web interface is a dynamic, responsive web application that allows users to browse, filter, and interact with newsletter posts from various Substack newsletters. The interface provides a clean, organized view of content with personalization features, intelligent categorization, and real-time updates.

## Core Layout Structure

### **Header Section**
- **Search Bar**: Full-width search input field with placeholder text "Search posts by title, newsletter, or content..."
- **Search Mode Visual Feedback**: When search is active, controls are dimmed and search bar is highlighted
- **Pending Downloads Indicator**: Shows count of posts downloading in background (if any)

### **Update Control Panel**
```
[⚡ Update Config] [🔧 Update Structure] [🔍 Discover & Download] [🚀 Deep Discovery]
```

**Button Functions:**
- **⚡ Update Config** (Gray): Fast configuration updates (Tier 1)
- **🔧 Update Structure** (Blue): Structure + metadata sync (Tier 2)  
- **🔍 Discover & Download** (Green): Content discovery + downloads (Tier 3)
- **🚀 Deep Discovery** (Orange): Advanced discovery using both RSS + Substack API for maximum coverage

### **Filter Row**
- **Main Category Radio Buttons**: Dynamically generated from `index.json` in human-curated order
  - **"All"** (default selection) - shows all posts from all categories
  - **"Science"** - shows only posts from the "Science" category
  - **"News and Opinion"** - shows only posts from the "News and Opinion" category
  - **"Tech"** - shows only posts from the "Tech" category
  - Categories respect the order defined in `newsletters.md`
  
- **Visibility Toggle Checkboxes**: Positioned on the same line as category buttons
  - **"Hidden Posts"** checkbox - when checked, shows ALL posts including hidden ones
  - **"Liked Posts"** checkbox - when checked, shows ONLY liked posts (exclusive filter)

- **Filter Row Logic**: All filters work together with simple AND logic - a post must pass ALL active filters to be displayed:
  - **Category Filter**: Post must be in the selected category (or any category if "All" is selected)
  - **Hidden Posts Filter**: If checked, hidden posts are included; if unchecked, hidden posts are excluded
  - **Liked Posts Filter**: If checked, only liked posts are shown; if unchecked, posts are shown regardless of like status
  - **Result**: Posts must satisfy ALL active filter criteria to be visible

### **Subcategory Navigation**
- **Subcategories** are defined in the file `newsletters.md` via `###` headings
- **Dynamic Subcategory Links** appear below main category selection when the category has subcategories
- **Subcategory Buttons**: Gray buttons for each subcategory (e.g., "Economics", "Psychology", "Philosophy")
- **Click Behavior**: Clicking a subcategory filters posts to show only that subcategory's content
- **Visual Feedback**: Active subcategory button changes to blue background with white text
- **Placement Logic**: Only visible if the selected category has subcategories. Not visible if "All" is selected

### **Content Display Area**
- **Post Layout**: Each post displayed as a horizontal line with multiple elements
- **Post Information**: Newsletter name, post title (clickable local link), original link (🔗), date, subcategory label
- **Action Buttons**: Four compact icon buttons per post with hover tooltips
  - **👁️ (Read)** - marks post as read and hides it
  - **👎 (Not Interesting)** - marks post as not interesting and hides it
  - **👍 (Like)** - marks post as liked (does NOT hide it)
  - **🚫 (Hide)** - marks post as hidden and hides it

## User Interaction Patterns

### **Filter Row Usage**
1. **Main Category Selection**: Click radio button to filter by category
2. **Visibility Controls**: Use checkboxes to show hidden posts or only liked posts
3. **Subcategory Navigation**: Click subcategory buttons for granular filtering
4. **View Persistence**: Selected category persists through page refresh
5. **Default Behavior**: "All" category selected by default on page load

### **Search Workflow**
1. **Set Filter Row**: First configure the base set of posts using category selection and visibility toggles
2. **Search Within Results**: Type search terms to narrow down the currently visible posts
3. **Clear Search**: Remove search terms to return to the full filtered view
4. **Filter-Search Independence**: Search only affects what's visible; it doesn't change Filter Row settings

### **Search Functionality**
- **Real-time Search**: Live updates as user types with debounced input to prevent excessive processing
- **Multi-field Search**: Searches across post title, newsletter name, and post content simultaneously
- **Filtered Search**: Search only searches within posts currently visible based on Filter Row settings
  - If "Science" category is selected, search only searches Science posts
  - If "Hidden Posts" is checked, search includes hidden posts in the search scope
  - If "Liked Posts" is checked, search only searches within liked posts
- **Search Mode Visual Feedback**: 
  - Controls are dimmed when search is active
  - Search bar is highlighted to indicate active search state
- **Search Result Display**: 
  - Posts matching search terms remain visible
  - Non-matching posts are hidden
  - Results maintain the same filtering context from Filter Row
- **Search Clearing**: 
  - Search results are cleared when user clears search input
  - Normal Filter Row filtering resumes after search is cleared
- **Search Persistence**: Search terms persist during user interactions until manually cleared

### **Personalization Actions**
1. **Read Posts**: Click 👁️ to mark as read (post disappears from view)
2. **Not Interesting**: Click 👎 to mark as not interesting (post disappears from view)
3. **Like Posts**: Click 👍 to like a post (post remains visible, button changes to green)
4. **Hide Posts**: Click 🚫 to hide a post (post disappears from view)

### **Visibility Controls**
1. **Hidden Posts Toggle**: Checkbox to show ALL posts including hidden ones
2. **Liked Posts Toggle**: Checkbox to show ONLY liked posts
3. **Combined Logic**: If both read and liked, post is hidden by default

## Visual Design Elements

### **Button States**
- **Default State**: Gray background with dark text
- **Active State**: 
  - Read button: Shows ✓ before 👁️
  - Not Interesting button: Red background with 👎 (no tick)
  - Like button: Green background with white 👍
  - Hide button: Shows ✓ before 🚫
- **Hover Effects**: Tooltips appear on hover for all action buttons

### **Status Indicators**
- **Download Status**:
  - **📖** - Post has offline content available
  - **📄** - Post has no offline content
  - **⏳ Downloading...** - Post content is being downloaded
- **Filter Status**: Active filters are visually highlighted
- **Search Status**: Search mode is clearly indicated

### **Layout Principles**
- **Single Line Layout**: All filter controls arranged horizontally on one line
- **Consistent Spacing**: Uniform margins and padding throughout
- **Responsive Design**: Interface adapts to different screen sizes
- **Visual Hierarchy**: Clear distinction between different UI sections

## JavaScript Functionality

### **Dynamic Category Generation**
- **`generateCategoryRadioButtons()`**: Dynamically generates category radio buttons from `index.json`
- **Human-Curated Order**: Categories displayed in order from `newsletters.md` (Science, News and Opinion, Tech)
- **Fallback Handling**: New categories not in predefined list are appended at the end

### **Filter and Search Functions**
- **`filterByMainCategory(category)`**: Filters posts by main category
- **`showSubcategoryLinks(category)`**: Shows subcategory buttons for selected category
- **`searchPosts(query)`**: Searches within currently visible posts
- **`toggleHiddenPosts()`**: Toggles visibility of hidden posts
- **`toggleLikedPosts()`**: Toggles visibility to show only liked posts

### **Update Functions**
- **`triggerConfigUpdate()`**: Triggers Tier 1 (pure configuration) update
- **`triggerStructureUpdate()`**: Triggers Tier 2 (structure + metadata) update
- **`triggerLinkDiscovery()`**: Triggers Tier 3a (fast link discovery)
- **`triggerBackgroundDownloads()`**: Triggers Tier 3b (background content download)

### **Background Processing**
- **`checkForMetadataUpdates()`**: Checks for configuration changes every 5 minutes
- **`updatePendingDownloadsCount()`**: Updates download progress every 30 seconds
- **Automatic Updates**: Metadata updates happen automatically when changes detected

## Responsive Design

### **Layout Adaptations**
- **Desktop**: Full horizontal layout with all controls on single lines
- **Tablet**: Maintains horizontal layout with adjusted spacing
- **Mobile**: Responsive adjustments for smaller screens

### **Touch Interactions**
- **Touch-Friendly Buttons**: Adequate size for mobile touch interaction
- **Swipe Support**: Potential for future gesture-based navigation
- **Mobile-Optimized**: Interface works well on mobile devices

## Accessibility Features

### **Keyboard Navigation**
- **Tab Order**: Logical tab sequence through all interactive elements
- **Keyboard Shortcuts**: Support for common keyboard shortcuts
- **Focus Indicators**: Clear visual focus indicators

### **Screen Reader Support**
- **ARIA Labels**: Proper ARIA labels for all interactive elements
- **Semantic HTML**: Use of appropriate HTML semantic elements
- **Alt Text**: Descriptive text for all non-text content

### **Visual Accessibility**
- **Color Contrast**: Sufficient color contrast for text readability
- **Font Sizes**: Readable font sizes with potential for user adjustment
- **Visual Cues**: Multiple visual indicators for important information

## Performance Optimization

### **Efficient Rendering**
- **Dynamic Generation**: UI elements generated from data rather than hardcoded
- **Lazy Loading**: Content loaded as needed
- **Optimized Updates**: Only necessary DOM elements updated during changes

### **User Experience**
- **Instant Feedback**: Immediate response to user actions
- **Progress Indicators**: Clear status for long-running operations
- **Non-blocking Updates**: UI remains responsive during background operations

## Error Handling

### **User Feedback**
- **Clear Error Messages**: Descriptive error messages for all failure cases
- **Recovery Options**: Suggested actions for resolving errors
- **Status Updates**: Real-time status updates for all operations

### **Graceful Degradation**
- **Partial Failures**: System continues operation even if some operations fail
- **Fallback Mechanisms**: Alternative approaches when primary methods fail
- **Data Preservation**: All user data preserved even during errors

## Future Enhancements

### **Planned Features**
- **Advanced Filtering**: More sophisticated filter combinations
- **Sorting Options**: Multiple sorting criteria for posts
- **Bulk Operations**: Select and act on multiple posts simultaneously
- **Custom Views**: User-defined view preferences

### **UI Improvements**
- **Dark Mode**: Alternative color scheme option
- **Customizable Layout**: User-adjustable interface layout
- **Advanced Search**: Enhanced search with filters and operators
- **Visual Themes**: Multiple visual theme options

