# Newsletter Personalization Features

This system allows you to mark newsletter posts as "not interesting" or "read/unread" and hide them from your view. All preferences are stored persistently in `index.json` and can be used for future AI training and automatic filtering.

## How to Use

### 1. Start the Personalization Server

```bash
python scripts/run_server.py
```

This will:
- Generate `index.json` with hierarchical categorization and user preferences
- Generate `index.html` from the JSON data (JSON-first architecture)
- Initialize existing posts with `not_interesting: false` and `read: false`
- Start the Flask server on port 8000 for interactive functionality

### 2. Open the Interface

Open `http://localhost:8000/data/index.html` in your web browser to access the personalized interface.

You'll see:
- **Main Category Selection**: Choose between "Science" and "News and Opinion" 
- **Subcategory View**: Posts grouped by subcategories (Economics, Health, Philosophy, etc.)
- **Date View**: Chronological view with category labels
- **Interactive Buttons**: "Not Interesting" and "Read" buttons for each post
- **Instant Hiding**: Posts are immediately hidden when buttons are clicked

### 3. Use the Personalization Features

**Not Interesting Feature:**
- Click the "Not Interesting" button on any post
- The post will be hidden immediately and the button will show a green checkmark  
- Click again to unmark the post and make it visible again

**Read/Unread Feature:**
- Click the "Read" button to mark a post as read
- The post will be hidden immediately and the button will show as "Read"
- Click again to mark as unread and make it visible again

**Show Hidden Posts:**
- Use the "Show Hidden Posts" checkbox to temporarily see all hidden posts
- Hidden posts appear with grayed-out styling

### 4. Data Storage

All user interactions are stored in `data/index.json`:
```json
{
  "url": "https://example.com/post",
  "title": "Example Post",
  "not_interesting": true,
  "read": false,
  "main_category": "Science",
  "subcategory": "Economics"
}
```

## Hierarchical Categorization

The system now supports a three-level hierarchy:

### **## Headlines (Main Categories)**
- **Science**: All scientific newsletters and subcategories
- **News and Opinion**: Current affairs and commentary

### **### Headlines (Subcategories)**
- **Under Science**: Economics, Health, Philosophy, Psychology, etc.
- **Under News and Opinion**: Journalism, Law, etc.

### **Individual Tags**
- Each newsletter has specific tags (economics, globalization, climate change, etc.)

### **User Interface**
- **Main Category Selection**: Radio buttons to choose Science vs. News and Opinion
- **Subcategory View**: Posts grouped by subcategory within the selected main category
- **Date View**: Chronological view with full category path (Science > Economics)

## Technical Details

### Files Modified
- `src/web/index_generator.py` - Core functionality with hierarchical parsing (data generation only)
- `src/web/server.py` - **Main server application** (Flask server with API endpoints)
- `scripts/run_server.py` - Simple runner script
- `requirements.txt` - Added Flask dependency

### New Features
- `not_interesting` and `read` fields for each post
- Interactive buttons in the HTML interface with instant hiding
- Clean single-server architecture (`Server` class)
- Flask server for AJAX updates
- Persistent storage in JSON with preservation across restarts
- Show/hide hidden posts toggle
- JSON-first architecture (`index.json` as single source of truth)

### Future Use Cases
- AI recommendation training (binary classification with both not_interesting and read signals)
- Automatic filtering of uninteresting content
- User preference learning and reading pattern analysis
- Reading progress tracking and analytics
- Content quality assessment

## Architecture

```
User clicks button → JavaScript → Flask API → Update JSON → Persist changes
```

The system maintains a clean separation between:
- **Monitoring data**: Newsletter content and metadata
- **Personalization data**: User preferences and interactions

Both are stored together in `index.json` for simplicity and future AI training.

## Server Architecture

The server (`src/web/server.py`) is now a core part of your application:

```
src/
  web/
    index_generator.py    # Generates HTML/JSON
    server.py             # Main server application (core)
    # Future: api/, models/, services/ modules
```

**Benefits of the new structure:**
- **Scalability**: Easy to add more API endpoints, services, models
- **Organization**: All web functionality in one logical place
- **Professional**: Looks like a serious application architecture
- **Future-ready**: Foundation for AI training, user management, etc.

## Running the Server

- **Main server**: `src/web/server.py` (core application)
- **Runner script**: `scripts/run_server.py` (simple entry point)
- **Port**: 8000 (unified for all functionality)
- **Features**: Static file serving + API endpoints + file generation
