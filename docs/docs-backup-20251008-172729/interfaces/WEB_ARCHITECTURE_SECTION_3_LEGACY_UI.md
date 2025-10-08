# Section 3: Legacy UI Interface

**Document:** OmicsOracle Web Interfaces Architecture Guide
**Section:** 3 - Legacy UI Interface
**Date:** June 24, 2025

---

## 🏛️ **LEGACY UI OVERVIEW**

The Legacy UI Interface (`web-ui-legacy/`) represents the original OmicsOracle web interface. While superseded by newer interfaces, it remains available for compatibility, fallback scenarios, and users who prefer the familiar interface.

### **Key Characteristics**
- **Purpose**: Compatibility fallback and legacy support
- **Port**: 8001
- **Technology**: FastAPI + Embedded HTML + Vanilla JavaScript
- **Target Users**: Legacy users, compatibility testing
- **Status**: Maintenance mode

---

## 🏗️ **ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────┐
│                Legacy UI Interface                       │
│                    (Port 8001)                          │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐ │
│  │   FastAPI App   │  │  Embedded HTML  │  │  Vanilla  │ │
│  │                 │  │     Pages       │  │    JS     │ │
│  └─────────────────┘  └─────────────────┘  └───────────┘ │
│            │                    │                        │
│            └────────────────────┼────────────────────────┘
│                                 │
│                     ┌───────────▼───────────┐
│                     │   OmicsOracle Core    │
│                     │      Pipeline         │
│                     └───────────────────────┘
```

### **Core Components**

#### **1. Server Application** (`main.py`)
- FastAPI backend with template rendering
- Static file serving for CSS/JS assets
- Form-based search interface
- Session management for user state

#### **2. Frontend Interface** (`index.html`)
- Server-side rendered HTML templates
- Bootstrap-based responsive design
- jQuery for dynamic interactions
- Traditional form submissions

#### **3. Static Assets**
- Custom CSS for styling
- JavaScript for form validation
- Icons and images
- Bootstrap framework

---

## 🚀 **QUICK START**

### **Start the Legacy Interface**
```bash
cd web-ui-legacy
./start.sh
```

### **Alternative Startup**
```bash
cd web-ui-legacy
./activate_and_run.sh
```

### **Access the Interface**
- **Main Interface**: http://localhost:8001
- **Health Check**: http://localhost:8001/health
- **Search Page**: http://localhost:8001/search

---

## 📋 **FEATURES & FUNCTIONALITY**

### **Core Features**
- ✅ Natural language search
- ✅ Dataset result display
- ✅ Basic filtering options
- ✅ Export functionality
- ✅ Health monitoring
- ⚠️ Limited real-time updates
- ⚠️ Basic error handling

### **User Interface Elements**

#### **Search Interface**
```html
<!-- Main search form -->
<form action="/search" method="POST" class="search-form">
  <div class="form-group">
    <label for="query">Search Query:</label>
    <input type="text" id="query" name="query"
           placeholder="e.g., breast cancer RNA-seq"
           class="form-control" required>
  </div>

  <div class="form-group">
    <label for="max_results">Max Results:</label>
    <select id="max_results" name="max_results" class="form-control">
      <option value="10">10</option>
      <option value="25" selected>25</option>
      <option value="50">50</option>
      <option value="100">100</option>
    </select>
  </div>

  <button type="submit" class="btn btn-primary">Search</button>
</form>
```

#### **Results Display**
```html
<!-- Results table -->
<table class="table table-striped results-table">
  <thead>
    <tr>
      <th>Dataset ID</th>
      <th>Title</th>
      <th>Organism</th>
      <th>Samples</th>
      <th>Platform</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {{#each results}}
    <tr>
      <td><a href="/dataset/{{id}}">{{id}}</a></td>
      <td>{{title}}</td>
      <td>{{organism}}</td>
      <td>{{sample_count}}</td>
      <td>{{platform}}</td>
      <td>
        <button class="btn btn-sm btn-info" onclick="viewDetails('{{id}}')">
          View Details
        </button>
      </td>
    </tr>
    {{/each}}
  </tbody>
</table>
```

---

## 🔧 **CONFIGURATION**

### **Server Configuration** (`main.py`)
```python
# Legacy UI Configuration
LEGACY_UI_CONFIG = {
    "host": "0.0.0.0",
    "port": 8001,
    "debug": False,
    "template_dir": "templates",
    "static_dir": "static",
    "max_results_limit": 1000,
    "session_timeout": 3600,
    "enable_caching": True
}
```

### **Frontend Configuration** (`static/js/config.js`)
```javascript
// Client-side configuration
const LEGACY_CONFIG = {
    apiBaseUrl: 'http://localhost:8001',
    maxQueryLength: 500,
    defaultMaxResults: 25,
    autoSubmitDelay: 1000,
    enableAutoComplete: true,
    resultRefreshInterval: 5000
};
```

---

## 📊 **COMPARISON WITH OTHER INTERFACES**

| Feature | Legacy UI | Stable UI | Modern UI |
|---------|-----------|-----------|-----------|
| **Technology** | FastAPI+HTML | FastAPI+HTML | React+TypeScript |
| **Performance** | Medium | High | High |
| **User Experience** | Basic | Good | Excellent |
| **Mobile Support** | Limited | Good | Excellent |
| **Real-time Updates** | No | Limited | Yes |
| **Search Features** | Basic | Advanced | Advanced |
| **Export Options** | Limited | Good | Excellent |
| **Customization** | Limited | Medium | High |
| **Browser Support** | IE11+ | Modern | Modern |

---

## 🔄 **MAINTENANCE GUIDELINES**

### **When to Use Legacy UI**
- **Compatibility Testing**: Verify functionality across interfaces
- **User Migration**: Gradual transition for existing users
- **Fallback Scenario**: When other interfaces are unavailable
- **Feature Comparison**: Reference implementation for new features

### **Maintenance Tasks**
```bash
# Regular maintenance
cd web-ui-legacy

# Update dependencies
pip install -r requirements.txt --upgrade

# Run basic functionality tests
python -m pytest tests/

# Check for security vulnerabilities
safety check

# Verify interface startup
./start.sh &
curl http://localhost:8001/health
pkill -f "uvicorn.*8001"
```

### **Security Updates**
```python
# Apply security patches
pip install --upgrade fastapi uvicorn jinja2

# Update static dependencies
# Update Bootstrap, jQuery versions in templates

# Review and update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],  # Restrict origins
    allow_credentials=False,  # Disable if not needed
    allow_methods=["GET", "POST"],  # Limit methods
    allow_headers=["*"],
)
```

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

#### **Port Conflicts**
```bash
# Check if port 8001 is in use
lsof -i :8001

# Kill existing process
pkill -f "uvicorn.*8001"

# Start with alternative port
uvicorn main:app --port 8002
```

#### **Template Rendering Errors**
```python
# Check template file paths
import os
template_path = "templates/index.html"
if not os.path.exists(template_path):
    print(f"Template not found: {template_path}")

# Verify Jinja2 configuration
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('index.html')
```

#### **Static File Issues**
```bash
# Verify static file structure
ls -la static/
static/
├── css/
│   └── style.css
├── js/
│   ├── app.js
│   └── config.js
└── images/
    └── logo.png

# Check file permissions
chmod -R 644 static/
```

### **Performance Optimization**

#### **Enable Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search_datasets(query: str, max_results: int):
    # Cached search implementation
    return pipeline.search(query, max_results)
```

#### **Optimize Static Files**
```bash
# Minify CSS and JavaScript
npm install -g clean-css-cli uglify-js

# Minify CSS
cleancss -o static/css/style.min.css static/css/style.css

# Minify JavaScript
uglifyjs static/js/app.js -c -m -o static/js/app.min.js
```

---

## 📈 **MIGRATION PATH**

### **Migrating from Legacy UI**

#### **To Stable UI**
```bash
# Export user preferences from Legacy UI
curl http://localhost:8001/export/preferences > legacy_prefs.json

# Import to Stable UI
curl -X POST http://localhost:8080/import/preferences \
  -H "Content-Type: application/json" \
  -d @legacy_prefs.json
```

#### **To Modern UI**
```javascript
// Modern UI migration helper
const migrateLegacyBookmarks = async (legacyBookmarks) => {
  const modernBookmarks = legacyBookmarks.map(bookmark => ({
    id: bookmark.dataset_id,
    title: bookmark.title,
    query: bookmark.search_query,
    timestamp: new Date(bookmark.created_at),
    tags: bookmark.tags || []
  }));

  await fetch('http://localhost:5173/api/bookmarks/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(modernBookmarks)
  });
};
```

### **Deprecation Timeline**
- **Phase 1** (Current): Maintenance mode, bug fixes only
- **Phase 2** (Q3 2025): Add deprecation warnings
- **Phase 3** (Q4 2025): Redirect to Stable UI by default
- **Phase 4** (Q1 2026): Archive interface, provide read-only access

---

## 📚 **LEGACY CODE EXAMPLES**

### **Basic Search Implementation**
```python
@app.post("/search")
async def legacy_search(
    request: Request,
    query: str = Form(...),
    max_results: int = Form(25)
):
    try:
        # Use OmicsOracle pipeline
        results = pipeline.search(query, max_results)

        # Render template with results
        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "query": query,
                "results": results,
                "total_count": len(results)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e)
            }
        )
```

### **JavaScript Enhancements**
```javascript
// Legacy UI JavaScript enhancements
$(document).ready(function() {
    // Auto-submit search form with delay
    let searchTimeout;
    $('#query').on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            if ($('#query').val().length > 3) {
                $('#search-form').submit();
            }
        }, 1000);
    });

    // Results pagination
    $('.pagination a').on('click', function(e) {
        e.preventDefault();
        const page = $(this).data('page');
        loadPage(page);
    });

    // Export functionality
    $('#export-btn').on('click', function() {
        const format = $('#export-format').val();
        window.location.href = `/export?format=${format}`;
    });
});
```

---

**Next Section: [Modern React Interface](./WEB_ARCHITECTURE_SECTION_4_MODERN_UI.md) →**
