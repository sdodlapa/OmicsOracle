# OmicsOracle - Alternative Frontend Design Options
**Version:** 1.0
**Date:** October 7, 2025
**Status:** DESIGN EXPLORATION
**Purpose:** Evaluate 3 modern frontend approaches for production deployment

---

## 📋 Design Philosophy

### Core Principles
1. **Framework Agnostic** - Backend contract remains constant
2. **Modern UX Standards** - 2025 best practices (micro-interactions, skeleton loading, optimistic UI)
3. **Information Density** - Progressive disclosure, not overwhelming
4. **Performance First** - Sub-second interactions, lazy loading
5. **Mobile Responsive** - Works on tablets, phones, desktop

### Evaluation Criteria
- ✅ **Scalability:** Can handle 20+ features without redesign?
- ✅ **Learnability:** Can new users find features in < 30 seconds?
- ✅ **Performance:** Can render 100+ results smoothly?
- ✅ **Maintenance:** Easy to add new features?
- ✅ **Migration Cost:** How much effort to implement?

---

## 🎨 Option A: Zone-Based Dashboard (Recommended)
**Style:** Modern SaaS application (Notion, Linear, Airtable)
**Complexity:** Medium
**Implementation Time:** 4 weeks

### Layout Structure

```
┌────────────────────────────────────────────────────────────────┐
│ 🧬 OmicsOracle    [Workspace ▼]  [New Search]  [@user ▼]      │ ← Persistent Header
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ 🔍 [CRISPR gene editing cancer therapy__________] [⚡]   │  │ ← Search Zone
│ │ 📅 2020-2024 | 🗂️ PubMed, Scholar | 🎯 Quality ≥80%      │  │    (Always visible)
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌─ RESULTS ────────────────────────────────────────────────┐  │
│ │ 47 results • 2.3s • Sort: Relevance ▼ • [Export ▼]      │  │ ← Results Summary
│ ├──────────────────────────────────────────────────────────┤  │
│ │                                                          │  │
│ │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │  │
│ │ ┃ 1. Novel CRISPR delivery mechanisms... 95% ⭐⭐⭐   ┃  │  │ ← ResultCard
│ │ ┃ Smith J, et al. • 2023 • 142 cites • Open Access↗ ┃  │  │    (Expandable)
│ │ ┃ [Abstract ▼] [🤖 AI] [📊 Citations] [🧬 Bio] [💬] ┃  │  │
│ │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │  │
│ │                                                          │  │
│ │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │  │
│ │ ┃ 2. CAR-T therapy using prime editing... 87% ⭐⭐    ┃  │  │
│ │ ┃ Doe A, et al. • 2022 • 67 cites • VPN Required🔐  ┃  │  │
│ │ ┃ [Abstract ▼] [🤖 AI] [📊 Citations] [🧬 Bio] [💬] ┃  │  │
│ │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │  │
│ │                                                          │  │
│ │ ... 45 more results ...                                 │  │
│ │ [1] [2] [3] [4] [5] ... [10] →                          │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌─ INSIGHTS ▲ ─────────────────────────────────────────────┐  │ ← Analysis Drawer
│ │ [🤖 LLM] [📊 Viz] [📈 Analytics] [🌐 Network] [⚖️ Compare]│  │    (Collapsible)
│ ├──────────────────────────────────────────────────────────┤  │
│ │ 🤖 AI Analysis:                                          │  │
│ │ • Peak research: 2023 (18 papers on CAR-T)              │  │
│ │ • Emerging: Prime editing, Base editing                 │  │
│ │ • Recommended: Start with Smith 2023 for delivery...    │  │
│ └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Key Features

**1. Card-Based Results**
- Each result is a self-contained card
- Expandable panels (accordion style)
- Inline actions (no modal dialogs)
- Skeleton loading for perceived performance

**2. Persistent Search Zone**
- Always visible (no scrolling to search again)
- Inline filter chips (removable)
- Query suggestions as you type
- Search history dropdown

**3. Analysis Drawer**
- Slides up from bottom (or in from side)
- Doesn't compete with results for space
- Can be minimized/maximized
- Tabs for different analysis types

**4. Smart Pagination**
- Virtual scrolling for performance
- "Load more" vs traditional pages
- Infinite scroll option

### Interaction Patterns

```
User Flow: Search → Review Results → Deep Dive → Analyze

1. SEARCH
   Type query → Auto-suggest → Hit Enter
   ↓
2. RESULTS LOAD
   Show skeleton cards → Populate real data → Enable interactions
   ↓
3. EXPAND CARD
   Click "AI Analysis" → Card expands → Show LLM insights
   ↓
4. OPEN DRAWER
   Click "Show Insights" → Drawer slides up → View aggregated analysis
   ↓
5. EXPORT
   Select cards → Click "Export" → Choose format → Download
```

### Visual Design

**Color Scheme (Light Mode):**
```css
--primary: #2563eb;        /* Blue - actions, links */
--success: #10b981;        /* Green - high quality, open access */
--warning: #f59e0b;        /* Amber - medium quality */
--danger: #ef4444;         /* Red - errors, low quality */
--bg-primary: #ffffff;     /* White - main background */
--bg-secondary: #f9fafb;   /* Light gray - cards */
--bg-tertiary: #f3f4f6;    /* Medium gray - hover states */
--text-primary: #111827;   /* Dark gray - main text */
--text-secondary: #6b7280; /* Medium gray - secondary text */
--border: #e5e7eb;         /* Light gray - borders */
```

**Typography:**
```css
--font-primary: 'Inter', -apple-system, sans-serif;
--font-mono: 'Fira Code', 'Monaco', monospace;

--text-xs: 0.75rem;   /* 12px - captions */
--text-sm: 0.875rem;  /* 14px - labels */
--text-base: 1rem;    /* 16px - body */
--text-lg: 1.125rem;  /* 18px - card titles */
--text-xl: 1.25rem;   /* 20px - section headers */
--text-2xl: 1.5rem;   /* 24px - page titles */
```

**Spacing (8px grid):**
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

### Pros & Cons

**✅ Pros:**
- Modern, familiar UX (Notion-like)
- Highly scalable (easy to add features)
- Good information density
- Works on current Streamlit stack
- Progressive disclosure reduces cognitive load

**❌ Cons:**
- Requires significant refactoring (4 weeks)
- Streamlit has CSS limitations
- Drawer animations might be janky
- Virtual scrolling hard in Streamlit

**🎯 Best For:**
- Users who want depth (researchers)
- Complex analysis workflows
- Power users with many filters

---

## 🎨 Option B: Command-K Interface (Modern)
**Style:** Developer tools (GitHub, Vercel, Raycast)
**Complexity:** High
**Implementation Time:** 5-6 weeks

### Layout Structure

```
┌────────────────────────────────────────────────────────────────┐
│ 🧬 OmicsOracle    Press ⌘K to search    [@user ▼] [Settings]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│        🎯 Recent Searches                 📚 Saved Filters    │
│        • CRISPR cancer therapy            • High Impact 2023  │
│        • CAR-T immunotherapy              • Open Access Only  │
│                                                                │
│        🔥 Trending Topics                 💡 Suggested       │
│        • mRNA vaccines                    • Your colleagues   │
│        • Gene editing                       are searching...  │
│                                                                │
│   [Press ⌘K to start searching] or [Browse collections →]    │
│                                                                │
└────────────────────────────────────────────────────────────────┘

When user presses ⌘K:

┌─────────────────────────────────────────────────┐
│ 🔍 [CRISPR gene editing_____________________]  │ ← Command Palette
│                                                 │    (Overlay)
│ 📋 Quick Actions                                │
│   ⚡ Search PubMed                             │
│   ⚡ Search All Databases                      │
│   📊 Open Analytics                            │
│   🧬 Extract Biomarkers                        │
│                                                 │
│ 📝 Recent Queries                               │
│   CRISPR cancer therapy • 47 results           │
│   CAR-T immunotherapy • 23 results             │
│                                                 │
│ 🎯 Filters                                      │
│   📅 Last 5 years                              │
│   ⭐ High quality only                         │
│   🔓 Open access                               │
└─────────────────────────────────────────────────┘

After search results:

┌────────────────────────────────────────────────────────────────┐
│ ← Back  [⌘K]    CRISPR gene editing    47 results • 2.3s      │
├────────────────────────────────────────────────────────────────┤
│ LEFT PANEL (30%)           │ RIGHT PANEL (70%)                 │
├────────────────────────────┼───────────────────────────────────┤
│ 🎯 FILTERS                 │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│                            │ ┃ 1. Novel CRISPR delivery   ┃ │
│ 📅 Year Range              │ ┃    95% ⭐⭐⭐               ┃ │
│ [====●=====] 2020-2024     │ ┃    Smith J, 2023 • 142🔗   ┃ │
│                            │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│ 🗂️ Databases               │                                 │
│ ☑ PubMed                   │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ☑ Google Scholar           │ ┃ 2. CAR-T therapy using...  ┃ │
│ ☐ Semantic Scholar         │ ┃    87% ⭐⭐                 ┃ │
│                            │ ┃    Doe A, 2022 • 67🔗      ┃ │
│ ⭐ Quality                  │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│ [======●===] 80%+          │                                 │
│                            │ ... more results ...            │
│ 🤖 AI INSIGHTS             │                                 │
│ • Peak: 2023 (18 papers)  │                                 │
│ • Emerging: Prime editing │                                 │
│ [View full analysis →]     │                                 │
│                            │                                 │
│ 📊 QUICK STATS             │                                 │
│ Papers: 47                 │                                 │
│ Avg Citations: 73          │                                 │
│ Open Access: 62%           │                                 │
│                            │                                 │
└────────────────────────────┴───────────────────────────────────┘
```

### Key Features

**1. Command Palette (⌘K)**
- Global search (like VS Code, GitHub)
- Quick actions (search, analyze, export)
- Keyboard-first navigation
- Fuzzy search history

**2. Sidebar Filters**
- Always visible
- Real-time updates
- Instant feedback
- AI insights embedded

**3. Master-Detail View**
- Click card → Detail panel slides in from right
- Full paper view without losing context
- Side-by-side comparison mode

**4. Keyboard Navigation**
- ⌘K: Search
- ⌘F: Filter
- ⌘E: Export
- ↑↓: Navigate results
- Enter: Open detail
- Esc: Close

### Interaction Patterns

```
User Flow: ⌘K → Type → Filter → Detail View

1. COMMAND PALETTE
   Press ⌘K → Type query → See suggestions → Select action
   ↓
2. FILTER IN REAL-TIME
   Adjust sliders → Results update instantly → No "search" button
   ↓
3. DETAIL VIEW
   Click result → Side panel slides in → Full paper + analysis
   ↓
4. COMPARISON MODE
   Select 2-3 papers → Click "Compare" → Side-by-side view
   ↓
5. QUICK EXPORT
   Press ⌘E → Select format → Download instantly
```

### Visual Design

**Layout System:**
- Left sidebar: 25-30% width (filters, insights)
- Main area: 70-75% width (results, detail view)
- Command palette: Full-width overlay
- Detail panel: Slides in from right (50% width)

**Animations:**
```css
/* Smooth transitions */
.card-enter { transform: translateY(20px); opacity: 0; }
.card-enter-active { transition: all 0.3s ease-out; }

/* Command palette */
.palette-overlay { backdrop-filter: blur(8px); }
.palette-enter { transform: scale(0.95); opacity: 0; }
.palette-enter-active { transition: all 0.2s ease-out; }

/* Detail panel slide */
.detail-enter { transform: translateX(100%); }
.detail-enter-active { transition: transform 0.3s ease-out; }
```

### Pros & Cons

**✅ Pros:**
- Ultra-modern UX (2025 standards)
- Keyboard-first (fast for power users)
- Permanent context (filters always visible)
- Great for comparison workflows
- Feels like native app

**❌ Cons:**
- **Hard to implement in Streamlit** (needs React/Vue)
- Steep learning curve for non-technical users
- Requires lots of JavaScript
- Complex state management
- 5-6 weeks development time

**🎯 Best For:**
- Power users, developers
- Users who love keyboard shortcuts
- Comparison-heavy workflows
- Users familiar with modern dev tools

**⚠️ Recommendation:** Only if migrating from Streamlit to React/Vue

---

## 🎨 Option C: Card-Grid Gallery (Visual)
**Style:** Pinterest, Dribbble, Research Rabbit
**Complexity:** Low-Medium
**Implementation Time:** 2-3 weeks

### Layout Structure

```
┌────────────────────────────────────────────────────────────────┐
│ 🧬 OmicsOracle           [🔍 Search_______]  [@user ▼]         │
├────────────────────────────────────────────────────────────────┤
│ [All] [PubMed] [Scholar] | 📅 2020-2024 | ⭐ Quality ▼ | [⚙️] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  47 results for "CRISPR gene editing"  [Grid ⊞] [List ☰]     │
│                                                                │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│ │  ⭐⭐⭐     │ │  ⭐⭐⭐     │ │  ⭐⭐       │ │  ⭐⭐⭐     │      │
│ │  95%      │ │  93%      │ │  87%      │ │  91%      │      │
│ │           │ │           │ │           │ │           │      │
│ │ Novel     │ │ CRISPR    │ │ CAR-T     │ │ Prime     │      │
│ │ CRISPR    │ │ base      │ │ therapy   │ │ editing   │      │
│ │ delivery  │ │ editing   │ │ using...  │ │ for...    │      │
│ │ mechanisms│ │ for...    │ │           │ │           │      │
│ │           │ │           │ │           │ │           │      │
│ │ Smith J   │ │ Lee K     │ │ Doe A     │ │ Zhang X   │      │
│ │ 2023      │ │ 2023      │ │ 2022      │ │ 2024      │      │
│ │ 142 cites │ │ 98 cites  │ │ 67 cites  │ │ 12 cites  │      │
│ │           │ │           │ │           │ │           │      │
│ │ [🤖][📊]  │ │ [🤖][📊]  │ │ [🤖][📊]  │ │ [🤖][📊]  │      │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
│                                                                │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│ │  ⭐⭐       │ │  ⭐⭐⭐     │ │  ⭐⭐       │ │  ⭐⭐⭐     │      │
│ │  85%      │ │  94%      │ │  82%      │ │  96%      │      │
│ │ ...       │ │ ...       │ │ ...       │ │ ...       │      │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
│                                                                │
│                  [Load more results ↓]                         │
│                                                                │
└────────────────────────────────────────────────────────────────┘

When user clicks a card:

┌────────────────────────────────────────────────────────────────┐
│ ← Back to results               [Bookmark] [Export] [Share]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │                                                          │  │
│ │  Novel CRISPR delivery mechanisms for cancer therapy    │  │
│ │  ⭐⭐⭐ 95% Quality Score                                 │  │
│ │                                                          │  │
│ │  Smith J, Doe A, Lee K, et al.                          │  │
│ │  Nature Biotechnology • 2023 • 142 citations            │  │
│ │  🔓 Open Access                                          │  │
│ │                                                          │  │
│ │  ─────────────────────────────────────────────────────  │  │
│ │                                                          │  │
│ │  📄 Abstract                                             │  │
│ │  Recent advances in CRISPR-Cas9 technology have...      │  │
│ │                                                          │  │
│ │  🤖 AI Analysis                                          │  │
│ │  Key Insights:                                           │  │
│ │  • Novel lipid nanoparticle delivery system             │  │
│ │  • 87% delivery efficiency in mouse models              │  │
│ │  • Clinical trial phase I completed                      │  │
│ │                                                          │  │
│ │  Recommendations:                                        │  │
│ │  ✓ Highly relevant for CAR-T therapy research           │  │
│ │  ✓ Cites 3 papers from your previous searches           │  │
│ │                                                          │  │
│ │  📊 Citation Analysis                                    │  │
│ │  [Chart: 142 citations over time]                       │  │
│ │  Cited by 23 reviews, 8 clinical trials                 │  │
│ │                                                          │  │
│ │  🧬 Biomarkers Mentioned                                │  │
│ │  • PD-L1 (87% confidence)                               │  │
│ │  • CAR-T cells (94% confidence)                          │  │
│ │  • CRISPR-Cas9 (100% confidence)                         │  │
│ │                                                          │  │
│ │  💬 Ask a Question                                       │  │
│ │  [What delivery mechanisms are used?___________] [Ask]   │  │
│ │                                                          │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Similar Papers:                                               │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                             │
│  │ ... │ │ ... │ │ ... │ │ ... │                             │
│  └─────┘ └─────┘ └─────┘ └─────┘                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Key Features

**1. Visual Cards**
- Large preview cards (Pinterest-style)
- Quality badge prominently displayed
- Hover effects (shadow, lift)
- Quick action icons

**2. Grid Layout**
- Responsive columns (2-4 cols based on screen width)
- Masonry layout (cards can be different heights)
- Infinite scroll
- Toggle grid/list view

**3. Full-Screen Detail**
- Click card → Full-screen overlay
- All analysis on one page (no tabs)
- Similar papers at bottom
- Swipe to next/previous paper

**4. Visual Grouping**
- Cluster similar papers
- Show network connections
- Timeline view option
- Topic clouds

### Interaction Patterns

```
User Flow: Browse → Preview → Deep Dive

1. BROWSE GALLERY
   Scroll through cards → Hover for preview → See quality scores
   ↓
2. QUICK FILTER
   Click filter chip → Cards filter instantly → No page reload
   ↓
3. PREVIEW ON HOVER
   Hover card → Show abstract snippet → Quick actions appear
   ↓
4. FULL DETAIL
   Click card → Full-screen view → All analysis visible
   ↓
5. SWIPE THROUGH
   Swipe right → Next paper → Swipe left → Previous paper
```

### Visual Design

**Card Design:**
```
┌─────────────────────┐
│ ⭐⭐⭐ 95%           │ ← Quality badge (top right)
│                     │
│ [Visual indicator]  │ ← Color bar (quality gradient)
│                     │
│ Title of the paper  │ ← Large, bold title
│ that wraps to 2-3   │
│ lines maximum       │
│                     │
│ Author Name         │ ← Secondary text
│ 2023 • 142 cites   │
│                     │
│ [🤖] [📊] [🧬]      │ ← Action icons
└─────────────────────┘
```

**Color-Coded Quality:**
- High (90%+): Green border, green badge
- Medium (70-89%): Yellow border, yellow badge
- Low (<70%): Red border, red badge

**Hover Effects:**
```css
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
  cursor: pointer;
}

.card:hover .actions {
  opacity: 1;
  transform: translateY(0);
}
```

### Pros & Cons

**✅ Pros:**
- **Fastest to implement** (2-3 weeks)
- Beautiful, engaging UX
- Great for visual learners
- Easy to scan many results
- Works well on tablets
- Can implement in Streamlit

**❌ Cons:**
- Less information density (more scrolling)
- Harder to compare papers side-by-side
- Grid layout can be inefficient for text-heavy content
- Full-screen detail might feel jarring

**🎯 Best For:**
- Visual learners
- Browsing/exploration workflows
- Users who prioritize aesthetics
- Tablet users
- Quick quality assessment

---

## 📊 Comparison Matrix

| Feature | Option A: Zones | Option B: Command-K | Option C: Gallery |
|---------|-----------------|---------------------|-------------------|
| **Implementation Time** | 4 weeks | 5-6 weeks | 2-3 weeks |
| **Streamlit Compatible** | ✅ Yes (with effort) | ❌ No (needs React) | ✅ Yes |
| **Information Density** | High | Very High | Medium |
| **Learning Curve** | Low | Medium | Very Low |
| **Keyboard Navigation** | Basic | ✅ Excellent | Limited |
| **Mobile Friendly** | Good | Poor | ✅ Excellent |
| **Scalability** | ✅ Excellent | ✅ Excellent | Good |
| **Visual Appeal** | Professional | Modern/Technical | ✅ Beautiful |
| **Comparison Workflow** | Good | ✅ Excellent | Poor |
| **Quick Browsing** | Good | Good | ✅ Excellent |
| **Power User Features** | Good | ✅ Excellent | Limited |

---

## 🎯 Recommendations

### For Current Phase (Streamlit)

**Primary:** **Option A - Zone-Based Dashboard**
- Best balance of functionality and implementation time
- Works with current Streamlit stack
- Highly scalable for future features
- Professional, familiar UX

**Backup:** **Option C - Card-Grid Gallery**
- Fastest to implement (2-3 weeks)
- Beautiful, engaging UX
- Good for MVP/demo purposes
- Can transition to Option A later

### For Future (Framework Migration)

**Primary:** **Option B - Command-K Interface**
- Best for React/Vue/Svelte migration
- Most modern UX (2025 standards)
- Power user friendly
- Requires significant dev effort

---

## 🔄 Hybrid Approach (Best of All Worlds)

### Option D: Adaptive Interface

```
Default View: Card Gallery (Option C)
├─ Beautiful, engaging, easy to learn
├─ Great first impression
└─ Works for casual users

Power User Mode: Zone-Based (Option A)
├─ Enable via settings or ⌘K
├─ More information density
├─ Advanced filters, comparison
└─ Keyboard shortcuts

Future Enhancement: Command Palette (Option B)
├─ Add ⌘K to any view
├─ Quick actions overlay
└─ Doesn't require full redesign
```

**Implementation:**
1. **Week 1-3:** Build Card Gallery (Option C) - Fast win
2. **Week 4-7:** Add Zone-Based view as "Power Mode" (Option A)
3. **Week 8+:** Add Command Palette overlay (Option B feature)

**User Controls:**
```
Settings → Interface Mode
○ Gallery View (Default) - Visual, easy browsing
○ Dashboard View - More data, power features
☑ Enable Command Palette (⌘K)
```

---

## 🎨 Design System Tokens (Framework Agnostic)

### Colors
```json
{
  "primary": {
    "50": "#eff6ff",
    "500": "#3b82f6",
    "600": "#2563eb",
    "700": "#1d4ed8"
  },
  "success": {
    "50": "#f0fdf4",
    "500": "#22c55e",
    "600": "#16a34a"
  },
  "warning": {
    "500": "#f59e0b",
    "600": "#d97706"
  },
  "danger": {
    "500": "#ef4444",
    "600": "#dc2626"
  },
  "gray": {
    "50": "#f9fafb",
    "100": "#f3f4f6",
    "200": "#e5e7eb",
    "300": "#d1d5db",
    "400": "#9ca3af",
    "500": "#6b7280",
    "600": "#4b5563",
    "700": "#374151",
    "800": "#1f2937",
    "900": "#111827"
  }
}
```

### Typography
```json
{
  "fontFamily": {
    "sans": ["Inter", "system-ui", "sans-serif"],
    "mono": ["Fira Code", "Monaco", "monospace"]
  },
  "fontSize": {
    "xs": "0.75rem",
    "sm": "0.875rem",
    "base": "1rem",
    "lg": "1.125rem",
    "xl": "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem"
  },
  "fontWeight": {
    "normal": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700
  }
}
```

### Spacing
```json
{
  "spacing": {
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "6": "1.5rem",
    "8": "2rem",
    "12": "3rem",
    "16": "4rem"
  }
}
```

### Shadows
```json
{
  "shadow": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "base": "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
    "md": "0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)",
    "lg": "0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)",
    "xl": "0 20px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.04)"
  }
}
```

### Border Radius
```json
{
  "borderRadius": {
    "none": "0",
    "sm": "0.125rem",
    "base": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem",
    "full": "9999px"
  }
}
```

---

## 📱 Responsive Breakpoints

```json
{
  "breakpoints": {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px"
  }
}
```

**Responsive Behavior:**

| Screen Size | Layout Adjustments |
|-------------|-------------------|
| **Mobile (<640px)** | Single column, stacked cards, drawer full-screen |
| **Tablet (640-1024px)** | 2 columns, side panel overlay, compact filters |
| **Desktop (1024-1280px)** | 3 columns, sidebar visible, full features |
| **Large (>1280px)** | 4 columns, multi-panel view, enhanced visualizations |

---

## 🚀 Next Steps

1. **Choose Primary Design:**
   - Option A (Recommended) - Zone-based, 4 weeks
   - Option C (Fast) - Gallery, 2-3 weeks
   - Option D (Hybrid) - Best of all, 8 weeks

2. **Create Detailed Mockups:**
   - I can generate Mermaid diagrams
   - Or specify design tool (Figma, Sketch, etc.)

3. **Build Component Library:**
   - Start with design tokens
   - Create reusable components
   - Document in Storybook

4. **Implement Incrementally:**
   - Week 1: Design system
   - Week 2: Layout structure
   - Week 3: Core components
   - Week 4: Integration & polish

**Ready to proceed with detailed implementation plan for chosen option!**
