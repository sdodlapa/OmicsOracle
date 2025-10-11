# File Logging Setup Guide

## 🎯 Why File Logging is Critical

**You're absolutely right - we should ALWAYS log to files!**

### Problems Without File Logging:
- ❌ Terminal output gets lost when scrolling
- ❌ Can't analyze bottlenecks after the fact
- ❌ Hard to compare performance across runs
- ❌ No way to debug issues that happened hours ago
- ❌ Can't share detailed logs with team

### Benefits With File Logging:
- ✅ Complete record of every operation
- ✅ Analyze bottlenecks at your leisure
- ✅ Compare performance before/after optimizations
- ✅ Debug issues days/weeks later
- ✅ Share logs for collaboration
- ✅ Track rate limiting patterns
- ✅ Measure exact timing of each phase

---

## 🚀 Quick Start

### Option 1: Use the New Test Script (Recommended)

```bash
# Run test with automatic file logging
python test_searchagent_migration_with_logging.py

# Logs saved to: logs/searchagent_migration_test_TIMESTAMP.log
```

**Features:**
- ✅ Logs to both file AND console
- ✅ Timestamped log files (never overwrite)
- ✅ Detailed phase timing
- ✅ Error handling and recovery
- ✅ Progress indicators

### Option 2: Add Logging to Any Script

```python
from setup_logging import setup_logging

# At the top of your script
log_file = setup_logging(log_name="my_test")

# Your code runs normally
# All logging.info(), .warning(), .error() goes to file AND console

print(f"Log saved to: {log_file}")
```

### Option 3: Manual Logging Setup

```python
import logging
from datetime import datetime
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Timestamped log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/my_test_{timestamp}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Write to file
        logging.StreamHandler(),  # Also print to console
    ],
)

# Now all logs go to both file and console!
```

---

## 📊 Analyzing Log Files

### View Latest Log

```bash
# Find latest log
ls -lt logs/*.log | head -1

# View with pager
less logs/searchagent_migration_test_20251011_031500.log

# Tail live (if still running)
tail -f logs/searchagent_migration_test_20251011_031500.log
```

### Extract Key Metrics

```bash
# Count API calls
grep "HTTP Request: POST" logs/*.log | wc -l

# Find rate limiting
grep "Rate limited" logs/*.log

# Extract timing info
grep "Time:" logs/*.log

# Find errors
grep "ERROR" logs/*.log

# Count phases
grep "INFO - " logs/*.log | grep -E "Enriching|Analyzing|Searching"
```

### Python Analysis

```python
from setup_logging import analyze_log_for_bottlenecks

# Analyze log file
analysis = analyze_log_for_bottlenecks(Path("logs/latest.log"))

print(f"Total API calls: {sum(analysis['api_calls'].values())}")
print(f"OpenAI calls: {analysis['api_calls']['openai']}")
print(f"Rate limits hit: {analysis['rate_limits']}")
print(f"Errors: {analysis['errors']}")
```

---

## 🔍 What to Look For in Logs

### Timing Analysis

**Look for patterns like:**
```
2025-10-11 03:00:00 - INFO - Starting full-text enrichment...
2025-10-11 03:02:00 - INFO - Full-text enrichment complete
```
→ **2 minutes for full-text** ✅ Good!

```
2025-10-11 03:02:00 - INFO - Starting citation analysis...
2025-10-11 03:12:00 - INFO - Citation analysis complete
```
→ **10 minutes for citations** 🚨 Bottleneck!

### Rate Limiting

**Count rate limit occurrences:**
```bash
grep "Rate limited" logs/*.log | grep -o "waiting [0-9]*s" | sort | uniq -c
```

Example output:
```
  45 waiting 2s   ← OpenAlex rate limiting
  12 waiting 3s   ← Semantic Scholar rate limiting
```

### API Costs

**Count OpenAI calls:**
```bash
grep "HTTP Request: POST https://api.openai.com" logs/*.log | wc -l
```

→ Multiply by ~$0.02 per call = estimated cost

### Error Patterns

**Find recurring errors:**
```bash
grep "ERROR" logs/*.log | cut -d'-' -f4 | sort | uniq -c | sort -rn
```

---

## 📁 Log File Organization

### Recommended Structure

```
OmicsOracle/
├── logs/
│   ├── searchagent_migration_test_20251011_031500.log
│   ├── searchagent_migration_test_20251011_032000.log
│   ├── citation_test_20251011_033000.log
│   ├── performance_benchmark_20251011_034000.log
│   └── README.md  ← Document what each log is for
├── test_searchagent_migration_with_logging.py
└── setup_logging.py
```

### Log File Naming Convention

```
{component}_{test_type}_{timestamp}.log

Examples:
- searchagent_migration_test_20251011_031500.log
- citation_enrichment_benchmark_20251011_032000.log
- fulltext_retrieval_debug_20251011_033000.log
- unified_pipeline_performance_20251011_034000.log
```

---

## 🎨 Log Levels - When to Use What

### INFO (Default)
**Use for:** Normal operation, progress updates, phase transitions
```python
logger.info("Starting search for 'diabetes insulin'")
logger.info("Found 99 publications from PubMed")
logger.info("Full-text enrichment: 99/99 complete")
```

### DEBUG
**Use for:** Detailed debugging, variable values, internal state
```python
logger.debug(f"Query after optimization: {optimized_query}")
logger.debug(f"Cache key: {cache_key}")
logger.debug(f"Trying source: {source_name}")
```

### WARNING
**Use for:** Recoverable issues, degraded performance, fallbacks
```python
logger.warning("Rate limited by OpenAlex, waiting 2s")
logger.warning("Cache miss - fetching from API")
logger.warning("Institutional access failed, trying Unpaywall")
```

### ERROR
**Use for:** Failures, exceptions, data loss
```python
logger.error(f"Failed to enrich publication: {e}")
logger.error("OpenAI API key not found")
logger.error("Redis connection failed")
```

---

## 🔧 Advanced Logging Configurations

### Different Log Levels for File vs Console

```python
import logging
from datetime import datetime
from pathlib import Path

# File handler (DEBUG - capture everything)
file_handler = logging.FileHandler(f"logs/debug_{datetime.now():%Y%m%d_%H%M%S}.log")
file_handler.setLevel(logging.DEBUG)

# Console handler (INFO - less verbose)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,  # Capture everything
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[file_handler, console_handler],
)
```

### Separate Logs Per Component

```python
# Citation client logs
citation_logger = logging.getLogger("omics_oracle_v2.lib.citations")
citation_handler = logging.FileHandler("logs/citations.log")
citation_logger.addHandler(citation_handler)

# LLM logs
llm_logger = logging.getLogger("omics_oracle_v2.lib.llm")
llm_handler = logging.FileHandler("logs/llm_calls.log")
llm_logger.addHandler(llm_handler)
```

### JSON Logging for Machine Analysis

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

handler = logging.FileHandler("logs/structured.json")
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

---

## 📈 Example: Analyzing a Real Log

### Sample Log Excerpt

```
2025-10-11 02:55:21 - INFO - Starting search: 'diabetes insulin resistance'
2025-10-11 02:55:21 - INFO - Query optimization: 2 entities extracted
2025-10-11 02:55:21 - INFO - Generated 7 query variations
2025-10-11 02:55:31 - INFO - PubMed: Found 99 publications
2025-10-11 02:55:31 - INFO - Starting full-text enrichment...
2025-10-11 02:57:30 - INFO - Full-text: 99/99 complete (100% success)
2025-10-11 02:57:30 - INFO - Starting citation enrichment...
2025-10-11 03:03:00 - WARNING - Rate limited by OpenAlex, waiting 2s
2025-10-11 03:08:00 - INFO - Citation enrichment: 50/99 complete
2025-10-11 03:12:30 - INFO - Citation enrichment complete
```

### Analysis

| Phase | Start | End | Duration | Notes |
|-------|-------|-----|----------|-------|
| Query optimization | 02:55:21 | 02:55:21 | <1s | ✅ Fast |
| PubMed search | 02:55:21 | 02:55:31 | 10s | ✅ Fast |
| Full-text enrichment | 02:55:31 | 02:57:30 | 2min | ✅ Fast & parallel |
| Citation enrichment | 02:57:30 | 03:12:30 | 15min | 🚨 Bottleneck! |

**Conclusion:** Citation enrichment is 7x slower than full-text!

---

## ✅ Best Practices

### DO:
- ✅ Always log to file for long-running processes (>10s)
- ✅ Use timestamped filenames (never overwrite)
- ✅ Log to both file AND console during development
- ✅ Include timing information (start/end/duration)
- ✅ Log phase transitions clearly
- ✅ Keep log files for at least a week
- ✅ Document what each log file contains

### DON'T:
- ❌ Log only to console for long processes
- ❌ Use fixed log filenames (gets overwritten)
- ❌ Log sensitive data (API keys, passwords)
- ❌ Set log level to DEBUG in production
- ❌ Delete logs immediately after tests
- ❌ Mix multiple test runs in same log file

---

## 🎯 Quick Reference

### Enable Logging in Any Script

```python
from setup_logging import setup_logging
log_file = setup_logging(log_name="my_test")
```

### Run Test with Logging

```bash
python test_searchagent_migration_with_logging.py
```

### Analyze Latest Log

```python
from setup_logging import analyze_log_for_bottlenecks, get_latest_log

log_file = get_latest_log()
analysis = analyze_log_for_bottlenecks(log_file)
print(analysis)
```

### View Live Logs

```bash
tail -f logs/*.log
```

---

## 📝 Summary

**Before:** Logs disappear when terminal scrolls
**After:** Permanent record in `logs/` directory

**Before:** Can't debug past issues
**After:** Analyze bottlenecks anytime

**Before:** Hard to measure performance
**After:** Exact timing of every phase

**You were 100% right - file logging is essential!** 🎯
