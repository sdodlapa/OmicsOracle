#!/usr/bin/env python3
"""
Stage 3 Pass 1a Cleanup Script

Remove duplicate preprocessing from PublicationSearchPipeline:
- ner instance
- synonym_expander instance
- _preprocess_query() method
- _build_pubmed_query() method
- _build_openalex_query() method

Total: ~160 LOC to remove
"""

import re
from pathlib import Path


def remove_duplicate_preprocessing():
    """Remove duplicate preprocessing from PublicationSearchPipeline."""

    file_path = Path("omics_oracle_v2/lib/pipelines/publication_pipeline.py")

    with open(file_path, "r") as f:
        content = f.read()

    original_lines = len(content.split("\n"))

    print("=" * 80)
    print("STAGE 3 PASS 1A - REMOVING DUPLICATE PREPROCESSING")
    print("=" * 80)
    print(f"File: {file_path}")
    print(f"Original lines: {original_lines}")
    print()

    # Step 1: Remove NER initialization (lines ~245-254)
    print("Step 1: Removing BiomedicalNER initialization...")
    pattern1 = r"\s+# Query preprocessing \(NEW - Phase 1\)\s+if config\.enable_query_preprocessing:.*?else:\s+self\.ner = None\s+"
    content = re.sub(pattern1, "\n", content, flags=re.DOTALL)
    print("✓ Removed NER initialization\n")

    # Step 2: Remove synonym expander initialization (lines ~256-270)
    print("Step 2: Removing SynonymExpander initialization...")
    pattern2 = r"\s+# Synonym expansion \(NEW - Phase 2B\)\s+if config\.enable_synonym_expansion:.*?else:\s+self\.synonym_expander = None\s+"
    content = re.sub(pattern2, "\n", content, flags=re.DOTALL)
    print("✓ Removed SynonymExpander initialization\n")

    # Step 3: Remove _preprocess_query method (lines ~366-415)
    print("Step 3: Removing _preprocess_query() method...")
    pattern3 = r"\s+def _preprocess_query\(self, query: str\) -> dict:.*?(?=\n    def )"
    content = re.sub(pattern3, "\n", content, flags=re.DOTALL)
    print("✓ Removed _preprocess_query() method\n")

    # Step 4: Remove _build_pubmed_query method (lines ~417-475)
    print("Step 4: Removing _build_pubmed_query() method...")
    pattern4 = r"\s+def _build_pubmed_query\(self, original_query: str, entities_by_type: dict\) -> str:.*?(?=\n    def )"
    content = re.sub(pattern4, "\n", content, flags=re.DOTALL)
    print("✓ Removed _build_pubmed_query() method\n")

    # Step 5: Remove _build_openalex_query method (lines ~477-525)
    print("Step 5: Removing _build_openalex_query() method...")
    pattern5 = r"\s+def _build_openalex_query\(self, original_query: str, entities_by_type: dict\) -> str:.*?(?=\n    def )"
    content = re.sub(pattern5, "\n", content, flags=re.DOTALL)
    print("✓ Removed _build_openalex_query() method\n")

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    new_lines = len(content.split("\n"))
    removed_lines = original_lines - new_lines

    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"Original lines: {original_lines}")
    print(f"New lines: {new_lines}")
    print(f"Lines removed: {removed_lines}")
    print()

    return removed_lines


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    removed = remove_duplicate_preprocessing()
    print(f"✓ Successfully removed {removed} lines of duplicate preprocessing")
