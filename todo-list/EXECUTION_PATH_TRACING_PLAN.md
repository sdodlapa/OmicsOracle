# Execution Path Tracing & Profiling System - Future Implementation

**Status:** 📋 Planned for Post-Production  
**Priority:** P2 (After core functionality is production-ready)  
**Estimated Effort:** 1-2 weeks  
**Created:** October 16, 2025  

---

## 📌 Context

This plan was developed during the performance optimization phase (Oct 2025) as a follow-up to the DFS/BFS execution tree analysis. The idea is to build an **automated profiling and tracing system** that monitors real execution paths through the application to identify:

1. **Frequently used code** (hot paths)
2. **Execution time profiling** (bottlenecks)
3. **Error detection** (failure modes)
4. **Unused code** (dead branches)

---

## 🎯 Prerequisites (Must Complete First)

Before implementing this tracing system, ensure the following core functionality is production-ready:

### Critical Features
- [x] ~~Dashboard bugs fixed~~ (Oct 2025)
- [x] ~~Auto-discovery implemented~~ (Oct 2025)
- [x] ~~Performance optimizations applied~~ (Oct 2025)
- [ ] **Citation counts displaying correctly**
- [ ] **PDF downloads working reliably**
- [ ] **AI analysis functioning properly**
- [ ] System stable in production environment
- [ ] Error handling mature and tested

### Why Wait?
- Tracing adds overhead - need stable baseline first
- Profiling data is only valuable when system works correctly
- Focus effort on user-facing features before internal tooling

---

## 🔬 What This System Will Do

### 1. Execution Path Tracking
Track every request as it flows through the system:

```
User Request: "breast cancer RNA-seq"
├─ T+0ms:    dashboard_v2.html::performSearch()
├─ T+5ms:    POST /api/search
├─ T+10ms:   SearchService.execute_search()
├─ T+15ms:   SearchOrchestrator.search()
├─ T+20ms:   [PARALLEL]
│            ├─ _search_geo() → 1209 results (1.5s)
│            ├─ _search_pubmed() → 555 results (2.0s)
│            └─ _search_openalex() → 284 results (2.5s)
├─ T+2510ms: _build_dataset_responses() [50 datasets]
│            ├─ GEOCache.get() × 50 (parallel)
│            │  ├─ 46 Redis hits (0.5ms each)
│            │  ├─ 3 DB hits (12ms each)
│            │  └─ 1 auto-discovery (8500ms) ← SLOW PATH
├─ T+10560ms: Return SearchResponse
└─ T+10565ms: Dashboard displays results
```

### 2. Frequency Analysis
Identify which paths are actually used:

```
Path Frequency Report:
═══════════════════════════════════════════════════════════
Search Paths (1000 requests):
  ├─ Cached GEO results:              92% (920 requests)  ✅ FAST
  ├─ Uncached GEO + DB hit:           6%  (60 requests)   ⚡ WARM
  └─ Uncached GEO + auto-discovery:   2%  (20 requests)   🐌 SLOW

Discovery Paths (20 auto-discovery requests):
  ├─ OpenAlex + Semantic Scholar:     100% (20 requests)
  ├─ Europe PMC:                      85%  (17 requests)
  ├─ OpenCitations:                   45%  (9 requests)
  └─ PubMed citations:                30%  (6 requests)

Unused Features (0 requests):
  ⚠️  Manual discovery button:        0%  (feature redundant?)
  ⚠️  LibGen fallback:                0%  (never triggered)
  ⚠️  Organism filter UI:             0%  (users don't use it)
```

### 3. Performance Profiling
Measure actual time spent in each component:

```
Performance Breakdown (avg of 1000 requests):
═══════════════════════════════════════════════════════════
Total Request Time: 243ms average

Top 10 Time Consumers:
1. Auto-discovery (when triggered):   8500ms  (35% of slow paths)
2. GEOClient.search():                 87ms    (36% of all requests)
3. _build_dataset_responses():         68ms    (28% of all requests)
4. PubMed search:                      45ms    (18% when enabled)
5. OpenAlex search:                    32ms    (13% when enabled)
6. Database JOIN queries:              20ms    (8% of all requests) ← POST-OPTIMIZATION
7. Redis cache lookups:                0.5ms   (0.2% of all requests) ✅
8. Request validation:                 2ms     (0.8% of all requests)
9. Response formatting:                3ms     (1.2% of all requests)
10. Logging overhead:                  1ms     (0.4% of all requests)

Optimization Opportunities:
🎯 GEOClient.search() - Consider caching search results (36% impact)
🎯 Auto-discovery - Already optimized, but high impact when triggered
✅ Redis cache - Already optimal
```

### 4. Error Detection
Identify failure patterns:

```
Error Hotspot Analysis (100 failures in 1000 requests):
═══════════════════════════════════════════════════════════
Error Rate by Component:
1. OpenAlexClient.get_citing_papers():    12% error rate (rate limit 429)
   ├─ Rate limit exceeded:    10 failures
   ├─ Timeout:                2 failures
   └─ 🔧 FIX: Implement exponential backoff

2. SemanticScholarClient:                 8% error rate (API instability)
   ├─ Service unavailable:    6 failures
   ├─ Invalid response:       2 failures
   └─ 🔧 FIX: Add circuit breaker pattern

3. GEOClient.get_metadata():              3.2% error rate (NCBI timeouts)
   ├─ NCBI timeout:           3 failures
   ├─ Invalid XML:            1 failure
   └─ 🔧 FIX: Increase timeout or add retry

4. UnifiedDB.get_complete_geo_data():     0.5% error rate (rare)
   ├─ Database locked:        0 failures
   └─ ✅ STABLE

Error Patterns by Query Type:
├─ Organism="Drosophila":     15% failure rate ← INVESTIGATE
├─ Organism="Homo sapiens":   2% failure rate  ✅
└─ Long queries (>50 chars):  8% failure rate  ← INVESTIGATE
```

---

## 🏗️ Implementation Architecture

### Component 1: ExecutionPathTracer

```python
"""
omics_oracle_v2/monitoring/execution_tracer.py

Lightweight tracing system for execution path analysis.
"""

import time
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import sqlite3

class ExecutionPathTracer:
    """
    Trace execution paths through the system for analysis.
    
    Features:
    - Minimal overhead (<1% performance impact)
    - Async-safe (thread-local storage)
    - Hierarchical path tracking
    - Performance metrics per node
    - Error tracking
    - Database persistence
    """
    
    def __init__(self, db_path: str = "data/analytics/execution_traces.db"):
        self.db_path = db_path
        self.current_path = []  # Thread-local in production
        self.paths = []
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0,
            'error_types': defaultdict(int)
        })
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for persistence."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                full_path TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                status TEXT NOT NULL,  -- 'success', 'error'
                error_type TEXT,
                metadata JSON
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS node_metrics (
                node_name TEXT PRIMARY KEY,
                total_calls INTEGER DEFAULT 0,
                total_time_ms REAL DEFAULT 0,
                avg_time_ms REAL DEFAULT 0,
                min_time_ms REAL DEFAULT 0,
                max_time_ms REAL DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    @contextmanager
    def trace_node(self, node_name: str, metadata: Dict[str, Any] = None):
        """
        Trace execution through a node.
        
        Usage:
            with tracer.trace_node('SearchService.execute_search', {'query': 'cancer'}):
                result = await execute_search(...)
        """
        start_time = time.time()
        self.current_path.append(node_name)
        error_occurred = None
        
        try:
            yield
            # Success path
        except Exception as e:
            # Error path
            error_occurred = e
            raise
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            
            if error_occurred:
                self._record_error(node_name, elapsed_ms, error_occurred)
            else:
                self._record_success(node_name, elapsed_ms, metadata)
            
            self.current_path.pop()
    
    def _record_success(self, node: str, elapsed_ms: float, metadata: Dict):
        """Record successful execution."""
        # Update in-memory metrics
        m = self.metrics[node]
        m['count'] += 1
        m['total_time'] += elapsed_ms
        m['avg_time'] = m['total_time'] / m['count']
        m['min_time'] = min(m['min_time'], elapsed_ms)
        m['max_time'] = max(m['max_time'], elapsed_ms)
        
        # Record full path
        self._persist_path(
            full_path=' → '.join(self.current_path),
            duration_ms=elapsed_ms,
            status='success',
            error_type=None,
            metadata=metadata
        )
    
    def _record_error(self, node: str, elapsed_ms: float, error: Exception):
        """Record failed execution."""
        m = self.metrics[node]
        m['errors'] += 1
        m['error_types'][type(error).__name__] += 1
        
        self._persist_path(
            full_path=' → '.join(self.current_path),
            duration_ms=elapsed_ms,
            status='error',
            error_type=type(error).__name__,
            metadata={'error': str(error)}
        )
    
    def _persist_path(self, full_path: str, duration_ms: float, 
                     status: str, error_type: Optional[str], metadata: Dict):
        """Persist path to database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO execution_paths 
            (timestamp, full_path, duration_ms, status, error_type, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            full_path,
            duration_ms,
            status,
            error_type,
            json.dumps(metadata) if metadata else None
        ))
        conn.commit()
        conn.close()
    
    def get_hot_paths(self, top_n: int = 10) -> List[Dict]:
        """Get most frequently executed paths."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT full_path, COUNT(*) as frequency, AVG(duration_ms) as avg_time
            FROM execution_paths
            WHERE status = 'success'
            GROUP BY full_path
            ORDER BY frequency DESC
            LIMIT ?
        """, (top_n,))
        results = [
            {'path': row[0], 'frequency': row[1], 'avg_time_ms': row[2]}
            for row in cursor
        ]
        conn.close()
        return results
    
    def get_slow_paths(self, top_n: int = 10) -> List[Dict]:
        """Get slowest execution paths."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT full_path, AVG(duration_ms) as avg_time, COUNT(*) as count
            FROM execution_paths
            WHERE status = 'success'
            GROUP BY full_path
            ORDER BY avg_time DESC
            LIMIT ?
        """, (top_n,))
        results = [
            {'path': row[0], 'avg_time_ms': row[1], 'count': row[2]}
            for row in cursor
        ]
        conn.close()
        return results
    
    def get_error_prone_paths(self, top_n: int = 10) -> List[Dict]:
        """Get paths with highest error rates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT 
                full_path,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                COUNT(*) as total,
                ROUND(100.0 * SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
            FROM execution_paths
            GROUP BY full_path
            HAVING errors > 0
            ORDER BY error_rate DESC
            LIMIT ?
        """, (top_n,))
        results = [
            {
                'path': row[0], 
                'errors': row[1], 
                'total': row[2], 
                'error_rate_pct': row[3]
            }
            for row in cursor
        ]
        conn.close()
        return results
    
    def get_unused_nodes(self, all_nodes: List[str]) -> List[str]:
        """Identify nodes that were never executed."""
        executed_nodes = set(self.metrics.keys())
        return [node for node in all_nodes if node not in executed_nodes]
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        return {
            'summary': {
                'total_paths_recorded': len(self.paths),
                'unique_paths': len(set(p['path'] for p in self.paths)),
                'total_nodes_tracked': len(self.metrics),
            },
            'hot_paths': self.get_hot_paths(10),
            'slow_paths': self.get_slow_paths(10),
            'error_prone_paths': self.get_error_prone_paths(10),
            'metrics_by_node': dict(self.metrics),
        }


# Global tracer instance (singleton)
_tracer = None

def get_tracer() -> ExecutionPathTracer:
    """Get global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = ExecutionPathTracer()
    return _tracer
```

### Component 2: Instrumentation Points

Add tracing to critical integration points:

```python
# In omics_oracle_v2/services/search_service.py

from omics_oracle_v2.monitoring.execution_tracer import get_tracer

class SearchService:
    def __init__(self):
        # ... existing code ...
        self.tracer = get_tracer()
    
    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """Execute search with tracing."""
        with self.tracer.trace_node(
            'SearchService.execute_search',
            metadata={'query': request.search_terms, 'max_results': request.max_results}
        ):
            # Build search configuration
            with self.tracer.trace_node('SearchService._build_search_config'):
                config = self._build_search_config(request, search_logs)
            
            # Execute search pipeline
            with self.tracer.trace_node('SearchOrchestrator.search'):
                search_result = await pipeline.search(...)
            
            # Process and rank datasets
            with self.tracer.trace_node('SearchService._rank_datasets'):
                ranked_datasets = self._rank_datasets(...)
            
            # Convert to response format
            with self.tracer.trace_node(
                'SearchService._build_dataset_responses',
                metadata={'dataset_count': len(ranked_datasets)}
            ):
                datasets = await self._build_dataset_responses(ranked_datasets)
            
            return SearchResponse(...)
```

### Component 3: Random Path Executor

```python
"""
omics_oracle_v2/monitoring/path_executor.py

Execute random paths through the system for testing and profiling.
"""

import random
import asyncio
from typing import List, Dict
from omics_oracle_v2.monitoring.execution_tracer import get_tracer
from omics_oracle_v2.services.search_service import SearchService
from omics_oracle_v2.api.models.requests import SearchRequest

class PathExecutor:
    """Execute random paths through system for comprehensive testing."""
    
    def __init__(self):
        self.tracer = get_tracer()
        self.search_service = SearchService()
        
        # Test data with different characteristics
        self.test_queries = {
            'common': [
                'breast cancer RNA-seq',
                'COVID-19 genomics',
                'CRISPR gene editing',
                'single cell RNA-seq',
            ],
            'organism_specific': [
                'Homo sapiens microarray',
                'Mus musculus RNA-seq',
                'Drosophila melanogaster',
                'Arabidopsis thaliana',
            ],
            'edge_cases': [
                '',  # Empty query
                'a' * 100,  # Very long query
                '!@#$%^&*()',  # Special characters
                'GSE123456',  # Direct GEO ID
            ],
        }
    
    async def execute_random_paths(self, num_iterations: int = 100):
        """
        Execute random paths through the system.
        
        This simulates real-world usage patterns to identify:
        - Most frequently used code paths
        - Performance bottlenecks
        - Error-prone paths
        - Unused code branches
        """
        
        print(f"Executing {num_iterations} random paths through system...")
        
        for i in range(num_iterations):
            # Select strategy with weighted probability
            strategy = random.choices(
                [
                    self._test_common_query,
                    self._test_organism_filter,
                    self._test_edge_case,
                    self._test_large_result_set,
                ],
                weights=[0.6, 0.2, 0.1, 0.1]  # Realistic usage distribution
            )[0]
            
            try:
                await strategy()
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{num_iterations} paths executed")
            except Exception as e:
                print(f"  ✗ Path {i + 1} failed: {e}")
        
        print("\n✅ Path execution complete!")
        print("Generating analysis report...\n")
        
        return self.tracer.generate_report()
    
    async def _test_common_query(self):
        """Test most common query pattern."""
        query = random.choice(self.test_queries['common'])
        request = SearchRequest(
            search_terms=query,
            max_results=50
        )
        await self.search_service.execute_search(request)
    
    async def _test_organism_filter(self):
        """Test organism filter path."""
        query = random.choice(self.test_queries['organism_specific'])
        request = SearchRequest(
            search_terms=query,
            max_results=50,
            filters={'organism': 'Homo sapiens'}
        )
        await self.search_service.execute_search(request)
    
    async def _test_edge_case(self):
        """Test edge case handling."""
        query = random.choice(self.test_queries['edge_cases'])
        request = SearchRequest(
            search_terms=query,
            max_results=10
        )
        await self.search_service.execute_search(request)
    
    async def _test_large_result_set(self):
        """Test large result set handling."""
        request = SearchRequest(
            search_terms='RNA-seq',  # Broad query
            max_results=200  # Large result set
        )
        await self.search_service.execute_search(request)


# CLI script for running path execution
async def main():
    executor = PathExecutor()
    report = await executor.execute_random_paths(num_iterations=100)
    
    print("=" * 80)
    print("EXECUTION PATH ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nTotal paths recorded: {report['summary']['total_paths_recorded']}")
    print(f"Unique paths: {report['summary']['unique_paths']}")
    print(f"Nodes tracked: {report['summary']['total_nodes_tracked']}")
    
    print("\n" + "=" * 80)
    print("TOP 10 HOT PATHS (Most Frequently Used)")
    print("=" * 80)
    for i, path in enumerate(report['hot_paths'], 1):
        print(f"{i}. {path['path']}")
        print(f"   Frequency: {path['frequency']} | Avg Time: {path['avg_time_ms']:.2f}ms")
    
    print("\n" + "=" * 80)
    print("TOP 10 SLOW PATHS (Performance Bottlenecks)")
    print("=" * 80)
    for i, path in enumerate(report['slow_paths'], 1):
        print(f"{i}. {path['path']}")
        print(f"   Avg Time: {path['avg_time_ms']:.2f}ms | Count: {path['count']}")
    
    print("\n" + "=" * 80)
    print("TOP 10 ERROR-PRONE PATHS")
    print("=" * 80)
    for i, path in enumerate(report['error_prone_paths'], 1):
        print(f"{i}. {path['path']}")
        print(f"   Error Rate: {path['error_rate_pct']}% ({path['errors']}/{path['total']})")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Visualization Dashboard

Create a simple dashboard using Streamlit:

```python
"""
omics_oracle_v2/monitoring/dashboard.py

Interactive dashboard for execution path analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from omics_oracle_v2.monitoring.execution_tracer import get_tracer

def main():
    st.set_page_config(page_title="OmicsOracle Execution Analysis", layout="wide")
    
    st.title("🔬 OmicsOracle Execution Path Analysis")
    st.markdown("Real-time profiling and path analysis dashboard")
    
    tracer = get_tracer()
    report = tracer.generate_report()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Paths", report['summary']['total_paths_recorded'])
    with col2:
        st.metric("Unique Paths", report['summary']['unique_paths'])
    with col3:
        st.metric("Nodes Tracked", report['summary']['total_nodes_tracked'])
    with col4:
        # Calculate average error rate
        total_errors = sum(p['errors'] for p in report['error_prone_paths'])
        total_requests = sum(p['total'] for p in report['error_prone_paths'])
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        st.metric("Error Rate", f"{error_rate:.2f}%")
    
    # Hot paths visualization
    st.header("🔥 Hot Paths (Most Frequently Used)")
    hot_df = pd.DataFrame(report['hot_paths'])
    if not hot_df.empty:
        fig = px.bar(hot_df, x='frequency', y='path', orientation='h',
                     title='Path Frequency Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance breakdown
    st.header("⏱️ Performance Breakdown")
    slow_df = pd.DataFrame(report['slow_paths'])
    if not slow_df.empty:
        fig = px.bar(slow_df, x='avg_time_ms', y='path', orientation='h',
                     title='Average Execution Time by Path',
                     color='avg_time_ms',
                     color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    
    # Error analysis
    st.header("❌ Error Analysis")
    error_df = pd.DataFrame(report['error_prone_paths'])
    if not error_df.empty:
        fig = px.scatter(error_df, x='total', y='error_rate_pct', 
                         size='errors', hover_data=['path'],
                         title='Error Rate vs Total Requests',
                         labels={'error_rate_pct': 'Error Rate (%)', 'total': 'Total Requests'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Node-level metrics
    st.header("📈 Node-Level Metrics")
    node_metrics = report['metrics_by_node']
    metrics_data = []
    for node, metrics in node_metrics.items():
        metrics_data.append({
            'Node': node,
            'Calls': metrics['count'],
            'Avg Time (ms)': metrics['avg_time'],
            'Min Time (ms)': metrics['min_time'],
            'Max Time (ms)': metrics['max_time'],
            'Errors': metrics['errors'],
            'Error Rate (%)': (metrics['errors'] / metrics['count'] * 100) if metrics['count'] > 0 else 0
        })
    
    metrics_df = pd.DataFrame(metrics_data)
    if not metrics_df.empty:
        st.dataframe(metrics_df.sort_values('Avg Time (ms)', ascending=False), 
                     use_container_width=True)

if __name__ == "__main__":
    main()
```

**To run:**
```bash
streamlit run omics_oracle_v2/monitoring/dashboard.py
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation (2-3 days)
- [ ] Create `omics_oracle_v2/monitoring/` directory
- [ ] Implement `ExecutionPathTracer` class
- [ ] Set up SQLite database schema
- [ ] Write unit tests for tracer
- [ ] Document API and usage

### Phase 2: Instrumentation (2-3 days)
- [ ] Add tracing to 5 critical integration points:
  - [ ] `dashboard_v2.html` → API endpoints
  - [ ] `routes/agents.py` → SearchService
  - [ ] `SearchService` → SearchOrchestrator
  - [ ] `SearchOrchestrator` → Data sources (GEO, PubMed, OpenAlex)
  - [ ] `_build_dataset_responses` → GEOCache → Auto-discovery
- [ ] Test instrumentation overhead (<1% target)
- [ ] Verify thread-safety for async operations

### Phase 3: Path Executor (1-2 days)
- [ ] Implement `PathExecutor` class
- [ ] Create test query datasets
- [ ] Add weighted random selection
- [ ] Write execution script
- [ ] Test with 100+ iterations

### Phase 4: Analysis & Reporting (2-3 days)
- [ ] Implement report generation
- [ ] Create Streamlit dashboard
- [ ] Add visualizations (bar charts, heatmaps, Sankey diagrams)
- [ ] Export functionality (CSV, JSON, HTML)

### Phase 5: Production Deployment (1-2 days)
- [ ] Add configuration (enable/disable tracing)
- [ ] Implement sampling (trace 10% of requests to reduce overhead)
- [ ] Set up log rotation for trace database
- [ ] Add monitoring alerts (high error rates, slow paths)
- [ ] Document operational procedures

### Phase 6: Analysis & Action (Ongoing)
- [ ] Run initial baseline analysis
- [ ] Identify optimization opportunities
- [ ] Remove dead code
- [ ] Fix error-prone paths
- [ ] Monitor improvements over time

---

## 🎯 Success Criteria

### Quantitative Metrics
- [ ] Tracing overhead < 1% of total request time
- [ ] Database size < 100MB for 10,000 requests
- [ ] Can identify top 10 hot paths with >95% accuracy
- [ ] Can detect performance regressions >10% slower
- [ ] Can identify unused code (0 frequency) with 100% accuracy

### Qualitative Outcomes
- [ ] Developers can quickly identify bottlenecks
- [ ] Dead code removal reduces codebase by >5%
- [ ] Error-prone paths identified and fixed
- [ ] Data-driven optimization priorities established
- [ ] Production monitoring operational

---

## 🚨 Important Considerations

### Performance Impact
- **Overhead:** Expect 0.5-1% performance overhead
- **Mitigation:** Use sampling (trace 10% of requests)
- **Monitoring:** Track overhead and disable if >2%

### Data Privacy
- **Concern:** Traces may contain user queries
- **Mitigation:** Anonymize or hash sensitive data
- **Compliance:** Follow GDPR/privacy regulations

### Database Growth
- **Concern:** Trace database can grow large
- **Mitigation:** Implement automatic cleanup (keep 30 days)
- **Monitoring:** Alert if database >1GB

### Thread Safety
- **Concern:** Async operations need thread-local storage
- **Mitigation:** Use `contextvars` for async safety
- **Testing:** Stress test with concurrent requests

---

## 📚 References & Resources

### Similar Tools & Inspiration
- **OpenTelemetry:** Distributed tracing standard
- **Jaeger:** Distributed tracing system
- **Datadog APM:** Application performance monitoring
- **Python cProfile:** Built-in profiling
- **py-spy:** Sampling profiler for Python

### Learning Resources
- Execution path tracing best practices
- Flame graph visualization techniques
- Statistical profiling methods
- Distributed tracing patterns

---

## 🔄 Integration with Existing Work

This tracing system complements recent optimizations:

1. **Performance Optimizations (Oct 2025)**
   - Tracing will validate 50x speedup in dataset enrichment
   - Can measure actual vs theoretical improvements

2. **Auto-Discovery Feature**
   - Track auto-discovery trigger frequency (currently estimated 2%)
   - Measure real-world performance impact

3. **Execution Tree Analysis (DFS/BFS)**
   - Validate tree structure with real execution data
   - Compare theoretical vs actual path frequencies

---

## 📝 Notes & Decisions

### Why Not Use Existing Tools?
- **OpenTelemetry:** Too heavyweight, complex setup
- **Datadog/NewRelic:** Expensive for this scale
- **Custom solution:** Lightweight, tailored to our needs, easy to extend

### Why Wait Until Production?
- Need stable baseline for meaningful metrics
- Core features must work before measuring them
- Avoid premature optimization
- Focus on user-facing features first

### Future Extensions
- Distributed tracing across microservices (if we scale)
- Machine learning anomaly detection
- Automated performance regression testing
- Real-time alerting on slow/error-prone paths

---

## ✅ Checklist for Implementation

When ready to implement, follow this checklist:

### Pre-Implementation
- [ ] Core features stable and tested
- [ ] Citations displaying correctly
- [ ] PDF downloads working
- [ ] AI analysis functional
- [ ] System in production with real users

### Implementation
- [ ] Review this document
- [ ] Create monitoring directory structure
- [ ] Implement ExecutionPathTracer
- [ ] Add instrumentation points
- [ ] Build PathExecutor
- [ ] Create analysis dashboard
- [ ] Test thoroughly
- [ ] Deploy to production
- [ ] Monitor overhead
- [ ] Generate first report

### Post-Implementation
- [ ] Analyze hot paths
- [ ] Identify optimization opportunities
- [ ] Remove dead code
- [ ] Fix error-prone paths
- [ ] Document findings
- [ ] Share insights with team

---

**Last Updated:** October 16, 2025  
**Next Review:** When core functionality is production-ready  
**Owner:** TBD  
**Priority:** P2 (Post-production feature)

