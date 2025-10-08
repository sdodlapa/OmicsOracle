# OmicsOracle - Backend-Frontend Integration Contract
**Version:** 1.0
**Date:** October 7, 2025
**Status:** FRAMEWORK AGNOSTIC SPECIFICATION
**Purpose:** Define clear contract between backend and ANY frontend framework

---

## 📋 Document Purpose

This document serves as the **single source of truth** for:
1. **What data** the backend provides
2. **How to access** that data (API endpoints)
3. **What format** the data is in (schemas)
4. **When to call** which endpoints (workflow)
5. **How to render** features (UI patterns)

With this contract, we can **migrate to any frontend framework** (React, Vue, Svelte, Angular) without touching backend code.

---

## 🏗️ System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Any Framework)                  │
│  React / Vue / Svelte / Streamlit / Angular / Solid / etc.     │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ HTTP REST API                      │ WebSocket (future)
             │ (JSON)                             │ (real-time updates)
             │                                    │
┌────────────▼────────────────────────────────────▼───────────────┐
│                     FASTAPI BACKEND                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Search     │  │   Analysis   │  │   ML/LLM     │          │
│  │   Engine     │  │   Pipeline   │  │   Services   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                   │                 │
│         └─────────────────┴───────────────────┘                 │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    DATA SOURCES                                  │
│  PubMed | Google Scholar | Semantic Scholar | PDF Repos         │
└──────────────────────────────────────────────────────────────────┘
```

### API Surface

```
Backend API (FastAPI) - http://localhost:8000

├─ /api/v1/search
│  ├─ POST /search                    → Basic search
│  ├─ POST /advanced_search            → Advanced search with filters
│  └─ GET /search/history              → Search history
│
├─ /api/v1/agents
│  ├─ POST /analyze                    → LLM analysis of results
│  ├─ POST /qa                         → Q&A about papers
│  └─ POST /recommend                  → Get recommendations
│
├─ /api/v1/analysis
│  ├─ POST /citations                  → Citation analysis
│  ├─ POST /biomarkers                 → Biomarker extraction
│  ├─ POST /quality                    → Quality assessment
│  ├─ POST /trends                     → Trend analysis
│  └─ POST /network                    → Network analysis
│
├─ /api/v1/export
│  ├─ POST /json                       → Export as JSON
│  ├─ POST /csv                        → Export as CSV
│  └─ POST /pdf                        → Generate PDF report
│
└─ /api/v1/config
   ├─ GET /databases                   → Available databases
   ├─ GET /filters                     → Available filters
   └─ GET /settings                    → User settings
```

---

## 🔄 Data Flow Diagram

### Flow 1: Basic Search

```
┌──────────┐
│  USER    │
│  TYPES   │
│  QUERY   │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Capture Input                                      │
│ ─────────────────────────────────────────────────────────── │
│ const query = document.getElementById('search').value;      │
│ const params = {                                            │
│   databases: ['pubmed', 'scholar'],                         │
│   year_range: [2020, 2024],                                 │
│   max_results: 50                                           │
│ };                                                          │
└────┬────────────────────────────────────────────────────────┘
     │
     │ POST /api/v1/search/search
     │ Body: { query, ...params }
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: Process Request                                     │
│ ─────────────────────────────────────────────────────────── │
│ 1. Parse query                                              │
│ 2. Search PubMed API                                        │
│ 3. Search Google Scholar                                    │
│ 4. Deduplicate results                                      │
│ 5. Enrich with citations                                    │
│ 6. Calculate quality scores                                 │
│ 7. Extract biomarkers                                       │
│ 8. Return JSON                                              │
└────┬────────────────────────────────────────────────────────┘
     │
     │ Response: SearchResponse (see schema below)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Render Results                                     │
│ ─────────────────────────────────────────────────────────── │
│ results.forEach(pub => {                                    │
│   renderResultCard(pub);                                    │
│ });                                                         │
│                                                             │
│ renderSummary(response.metadata);                           │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: LLM Analysis

```
┌──────────┐
│  USER    │
│  ENABLES │
│ LLM FLAG │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: After Search Results                               │
│ ─────────────────────────────────────────────────────────── │
│ if (useLLM) {                                               │
│   const datasets = results.slice(0, 10).map(r => ({        │
│     title: r.title,                                         │
│     abstract: r.abstract,                                   │
│     year: r.year,                                           │
│     citations: r.citation_count                             │
│   }));                                                      │
│                                                             │
│   showLoading('Analyzing with AI...');                      │
│ }                                                           │
└────┬────────────────────────────────────────────────────────┘
     │
     │ POST /api/v1/agents/analyze
     │ Body: { query, datasets, analysis_type: 'comprehensive' }
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: LLM Analysis                                        │
│ ─────────────────────────────────────────────────────────── │
│ 1. Load LLM model (GPT-4, Claude, etc.)                     │
│ 2. Create analysis prompt                                   │
│ 3. Generate overview                                        │
│ 4. Extract key insights                                     │
│ 5. Generate recommendations                                 │
│ 6. Analyze trends                                           │
│ 7. Return structured analysis                               │
└────┬────────────────────────────────────────────────────────┘
     │
     │ Response: AnalysisResponse (see schema below)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Display Analysis                                   │
│ ─────────────────────────────────────────────────────────── │
│ renderLLMAnalysis({                                         │
│   overview: analysis.overview,                              │
│   insights: analysis.key_insights,                          │
│   recommendations: analysis.recommendations,                │
│   trends: analysis.trends                                   │
│ });                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Flow 3: Q&A Interaction

```
┌──────────┐
│  USER    │
│  ASKS    │
│ QUESTION │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Capture Question                                   │
│ ─────────────────────────────────────────────────────────── │
│ const question = document.getElementById('qa-input').value; │
│ const context = currentResults.map(r => ({                  │
│   title: r.title,                                           │
│   abstract: r.abstract                                      │
│ }));                                                        │
└────┬────────────────────────────────────────────────────────┘
     │
     │ POST /api/v1/agents/qa
     │ Body: { question, context }
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND: Answer Question                                     │
│ ─────────────────────────────────────────────────────────── │
│ 1. Load Q&A model                                           │
│ 2. Create RAG context from papers                           │
│ 3. Generate answer                                          │
│ 4. Cite sources                                             │
│ 5. Calculate confidence                                     │
└────┬────────────────────────────────────────────────────────┘
     │
     │ Response: QAResponse (see schema below)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Display Answer                                     │
│ ─────────────────────────────────────────────────────────── │
│ renderAnswer({                                              │
│   question: question,                                       │
│   answer: response.answer,                                  │
│   sources: response.sources,                                │
│   confidence: response.confidence                           │
│ });                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 API Endpoint Specifications

### 1. Search Endpoint

**Endpoint:** `POST /api/v1/search/search`

**Request Schema:**
```typescript
interface SearchRequest {
  query: string;                    // Required: Search query
  databases?: string[];             // Optional: ['pubmed', 'scholar', 'semantic']
  year_range?: [number, number];   // Optional: [start_year, end_year]
  max_results?: number;             // Optional: Default 50, max 200
  filters?: {
    quality_threshold?: number;     // Optional: 0-1 (0.8 = 80%+)
    citation_min?: number;          // Optional: Minimum citations
    open_access_only?: boolean;     // Optional: Filter for OA papers
    publication_types?: string[];   // Optional: ['journal', 'conference', 'preprint']
  };
  use_semantic_search?: boolean;    // Optional: Enable semantic matching
  use_llm?: boolean;                // Optional: Enable LLM analysis
}
```

**Example Request:**
```json
{
  "query": "CRISPR gene editing cancer therapy",
  "databases": ["pubmed", "scholar"],
  "year_range": [2020, 2024],
  "max_results": 50,
  "filters": {
    "quality_threshold": 0.8,
    "open_access_only": false
  },
  "use_semantic_search": true,
  "use_llm": false
}
```

**Response Schema:**
```typescript
interface SearchResponse {
  status: 'success' | 'error';
  metadata: {
    query: string;
    total_results: number;
    search_time_ms: number;
    databases_searched: string[];
    timestamp: string;              // ISO 8601 format
  };
  results: Publication[];           // See Publication schema below
  filters_applied: object;
  suggestions?: string[];           // Query suggestions
}
```

**Publication Schema:**
```typescript
interface Publication {
  // Core metadata
  publication_id: string;
  title: string;
  authors: Author[];
  abstract: string;
  year: number;
  publication_date?: string;        // ISO 8601

  // Source information
  source: 'pubmed' | 'scholar' | 'semantic' | 'crossref';
  source_id: string;                // e.g., "PMC12345", "DOI:10.1234/..."
  doi?: string;
  pmid?: string;
  pmcid?: string;

  // Citation data
  citation_count: number;
  citation_analysis?: CitationAnalysis;  // See schema below

  // Quality metrics
  quality_score: QualityScore;      // See schema below

  // Biomarkers
  biomarkers?: Biomarker[];         // See schema below

  // Semantic search
  semantic_match?: {
    score: number;                  // 0-1 relevance score
    matched_concepts: string[];
    explanation: string;
  };

  // Access information
  access: {
    is_open_access: boolean;
    pdf_url?: string;
    fulltext_url?: string;
    requires_vpn: boolean;
    institutional_access?: string;  // e.g., "Georgia Tech"
  };

  // Publication details
  journal?: string;
  volume?: string;
  issue?: string;
  pages?: string;
  publication_type?: string;

  // Trends
  trend_data?: {
    trend: 'emerging' | 'hot' | 'stable' | 'declining';
    growth_rate?: number;
  };
}

interface Author {
  name: string;
  affiliation?: string;
  orcid?: string;
}

interface CitationAnalysis {
  total_citations: number;
  citations_per_year: number;
  citation_velocity: 'increasing' | 'stable' | 'declining';
  h_index_contribution: number;
  usage_patterns: {
    cited_by_reviews: number;
    cited_by_clinical_trials: number;
    cited_by_meta_analyses: number;
  };
  impact_metrics: {
    relative_citation_ratio: number;
    field_normalized_score: number;
  };
  top_citing_papers?: Array<{
    title: string;
    year: number;
    citations: number;
  }>;
}

interface QualityScore {
  overall: number;                  // 0-1 overall score
  rating: 'high' | 'medium' | 'low';
  components: {
    citation_score: number;         // 0-1
    journal_impact: number;         // 0-1
    recency: number;                // 0-1
    methodological_rigor: number;   // 0-1
  };
  confidence: number;               // 0-1 confidence in score
}

interface Biomarker {
  name: string;
  category: 'protein' | 'gene' | 'metabolite' | 'cell' | 'other';
  confidence: number;               // 0-1
  context?: string;                 // Sentence where mentioned
  mentions: number;                 // Number of times mentioned
}
```

**Example Response:**
```json
{
  "status": "success",
  "metadata": {
    "query": "CRISPR gene editing cancer therapy",
    "total_results": 47,
    "search_time_ms": 2340,
    "databases_searched": ["pubmed", "scholar"],
    "timestamp": "2025-10-07T14:32:15Z"
  },
  "results": [
    {
      "publication_id": "PMC12345",
      "title": "Novel CRISPR delivery mechanisms for cancer therapy",
      "authors": [
        {"name": "Smith J", "affiliation": "MIT"},
        {"name": "Doe A", "affiliation": "Harvard"}
      ],
      "abstract": "Recent advances in CRISPR-Cas9...",
      "year": 2023,
      "source": "pubmed",
      "source_id": "PMC12345",
      "doi": "10.1234/example",
      "citation_count": 142,
      "citation_analysis": {
        "total_citations": 142,
        "citations_per_year": 71.0,
        "citation_velocity": "increasing",
        "usage_patterns": {
          "cited_by_reviews": 23,
          "cited_by_clinical_trials": 8
        }
      },
      "quality_score": {
        "overall": 0.95,
        "rating": "high",
        "components": {
          "citation_score": 0.92,
          "journal_impact": 0.98,
          "recency": 1.0,
          "methodological_rigor": 0.91
        },
        "confidence": 0.87
      },
      "biomarkers": [
        {
          "name": "PD-L1",
          "category": "protein",
          "confidence": 0.87,
          "mentions": 5
        }
      ],
      "semantic_match": {
        "score": 0.95,
        "matched_concepts": ["CRISPR", "cancer therapy", "gene editing"],
        "explanation": "High relevance: mentions all key concepts"
      },
      "access": {
        "is_open_access": true,
        "pdf_url": "https://example.com/paper.pdf",
        "requires_vpn": false
      },
      "trend_data": {
        "trend": "hot",
        "growth_rate": 0.45
      }
    }
  ],
  "filters_applied": {
    "quality_threshold": 0.8,
    "year_range": [2020, 2024]
  }
}
```

---

### 2. LLM Analysis Endpoint

**Endpoint:** `POST /api/v1/agents/analyze`

**Request Schema:**
```typescript
interface AnalysisRequest {
  query: string;
  datasets: Array<{
    title: string;
    abstract: string;
    year: number;
    citations: number;
  }>;
  analysis_type?: 'quick' | 'comprehensive' | 'custom';
  focus_areas?: string[];  // e.g., ['trends', 'methodologies', 'gaps']
}
```

**Response Schema:**
```typescript
interface AnalysisResponse {
  status: 'success' | 'error';
  analysis: {
    overview: string;              // 2-3 sentence summary
    key_insights: string[];        // 3-5 bullet points
    recommendations: string[];     // 3-5 actionable items
    trends: {
      emerging_topics: string[];
      declining_topics: string[];
      future_directions: string;
    };
    quality_assessment: {
      high_quality_papers: number;
      medium_quality_papers: number;
      low_quality_papers: number;
    };
    gaps_identified?: string[];
    methodologies_summary?: string;
  };
  timestamp: string;
  processing_time_ms: number;
}
```

---

### 3. Q&A Endpoint

**Endpoint:** `POST /api/v1/agents/qa`

**Request Schema:**
```typescript
interface QARequest {
  question: string;
  context: Array<{
    title: string;
    abstract: string;
  }>;
  max_sources?: number;  // Default 5
}
```

**Response Schema:**
```typescript
interface QAResponse {
  status: 'success' | 'error';
  answer: string;
  sources: Array<{
    title: string;
    relevance_score: number;
    excerpt: string;
  }>;
  confidence: number;  // 0-1
  follow_up_questions?: string[];
}
```

---

### 4. Citation Analysis Endpoint

**Endpoint:** `POST /api/v1/analysis/citations`

**Request Schema:**
```typescript
interface CitationAnalysisRequest {
  publication_ids: string[];
  analysis_depth?: 'basic' | 'detailed';
}
```

**Response Schema:**
```typescript
interface CitationAnalysisResponse {
  status: 'success' | 'error';
  results: Array<{
    publication_id: string;
    citation_network: {
      direct_citations: number;
      co_citation_cluster: string[];  // Related paper IDs
      citation_context: object;
    };
  }>;
}
```

---

### 5. Biomarker Extraction Endpoint

**Endpoint:** `POST /api/v1/analysis/biomarkers`

**Request Schema:**
```typescript
interface BiomarkerRequest {
  text: string;  // Abstract or full text
  categories?: string[];  // Filter by category
}
```

**Response Schema:**
```typescript
interface BiomarkerResponse {
  status: 'success' | 'error';
  biomarkers: Biomarker[];
  aggregated_counts: {
    [category: string]: number;
  };
}
```

---

### 6. Trend Analysis Endpoint

**Endpoint:** `POST /api/v1/analysis/trends`

**Request Schema:**
```typescript
interface TrendRequest {
  publications: Publication[];
  time_window?: 'yearly' | 'monthly';
}
```

**Response Schema:**
```typescript
interface TrendResponse {
  status: 'success' | 'error';
  trends: {
    publication_timeline: Array<{
      year: number;
      count: number;
      avg_citations: number;
    }>;
    topic_evolution: Array<{
      topic: string;
      trend: 'emerging' | 'hot' | 'declining';
      papers_count: number;
      growth_rate: number;
    }>;
    research_clusters: Array<{
      cluster_name: string;
      papers: number;
      key_authors: string[];
    }>;
  };
}
```

---

### 7. Network Analysis Endpoint

**Endpoint:** `POST /api/v1/analysis/network`

**Request Schema:**
```typescript
interface NetworkRequest {
  publications: Publication[];
  network_type?: 'citation' | 'author' | 'topic';
}
```

**Response Schema:**
```typescript
interface NetworkResponse {
  status: 'success' | 'error';
  network: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      metrics: object;
    }>;
    edges: Array<{
      source: string;
      target: string;
      weight: number;
      type: string;
    }>;
  };
}
```

---

### 8. Export Endpoints

**Endpoint:** `POST /api/v1/export/json`

**Request Schema:**
```typescript
interface ExportRequest {
  publications: Publication[];
  include_analysis?: boolean;
  include_llm?: boolean;
}
```

**Response:**
```
Content-Type: application/json
Content-Disposition: attachment; filename="omics_oracle_export.json"

{
  "metadata": {...},
  "publications": [...],
  "analysis": {...}  // if requested
}
```

---

## 🎨 UI Integration Patterns

### Pattern 1: Progressive Loading

```typescript
// PATTERN: Show skeleton → Load data → Render real content

async function searchAndRender(query: string) {
  // Step 1: Show loading state
  showSkeletonCards(10);

  // Step 2: Fetch data
  const response = await fetch('/api/v1/search/search', {
    method: 'POST',
    body: JSON.stringify({ query, max_results: 50 })
  });

  const data = await response.json();

  // Step 3: Render real data
  hideSkeletonCards();
  data.results.forEach(pub => renderResultCard(pub));

  // Step 4: Optional LLM analysis
  if (useLLM) {
    await fetchAndRenderLLMAnalysis(query, data.results);
  }
}
```

### Pattern 2: Expandable Sections

```typescript
// PATTERN: Compact → Expand on demand → Fetch details if needed

function renderResultCard(pub: Publication) {
  const card = createCard(pub);

  // Always visible
  card.renderHeader(pub.title, pub.quality_score);
  card.renderMetadata(pub.authors, pub.year, pub.citation_count);

  // Expandable sections
  card.addExpandableSection('Abstract', () => {
    return formatAbstract(pub.abstract);
  });

  card.addExpandableSection('AI Analysis', async () => {
    // Fetch on demand if not already loaded
    if (!pub.llm_analysis) {
      const analysis = await fetchLLMAnalysisForPaper(pub);
      pub.llm_analysis = analysis;
    }
    return renderLLMAnalysis(pub.llm_analysis);
  });

  card.addExpandableSection('Citations', () => {
    return renderCitationPanel(pub.citation_analysis);
  });

  return card;
}
```

### Pattern 3: Real-Time Filtering

```typescript
// PATTERN: Client-side filter for instant feedback

let allResults: Publication[] = [];

async function initialSearch(query: string) {
  const response = await fetch('/api/v1/search/search', {
    method: 'POST',
    body: JSON.stringify({ query, max_results: 200 })
  });

  allResults = (await response.json()).results;
  renderResults(allResults);
}

function applyFilters(filters: Filters) {
  const filtered = allResults.filter(pub => {
    if (filters.quality_min && pub.quality_score.overall < filters.quality_min) {
      return false;
    }
    if (filters.year_range && !inRange(pub.year, filters.year_range)) {
      return false;
    }
    if (filters.open_access_only && !pub.access.is_open_access) {
      return false;
    }
    return true;
  });

  renderResults(filtered);
}
```

### Pattern 4: Optimistic UI

```typescript
// PATTERN: Update UI immediately, then sync with server

async function bookmarkPaper(pub: Publication) {
  // Step 1: Update UI optimistically
  pub.bookmarked = true;
  updateCardUI(pub);

  try {
    // Step 2: Sync with server
    await fetch('/api/v1/bookmarks/add', {
      method: 'POST',
      body: JSON.stringify({ publication_id: pub.publication_id })
    });
  } catch (error) {
    // Step 3: Revert on error
    pub.bookmarked = false;
    updateCardUI(pub);
    showError('Failed to bookmark paper');
  }
}
```

---

## 🔧 Framework Migration Guide

### Migrating to React

```tsx
// React Component Example

import React, { useState, useEffect } from 'react';
import { SearchAPI } from './api/search';

function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(true);
  const [llmAnalysis, setLLMAnalysis] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);

      // Call search API
      const response = await SearchAPI.search({
        query,
        databases: ['pubmed', 'scholar'],
        max_results: 50
      });

      setResults(response.results);
      setLoading(false);

      // Optional: Fetch LLM analysis
      if (useLLM) {
        const analysis = await SearchAPI.analyze({
          query,
          datasets: response.results.slice(0, 10)
        });
        setLLMAnalysis(analysis);
      }
    }

    fetchData();
  }, [query]);

  if (loading) return <SkeletonCards count={10} />;

  return (
    <>
      {llmAnalysis && <LLMAnalysisPanel analysis={llmAnalysis} />}
      {results.map(pub => (
        <ResultCard key={pub.publication_id} publication={pub} />
      ))}
    </>
  );
}
```

### Migrating to Vue

```vue
<template>
  <div>
    <LLMAnalysisPanel v-if="llmAnalysis" :analysis="llmAnalysis" />
    <ResultCard
      v-for="pub in results"
      :key="pub.publication_id"
      :publication="pub"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { SearchAPI } from './api/search';

const props = defineProps<{ query: string }>();
const results = ref<Publication[]>([]);
const llmAnalysis = ref(null);

async function fetchData() {
  const response = await SearchAPI.search({
    query: props.query,
    databases: ['pubmed', 'scholar'],
    max_results: 50
  });

  results.value = response.results;

  if (useLLM) {
    llmAnalysis.value = await SearchAPI.analyze({
      query: props.query,
      datasets: response.results.slice(0, 10)
    });
  }
}

onMounted(fetchData);
watch(() => props.query, fetchData);
</script>
```

### Migrating to Svelte

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { SearchAPI } from './api/search';

  export let query: string;

  let results: Publication[] = [];
  let llmAnalysis = null;
  let loading = true;

  async function fetchData() {
    loading = true;

    const response = await SearchAPI.search({
      query,
      databases: ['pubmed', 'scholar'],
      max_results: 50
    });

    results = response.results;
    loading = false;

    if (useLLM) {
      llmAnalysis = await SearchAPI.analyze({
        query,
        datasets: response.results.slice(0, 10)
      });
    }
  }

  onMount(fetchData);

  $: query && fetchData();
</script>

{#if loading}
  <SkeletonCards count={10} />
{:else}
  {#if llmAnalysis}
    <LLMAnalysisPanel analysis={llmAnalysis} />
  {/if}

  {#each results as pub (pub.publication_id)}
    <ResultCard publication={pub} />
  {/each}
{/if}
```

---

## 🧪 Testing Integration

### API Client Example (Framework Agnostic)

```typescript
// api/search.ts - Reusable API client

export class SearchAPI {
  private static baseURL = 'http://localhost:8000/api/v1';

  static async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseURL}/search/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await fetch(`${this.baseURL}/agents/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async qa(request: QARequest): Promise<QAResponse> {
    const response = await fetch(`${this.baseURL}/agents/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Q&A failed: ${response.statusText}`);
    }

    return response.json();
  }

  // ... other endpoints
}
```

### Unit Tests

```typescript
// api/search.test.ts

import { SearchAPI } from './search';

describe('SearchAPI', () => {
  it('should search publications', async () => {
    const response = await SearchAPI.search({
      query: 'CRISPR',
      databases: ['pubmed'],
      max_results: 10
    });

    expect(response.status).toBe('success');
    expect(response.results).toHaveLength(10);
    expect(response.results[0]).toHaveProperty('title');
    expect(response.results[0]).toHaveProperty('quality_score');
  });

  it('should handle errors gracefully', async () => {
    await expect(
      SearchAPI.search({ query: '', max_results: 0 })
    ).rejects.toThrow();
  });
});
```

---

## 📊 Feature Rendering Map

### Feature → API → UI Mapping

| Feature | API Endpoint | Data Used | UI Component | Location |
|---------|-------------|-----------|--------------|----------|
| **Basic Search** | `POST /search/search` | `results[]` | `ResultCard` | Main area |
| **LLM Analysis** | `POST /agents/analyze` | `analysis.*` | `LLMAnalysisPanel` | Above results |
| **Quality Scores** | (in search results) | `quality_score` | `QualityBadge` | Card header |
| **Citations** | (in search results) | `citation_analysis` | `CitationPanel` | Expandable |
| **Biomarkers** | (in search results) | `biomarkers[]` | `BiomarkerPanel` | Expandable |
| **Q&A** | `POST /agents/qa` | `answer, sources` | `QAPanel` | Drawer/Modal |
| **Semantic Match** | (in search results) | `semantic_match` | `SemanticBadge` | Card metadata |
| **Trends** | `POST /analysis/trends` | `trends.*` | `TrendsChart` | Analytics tab |
| **Network** | `POST /analysis/network` | `network.*` | `NetworkGraph` | Network tab |
| **Export** | `POST /export/json` | All data | Download | Toolbar |

---

## 🚀 Quick Start Checklist

For implementing **any** frontend framework:

### Step 1: API Client
- [ ] Create API client module
- [ ] Implement search endpoint
- [ ] Implement analysis endpoints
- [ ] Add error handling
- [ ] Add TypeScript types

### Step 2: Core Components
- [ ] ResultCard component
- [ ] SkeletonLoader component
- [ ] SearchBar component
- [ ] FilterPanel component

### Step 3: Feature Components
- [ ] LLMAnalysisPanel
- [ ] QualityBadge
- [ ] CitationPanel
- [ ] BiomarkerPanel
- [ ] QAPanel

### Step 4: Layout
- [ ] Main layout structure
- [ ] Responsive breakpoints
- [ ] Navigation/header
- [ ] Footer

### Step 5: State Management
- [ ] Search state
- [ ] Results state
- [ ] UI state (expanded sections, etc.)
- [ ] User preferences

### Step 6: Testing
- [ ] API client tests
- [ ] Component unit tests
- [ ] Integration tests
- [ ] E2E tests

---

## 📚 Additional Resources

### API Documentation
- Full OpenAPI spec: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example Implementations
- Streamlit: `omics_oracle_v2/lib/dashboard/`
- React (future): TBD
- Vue (future): TBD

### Code Generation
Can auto-generate API clients using:
- OpenAPI Generator
- Swagger Codegen
- TypeScript from OpenAPI

---

**This contract ensures:**
✅ Backend remains stable regardless of frontend changes
✅ Multiple frontends can coexist (Streamlit + React admin panel)
✅ Easy to add new features (just extend API + update contract)
✅ Clear testing boundaries (test API separately from UI)
✅ Framework migrations are straightforward (same data flow)

**Ready to build any frontend on top of OmicsOracle! 🚀**
