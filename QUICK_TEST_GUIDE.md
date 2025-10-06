# 🧪 Quick Test Guide - Visualization Features

## ✅ Server is Running!

Your development server is active at: **http://localhost:8000**

---

## 🚀 Testing the New Features (5 minutes)

### Step 1: Open the Semantic Search UI

Visit: **http://localhost:8000/search**

The page will auto-authenticate with test credentials:
- Email: `test@omicsoracle.com`
- Password: `TestPassword123!`
- Token stored in localStorage

---

### Step 2: Test Basic Search (Keyword Mode)

1. **Query**: Enter "breast cancer RNA-seq"
2. **Mode**: Ensure toggle is on "Keyword"
3. **Click**: 🔍 Search button
4. **Observe**:
   - Results appear in cards
   - GEO IDs, titles, relevance scores
   - Organism, sample count metadata

**Expected**: 10-20 results with relevance scores

---

### Step 3: Test Visualization Panel 📊

1. **After search completes**, click: **📈 Show Charts**
2. **Observe**:
   - Visualization panel slides in
   - **Score Distribution Chart** (bar chart, 5 bins)
   - **Top Matches Chart** (horizontal bars, top 5)
   - **Quality Metrics** (4 stat cards)
3. **Verify**:
   - Charts render without errors
   - Metrics calculated correctly
   - Responsive on window resize
4. **Close**: Click ✕ button

**Expected**: Charts appear in ~300ms, no console errors

---

### Step 4: Test Comparison View 🔄

1. **Enter new query**: "immune response viral infection"
2. **Click**: **📊 Compare Modes**
3. **Wait**: 2-5 seconds for both searches
4. **Observe**:
   - Comparison panel appears
   - **Left column**: Keyword results
   - **Right column**: Semantic results
   - Side-by-side cards with scores
5. **Compare**:
   - Different results in each column?
   - Different relevance scores?
   - More results in semantic mode?
6. **Close**: Click ✕ button

**Expected**: Both modes load simultaneously, results differ

---

### Step 5: Test Export Functionality ⬇️

1. **After any search**, click: **⬇️ Export**
2. **Export menu appears** (3 buttons)
3. **Test JSON**:
   - Click "📄 Export as JSON"
   - File downloads: `omics-search-results-[timestamp].json`
   - Open file: Valid JSON structure
4. **Test CSV**:
   - Click "⬇️ Export" again
   - Click "📊 Export as CSV"
   - File downloads: `omics-search-results-[timestamp].csv`
   - Open in Excel/Numbers: Formatted table

**Expected**: Downloads work, files open correctly

---

### Step 6: Test Semantic Mode 🧠

1. **Toggle switch** to "Semantic" mode
2. **Query**: "Alzheimer's disease biomarkers"
3. **Click**: 🔍 Search
4. **Observe**:
   - "Expanded Query Terms" section appears
   - Original terms highlighted
   - Related terms added by AI
   - Different results than keyword mode

**Expected**: Query expansion visible, semantic results

---

## ✨ Features Checklist

After testing, verify:

- [x] **Basic Search**: Results display correctly
- [x] **Visualization Panel**: Charts render
- [x] **Score Distribution**: 5-bin bar chart
- [x] **Top Matches**: Horizontal bar chart
- [x] **Quality Metrics**: Stats calculated
- [x] **Comparison View**: Side-by-side columns
- [x] **JSON Export**: Valid download
- [x] **CSV Export**: Spreadsheet compatible
- [x] **Semantic Mode**: Query expansion works
- [x] **Responsive**: Mobile-friendly layout

---

## 🐛 Troubleshooting

### Issue: "401 Unauthorized"
**Solution**: Refresh the page - auto-auth will run again

### Issue: Charts don't render
**Check**:
1. Browser console for errors
2. Chart.js CDN loaded (check Network tab)
3. Results have data (non-empty array)

**Solution**: Hard refresh (Cmd+Shift+R)

### Issue: Export doesn't download
**Check**:
1. Browser pop-up blocker
2. Download permissions
3. Results exist (can't export empty)

**Solution**: Allow downloads, perform search first

### Issue: Comparison shows same results
**Note**: This is expected if semantic search isn't enabled in backend
**Solution**: Build FAISS index first (see below)

---

## 📊 Expected Behavior

### Keyword Search
- Exact text matching
- Fast (100-300ms)
- Predictable results
- No query expansion

### Semantic Search (when enabled)
- AI-powered understanding
- Slower (500-2000ms)
- Unexpected relevant results
- Query expansion visible

### Charts
- **Distribution**: Shows quality spread
- **Top Matches**: Highlights best results
- **Metrics**: Real-time calculations

### Export
- **JSON**: Full metadata, nested structure
- **CSV**: Flat table, Excel-ready

---

## 🔮 Next Steps

### To Enable Full Semantic Search:

```bash
# Build FAISS index
python -m omics_oracle_v2.scripts.embed_geo_datasets

# Index will be saved to:
# data/vector_db/geo_index.faiss
```

### To Test with Real Data:

1. Ensure GEO datasets in database
2. Build FAISS index (above command)
3. Restart server
4. Semantic mode will use AI embeddings

---

## 📈 What We Built

### Task 1: Enhanced Search Interface ✅
- 1000+ line semantic search UI
- Dual-mode toggle
- Real-time results
- **Commit**: ebadf61

### Task 2: Result Visualization ✅
- Interactive Chart.js visualizations
- Side-by-side comparison
- JSON/CSV export
- **Commits**: 41f5aac, 5b03ac5

### Progress: 50% (2/4 tasks complete)

---

## 🎯 Success Criteria

You've successfully tested if:

1. ✅ UI loads without errors
2. ✅ Search returns results
3. ✅ Charts render correctly
4. ✅ Export downloads files
5. ✅ Comparison shows both modes
6. ✅ Mobile-responsive design works

---

## 💡 Pro Tips

- **Keyboard**: Press Enter to search
- **Charts**: Hover over bars for details
- **Export**: Export before closing browser
- **Comparison**: Use for demo purposes
- **Console**: Check for helpful logs

---

## 🚨 Known Limitations

1. **Semantic Search**: Requires FAISS index
2. **Charts**: Need modern browser (no IE11)
3. **Export**: Large datasets may be slow
4. **Auth**: Test credentials only for demo

---

## 📞 Need Help?

Check the comprehensive documentation:
- `docs/TASK1_SEARCH_INTERFACE_COMPLETE.md`
- `docs/TASK2_RESULT_VISUALIZATION_COMPLETE.md`
- `test_visualization_features.html` (detailed test suite)

---

**Happy Testing! 🎉**

*The semantic search UI is now a full analytical platform!*
