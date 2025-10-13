#!/usr/bin/env python3
"""
Script to clean up SearchAgent legacy code - Stage 2 Pass 1.

Removes:
1. Feature flag _use_unified_pipeline (line 79)
2. Old pipeline initialization code in __init__
3. Legacy implementation in _process method (lines 373-522)
4. Unused legacy methods: _build_search_query, _build_geo_query_from_preprocessed, _apply_semantic_filters, _semantic_search
5. Unused old imports

Keeps:
- Unified pipeline implementation (_process_unified)
- Helper methods used by unified pipeline (_apply_filters, _rank_datasets, _calculate_relevance, _get_applied_filters)
- Initialization methods (for semantic search, publication search, query preprocessing)
"""

import re
from pathlib import Path


def clean_search_agent():
    file_path = Path("omics_oracle_v2/agents/search_agent.py")
    content = file_path.read_text()
    original_lines = len(content.split("\n"))

    print(f"Original file: {original_lines} lines")

    # 1. Remove old imports (lines to remove)
    # Remove: AdvancedSearchPipeline, PublicationSearchPipeline imports (old ones)
    content = content.replace(
        "from ..lib.search.advanced import AdvancedSearchConfig, AdvancedSearchPipeline\n", ""
    )
    content = content.replace(
        "from ..lib.pipelines.publication_pipeline import PublicationSearchPipeline\n", ""
    )

    # 2. Simplify __init__ docstring and remove feature flag
    init_old = '''        """
        Initialize Search Agent.

        Week 2 Day 4: Adding unified pipeline support alongside existing implementation.
        Feature flag `_use_unified_pipeline` controls which path is used.

        Args:
            settings: Application settings
            enable_semantic: Enable semantic search with AdvancedSearchPipeline
            enable_publications: Enable publications search with PublicationSearchPipeline
            enable_query_preprocessing: Enable query preprocessing with synonym expansion (Phase 2B)
        """
        super().__init__(settings)

        # OLD IMPLEMENTATION (keep for backward compatibility)
        self._geo_client: GEOClient = None
        self._ranker = KeywordRanker(settings.ranking)
        self._enable_semantic = enable_semantic
        self._enable_publications = enable_publications
        self._enable_query_preprocessing = enable_query_preprocessing
        self._semantic_pipeline: Optional[AdvancedSearchPipeline] = None
        self._semantic_index_loaded = False
        self._publication_pipeline = None
        self._preprocessing_pipeline = None

        # NEW IMPLEMENTATION (Week 2 Day 4 - Unified Pipeline)
        self._use_unified_pipeline = True  # Feature flag: True = use new pipeline, False = use old code'''

    init_new = '''        """
        Initialize Search Agent.

        Args:
            settings: Application settings
            enable_semantic: Enable semantic search
            enable_publications: Enable publications search
            enable_query_preprocessing: Enable query preprocessing with synonym expansion
        """
        super().__init__(settings)'''

    content = content.replace(init_old, init_new)

    # 3. Simplify _process method to just call _process_unified
    process_old_start = '''    def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        """
        Execute GEO dataset search.

        Week 2 Day 4: Routes to unified pipeline if enabled, otherwise uses legacy implementation.'''

    process_new_start = '''    def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        """
        Execute GEO dataset search using unified OmicsSearchPipeline.'''

    content = content.replace(process_old_start, process_new_start)

    # Find the start of the legacy implementation block and remove it
    # Remove from "# WEEK 2 DAY 4: Route to unified pipeline" to "raise AgentExecutionError"
    pattern = re.compile(
        r"        # WEEK 2 DAY 4: Route to unified pipeline.*?"
        r'            raise AgentExecutionError\(f"Failed to execute search: \{e\}"\) from e\n\n',
        re.DOTALL,
    )

    replacement = """        logger.info("Using unified pipeline")
        context.set_metric("implementation", "unified_pipeline")
        return self._process_unified(input_data, context)

"""

    content = pattern.sub(replacement, content)

    # 4. Remove unused legacy methods
    # Remove _build_search_query
    pattern_build_search = re.compile(
        r"    def _build_search_query\(self, input_data: SearchInput\).*?" r"        return query\n\n",
        re.DOTALL,
    )
    content = pattern_build_search.sub("", content)

    # Remove _build_geo_query_from_preprocessed
    pattern_build_geo = re.compile(
        r"    def _build_geo_query_from_preprocessed\(self, expanded_query: str.*?"
        r"            return expanded_query\n\n",
        re.DOTALL,
    )
    content = pattern_build_geo.sub("", content)

    # Remove _apply_semantic_filters
    pattern_semantic_filter = re.compile(
        r"    def _apply_semantic_filters\(.*?" r"        return filtered\n\n", re.DOTALL
    )
    content = pattern_semantic_filter.sub("", content)

    # Remove _semantic_search method
    pattern_semantic_search = re.compile(
        r"    def _semantic_search\(.*?" r"            return \[\]\n\n", re.DOTALL
    )
    content = pattern_semantic_search.sub("", content)

    # Remove unused initialization methods
    # _initialize_semantic_search
    pattern_init_semantic = re.compile(
        r"    def _initialize_semantic_search\(self\) -> None:.*?" r"            raise\n\n", re.DOTALL
    )
    content = pattern_init_semantic.sub("", content)

    # _initialize_publication_search
    pattern_init_pub = re.compile(
        r"    def _initialize_publication_search\(self\) -> None:.*?"
        r"            self\._semantic_pipeline = None\n\n",
        re.DOTALL,
    )
    content = pattern_init_pub.sub("", content)

    # _initialize_query_preprocessing
    pattern_init_preproc = re.compile(
        r"    def _initialize_query_preprocessing\(self\) -> None:.*?"
        r"            self\._preprocessing_pipeline = None\n\n",
        re.DOTALL,
    )
    content = pattern_init_preproc.sub("", content)

    # Remove enable_semantic_search and is_semantic_search_available methods
    pattern_enable = re.compile(
        r"    def enable_semantic_search\(self, enable: bool.*?"
        r'            logger\.info\("Disabling semantic search"\)\n\n',
        re.DOTALL,
    )
    content = pattern_enable.sub("", content)

    pattern_is_available = re.compile(
        r"    def is_semantic_search_available\(self\) -> bool:.*?"
        r"        return self\._enable_semantic and self\._semantic_index_loaded\n",
        re.DOTALL,
    )
    content = pattern_is_available.sub("", content)

    # Write back
    file_path.write_text(content)
    new_lines = len(content.split("\n"))

    print(f"Cleaned file: {new_lines} lines")
    print(
        f"Removed: {original_lines - new_lines} lines ({100 * (original_lines - new_lines) / original_lines:.1f}%)"
    )

    return original_lines, new_lines


if __name__ == "__main__":
    original, new = clean_search_agent()
    print("\n[OK] Stage 2 Pass 1 cleanup complete!")
    print(f"   {original} LOC -> {new} LOC (removed {original - new} LOC)")
