# Newsletter Personalization UI Specification

## Overview
The newsletter personalization interface is a web-based application that allows users to browse, filter, and interact with newsletter posts from various Substack newsletters. The interface provides a clean, organized view of content with personalization features and intelligent categorization.

## Core Layout Structure

### Header Section
- **Search Bar**: Full-width search input field with placeholder text "Search posts by title, newsletter, or content..."
- **Search Mode Visual Feedback**: When search is active, controls are dimmed and search bar is highlighted

### Filter Row
- **Main Category Radio Buttons**: Three mutually exclusive options arranged horizontally
  - "All" (default selection) - shows all posts from all categories
  - "Science" - shows only posts from the "Science" category
  - "News and Opinion" - shows only posts from the "News and Opinion" category
  - Categories are user defined in the file `config/newsletters.md` via `##` headings.
  
- **Visibility Toggle Checkboxes**: Positioned next to main category selection
  - "Hidden Posts" checkbox - when checked, shows ALL posts including hidden ones
  - "Liked Posts" checkbox - when checked, shows ONLY liked posts (exclusive filter)

- **Filter Row Logic**: All filters work together with simple AND logic - a post must pass ALL active filters to be displayed:
  - **Category Filter**: Post must be in the selected category (or any category if "All" is selected)
  - **Hidden Posts Filter**: If checked, hidden posts are included; if unchecked, hidden posts are excluded
  - **Liked Posts Filter**: If checked, only liked posts are shown; if unchecked, posts are shown regardless of like status
  - **Result**: Posts must satisfy ALL active filter criteria to be visible

### Subcategory Navigation
- **Subcategories** are defined in the file `config/newsletters.md` via `###` headings.
- **Dynamic Subcategory Links** appear below main category selection when the category has subcategories.
- **Subcategory Buttons**: Gray buttons for each subcategory (e.g., "Economics", "Psychology", "Philosophy")
- **Click Behavior**: Clicking a subcategory filters posts to show only that subcategory's content
- **Visual Feedback**: Active subcategory button changes to blue background with white text
- **Placement Logic**: Only visible if the selected category has subcategories. Not visible if "All" is selected.

### Content Display Area
- **Post Layout**: Each post displayed as a horizontal line with multiple elements
- **Post Information**: Newsletter name, post title (clickable local link), original link (🔗), date, subcategory label
- **Action Buttons**: Four compact icon buttons per post with hover tooltips
  - 👁️ (Read) - marks post as read and hides it
  - 👎 (Not Interesting) - marks post as not interesting and hides it
  - 👍 (Like) - marks post as liked (does NOT hide it)
  - 🚫 (Hide) - marks post as hidden and hides it

## User Interaction Patterns

### Filter Row Usage
1. **Main Category Selection**: Click radio button to filter by category
2. **Visibility Controls**: Use checkboxes to show hidden posts or only liked posts
3. **Subcategory Navigation**: Click subcategory buttons for granular filtering
4. **View Persistence**: Selected category persists through page refresh
5. **Default Behavior**: "All" category selected by default on page load

### Search Workflow
1. **Set Filter Row**: First configure the base set of posts using category selection and visibility toggles
2. **Search Within Results**: Type search terms to narrow down the currently visible posts
3. **Clear Search**: Remove search terms to return to the full filtered view
4. **Filter-Search Independence**: Search only affects what's visible; it doesn't change Filter Row settings

### Search Functionality
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

### Personalization Actions
1. **Read Posts**: Click 👁️ to mark as read (post disappears from view)
2. **Not Interesting**: Click 👎 to mark as not interesting (post disappears from view)
3. **Like Posts**: Click 👍 to like a post (post remains visible, button changes to green)
4. **Hide Posts**: Click 🚫 to hide a post (post disappears from view)

### Visibility Controls
1. **Hidden Posts Toggle**: Checkbox to show ALL posts including hidden ones
2. **Liked Posts Toggle**: Checkbox to show ONLY liked posts
3. **Combined Logic**: If both read and liked, post is hidden by default

## Visual Design Elements

### Button States
- **Default State**: Gray background with dark text
- **Active State**: 
  - Read button: Shows ✓ before 👁️
  - Not Interesting button: Red background with 👎 (no tick)
  - Like button: Green background with white 👍
  - Hide button: Shows ✓ before 🚫
- **Hover Effects**: Tooltips appear on hover for all action buttons

### Color Scheme
- **Primary Actions**: Blue (#007bff) for active subcategory buttons
- **Success State**: Green background for liked posts
- **Warning State**: Red background for not-interesting button when active
- **Neutral**: Gray (#f8f9fa) for default button states

### Typography and Spacing
- **Post Layout**: Horizontal arrangement with consistent spacing
- **Labels**: Subcategory labels in smaller, muted text
- **Dates**: Formatted as "Aug 23, 2025" style
- **Margins**: Consistent 20px spacing between major sections

## Content Organization

### Post Sorting
- **Default Order**: Posts sorted by date (most recent first)
- **Category Views**: All views maintain chronological sorting
- **Subcategory Filtering**: When filtering by subcategory, posts remain date-sorted within that subcategory

### Information Hierarchy
1. **Newsletter Name**: Primary identifier for content source
2. **Post Title**: Main content identifier (clickable)
3. **Original Link**: External reference (🔗 icon)
4. **Date**: Publication timestamp
5. **Subcategory**: Content classification (when applicable)
6. **Action Buttons**: User interaction controls

### Content Filtering Logic
- **Filter Row Controls**: Main category selection and visibility toggles determine the base set of visible posts
- **Simple AND Logic**: A post must pass ALL active filters to be displayed:
  1. **Category Filter**: Post must match the selected category (or any category if "All" is selected)
  2. **Hidden Posts Filter**: If checked, hidden posts are included; if unchecked, hidden posts are excluded
  3. **Liked Posts Filter**: If checked, only liked posts are shown; if unchecked, posts are shown regardless of like status
- **Hidden Posts**: Posts marked as not interesting, read, hide, or liked (when read+liked)
- **Visible Posts**: Posts that pass all active filter criteria
- **Search Scope**: Search only operates within posts currently visible based on Filter Row settings
- **Category Switching**: Clears subcategory filters and resets to main category view
- **Search Integration**: Search narrows down the currently filtered results without changing the base filter

## Responsive Behavior

### Layout Adaptations
- **Horizontal Scrolling**: Post lines may scroll horizontally on narrow screens
- **Button Spacing**: Action buttons maintain consistent spacing regardless of content length
- **Text Wrapping**: Long titles and newsletter names wrap appropriately

### Interaction Patterns
- **Touch-Friendly**: Button sizes accommodate touch interfaces
- **Hover States**: Tooltips work on both desktop and mobile
- **Click Targets**: All interactive elements have sufficient click area

## State Management

### Persistent Data
- **User Preferences**: All personalization actions (read, like, hide, not interesting) persist through page refresh
- **Category Selection**: Selected main category persists through page refresh
- **Search State**: Search terms and results are not persistent

### Dynamic Updates
- **Real-time Changes**: Personalization actions update immediately in the UI
- **Server Synchronization**: Changes are sent to server and HTML is regenerated
- **State Consistency**: UI always reflects the current state from the server

## Accessibility Features

### Visual Indicators
- **Button States**: Clear visual feedback for all button states
- **Hover Tooltips**: Descriptive text for all action buttons
- **Color Contrast**: Sufficient contrast for all text and button elements

### Keyboard Navigation
- **Tab Order**: Logical tab sequence through all interactive elements
- **Focus Indicators**: Clear focus states for all clickable elements
- **Action Confirmation**: Visual feedback confirms all user actions

## Error Handling

### User Feedback
- **Success Messages**: Confirmation when personalization actions succeed
- **Error Messages**: Clear error messages when actions fail
- **Loading States**: Visual feedback during server communication

### Graceful Degradation
- **Offline Behavior**: Interface remains functional even if server communication fails
- **Fallback States**: Default behaviors when personalization data is unavailable
- **Error Recovery**: Automatic retry mechanisms for failed operations
