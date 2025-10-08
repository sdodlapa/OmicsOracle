# OmicsOracle Feature Integration Plan
**Version:** 1.0
**Date:** October 7, 2025
**Status:** IMPLEMENTATION READY
**Dependencies:** FRONTEND_REDESIGN_ARCHITECTURE.md

---

## 📋 Executive Summary

This document provides detailed implementation plans for integrating **10 missing backend features** into the redesigned frontend. Each feature includes:
- API integration points
- UI component specifications
- State management approach
- Error handling strategy
- Testing requirements
- Estimated effort

**Total Estimated Time:** 2-3 weeks (1 senior developer)
**Priority Order:** Based on user impact & technical complexity

---

## 🎯 Feature Inventory

### Priority Matrix

| Priority | Feature | Impact | Complexity | Effort | Status |
|----------|---------|--------|------------|--------|--------|
| 🔴 P0 | LLM Analysis Display | 🔥 Critical | Medium | 2 days | Not Started |
| 🔴 P0 | Quality Score Indicators | 🔥 Critical | Low | 1 day | Not Started |
| 🟡 P1 | Citation Analysis Panel | High | Medium | 2 days | Not Started |
| 🟡 P1 | Per-Publication Biomarkers | High | Low | 1 day | Not Started |
| 🟡 P1 | Q&A Interface | High | High | 3 days | Not Started |
| 🟢 P2 | Semantic Insights Explanation | Medium | Medium | 1.5 days | Not Started |
| 🟢 P2 | Trend Context Badges | Medium | Low | 1 day | Not Started |
| 🟢 P2 | Network Position Link | Medium | Low | 0.5 days | Not Started |
| 🟢 P3 | Enhanced Export | Low | Low | 1 day | Not Started |
| 🟢 P3 | Advanced Search Filters | Low | Medium | 2 days | Not Started |

**Total:** 15.5 days ≈ 3 weeks

---

## 🔴 Priority 0: Critical Features

### Feature 1: LLM Analysis Display

**Problem:** Backend generates AI analysis (overview, insights, recommendations) but frontend never calls or displays it.

**API Endpoint:** `POST /api/v1/agents/analyze`

**Request:**
```json
{
  "query": "CRISPR gene editing in cancer therapy",
  "datasets": [
    {
      "title": "Novel CRISPR delivery mechanisms...",
      "abstract": "Recent advances in CRISPR...",
      "year": 2023,
      "citations": 142
    },
    // ... up to 10 publications
  ],
  "analysis_type": "comprehensive"
}
```

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "overview": "Your search returned 47 publications on CRISPR gene editing...",
    "key_insights": [
      "Peak research activity in 2023 with 18 publications",
      "Dominant themes: CAR-T therapy (12 papers), delivery mechanisms (8 papers)",
      "High-impact cluster: Memorial Sloan Kettering research group"
    ],
    "recommendations": [
      "Focus on Smith et al. (2023) for latest delivery mechanisms",
      "Review Doe et al. (2022) for clinical trial results",
      "Consider cross-referencing with immunotherapy literature"
    ],
    "trends": {
      "emerging_topics": ["base editing", "prime editing"],
      "declining_topics": ["zinc finger nucleases"],
      "future_directions": "Expect more in vivo delivery research in 2024-2025"
    },
    "quality_assessment": {
      "high_quality_papers": 23,
      "medium_quality_papers": 18,
      "low_quality_papers": 6
    }
  },
  "timestamp": "2025-10-07T14:32:15Z",
  "processing_time_ms": 3420
}
```

#### Implementation Plan

**Step 1: API Integration in Search Flow**

File: `omics_oracle_v2/lib/dashboard/app.py`

```python
def _execute_search(self, query: str, params: Dict):
    """Execute search with optional LLM analysis."""

    # Existing search logic
    results = self.search_service.search(query, params)

    # NEW: LLM Analysis Integration
    if params.get("use_llm", False) and results.get("results"):
        try:
            # Prepare datasets (top 10 results)
            datasets = [
                {
                    "title": r.get("title", ""),
                    "abstract": r.get("abstract", ""),
                    "year": r.get("year"),
                    "citations": r.get("citation_count", 0),
                    "authors": r.get("authors", [])
                }
                for r in results["results"][:10]
            ]

            # Call LLM analysis API
            response = requests.post(
                f"{self.config.api_base_url}/api/v1/agents/analyze",
                json={
                    "query": query,
                    "datasets": datasets,
                    "analysis_type": "comprehensive"
                },
                timeout=30  # LLM can take time
            )

            if response.status_code == 200:
                analysis_data = response.json()
                st.session_state.llm_analysis = analysis_data.get("analysis")
                st.session_state.llm_timestamp = analysis_data.get("timestamp")
            else:
                st.warning(f"⚠️ LLM analysis failed: {response.status_code}")
                st.session_state.llm_analysis = None

        except requests.exceptions.Timeout:
            st.warning("⚠️ LLM analysis timed out. Showing results without AI insights.")
            st.session_state.llm_analysis = None
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            st.session_state.llm_analysis = None

    return results
```

**Step 2: LLM Analysis Component**

File: `omics_oracle_v2/lib/dashboard/components/llm_analysis_panel.py` (NEW)

```python
import streamlit as st
from typing import Dict, Optional
from datetime import datetime

class LLMAnalysisPanel:
    """Display AI-generated analysis of search results."""

    def __init__(self, analysis: Optional[Dict] = None):
        self.analysis = analysis

    def render(self):
        """Render the LLM analysis panel."""
        if not self.analysis:
            st.info("💡 Enable 'LLM Analysis' in search options to see AI insights")
            return

        # Container with styled border
        with st.container():
            st.markdown("### 🤖 AI Analysis")

            # Overview section
            with st.expander("📋 Overview", expanded=True):
                st.markdown(self.analysis.get("overview", "No overview available"))

            # Key insights
            if insights := self.analysis.get("key_insights"):
                with st.expander("💡 Key Insights", expanded=True):
                    for insight in insights:
                        st.markdown(f"• {insight}")

            # Recommendations
            if recs := self.analysis.get("recommendations"):
                with st.expander("✅ Recommendations", expanded=True):
                    for i, rec in enumerate(recs, 1):
                        st.markdown(f"{i}. {rec}")

            # Trends analysis
            if trends := self.analysis.get("trends"):
                with st.expander("📈 Trends & Future Directions", expanded=False):
                    cols = st.columns(2)

                    with cols[0]:
                        st.markdown("**Emerging Topics:**")
                        for topic in trends.get("emerging_topics", []):
                            st.markdown(f"🔥 {topic}")

                    with cols[1]:
                        st.markdown("**Declining Topics:**")
                        for topic in trends.get("declining_topics", []):
                            st.markdown(f"📉 {topic}")

                    if future := trends.get("future_directions"):
                        st.markdown("**Future Directions:**")
                        st.info(future)

            # Quality assessment summary
            if qa := self.analysis.get("quality_assessment"):
                with st.expander("🎯 Quality Assessment", expanded=False):
                    cols = st.columns(3)
                    cols[0].metric("High Quality", qa.get("high_quality_papers", 0), "⭐⭐⭐")
                    cols[1].metric("Medium Quality", qa.get("medium_quality_papers", 0), "⭐⭐")
                    cols[2].metric("Low Quality", qa.get("low_quality_papers", 0), "⭐")

            # Timestamp
            st.caption(f"Generated: {self._format_timestamp()}")

    def _format_timestamp(self) -> str:
        """Format analysis timestamp."""
        if not hasattr(st.session_state, 'llm_timestamp'):
            return "Unknown"

        ts = datetime.fromisoformat(st.session_state.llm_timestamp.replace('Z', '+00:00'))
        return ts.strftime("%Y-%m-%d %I:%M %p")
```

**Step 3: Integration in Results Layout**

File: `omics_oracle_v2/lib/dashboard/app.py`

```python
def _render_results(self):
    """Render search results with LLM analysis."""

    # NEW: Show LLM Analysis at top (if available)
    if hasattr(st.session_state, 'llm_analysis') and st.session_state.llm_analysis:
        from omics_oracle_v2.lib.dashboard.components.llm_analysis_panel import LLMAnalysisPanel

        # Prominent placement above results
        llm_panel = LLMAnalysisPanel(st.session_state.llm_analysis)
        llm_panel.render()

        st.markdown("---")  # Visual separator

    # Existing results rendering
    st.markdown("### 📄 Publications")
    # ... existing code
```

#### Testing Requirements

1. **Unit Tests:**
   - Test API call with valid query
   - Test timeout handling
   - Test error responses
   - Test missing analysis data

2. **Integration Tests:**
   - Test full search flow with LLM enabled
   - Test UI rendering with analysis
   - Test UI without analysis

3. **User Acceptance:**
   - Verify insights are relevant
   - Verify recommendations are actionable
   - Verify performance (< 5s for analysis)

#### Error Handling

```python
# Graceful degradation
try:
    # LLM API call
except requests.exceptions.Timeout:
    st.warning("⏱️ Analysis is taking longer than expected. Results shown without AI insights.")
except requests.exceptions.ConnectionError:
    st.error("🔌 Cannot connect to analysis service. Check if API is running.")
except Exception as e:
    st.error(f"❌ Analysis failed: {str(e)}")
    logger.exception("LLM analysis error")
```

**Estimated Effort:** 2 days
**Dependencies:** None (backend API exists)
**Risk:** Low (graceful degradation implemented)

---

### Feature 2: Quality Score Indicators

**Problem:** Backend calculates multi-dimensional quality scores but frontend doesn't display them.

**API Endpoint:** Already included in search results (no new API needed)

**Data Structure:**
```json
{
  "publication_id": "PMC12345",
  "quality_score": {
    "overall": 0.87,
    "components": {
      "citation_score": 0.92,
      "journal_impact": 0.85,
      "recency": 0.78,
      "methodological_rigor": 0.91
    },
    "rating": "high",  // high, medium, low
    "confidence": 0.83
  }
}
```

#### Implementation Plan

**Step 1: Quality Badge Component**

File: `omics_oracle_v2/lib/dashboard/components/quality_badge.py` (NEW)

```python
import streamlit as st
from typing import Dict

class QualityBadge:
    """Display quality score as visual badge."""

    COLORS = {
        'high': '#4caf50',     # Green
        'medium': '#ff9800',   # Orange
        'low': '#f44336'       # Red
    }

    STARS = {
        'high': '⭐⭐⭐',
        'medium': '⭐⭐',
        'low': '⭐'
    }

    def __init__(self, quality_data: Dict):
        self.data = quality_data
        self.rating = quality_data.get("rating", "medium")
        self.overall = quality_data.get("overall", 0.0)

    def render_inline(self):
        """Render compact badge for result cards."""
        color = self.COLORS.get(self.rating, self.COLORS['medium'])
        stars = self.STARS.get(self.rating, '⭐⭐')

        st.markdown(
            f"""
            <span style="
                background-color: {color}15;
                color: {color};
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 600;
            ">
                {stars} {int(self.overall * 100)}%
            </span>
            """,
            unsafe_allow_html=True
        )

    def render_detailed(self):
        """Render detailed quality breakdown."""
        st.markdown("#### 🎯 Quality Assessment")

        # Overall score
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Overall Quality", f"{int(self.overall * 100)}%", self.rating.upper())
        with col2:
            st.markdown(f"### {self.STARS[self.rating]}")

        # Component breakdown
        components = self.data.get("components", {})
        if components:
            st.markdown("**Score Breakdown:**")

            for key, value in components.items():
                # Format key (citation_score → Citation Score)
                label = key.replace('_', ' ').title()

                # Progress bar
                st.progress(value)
                st.caption(f"{label}: {int(value * 100)}%")

        # Confidence
        confidence = self.data.get("confidence", 0.0)
        st.markdown(f"*Confidence: {int(confidence * 100)}%*")
```

**Step 2: Integration in ResultCard**

File: `omics_oracle_v2/lib/dashboard/components/result_card.py`

```python
from omics_oracle_v2.lib.dashboard.components.quality_badge import QualityBadge

class ResultCard:
    def _render_header(self):
        """Render card header with title and quality badge."""
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### {self.index}. {self.pub['title']}")

        with col2:
            # NEW: Quality badge
            if quality_data := self.pub.get("quality_score"):
                badge = QualityBadge(quality_data)
                badge.render_inline()

    def _render_expandable_quality(self):
        """Render detailed quality panel when expanded."""
        if quality_data := self.pub.get("quality_score"):
            with st.expander("🎯 Quality Details", expanded=False):
                badge = QualityBadge(quality_data)
                badge.render_detailed()
```

**Step 3: Add to Result Metadata Row**

```python
def _render_metadata(self):
    """Render metadata row with quality indicator."""
    # Existing: Authors, year, citations
    st.markdown(f"**Authors:** {', '.join(self.pub.get('authors', [])[:3])}")

    # NEW: Quality indicator inline
    metadata_parts = [
        f"📅 {self.pub.get('year', 'N/A')}",
        f"📚 {self.pub.get('citation_count', 0)} citations",
    ]

    if quality_data := self.pub.get("quality_score"):
        rating = quality_data.get("rating", "medium")
        stars = QualityBadge.STARS.get(rating, "⭐⭐")
        metadata_parts.append(f"{stars} {rating.upper()}")

    st.caption(" | ".join(metadata_parts))
```

#### Testing Requirements

1. **Visual Tests:**
   - Verify badge colors match design system
   - Test badge with all ratings (high/medium/low)
   - Test responsive layout

2. **Data Tests:**
   - Test missing quality data (graceful fallback)
   - Test partial quality components
   - Test edge cases (0%, 100%)

**Estimated Effort:** 1 day
**Dependencies:** Design system (colors, spacing)
**Risk:** Very low (pure UI component)

---

## 🟡 Priority 1: High-Impact Features

### Feature 3: Citation Analysis Panel

**Problem:** Backend generates rich citation metrics but frontend only shows count.

**API Endpoint:** Already in search results under `citation_analysis` field

**Data Structure:**
```json
{
  "publication_id": "PMC12345",
  "citation_analysis": {
    "total_citations": 142,
    "citations_per_year": 23.67,
    "citation_velocity": "increasing",  // increasing, stable, declining
    "h_index_contribution": 1,
    "usage_patterns": {
      "cited_by_reviews": 23,
      "cited_by_clinical_trials": 8,
      "cited_by_meta_analyses": 4
    },
    "impact_metrics": {
      "relative_citation_ratio": 1.87,
      "field_normalized_score": 2.34
    },
    "top_citing_papers": [
      {
        "title": "CRISPR applications in...",
        "year": 2024,
        "citations": 87
      }
    ]
  }
}
```

#### Implementation Plan

**Step 1: Citation Panel Component**

File: `omics_oracle_v2/lib/dashboard/components/citation_panel.py` (NEW)

```python
import streamlit as st
from typing import Dict
import plotly.graph_objects as go

class CitationAnalysisPanel:
    """Display detailed citation metrics and analysis."""

    VELOCITY_ICONS = {
        'increasing': '📈',
        'stable': '➡️',
        'declining': '📉'
    }

    def __init__(self, citation_data: Dict):
        self.data = citation_data

    def render(self):
        """Render citation analysis panel."""
        if not self.data:
            st.info("No citation data available")
            return

        # Summary metrics
        self._render_summary()

        # Usage patterns
        if usage := self.data.get("usage_patterns"):
            self._render_usage_patterns(usage)

        # Impact metrics
        if impact := self.data.get("impact_metrics"):
            self._render_impact_metrics(impact)

        # Top citing papers
        if top_citing := self.data.get("top_citing_papers"):
            self._render_top_citing(top_citing)

    def _render_summary(self):
        """Render summary metrics."""
        cols = st.columns(4)

        total = self.data.get("total_citations", 0)
        per_year = self.data.get("citations_per_year", 0)
        velocity = self.data.get("citation_velocity", "stable")
        h_index = self.data.get("h_index_contribution", 0)

        cols[0].metric("Total Citations", total)
        cols[1].metric("Per Year", f"{per_year:.1f}")
        cols[2].metric("Velocity", velocity.title(),
                      delta=self.VELOCITY_ICONS[velocity])
        cols[3].metric("h-index", h_index)

    def _render_usage_patterns(self, usage: Dict):
        """Render citation usage patterns."""
        st.markdown("**Citation Context:**")

        # Bar chart
        categories = []
        counts = []

        for key, value in usage.items():
            label = key.replace('cited_by_', '').replace('_', ' ').title()
            categories.append(label)
            counts.append(value)

        fig = go.Figure(data=[
            go.Bar(x=categories, y=counts, marker_color='#1f77b4')
        ])
        fig.update_layout(
            title="How This Paper is Cited",
            xaxis_title="Citation Type",
            yaxis_title="Count",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_impact_metrics(self, impact: Dict):
        """Render impact metrics."""
        st.markdown("**Impact Metrics:**")

        cols = st.columns(2)

        rcr = impact.get("relative_citation_ratio", 0)
        fns = impact.get("field_normalized_score", 0)

        cols[0].metric(
            "Relative Citation Ratio",
            f"{rcr:.2f}",
            help="Compares citation rate to similar papers"
        )
        cols[1].metric(
            "Field-Normalized Score",
            f"{fns:.2f}",
            help="Citations adjusted for research field"
        )

    def _render_top_citing(self, papers: list):
        """Render top citing papers."""
        st.markdown("**Top Citing Papers:**")

        for i, paper in enumerate(papers[:5], 1):
            with st.expander(f"{i}. {paper['title']}", expanded=False):
                st.markdown(f"**Year:** {paper.get('year', 'N/A')}")
                st.markdown(f"**Citations:** {paper.get('citations', 0)}")
```

**Step 2: Integration in ResultCard**

```python
class ResultCard:
    def render(self):
        # ... existing code ...

        # Citation analysis button
        if st.button("📊 Citations", key=f"citations_{self.index}"):
            self._toggle_section("citations")

        if "citations" in self.expanded_sections:
            from omics_oracle_v2.lib.dashboard.components.citation_panel import CitationAnalysisPanel

            citation_data = self.pub.get("citation_analysis")
            panel = CitationAnalysisPanel(citation_data)
            panel.render()
```

**Estimated Effort:** 2 days
**Dependencies:** Plotly for charts
**Risk:** Low

---

### Feature 4: Per-Publication Biomarkers

**Problem:** Biomarkers extracted per publication but only aggregated view shown.

**Implementation:**

```python
class BiomarkerPanel:
    """Display biomarkers mentioned in this publication."""

    def render(self, biomarkers: list):
        if not biomarkers:
            st.info("No biomarkers detected in this publication")
            return

        st.markdown("**🧬 Biomarkers Mentioned:**")

        # Group by category
        by_category = {}
        for bio in biomarkers:
            category = bio.get("category", "Other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(bio)

        # Render by category
        for category, items in by_category.items():
            with st.expander(f"{category} ({len(items)})", expanded=True):
                for bio in items:
                    cols = st.columns([3, 1])
                    cols[0].markdown(f"**{bio['name']}**")
                    if confidence := bio.get("confidence"):
                        cols[1].caption(f"{int(confidence*100)}% conf.")

                    if context := bio.get("context"):
                        st.caption(f"Context: {context}")
```

**Estimated Effort:** 1 day
**Risk:** Very low

---

### Feature 5: Q&A Interface

**Problem:** Q&A API exists but no UI to ask questions.

**API Endpoint:** `POST /api/v1/agents/qa`

**Request:**
```json
{
  "question": "What delivery mechanisms are used?",
  "context": [
    {"title": "...", "abstract": "..."},
    ...
  ]
}
```

**Implementation:**

File: `omics_oracle_v2/lib/dashboard/components/qa_panel.py` (NEW)

```python
class QAPanel:
    """Interactive Q&A interface for publications."""

    def __init__(self, publications: list, api_base_url: str):
        self.pubs = publications
        self.api_url = api_base_url

    def render(self):
        st.markdown("### 💬 Ask a Question")

        # Question input
        question = st.text_input(
            "What would you like to know about these papers?",
            placeholder="e.g., What delivery mechanisms are discussed?"
        )

        if st.button("Ask", disabled=not question):
            with st.spinner("🤔 Analyzing publications..."):
                answer = self._get_answer(question)

                if answer:
                    st.markdown("**Answer:**")
                    st.info(answer['response'])

                    if sources := answer.get('sources'):
                        with st.expander("📚 Sources"):
                            for src in sources:
                                st.markdown(f"• {src['title']} ({src['year']})")

    def _get_answer(self, question: str) -> dict:
        """Call Q&A API."""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/agents/qa",
                json={
                    "question": question,
                    "context": [
                        {"title": p['title'], "abstract": p.get('abstract', '')}
                        for p in self.pubs[:10]
                    ]
                },
                timeout=15
            )
            return response.json() if response.ok else None
        except Exception as e:
            st.error(f"Error: {e}")
            return None
```

**Integration:** Add Q&A tab in Analysis Zone or as per-result panel

**Estimated Effort:** 3 days
**Risk:** Medium (depends on backend Q&A quality)

---

## 🟢 Priority 2: Medium-Impact Features

### Feature 6: Semantic Insights Explanation

**Problem:** Search uses semantic matching but doesn't explain why results match.

**Implementation:**

```python
class SemanticInsightBadge:
    """Show why this result matched the query."""

    def render(self, match_data: dict):
        score = match_data.get("semantic_score", 0)
        concepts = match_data.get("matched_concepts", [])

        # Inline badge
        st.markdown(
            f"""
            <div style="display: inline-block; padding: 4px 8px;
                        background: #e3f2fd; border-radius: 4px;">
                🎯 {int(score*100)}% relevant
                <span title="Matched concepts: {', '.join(concepts)}">ℹ️</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Expandable details
        with st.expander("Why this match?", expanded=False):
            st.markdown("**Matched Concepts:**")
            for concept in concepts:
                st.markdown(f"• {concept}")
```

**Estimated Effort:** 1.5 days

---

### Feature 7: Trend Context Badges

**Problem:** Trends only shown in Analytics tab, not per publication.

**Implementation:**

```python
class TrendBadge:
    """Show if paper is part of emerging/declining trend."""

    def render(self, trend_data: dict):
        trend_type = trend_data.get("trend", "stable")  # emerging, hot, declining

        badges = {
            'emerging': ('🔥', 'Emerging Topic', '#ff6b6b'),
            'hot': ('🌟', 'Hot Topic', '#ffd700'),
            'declining': ('📉', 'Declining Interest', '#aaa')
        }

        if trend_type in badges:
            icon, label, color = badges[trend_type]
            st.markdown(
                f"<span style='color: {color}'>{icon} {label}</span>",
                unsafe_allow_html=True
            )
```

**Estimated Effort:** 1 day

---

### Feature 8: Network Position Link

**Problem:** Network viz exists but not linked to individual papers.

**Implementation:**

```python
def _render_network_link(self, pub_id: str):
    """Show this paper's position in citation network."""

    if st.button("🌐 View in Network", key=f"network_{pub_id}"):
        # Switch to Network tab and highlight this node
        st.session_state.active_tab = "Network"
        st.session_state.highlighted_node = pub_id
        st.rerun()
```

**Estimated Effort:** 0.5 days

---

## 🟢 Priority 3: Nice-to-Have Features

### Feature 9: Enhanced Export

**Problem:** Export only includes basic metadata, not analysis.

**Implementation:**

```python
def export_full_data(results: list, llm_analysis: dict) -> dict:
    """Export complete data including all analysis."""

    return {
        "metadata": {
            "query": st.session_state.last_query,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results)
        },
        "llm_analysis": llm_analysis,
        "publications": [
            {
                **pub,
                "quality_score": pub.get("quality_score"),
                "citation_analysis": pub.get("citation_analysis"),
                "biomarkers": pub.get("biomarkers"),
                "semantic_match": pub.get("semantic_match")
            }
            for pub in results
        ]
    }
```

**Estimated Effort:** 1 day

---

### Feature 10: Advanced Search Filters

**Problem:** No UI for advanced filters (quality threshold, citation range, etc.)

**Implementation:**

```python
class AdvancedFilterModal:
    """Modal dialog for advanced search options."""

    def render(self):
        with st.expander("⚙️ Advanced Filters", expanded=False):
            cols = st.columns(2)

            with cols[0]:
                st.slider("Min Quality Score", 0, 100, 0)
                st.slider("Min Citations", 0, 1000, 0)

            with cols[1]:
                st.multiselect("Trends", ["Emerging", "Hot", "Declining"])
                st.multiselect("Publication Types", ["Journal", "Conference", "Preprint"])
```

**Estimated Effort:** 2 days

---

## 📅 Implementation Timeline

### Week 1: Critical Features
- **Day 1-2:** LLM Analysis Display (P0)
- **Day 3:** Quality Score Indicators (P0)
- **Day 4-5:** Citation Analysis Panel (P1)

### Week 2: High-Impact Features
- **Day 6:** Per-Publication Biomarkers (P1)
- **Day 7-9:** Q&A Interface (P1)
- **Day 10:** Semantic Insights (P2)

### Week 3: Polish & Nice-to-Haves
- **Day 11:** Trend Context Badges (P2)
- **Day 11:** Network Position Link (P2)
- **Day 12:** Enhanced Export (P3)
- **Day 13-14:** Advanced Filters (P3)
- **Day 15:** Testing, bug fixes, documentation

---

## 🧪 Testing Strategy

### Unit Tests
Each component should have:
- Render test with valid data
- Render test with missing data
- Render test with edge cases
- Interaction tests (buttons, expanders)

### Integration Tests
- Full search flow with all features enabled
- Performance test with 100+ results
- Error handling (API timeouts, failures)
- State management (session_state consistency)

### User Acceptance Tests
- 5 researchers test each feature
- Collect feedback on usefulness
- Measure task completion time
- A/B test feature adoption

---

## 🚀 Rollout Strategy

### Phase 1: Alpha (Internal)
- Deploy to staging environment
- Test with 2-3 internal users
- Fix critical bugs
- **Duration:** 3 days

### Phase 2: Beta (Limited)
- Deploy to production with feature flags
- Enable for 10% of users
- Monitor usage analytics
- Collect feedback
- **Duration:** 1 week

### Phase 3: General Availability
- Enable for all users
- Monitor performance metrics
- Iterate based on data
- **Duration:** Ongoing

---

## 📊 Success Metrics

### Adoption Metrics
- % users enabling LLM analysis
- % users expanding citation panels
- % users asking Q&A questions
- % users using advanced filters

### Engagement Metrics
- Time spent on results page (should increase)
- Number of papers bookmarked (should increase)
- Export rate (should increase)
- Repeat usage (should increase)

### Quality Metrics
- User satisfaction score (target: 4.5/5)
- Feature usefulness rating (target: 4/5)
- Bug report rate (target: < 1% users)
- Performance (target: < 3s render time)

---

## 🎯 Next Actions

1. **Review this plan** with stakeholders
2. **Prioritize features** based on user needs
3. **Assign developer resources**
4. **Create detailed mockups** for complex features (Q&A, Citation Panel)
5. **Set up feature flags** in config
6. **Start Week 1 implementation** (LLM Analysis)

---

**Questions? Feedback?**
- Adjust priorities based on user research
- Request detailed mockups for any feature
- Discuss alternative implementation approaches
- Ready to start coding when approved
