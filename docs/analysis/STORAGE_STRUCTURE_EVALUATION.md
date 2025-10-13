# Storage Structure Evaluation: Source-Based vs Alternatives

**Date:** October 11, 2025
**Question:** Is source-based directory structure the best approach for our use case?

---

## Current Proposed Structure (Source-Based)

```
data/fulltext/
├── pdf/
│   ├── arxiv/          # arXiv papers
│   ├── pmc/            # PubMed Central PDFs
│   ├── institutional/  # Georgia Tech/ODU downloads
│   ├── publisher/      # Direct from publisher
│   ├── scihub/         # Sci-Hub downloads
│   └── {hash}.pdf      # Legacy cache
├── xml/
│   └── pmc/            # PMC NXML files
└── parsed/
    └── {id}.json       # Parsed content cache
```

### Pros ✅
1. **Clear provenance** - Know exactly where each file came from
2. **Legal separation** - Easy to delete scihub/ if needed for compliance
3. **Source-specific optimization** - Can apply different parsing strategies per source
4. **Debugging** - "Show me all institutional downloads" is trivial
5. **Quality tracking** - Monitor success rates by source
6. **Selective re-parsing** - "Re-parse only arXiv papers" is simple

### Cons ❌
1. **Duplicate file risk** - Same paper from multiple sources = multiple files
2. **More complex lookups** - Must check 7+ directories
3. **Identifier dependency** - Need to know source to find file efficiently
4. **Migration complexity** - Moving between sources requires file moves

---

## Alternative 1: Flat Structure (All Files Together)

```
data/fulltext/
├── pdf/
│   └── {identifier}.pdf    # All PDFs together
├── xml/
│   └── {identifier}.xml    # All XMLs together
└── parsed/
    └── {identifier}.json   # Parsed cache
```

### Implementation
```python
# Single lookup
pdf_file = Path(f"data/fulltext/pdf/{publication.pmc_id}.pdf")
if pdf_file.exists():
    return pdf_file
```

### Pros ✅
1. **Simple lookups** - Single directory check
2. **Fast filesystem** - No subdirectory traversal
3. **Deduplication** - Same identifier = same file (automatic dedup)
4. **Easy backup** - `rsync data/fulltext/pdf/` backs up everything
5. **No duplicate storage** - Paper downloaded from multiple sources only stored once

### Cons ❌
1. **Lost provenance** - Can't tell source without metadata DB
2. **No legal separation** - Can't easily delete Sci-Hub files
3. **Huge directories** - Millions of files in one folder (filesystem limits)
4. **Lost debugging** - Can't analyze by source
5. **Identifier conflicts** - What if PMC ID = arXiv ID?

### Filesystem Limits
```
ext4: 10 million files per directory (slow after 100k)
APFS: No hard limit, but slow after ~500k files
XFS: Better, but still slow after 1M files
```

**Verdict:** ❌ **NOT RECOMMENDED** - Will hit filesystem limits at scale

---

## Alternative 2: Content-Addressable (Hash-Based)

```
data/fulltext/
├── pdf/
│   └── ab/
│       └── cd/
│           └── abcd1234efgh5678.pdf  # Content hash
├── xml/
│   └── 12/
│       └── 34/
│           └── 12345678abcd.xml
└── metadata/
    └── {publication_id}.json  # Maps ID → hash + source
```

### Implementation (Git-like)
```python
import hashlib

# Store
content_hash = hashlib.sha256(pdf_content).hexdigest()
prefix = content_hash[:2]
subdir = content_hash[2:4]
path = Path(f"data/fulltext/pdf/{prefix}/{subdir}/{content_hash}.pdf")

# Metadata
metadata = {
    'publication_id': pub.id,
    'content_hash': content_hash,
    'source': 'arxiv',
    'doi': pub.doi,
    'downloaded_at': '2025-10-11T12:00:00Z'
}
```

### Pros ✅
1. **Automatic deduplication** - Identical content = same file (saves space)
2. **Integrity verification** - Filename IS the checksum
3. **Scales infinitely** - 256 * 256 = 65,536 subdirectories
4. **Fast lookups** - O(1) with hash, no directory scanning
5. **Corruption detection** - Re-hash file to verify integrity
6. **Publisher update detection** - Updated PDF = different hash

### Cons ❌
1. **Extra metadata layer** - MUST maintain publication_id → hash mapping
2. **Lost human readability** - Can't eyeball "what's this file?"
3. **Metadata dependency** - If metadata DB corrupted, files are orphaned
4. **Debugging harder** - "Show me arXiv papers" requires metadata query
5. **Overhead** - Must hash 100MB PDF before storing

### Real-World Example (Git)
```
.git/objects/
├── ab/
│   └── cdef1234...  # Git uses this, works great
└── cd/
    └── 5678abcd...

# Git also keeps metadata (refs, logs, etc.)
```

**Verdict:** ⚠️ **GOOD FOR LARGE SCALE** - But requires robust metadata DB

---

## Alternative 3: Hybrid (Source + Identifier)

```
data/fulltext/
├── pdf/
│   ├── arxiv/
│   │   └── 23/          # Year-based
│   │       └── 01/      # Month-based
│   │           └── 2301.12345.pdf
│   ├── pmc/
│   │   └── 98/          # First 2 digits of PMC ID
│   │       └── 76/      # Next 2 digits
│   │           └── PMC9876543.pdf
│   └── institutional/
│       └── 2025/        # Year downloaded
│           └── 10/      # Month downloaded
│               └── {sanitized_doi}.pdf
├── xml/
│   └── pmc/
│       └── 98/
│           └── 76/
│               └── PMC9876543.nxml
├── parsed/
│   └── {first_2_chars}/
│       └── {next_2_chars}/
│           └── {publication_id}.json
└── metadata.db          # SQLite: pub_id → file_path + source + metadata
```

### Pros ✅
1. **Provenance preserved** - Source in path
2. **Scales well** - Subdirectories keep each folder manageable
3. **Human readable** - Can still browse by source/date
4. **Legal separation** - Delete scihub/ still works
5. **Fast lookups** - Predictable paths, no full directory scan
6. **Time-based analysis** - "Show me papers from 2024"

### Cons ❌
1. **More complex paths** - Deeper nesting
2. **Still potential duplicates** - Same paper from multiple sources
3. **Path calculation** - Must extract year/month/prefix from identifiers

**Verdict:** ✅ **BEST BALANCE** - Combines benefits of source-based + scalability

---

## Alternative 4: Database-Centric (Minimal Files)

```
data/fulltext/
├── blobs/
│   └── {hash}.blob      # Just raw files, no structure
└── database/
    └── fulltext.db      # All metadata + paths

# Database schema
CREATE TABLE fulltext_files (
    publication_id TEXT PRIMARY KEY,
    file_hash TEXT,
    file_type TEXT,
    source TEXT,
    file_path TEXT,
    size_bytes INTEGER,
    downloaded_at TIMESTAMP,
    quality_score REAL,
    INDEX idx_source (source),
    INDEX idx_hash (file_hash)
);
```

### Pros ✅
1. **Single source of truth** - Database knows everything
2. **Powerful queries** - "Find all PDFs from institutional access in 2024"
3. **Easy deduplication** - Query by hash before storing
4. **Flexible metadata** - Add columns without restructuring files
5. **Analytics ready** - Built-in reporting

### Cons ❌
1. **Database dependency** - If DB corrupted, everything lost
2. **Backup complexity** - Must backup DB + files together
3. **Opaque storage** - Can't browse files without DB
4. **Migration risk** - DB schema changes require migrations

**Verdict:** ✅ **BEST FOR PRODUCTION** - But needs good backup strategy

---

## Recommended Hybrid Approach

### Final Recommendation: **Hybrid Source-Based + Database**

```
data/fulltext/
├── pdf/
│   ├── arxiv/
│   │   └── {arxiv_id}.pdf         # E.g., 2301.12345.pdf
│   ├── pmc/
│   │   └── PMC{id}.pdf            # E.g., PMC9876543.pdf
│   ├── institutional/
│   │   └── {sanitized_doi}.pdf    # E.g., 10_1234_test_2023_001.pdf
│   ├── publisher/
│   │   └── {sanitized_doi}.pdf
│   ├── scihub/
│   │   └── {sanitized_doi}.pdf
│   └── biorxiv/
│       └── {doi_suffix}.pdf
├── xml/
│   └── pmc/
│       └── PMC{id}.nxml
├── parsed/
│   └── {publication_id}.json      # Fast access cache
└── metadata/
    ├── fulltext.db                # SQLite metadata
    └── checksums.txt              # Backup verification
```

### Database Schema
```sql
CREATE TABLE fulltext_cache (
    publication_id TEXT PRIMARY KEY,
    doi TEXT,
    pmid TEXT,
    pmc_id TEXT,

    -- File info
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,      -- 'pdf', 'xml', 'nxml'
    file_source TEXT NOT NULL,    -- 'arxiv', 'pmc', 'institutional', etc.
    file_hash TEXT,               -- SHA256 for integrity
    file_size_bytes INTEGER,

    -- Timestamps
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,
    last_accessed TIMESTAMP,

    -- Content metadata
    has_fulltext BOOLEAN DEFAULT TRUE,
    has_tables BOOLEAN DEFAULT FALSE,
    table_count INTEGER DEFAULT 0,
    figure_count INTEGER DEFAULT 0,
    word_count INTEGER,
    quality_score REAL,

    -- Indexing
    INDEX idx_doi (doi),
    INDEX idx_pmc_id (pmc_id),
    INDEX idx_source (file_source),
    INDEX idx_has_tables (has_tables),
    INDEX idx_downloaded (downloaded_at)
);

-- Deduplication tracking
CREATE TABLE file_duplicates (
    file_hash TEXT,
    publication_id TEXT,
    file_path TEXT,
    PRIMARY KEY (file_hash, publication_id)
);
```

### Implementation
```python
class SmartCacheWithDB:
    """Enhanced SmartCache with database metadata."""

    def find_local_file(self, publication):
        """Check DB first, then filesystem."""

        # FAST PATH: Check database
        cached = self.db.get_cached_file(publication.id)
        if cached and Path(cached['file_path']).exists():
            # Update last accessed
            self.db.update_access_time(publication.id)
            return LocalFileResult(
                found=True,
                file_path=Path(cached['file_path']),
                file_type=cached['file_type'],
                source=cached['file_source'],
                size_bytes=cached['file_size_bytes']
            )

        # SLOW PATH: Scan filesystem
        result = self._scan_filesystem(publication)

        if result.found:
            # Cache in DB for next time
            self.db.add_cached_file(
                publication_id=publication.id,
                file_path=str(result.file_path),
                file_type=result.file_type,
                file_source=result.source,
                file_hash=self._compute_hash(result.file_path),
                file_size_bytes=result.size_bytes
            )

        return result

    def save_file(self, content, publication, source, file_type='pdf'):
        """Save file and record in database."""

        # Compute hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        # Check if already exists
        existing = self.db.get_by_hash(file_hash)
        if existing:
            logger.info(f"Duplicate detected: {file_hash[:8]}... already at {existing['file_path']}")
            # Add reference to existing file
            self.db.add_duplicate_reference(file_hash, publication.id)
            return Path(existing['file_path'])

        # Save new file
        file_path = self._get_save_path(publication, source, file_type)
        file_path.write_bytes(content)

        # Record in database
        self.db.add_cached_file(
            publication_id=publication.id,
            file_path=str(file_path),
            file_type=file_type,
            file_source=source,
            file_hash=file_hash,
            file_size_bytes=len(content)
        )

        return file_path
```

---

## Comparison Matrix

| Feature | Source-Based | Flat | Hash-Based | Hybrid | DB-Centric |
|---------|-------------|------|------------|--------|------------|
| **Lookup Speed** | Medium (7 dirs) | Fast (1 dir) | Very Fast (O(1)) | Fast (predictable) | Very Fast (indexed) |
| **Provenance** | ✅ Excellent | ❌ Lost | ⚠️ DB-dependent | ✅ Excellent | ✅ Excellent |
| **Deduplication** | ❌ Manual | ✅ Auto | ✅ Auto | ⚠️ Manual/DB | ✅ Auto |
| **Scale (1M files)** | ⚠️ OK | ❌ Slow | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| **Human Readable** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ⚠️ DB-dependent |
| **Legal Separation** | ✅ Easy | ❌ Hard | ❌ Hard | ✅ Easy | ✅ Easy |
| **Debugging** | ✅ Easy | ❌ Hard | ⚠️ DB-dependent | ✅ Easy | ✅ Easy |
| **Backup Complexity** | ✅ Simple | ✅ Simple | ⚠️ Medium | ✅ Simple | ⚠️ Medium |
| **Migration Risk** | ✅ Low | ✅ Low | ⚠️ Medium | ✅ Low | ⚠️ Medium |
| **Implementation** | ✅ Simple | ✅ Simple | ⚠️ Complex | ⚠️ Medium | ⚠️ Complex |

---

## Performance Analysis

### Lookup Performance (1M papers)

**Source-Based (Current Plan):**
```
Average lookup: 7 stat() calls = ~7ms
Worst case: 7 directories to check
Best case: XML found first = 1ms
Cache hit: Database lookup = 0.1ms
```

**Flat Structure:**
```
Average lookup: 1 stat() call = 1ms
BUT: ls on 1M directory = 30+ seconds
Filesystem degradation at 100k+ files
```

**Hash-Based:**
```
Average lookup: 1 stat() call (if hash known) = 1ms
Calculate hash: 100MB PDF = ~200ms (expensive!)
With DB cache: 0.1ms
```

**Hybrid (Source + DB):**
```
Average lookup: 0.1ms (DB cached)
DB miss + filesystem: 2-3ms
No filesystem degradation (subdirs keep it fast)
```

### Storage Efficiency (1M papers)

**Scenario:** 1M papers, 30% duplicates (same paper from multiple sources)

**Source-Based (No Dedup):**
```
Total files: 1M + 300k duplicates = 1.3M files
Average size: 5MB per PDF
Total storage: 1.3M * 5MB = 6.5TB
Wasted: 1.5TB (30% duplication)
```

**With Deduplication (Hash-Based or DB-Centric):**
```
Total unique files: 1M files
Total storage: 1M * 5MB = 5TB
Saved: 1.5TB (23% reduction)
```

---

## Migration Path

### Phase 1: Current (Source-Based) ← **WE ARE HERE**
```
✅ Simple to implement
✅ Easy to debug
✅ Clear provenance
⚠️ No deduplication
⚠️ 7 directories to check
```

### Phase 2: Add Database Layer (Week 2-3)
```python
# Add metadata.db
# Index all existing files
# Use DB for fast lookups
# Still source-based storage

✅ Fast lookups (DB cached)
✅ Deduplication detection
✅ Analytics ready
⚠️ Need to maintain DB
```

### Phase 3: Optimize Storage (Month 2-3)
```python
# Option A: Keep source-based, add symlinks for duplicates
# Option B: Migrate to hash-based storage
# Option C: Keep source-based, delete confirmed duplicates

✅ Space savings
✅ Faster queries
⚠️ Migration complexity
```

---

## Real-World Examples

### PubMed Central (PMC)
```
PMC uses:
- Source-based (bulk/ vs individual/)
- Subdirectories by ID range (PMC9876/PMC9876543.xml)
- Database metadata (Entrez)

Why: Scale (7M+ articles), provenance tracking
```

### arXiv
```
arXiv uses:
- Year/month subdirectories (2301/2301.12345.pdf)
- Source files separate (2301/2301.12345.tar.gz)
- Database metadata

Why: Time-based access patterns, version tracking
```

### Internet Archive
```
Archive.org uses:
- Content-addressable (hash-based)
- Metadata in database
- Multiple replicas

Why: Maximum deduplication, integrity verification
```

### Our Use Case
```
We need:
- Provenance (source tracking) ✅ Source-based
- Legal separation (Sci-Hub) ✅ Source-based
- Scale (1M+ papers) ✅ Database
- Fast lookups ✅ Database
- Deduplication ✅ Database
- Analytics ✅ Database

Best: Source-based storage + Database metadata
```

---

## Final Recommendation

### 🎯 **Recommended: Source-Based + Database (Hybrid)**

```
data/fulltext/
├── pdf/
│   ├── arxiv/{arxiv_id}.pdf
│   ├── pmc/PMC{id}.pdf
│   ├── institutional/{doi}.pdf
│   ├── publisher/{doi}.pdf
│   ├── scihub/{doi}.pdf
│   └── biorxiv/{doi}.pdf
├── xml/
│   └── pmc/PMC{id}.nxml
├── parsed/
│   └── {pub_id}.json
└── metadata/
    └── fulltext.db          # Fast lookups + analytics
```

### Why This Structure?

**1. Provenance (Critical for Research)**
- Can cite source: "Full-text obtained via institutional access"
- Legal compliance: Easy to remove Sci-Hub files if needed
- Quality tracking: "Institutional access has 99% success rate"

**2. Debugging & Monitoring**
- "Show me all arXiv downloads" = `ls data/fulltext/pdf/arxiv/ | wc -l`
- "Check institutional access files" = simple directory check
- Source-specific issues easy to identify

**3. Scalability**
- Database indexes handle 1M+ papers easily
- Source-based dirs keep each folder manageable (<100k files each)
- No filesystem degradation

**4. Implementation**
- ✅ Already implemented (SmartCache.py)
- ✅ Database layer = 1 week of work
- ✅ Backwards compatible

**5. Flexibility**
- Can migrate to hash-based later if needed
- Can add deduplication without restructuring
- Can add new sources without breaking existing code

### Implementation Timeline

**Week 1 (Current):** ✅ Source-based storage + SmartCache
**Week 2:** 📋 Add SQLite database for metadata
**Week 3:** 🚀 Add deduplication detection (via DB)
**Week 4:** 📊 Add analytics dashboard
**Month 2:** ⚡ Optimize based on real-world usage patterns

---

## Alternative: If You Want Maximum Simplicity

### Ultra-Simple (Flat + Database)

```
data/fulltext/
├── files/
│   └── {file_hash}.blob    # All files, no structure
└── fulltext.db             # Maps pub_id → hash + metadata
```

**Pros:**
- Automatic deduplication
- Simplest code
- Fastest lookups

**Cons:**
- Lost human readability
- Database dependency critical
- Harder to debug

**Use if:** You value simplicity over provenance

---

## Conclusion

**Your question is excellent** - the source-based structure IS slightly more complex than alternatives.

**However, for a research tool, provenance matters:**
- Legal: Need to track Sci-Hub vs institutional
- Citations: Need to cite data sources
- Debugging: Need to monitor source effectiveness
- Compliance: Need to delete questionable sources if required

**Recommended: Stick with source-based storage + add database layer next week**

This gives you:
- ✅ Clear provenance (research requirement)
- ✅ Fast lookups (database cached)
- ✅ Deduplication (database detected)
- ✅ Easy debugging (source directories)
- ✅ Legal compliance (delete scihub/ if needed)

**Alternative if you prefer:** Go database-centric from day 1, but you'll need robust backup strategy.

Want me to implement the database layer next, or stick with filesystem-only for now?
