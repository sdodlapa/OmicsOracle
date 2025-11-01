# Data Organization Analysis - October 13, 2025

## Current Architecture Issues

### Problem Statement
When frontend clicks "Download Papers", it needs comprehensive access to:
- GEO dataset metadata (organism, platform, samples, etc.)
- All publication metadata (PMIDs, DOIs, titles, authors, etc.)
- All collected URLs for each paper (for retry/fallback)
- Download status and history
- Citation relationships
- File paths and organization

**Current Issues:**
1. ❌ Data scattered across multiple systems (API response, filesystem, database)
2. ❌ No single source of truth for GEO → Papers → URLs mapping
3. ❌ URL information lost after download attempt
4. ❌ Difficult to retry failed downloads
5. ❌ No clear citation graph/relationships
6. ❌ Frontend must reconstruct relationships from partial data

## Requirements Analysis

### Functional Requirements
1. **Fast Lookup**: Get all papers for a GEO ID in O(1) time
2. **Relationship Traversal**: Navigate GEO → Original Paper → Citing Papers
3. **URL Access**: Get all URLs for any paper (for retry)
4. **Status Tracking**: Know download status for each paper
5. **Metadata Access**: Full GEO and publication metadata
6. **File Mapping**: Quick path lookup for downloaded PDFs
7. **Persistence**: Survive server restarts
8. **Concurrent Access**: Multiple users/processes can access safely

### Non-Functional Requirements
1. **Performance**: Sub-millisecond lookups for cached data
2. **Scalability**: Handle 10,000+ GEO IDs
3. **Maintainability**: Easy to understand and modify
4. **Robustness**: Graceful degradation on partial failures
5. **Extensibility**: Easy to add new data types (e.g., protein datasets)

---

## Solution 1: GEO-Centric Graph Database

### Architecture
```python
# Neo4j/NetworkX Graph Structure
(GEO:Dataset {geo_id, title, organism, ...})
  |
  ├─[:GENERATED_BY]─> (Paper:Original {pmid, doi, ...})
  │                         |
  │                         └─[:CITED_BY]─> (Paper:Citing {pmid, doi, ...})
  │
  ├─[:HAS_URL]─> (URL {url, source, priority, ...})
  └─[:STORED_AT]─> (File {path, size, format, ...})

# Query Examples
MATCH (g:GEO {geo_id: 'GSE12345'})-[:GENERATED_BY]->(o:Paper)-[:CITED_BY]->(c:Paper)
RETURN o, c

MATCH (p:Paper {pmid: '12345'})-[:HAS_URL]->(u:URL)
RETURN u ORDER BY u.priority
```

### Pros
✅ **Natural Relationship Modeling**: Citations, derivations, mentions
✅ **Flexible Queries**: Can traverse any relationship path
✅ **Graph Algorithms**: PageRank for paper importance, community detection
✅ **Visual Exploration**: Can visualize citation networks
✅ **Schema Evolution**: Easy to add new node/edge types
✅ **Efficient Traversal**: Optimized for relationship queries

### Cons
❌ **Complexity**: Requires Neo4j or graph database setup
❌ **Learning Curve**: Team needs to learn Cypher/graph concepts
❌ **Overkill**: May be too heavy for current use case
❌ **Deployment**: Another service to maintain/monitor
❌ **Performance**: Network overhead for remote queries
❌ **Cost**: Neo4j Cloud can be expensive

### Implementation Complexity: **HIGH**
### Best For: Large-scale citation analysis, complex queries

---

## Solution 2: Hierarchical JSON Store (File-Based)

### Architecture
```
data/geo_registry/
  {geo_id}/
    metadata.json          # Complete GEO + papers + URLs
    papers/
      original/
        {pmid}.json       # Paper metadata + URLs + status
        {pmid}.pdf
      citing/
        {pmid}.json
        {pmid}.pdf
    cache/
      urls_collected.json  # All URLs for all papers
      download_history.json
```

### metadata.json Structure
```json
{
  "geo": {
    "geo_id": "GSE12345",
    "title": "...",
    "organism": "Homo sapiens",
    "platform": "GPL570",
    "sample_count": 100,
    "metadata": {...}
  },
  "papers": {
    "original": {
      "12345": {
        "pmid": "12345",
        "doi": "10.1234/...",
        "title": "...",
        "authors": [...],
        "urls": [
          {"url": "...", "source": "pmc", "priority": 1, "status": "success"},
          {"url": "...", "source": "unpaywall", "priority": 2, "status": "failed"}
        ],
        "download": {
          "status": "success",
          "path": "papers/original/12345.pdf",
          "size": 1234567,
          "downloaded_at": "2025-10-13T20:00:00Z",
          "source_used": "pmc"
        }
      }
    },
    "citing": {
      "67890": {...},
      "67891": {...}
    }
  },
  "relationships": {
    "original_pmids": ["12345"],
    "citing_pmids": ["67890", "67891"],
    "citation_graph": {
      "12345": {"cited_by": ["67890", "67891"]}
    }
  },
  "index": {
    "by_pmid": {"12345": "original", "67890": "citing"},
    "by_doi": {"10.1234/...": "12345"}
  }
}
```

### Pros
✅ **Simple**: Just JSON files, no external dependencies
✅ **Portable**: Can copy/backup entire directory
✅ **Version Control**: Can track changes with git
✅ **Human Readable**: Easy to inspect and debug
✅ **Self-Contained**: All data for GEO in one place
✅ **Fast Reads**: OS file cache for frequently accessed files

### Cons
❌ **Scaling**: Large files (>10MB) become slow
❌ **Concurrent Writes**: File locking issues
❌ **Atomicity**: No transaction support
❌ **Query Performance**: Must load entire file to query
❌ **Memory**: Large datasets consume RAM
❌ **No Indexing**: Linear search for cross-GEO queries

### Implementation Complexity: **LOW**
### Best For: Small-medium datasets (<1000 GEO IDs), prototyping

---

## Solution 3: Redis + PostgreSQL Hybrid

### Architecture
```python
# Redis (Fast Cache - In-Memory)
geo:{geo_id}:metadata          → Hash: {title, organism, ...}
geo:{geo_id}:papers:original   → Set: [pmid1, pmid2, ...]
geo:{geo_id}:papers:citing     → Set: [pmid3, pmid4, ...]
paper:{pmid}:metadata          → Hash: {title, authors, ...}
paper:{pmid}:urls              → List: [{url, source, priority}, ...]
paper:{pmid}:status            → Hash: {download_status, path, ...}

# PostgreSQL (Persistent Storage)
Table: geo_datasets
  - geo_id (PK)
  - title, organism, platform, sample_count, ...
  - metadata (JSONB)

Table: publications
  - pmid (PK)
  - doi, title, authors (ARRAY), journal, year
  - metadata (JSONB)

Table: geo_paper_relationships
  - geo_id (FK)
  - pmid (FK)
  - relationship_type (original | citing)
  - discovered_at

Table: paper_urls
  - id (PK)
  - pmid (FK)
  - url, source, priority
  - metadata (JSONB)

Table: download_history
  - id (PK)
  - pmid (FK)
  - url, source
  - status, error_message
  - file_path, file_size
  - downloaded_at
```

### Access Pattern
```python
# Fast lookup (Redis)
def get_papers_for_geo(geo_id: str):
    # Check cache first
    cached = redis.hgetall(f"geo:{geo_id}:metadata")
    if cached:
        return cached

    # Fallback to DB
    data = db.query("""
        SELECT p.* FROM publications p
        JOIN geo_paper_relationships r ON p.pmid = r.pmid
        WHERE r.geo_id = %s
    """, geo_id)

    # Cache result
    redis.hmset(f"geo:{geo_id}:metadata", data)
    redis.expire(f"geo:{geo_id}:metadata", 3600)

    return data

# Get all URLs for retry
def get_all_urls_for_paper(pmid: str):
    return db.query("""
        SELECT * FROM paper_urls
        WHERE pmid = %s
        ORDER BY priority ASC
    """, pmid)
```

### Pros
✅ **Performance**: Sub-millisecond Redis lookups
✅ **Persistence**: PostgreSQL for long-term storage
✅ **ACID**: Transactions for consistent updates
✅ **Scalability**: Can handle millions of records
✅ **Mature**: Battle-tested technologies
✅ **Rich Queries**: SQL for complex analytics
✅ **Concurrent Access**: Built-in locking/transactions
✅ **Monitoring**: Excellent tooling (pgAdmin, RedisInsight)

### Cons
❌ **Infrastructure**: Requires Redis + PostgreSQL setup
❌ **Complexity**: More moving parts to maintain
❌ **Sync Overhead**: Must keep Redis/PG in sync
❌ **Memory Cost**: Redis consumes RAM
❌ **Learning Curve**: Team needs SQL + Redis knowledge

### Implementation Complexity: **MEDIUM-HIGH**
### Best For: Production systems, high traffic, large scale

---

## Solution 4: SQLite + JSON Hybrid (RECOMMENDED)

### Architecture
```python
# SQLite Database (Single File)
data/omics_oracle.db

# Tables
geo_datasets
  - geo_id TEXT PRIMARY KEY
  - metadata JSON  # All GEO metadata
  - updated_at TIMESTAMP

publications
  - id INTEGER PRIMARY KEY
  - pmid TEXT UNIQUE
  - doi TEXT
  - metadata JSON  # Title, authors, journal, etc.
  - urls JSON  # All collected URLs with metadata
  - updated_at TIMESTAMP

geo_publications
  - geo_id TEXT
  - publication_id INTEGER
  - relationship_type TEXT  # 'original' | 'citing'
  - FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id)
  - FOREIGN KEY (publication_id) REFERENCES publications(id)
  - PRIMARY KEY (geo_id, publication_id)

download_history
  - id INTEGER PRIMARY KEY
  - publication_id INTEGER
  - url TEXT
  - source TEXT
  - status TEXT  # 'success' | 'failed' | 'retry'
  - file_path TEXT
  - error_message TEXT
  - downloaded_at TIMESTAMP
  - FOREIGN KEY (publication_id) REFERENCES publications(id)

# File Structure
data/pdfs/
  {geo_id}/
    original/
      {pmid}.pdf
    citing/
      {pmid}.pdf
```

### Implementation
```python
import sqlite3
import json
from typing import Dict, List, Optional

class GEORegistry:
    """Centralized GEO-centric data store"""

    def __init__(self, db_path: str = "data/omics_oracle.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        """Create tables with indexes"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS geo_datasets (
                geo_id TEXT PRIMARY KEY,
                metadata JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pmid TEXT UNIQUE,
                doi TEXT,
                metadata JSON NOT NULL,
                urls JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_pub_pmid ON publications(pmid);
            CREATE INDEX IF NOT EXISTS idx_pub_doi ON publications(doi);

            CREATE TABLE IF NOT EXISTS geo_publications (
                geo_id TEXT NOT NULL,
                publication_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (geo_id, publication_id),
                FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id),
                FOREIGN KEY (publication_id) REFERENCES publications(id)
            );

            CREATE INDEX IF NOT EXISTS idx_geo_pub_geo ON geo_publications(geo_id);
            CREATE INDEX IF NOT EXISTS idx_geo_pub_type ON geo_publications(relationship_type);

            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                file_path TEXT,
                file_size INTEGER,
                error_message TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (publication_id) REFERENCES publications(id)
            );

            CREATE INDEX IF NOT EXISTS idx_download_pub ON download_history(publication_id);
            CREATE INDEX IF NOT EXISTS idx_download_status ON download_history(status);
        """)
        self.conn.commit()

    def register_geo_dataset(self, geo_id: str, metadata: Dict):
        """Register GEO dataset with all metadata"""
        self.conn.execute(
            "INSERT OR REPLACE INTO geo_datasets (geo_id, metadata) VALUES (?, ?)",
            (geo_id, json.dumps(metadata))
        )
        self.conn.commit()

    def register_publication(self, pmid: str, metadata: Dict, urls: List[Dict]) -> int:
        """Register publication with URLs"""
        cursor = self.conn.execute(
            """INSERT OR REPLACE INTO publications (pmid, doi, metadata, urls)
               VALUES (?, ?, ?, ?)""",
            (pmid, metadata.get("doi"), json.dumps(metadata), json.dumps(urls))
        )
        self.conn.commit()
        return cursor.lastrowid

    def link_geo_to_publication(self, geo_id: str, pmid: str, relationship_type: str):
        """Link GEO dataset to publication"""
        pub_id = self.conn.execute(
            "SELECT id FROM publications WHERE pmid = ?", (pmid,)
        ).fetchone()[0]

        self.conn.execute(
            """INSERT OR IGNORE INTO geo_publications
               (geo_id, publication_id, relationship_type) VALUES (?, ?, ?)""",
            (geo_id, pub_id, relationship_type)
        )
        self.conn.commit()

    def get_complete_geo_data(self, geo_id: str) -> Dict:
        """Get ALL data for GEO ID in one call - O(1) lookup!"""
        cursor = self.conn.execute("""
            SELECT
                g.metadata as geo_metadata,
                p.pmid,
                p.metadata as pub_metadata,
                p.urls,
                gp.relationship_type,
                (SELECT json_group_array(json_object(
                    'url', url,
                    'source', source,
                    'status', status,
                    'file_path', file_path,
                    'downloaded_at', downloaded_at
                )) FROM download_history WHERE publication_id = p.id) as download_history
            FROM geo_datasets g
            LEFT JOIN geo_publications gp ON g.geo_id = gp.geo_id
            LEFT JOIN publications p ON gp.publication_id = p.id
            WHERE g.geo_id = ?
        """, (geo_id,))

        rows = cursor.fetchall()
        if not rows:
            return None

        # Build complete structure
        result = {
            "geo": json.loads(rows[0][0]),
            "papers": {
                "original": [],
                "citing": []
            }
        }

        for row in rows:
            if row[1]:  # Has publication
                paper = {
                    "pmid": row[1],
                    **json.loads(row[2]),
                    "urls": json.loads(row[3]) if row[3] else [],
                    "download_history": json.loads(row[5]) if row[5] else []
                }

                if row[4] == "original":
                    result["papers"]["original"].append(paper)
                else:
                    result["papers"]["citing"].append(paper)

        return result

    def get_urls_for_retry(self, pmid: str) -> List[Dict]:
        """Get all URLs for a paper (for retry logic)"""
        cursor = self.conn.execute(
            "SELECT urls FROM publications WHERE pmid = ?", (pmid,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row and row[0] else []

    def record_download_attempt(self, pmid: str, url: str, source: str,
                               status: str, file_path: Optional[str] = None,
                               error: Optional[str] = None):
        """Record download attempt for analytics"""
        pub_id = self.conn.execute(
            "SELECT id FROM publications WHERE pmid = ?", (pmid,)
        ).fetchone()[0]

        self.conn.execute("""
            INSERT INTO download_history
            (publication_id, url, source, status, file_path, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pub_id, url, source, status, file_path, error))
        self.conn.commit()
```

### Usage Example
```python
# Initialize registry
registry = GEORegistry()

# Register GEO dataset
registry.register_geo_dataset("GSE12345", {
    "title": "Study of X",
    "organism": "Homo sapiens",
    "platform": "GPL570",
    "sample_count": 100
})

# Register publications with URLs
pub_id = registry.register_publication("12345", {
    "title": "Original paper",
    "authors": ["Smith J", "Doe J"],
    "journal": "Nature"
}, urls=[
    {"url": "https://pmc.../", "source": "pmc", "priority": 1},
    {"url": "https://unpaywall.../", "source": "unpaywall", "priority": 2}
])

# Link them
registry.link_geo_to_publication("GSE12345", "12345", "original")

# Get EVERYTHING in one call!
data = registry.get_complete_geo_data("GSE12345")
# Returns: {geo: {...}, papers: {original: [...], citing: [...]}}

# Get URLs for retry
urls = registry.get_urls_for_retry("12345")
```

### Pros
✅ **Single File**: Easy deployment, backup, portability
✅ **No Setup**: SQLite built into Python
✅ **ACID**: Full transaction support
✅ **Fast**: Indexed queries, compiled C code
✅ **JSON Support**: Store complex objects
✅ **Simple**: Straightforward SQL queries
✅ **Size**: Can handle GBs of data
✅ **Concurrent Reads**: Multiple readers OK
✅ **Tooling**: DB Browser for SQLite, many GUIs
✅ **Low Overhead**: Minimal resource usage

### Cons
❌ **Single Writer**: Only one write at a time
❌ **No Network**: Can't query from remote
❌ **Limited Concurrency**: Not for high-traffic writes
❌ **No Clustering**: Single-server only

### Implementation Complexity: **MEDIUM**
### Best For: **Current use case** - moderate scale, file-based deployment

---

## Solution 5: In-Memory Cache + File Store

### Architecture
```python
# In-Memory Cache (Python dict/dataclass)
@dataclass
class GEONode:
    geo_id: str
    metadata: Dict
    original_papers: List[Publication]
    citing_papers: List[Publication]
    _index: Dict[str, Publication]  # pmid → Publication

@dataclass
class Publication:
    pmid: str
    metadata: Dict
    urls: List[URLSource]
    download_status: DownloadStatus
    file_path: Optional[Path]

# Global registry
geo_registry: Dict[str, GEONode] = {}

# Persistence (JSON files)
data/registry/{geo_id}.json
```

### Pros
✅ **Fastest**: Pure memory access, no I/O
✅ **Simple**: Just Python objects
✅ **Type Safety**: With dataclasses/Pydantic
✅ **Easy Debugging**: Can inspect in debugger

### Cons
❌ **No Persistence**: Lost on restart (unless saved)
❌ **Memory Usage**: Entire dataset in RAM
❌ **No Concurrency**: Race conditions possible
❌ **Manual Management**: Must handle save/load

### Implementation Complexity: **LOW**
### Best For: Prototyping, temporary caching

---

## Recommendation Matrix

| Solution | Complexity | Performance | Scalability | Persistence | Recommended Use |
|----------|-----------|-------------|-------------|-------------|-----------------|
| **Graph DB** | HIGH | Good | Excellent | Excellent | Large-scale citation analysis |
| **JSON Files** | LOW | Poor | Poor | Good | Prototyping, small datasets |
| **Redis+PG** | HIGH | Excellent | Excellent | Excellent | High-traffic production |
| **SQLite+JSON** | **MEDIUM** | **Very Good** | **Good** | **Excellent** | **CURRENT SYSTEM** ✅ |
| **In-Memory** | LOW | Excellent | Poor | Poor | Temporary caching |

---

## Final Recommendation: **Solution 4 (SQLite + JSON Hybrid)**

### Why?
1. ✅ **Right Complexity**: Not too simple, not too complex
2. ✅ **No Infrastructure**: Single file, no services to manage
3. ✅ **Fast Enough**: Sub-10ms queries for typical workloads
4. ✅ **Scalable Enough**: Can handle 10,000+ GEO IDs easily
5. ✅ **ACID Guarantees**: Safe concurrent access
6. ✅ **Portable**: Can move/backup entire database
7. ✅ **Easy Debugging**: Many SQL tools available
8. ✅ **JSON Flexibility**: Store complex metadata without schema changes
9. ✅ **Future-Proof**: Can migrate to PostgreSQL if needed

### Implementation Plan

**Phase 1**: Core Schema (1-2 hours)
- Create GEORegistry class
- Implement basic CRUD operations
- Add indexes for fast lookups

**Phase 2**: Integration (2-3 hours)
- Update enrichment endpoint to use registry
- Store all URLs for retry capability
- Track download history

**Phase 3**: Frontend Support (1 hour)
- Add API endpoint: `GET /api/geo/{geo_id}/complete`
- Returns everything frontend needs in one call

**Phase 4**: Migration (1 hour)
- Migrate existing metadata.json files to SQLite
- Verify data integrity

**Total Effort**: ~6 hours

### Alternative for Future Scale
If traffic grows significantly (>1000 req/s), migrate to:
- **Redis** for hot cache (most accessed GEO IDs)
- **PostgreSQL** for persistent storage
- Keep SQLite schema → PostgreSQL migration is straightforward

---

## Code Example: Complete Implementation

See `/omics_oracle_v2/lib/registry/geo_registry.py` for full implementation.

Usage in enrichment endpoint:
```python
# Initialize once at startup
registry = GEORegistry()

@router.post("/enrich-fulltext")
async def enrich_fulltext(datasets):
    for dataset in datasets:
        # Register GEO
        registry.register_geo_dataset(dataset.geo_id, dataset.dict())

        # Register papers with URLs
        for pub in publications:
            registry.register_publication(
                pub.pmid,
                pub.dict(),
                url_result.all_urls
            )
            registry.link_geo_to_publication(
                dataset.geo_id,
                pub.pmid,
                "original" if pub in original_papers else "citing"
            )

        # Record download attempts
        for result in download_results:
            registry.record_download_attempt(
                pub.pmid, result.url, result.source,
                "success" if result.success else "failed",
                result.pdf_path, result.error
            )

# Frontend gets everything in one call!
@router.get("/api/geo/{geo_id}/complete")
async def get_geo_complete(geo_id: str):
    return registry.get_complete_geo_data(geo_id)
```

---

## Conclusion

**Start with Solution 4 (SQLite + JSON)** for immediate needs:
- Fast to implement
- Solves all current problems
- Easy to maintain
- Can scale to 10K+ GEO IDs

**Migrate to Solution 3 (Redis + PostgreSQL)** if/when:
- Traffic exceeds 1000 req/s
- Need multi-region deployment
- Dataset grows beyond 100K GEO IDs
- Need advanced analytics/reporting

**Consider Solution 1 (Graph DB)** only if:
- Citation network analysis becomes core feature
- Need complex graph algorithms
- Have dedicated DevOps resources
