# Migration Guide: Old → New Frontend System

**Date:** October 7, 2025
**Applies to:** Users upgrading from pre-Day 24 versions

---

## What Changed?

We consolidated multiple confusing frontends into a single, clear system.

### Old System (Before)

```
Multiple frontends:
  - start.sh → Old web interface (BROKEN)
  - web-api-backend/ → HTML/JS interface (DEPRECATED)
  - futuristic_enhanced/ → Angular interface (EXPERIMENTAL)
  - Streamlit dashboard → Separate, unclear

User confusion: "Which one do I use?"
```

### New System (After)

```
Single primary frontend:
  - Streamlit Dashboard (port 8502) ← PRIMARY
  - FastAPI API (port 8000) ← Backend

One startup command:
  - ./start_omics_oracle.sh → Starts everything
```

---

## Migration Steps

### Step 1: Update Your Repository

```bash
# Pull latest changes
git pull origin phase-4-production-features

# Or if you forked:
git fetch upstream
git merge upstream/phase-4-production-features
```

### Step 2: Stop Old Processes

```bash
# Kill any old processes
pkill -f "start.sh"
pkill -f "omics_oracle"
pkill -f "streamlit"

# Verify nothing is running on ports 8000 or 8502
lsof -Pi :8000 -sTCP:LISTEN
lsof -Pi :8502 -sTCP:LISTEN
```

### Step 3: Use New Startup

```bash
# Old way (DON'T USE):
# ./start.sh  ← DELETED

# New way (USE THIS):
./start_omics_oracle.sh
```

### Step 4: Update Bookmarks

**Old URLs (DON'T USE):**
- ❌ http://localhost:8000/static/semantic_search.html
- ❌ http://localhost:8000/dashboard
- ❌ http://localhost:3000 (Angular frontend)

**New URLs (USE THESE):**
- ✅ **http://localhost:8502** ← Primary Dashboard
- ✅ http://localhost:8000/docs ← API Documentation
- ✅ http://localhost:8000/health ← Health Check
- ✅ http://localhost:8000/debug/dashboard ← Debug Tool

---

## Feature Mapping

### Old Web Interface → Streamlit Dashboard

| Old Feature | New Location | Notes |
|-------------|--------------|-------|
| Search form | Dashboard main page | Enhanced with more options |
| Results display | Dashboard Results panel | Better formatting |
| Basic stats | Dashboard Analytics panel | More comprehensive |
| Export buttons | Dashboard Results panel | JSON + CSV export |

### New Features (Not in Old Interface)

| Feature | Description | Location |
|---------|-------------|----------|
| Search History | Persistent search tracking | Dashboard sidebar |
| User Preferences | Save default settings | Dashboard sidebar |
| 7 Visualizations | Network, trends, heatmap, etc. | Dashboard Visualizations tab |
| Analytics Panel | Detailed metrics & insights | Dashboard Analytics tab |

---

## Environment Variables

### No Changes Required

The same `.env` file works with the new system:

```bash
# Required (same as before)
NCBI_EMAIL=your.email@example.com
NCBI_API_KEY=your_ncbi_api_key
OPENAI_API_KEY=sk-...

# Optional (defaults work fine)
OMICS_DB_URL=sqlite+aiosqlite:///./omics_oracle.db
OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=true
```

---

## Scripts & Commands

### Startup Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `./start.sh` | `./start_omics_oracle.sh` | Unified startup |
| `./start.sh --dev` | `./start_omics_oracle.sh` | Same behavior |
| Manual multi-process | `./start_omics_oracle.sh` | Automatic now |

### Alternative Startup (Advanced)

If you need to run services separately:

```bash
# Terminal 1 - API only
./start_dev_server.sh

# Terminal 2 - Dashboard only
python scripts/run_dashboard.py --port 8502
```

### Logs

| Old Location | New Location |
|--------------|--------------|
| Console output | `/tmp/omics_api.log` |
| Console output | `/tmp/omics_dashboard.log` |

```bash
# View logs
tail -f /tmp/omics_api.log
tail -f /tmp/omics_dashboard.log
```

---

## Troubleshooting

### "start.sh not found"

**Cause:** Old script was deleted.
**Solution:** Use `./start_omics_oracle.sh` instead.

### "Port 8000 already in use"

**Cause:** Old API server still running.
**Solution:**
```bash
lsof -Pi :8000 -sTCP:LISTEN
kill -9 <PID>
./start_omics_oracle.sh
```

### "Can't find old web interface"

**Cause:** Deprecated interfaces were removed.
**Solution:** Use new Streamlit Dashboard at http://localhost:8502

### "Where's my data?"

**Cause:** Database location unchanged.
**Solution:** All data is still in `omics_oracle.db` - no migration needed.

### "Dashboard looks different"

**Cause:** New Streamlit interface replaced old HTML.
**Solution:** This is expected! New interface has more features.

---

## Rollback (Emergency)

If you absolutely need the old system:

```bash
# Checkout before consolidation
git checkout fe8a482

# Note: This is NOT recommended
# Old system has bugs and deprecated code
```

**Better approach:** Report issues and we'll fix them in the new system.

---

## FAQ

### Q: Do I need to reinstall dependencies?

**A:** No, same `requirements.txt` works.

### Q: Will my saved searches/preferences be lost?

**A:** No, they're in the SQLite database which wasn't changed.

### Q: Can I use the old API endpoints?

**A:** Yes! API endpoints are unchanged, only the frontend changed.

### Q: Is the REST API different?

**A:** No, same API at http://localhost:8000/docs

### Q: Do I need to update my automation scripts?

**A:** Only if they referenced:
- `start.sh` → Change to `start_omics_oracle.sh`
- Old web URLs → Change to new dashboard URL

### Q: What if I prefer the old interface?

**A:** The new Streamlit dashboard has all old features PLUS:
- Search history
- User preferences
- 7 visualization types
- Better analytics
- Modern UI

Give it a try! If something is missing, let us know.

---

## Benefits of New System

### For Users

✅ **Simpler:** One command to start everything
✅ **Clearer:** No confusion about which interface to use
✅ **Better:** More features (visualizations, history, preferences)
✅ **Faster:** Modern, optimized interface

### For Developers

✅ **Cleaner:** No deprecated code to maintain
✅ **Documented:** Clear architecture and guides
✅ **Tested:** 102/103 tests passing
✅ **Modern:** Built with current best practices

---

## Support

### Getting Help

1. **Documentation:**
   - Quick Start: `QUICK_START.md`
   - README: `README.md`
   - Analysis: `docs/planning/FRONTEND_CONSOLIDATION_ANALYSIS.md`

2. **Troubleshooting:**
   - Check logs: `tail -f /tmp/omics_*.log`
   - Verify ports: `lsof -Pi :8000 -sTCP:LISTEN`
   - Test health: `curl http://localhost:8000/health`

3. **Issues:**
   - Create GitHub issue
   - Include logs and steps to reproduce

---

## Timeline

- **Oct 7, 2025:** Frontend consolidation complete (commit a88f16e)
- **Going forward:** Use `./start_omics_oracle.sh` for all startups

---

## Summary

**Old Way (Before Oct 7, 2025):**
```bash
# Confusing, multiple options
./start.sh  # or other scripts
# Multiple interfaces, unclear which to use
```

**New Way (After Oct 7, 2025):**
```bash
# Simple, one command
./start_omics_oracle.sh

# One primary interface
http://localhost:8502
```

**Migration:** Just use the new startup command! Everything else works the same.

---

**Questions?** See `QUICK_START.md` or create an issue.
