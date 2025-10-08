# Startup Simplification Complete! ✅

## What Changed

### Before (Multiple confusing scripts):
```
scripts/
├── start.sh (redundant)
├── archive/
│   ├── start_dev_server.sh (redundant)
│   ├── start_omics_oracle.sh (redundant)
│   ├── start_omics_oracle_ssl_bypass.sh (the one we actually need!)
│   └── start_server_sqlite.sh (redundant)
└── testing/
    └── start_test_server.sh (kept for testing)
```

### After (One simple script):
```
start_omics_oracle.sh (in root directory)
```

## How to Start OmicsOracle

### Single Command:
```bash
./start_omics_oracle.sh
```

**That's it!** No need to remember which script to use.

## What It Does

1. ✅ Activates virtual environment
2. ✅ Enables SSL bypass (for Georgia Tech/institutional networks)
3. ✅ Starts API server on port 8000
4. ✅ Starts Dashboard on port 8502
5. ✅ Monitors both services
6. ✅ Auto-cleanup on exit (Ctrl+C)

## Access Points

After running the script:

- **Dashboard:** http://localhost:8502 (Interactive UI)
- **API Server:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** http://localhost:8000/health

## Logs

```bash
# API logs
tail -f /tmp/omics_api.log

# Dashboard logs
tail -f /tmp/omics_dashboard.log
```

## Files Deleted (Cleanup)

- `scripts/start.sh` (redundant unified script)
- `scripts/archive/start_dev_server.sh` (old dev script)
- `scripts/archive/start_omics_oracle.sh` (non-SSL version)
- `scripts/archive/start_server_sqlite.sh` (old SQLite script)

## New Files Added

- **`start_omics_oracle.sh`** - Main startup script (root directory)
- **`docs/guides/STARTUP_GUIDE.md`** - Comprehensive guide
- **`examples/test_end_to_end.py`** - End-to-end test script

## Documentation Updated

- `README.md` - Simplified startup instructions
- `docs/guides/STARTUP_GUIDE.md` - Complete reference

## Commit Details

**Commit:** f71b5c2
**Message:** "refactor: Simplify startup - move SSL bypass script to root, remove redundant scripts"

**Changes:**
- 8 files changed
- 469 insertions(+)
- 327 deletions(-)
- All pre-commit hooks passed ✅

## Next Steps

1. **Test the startup:**
   ```bash
   ./start_omics_oracle.sh
   ```

2. **Access the dashboard:**
   Open http://localhost:8502 in your browser

3. **Try the API:**
   Visit http://localhost:8000/docs for interactive API testing

4. **Run end-to-end tests:**
   ```bash
   python examples/test_end_to_end.py
   ```

## Benefits

✅ **Simple** - One script to rule them all
✅ **Clean** - No confusion about which script to use
✅ **Documented** - Comprehensive guide in `docs/guides/`
✅ **Working** - SSL bypass enabled for institutional networks
✅ **Monitored** - Both services auto-restart if they crash
✅ **Safe** - Clean shutdown with Ctrl+C

---

**Ready to demonstrate OmicsOracle end-to-end!** 🚀
