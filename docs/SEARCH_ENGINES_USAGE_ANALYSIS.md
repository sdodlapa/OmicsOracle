# Search Engines Module Usage Analysis

**Date:** October 15, 2025  
**Module:** `omics_oracle_v2/lib/search_engines/`  
**Status:** ✅ **ACTIVELY USED IN PRODUCTION**

---

## 📊 Executive Summary

**YES, `search_engines/` is heavily used!** It's a **core production module** with 40+ import statements across the codebase.

**Key Finding:** `search_engines/` provides the foundational **data models** and **client interfaces** used by:
- Production API routes
- Search orchestration layer
- Citation discovery pipelines
- URL collection pipelines

---

## 📁 Module Structure

```
search_engines/
├── citations/              (Citation search clients & models)
│   ├── __init__.py
│   ├── base.py            ← BasePublicationClient interface
│   ├── config.py          ← PubMedConfig, OpenAlexConfig
│   ├── models.py          ← Publication, PublicationSource (core models)
│   ├── openalex.py        ← OpenAlexClient implementation
│   └── pubmed.py          ← PubMedClient implementation
│
└── geo/                   (GEO database search)
    ├── __init__.py
    ├── client.py          ← GEOClient
    ├── models.py          ← GEOSeriesMetadata (core model)
    ├── query_builder.py   ← GEOQueryBuilder
    └── utils.py
```

**Total:** 11 Python files

---

## 🎯 Primary Usage Patterns

### **1. Data Models (Most Critical)**

The **`Publication`** and **`GEOSeriesMetadata`** models from search_engines are used **everywhere**:

```python
# Core data models used across entire codebase
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication,           # Citation/paper representation
    PublicationSource      # Source tracking (PubMed, OpenAlex, etc.)
)

from omics_oracle_v2.lib.search_engines.geo.models import (
    GEOSeriesMetadata      # GEO dataset metadata
)
```

**Used by:**
- ✅ `search_orchestration/` - 3 files (models.py, orchestrator.py, config.py)
- ✅ `pipelines/citation_discovery/` - 8+ files (all major components)
- ✅ `pipelines/citation_download/` - download_manager.py
- ✅ `pipelines/url_collection/` - manager.py, institutional_access.py
- ✅ `api/routes/agents.py` - Production API

**Why Critical:** These are the **canonical data models** for publications and GEO datasets throughout OmicsOracle.

---

### **2. Client Implementations**

#### **A. Used by SearchOrchestrator (Production)**

```python
# omics_oracle_v2/lib/search_orchestration/orchestrator.py

from omics_oracle_v2.lib.search_engines.citations.openalex import (
    OpenAlexClient, 
    OpenAlexConfig
)
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.search_engines.geo import GEOClient
from omics_oracle_v2.lib.search_engines.geo.query_builder import GEOQueryBuilder
```

**SearchOrchestrator** (used by production API) directly instantiates:
- `PubMedClient` - Search PubMed for citations
- `OpenAlexClient` - Search OpenAlex for citations
- `GEOClient` - Search GEO database

**Production Flow:**
```
API Request 
  → SearchOrchestrator (search_orchestration/orchestrator.py)
      → PubMedClient (search_engines/citations/pubmed.py)
      → OpenAlexClient (search_engines/citations/openalex.py)
      → GEOClient (search_engines/geo/client.py)
```

#### **B. Used Directly in API**

```python
# omics_oracle_v2/api/routes/agents.py (Line 457)

from omics_oracle_v2.lib.search_engines.citations.pubmed import (
    PubMedClient, 
    PubMedConfig
)
```

**Direct usage in `/agents/download_pdf` endpoint** for citation lookup.

---

### **3. Base Classes & Configuration**

#### **BasePublicationClient Interface**

```python
# Used by pipelines/citation_discovery/clients/

from omics_oracle_v2.lib.search_engines.citations.base import (
    BasePublicationClient,
    FetchError,
    SearchError
)
```

**Used by:**
- `pipelines/citation_discovery/clients/pubmed.py` - Extends BasePublicationClient
- `pipelines/citation_discovery/clients/openalex.py` - Extends BasePublicationClient
- `pipelines/url_collection/sources/oa_sources/biorxiv_client.py` - Extends BasePublicationClient

**Why Important:** Provides standardized interface for all citation clients (both in search_engines and pipelines).

#### **Configuration Classes**

```python
from omics_oracle_v2.lib.search_engines.citations.config import PubMedConfig

# Used by:
# - search_orchestration/config.py
# - pipelines/citation_discovery/clients/pubmed.py
# - api/routes/agents.py
```

---

## 📊 Usage Statistics

### **Import Count by Module:**

| Importing Module | Import Count | Usage Type |
|------------------|--------------|------------|
| **search_orchestration/** | 9 | Models, Clients, Config |
| **pipelines/citation_discovery/** | 20+ | Models, Base classes, Clients |
| **pipelines/url_collection/** | 4 | Models, Base classes |
| **pipelines/citation_download/** | 1 | Models |
| **api/routes/agents.py** | 2 | Models, Clients |
| **extras/** | 1 | Models |
| **scripts/** | 1 | Models |
| **TOTAL** | **40+** | Production + Pipelines |

---

## 🔍 Detailed Usage by Component

### **1. Production API (api/routes/agents.py)**

**Line 25:**
```python
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
```
- Used for type hints in search response formatting
- Production endpoint data models

**Line 457:**
```python
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient, PubMedConfig
```
- Direct PubMed client usage in `/agents/download_pdf` endpoint
- Fetches citation details for PDF download

---

### **2. SearchOrchestrator (CRITICAL - Production Component)**

**File:** `search_orchestration/orchestrator.py`

**Imports:**
```python
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.search_engines.geo import GEOClient
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.search_engines.geo.query_builder import GEOQueryBuilder
```

**What it does:**
- Orchestrates parallel searches across PubMed, OpenAlex, GEO
- Returns unified search results
- **Used by production API** (`/agents/search` endpoint)

**Flow:**
```python
class SearchOrchestrator:
    def __init__(self):
        self.pubmed = PubMedClient()
        self.openalex = OpenAlexClient()
        self.geo = GEOClient()
    
    async def search(query):
        # Run searches in parallel
        pubmed_results = await self.pubmed.search(query)
        openalex_results = await self.openalex.search(query)
        geo_results = await self.geo.search(query)
        
        # Return unified SearchResult
```

---

### **3. Citation Discovery Pipeline**

**File:** `pipelines/citation_discovery/geo_discovery.py`

**Imports:**
```python
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
```

**What it does:**
- Discovers citations for GEO datasets
- Uses Publication model to represent found papers
- Uses GEOSeriesMetadata for dataset information

**Also uses search_engines models in:**
- `deduplication.py` - Deduplicates Publication objects
- `relevance_scoring.py` - Scores Publication relevance
- `quality_validation.py` - Validates Publication data
- `cache.py` - Caches Publication objects

---

### **4. Pipeline Clients (The Duplication Issue)**

**Critical Finding:** `pipelines/citation_discovery/clients/` **EXTENDS** search_engines base classes:

```python
# pipelines/citation_discovery/clients/pubmed.py

from omics_oracle_v2.lib.search_engines.citations.base import (
    BasePublicationClient,  # ← Inherits from search_engines
    FetchError,
    SearchError
)
from omics_oracle_v2.lib.search_engines.citations.config import PubMedConfig
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication,
    PublicationSource
)

class PubMedClient(BasePublicationClient):  # ← Extends base class
    """Enhanced PubMed client with additional features"""
```

**Same pattern for:**
- `pipelines/citation_discovery/clients/openalex.py`
- `pipelines/citation_discovery/clients/crossref.py`
- `pipelines/citation_discovery/clients/europepmc.py`

**Dependency relationship:**
```
search_engines/citations/
  ├── base.py (BasePublicationClient)
  ├── models.py (Publication, PublicationSource)
  └── config.py (PubMedConfig)
         ↑
         │ (inherits/imports from)
         │
pipelines/citation_discovery/clients/
  ├── pubmed.py (extends BasePublicationClient)
  ├── openalex.py (extends BasePublicationClient)
  ├── crossref.py (uses Publication model)
  └── europepmc.py (uses Publication model)
```

---

## 🎯 Why Search Engines is Critical

### **1. Canonical Data Models**
- `Publication` - Used in 20+ files across codebase
- `GEOSeriesMetadata` - Used in 10+ files
- These are the **single source of truth** for data structure

### **2. Base Abstractions**
- `BasePublicationClient` - Interface contract for all citation clients
- Ensures consistent API across different search sources

### **3. Production Client Implementations**
- `PubMedClient` - Used by SearchOrchestrator (production)
- `OpenAlexClient` - Used by SearchOrchestrator (production)
- `GEOClient` - Used by SearchOrchestrator (production)

### **4. Configuration Objects**
- `PubMedConfig`, `OpenAlexConfig` - Shared across multiple modules
- Centralized configuration management

---

## 🔄 Duplication Analysis: search_engines vs pipelines

### **Current State:**

**search_engines/citations/** (Original)
- Purpose: **Core client implementations + base classes**
- Contains: PubMedClient, OpenAlexClient, BasePublicationClient
- Used by: SearchOrchestrator (production)
- Status: ✅ **CANONICAL LOCATION**

**pipelines/citation_discovery/clients/** (Extended)
- Purpose: **Enhanced clients with pipeline-specific features**
- Contains: Same clients + 4 extras (CrossRef, EuropePMC, OpenCitations, SemanticScholar)
- Used by: GEOCitationDiscovery pipeline
- Status: ⚠️ **EXTENDS search_engines base classes**

### **Key Insight:**

**These are NOT complete duplicates!**

```python
# search_engines/citations/pubmed.py (397 lines)
# - Basic PubMed search functionality
# - Used by SearchOrchestrator for simple searches

# pipelines/citation_discovery/clients/pubmed.py (461 lines - 64 MORE)
# - EXTENDS BasePublicationClient from search_engines
# - Additional pipeline-specific features
# - Used by citation discovery for comprehensive searches
```

**Relationship:**
```
search_engines/citations/
  ├── Base implementations (simple, fast)
  └── Used by: SearchOrchestrator, API
         ↑
         │ (base class dependency)
         │
pipelines/citation_discovery/clients/
  ├── Enhanced implementations (feature-rich)
  ├── PLUS 4 extra sources
  └── Used by: GEOCitationDiscovery
```

---

## ✅ Conclusion

### **Is search_engines used?**
**YES! Heavily used across the entire codebase.**

### **Usage Summary:**

1. **Data Models (CRITICAL)**
   - Publication, PublicationSource, GEOSeriesMetadata
   - Used in 30+ files
   - Single source of truth

2. **Production Clients (ACTIVE)**
   - PubMedClient, OpenAlexClient, GEOClient
   - Used by SearchOrchestrator (production API)
   - Direct API usage

3. **Base Classes (FOUNDATION)**
   - BasePublicationClient
   - Extended by pipelines clients
   - Provides interface contract

4. **Configuration (SHARED)**
   - PubMedConfig, OpenAlexConfig
   - Used across search_orchestration and pipelines

### **Architecture:**

```
API Layer
  ↓
SearchOrchestrator (search_orchestration/)
  ↓
search_engines/ ← CORE MODULE (canonical clients + models)
  ↓
  └→ Extended by pipelines/citation_discovery/clients/
       (enhanced versions + extra sources)
```

### **Recommendation:**

**DO NOT MERGE OR ARCHIVE search_engines/**

**Reasons:**
1. ✅ Core production module (used by API)
2. ✅ Provides canonical data models
3. ✅ Base classes for all clients
4. ✅ 40+ active imports
5. ✅ Foundation for pipelines clients

**Instead:**
- Keep search_engines as the **canonical source**
- Keep pipelines/citation_discovery/clients as **enhanced versions**
- This is **intentional architecture**, not duplication
- Separation of concerns:
  - search_engines = simple, fast, production
  - pipelines/clients = comprehensive, feature-rich, batch processing

---

## 📊 Import Map

```
Production Flow:
API → SearchOrchestrator → search_engines/citations/{pubmed,openalex}
                        → search_engines/geo/client

Pipeline Flow:
GEOCitationDiscovery → pipelines/citation_discovery/clients/{pubmed,openalex,...}
                          ↓ (extends)
                    search_engines/citations/base.BasePublicationClient
                    search_engines/citations/models.Publication
```

---

**Status:** search_engines is a **CORE, ACTIVE, CRITICAL** production module.  
**Action:** No changes needed - keep as-is.

---

*Generated: October 15, 2025*  
*Module: search_engines/*  
*Import Count: 40+*  
*Production Usage: YES ✅*
