#!/usr/bin/env python3
"""
Test search with PubMed ONLY (bypassing SSL verification for testing)
This is for debugging network/SSL issues.
"""

import os
import ssl
import sys
import urllib.request

# Temporarily disable SSL verification (FOR TESTING ONLY)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

print("\n" + "=" * 60)
print("Testing PubMed with SSL verification DISABLED (test only)")
print("=" * 60 + "\n")

# Configure PubMed only
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_scholar=False,
)

pipeline = PublicationSearchPipeline(config)

# Test query
query = "cancer genomics"
print(f"Query: {query}")
print(f"Max results: 5\n")

import time

start = time.time()

try:
    result = pipeline.search(query=query, max_results=5)
    elapsed = (time.time() - start) * 1000

    print(f"\nResults:")
    print(f"  - Publications found: {len(result.publications)}")
    print(f"  - Sources used: {result.sources_used}")
    print(f"  - Search time: {elapsed:.2f}ms")

    if result.publications:
        print(f"\n✅ SUCCESS! PubMed works (with SSL disabled)")
        print(f"\nFirst 3 results:")
        for i, search_result in enumerate(result.publications[:3], 1):
            pub = search_result.publication
            authors_str = ", ".join(pub.authors[:3]) if pub.authors else "N/A"
            if len(pub.authors) > 3:
                authors_str += f" (+ {len(pub.authors) - 3} more)"
            year = pub.publication_date.year if pub.publication_date else "N/A"
            print(f"\n  {i}. {pub.title}")
            print(f"     Authors: {authors_str}")
            print(f"     Year: {year}")
            print(f"     Journal: {pub.journal or 'N/A'}")
            print(f"     Relevance: {search_result.relevance_score:.1f}/100")
    else:
        print(f"\n⚠️ No results but no errors - PubMed connection works!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("NOTE: This test DISABLES SSL verification")
print("For production, you need to:")
print("  1. Install your institution's SSL certificate")
print("  2. Or use only Google Scholar (if not blocked)")
print("  3. Or configure proxy with proper SSL")
print("=" * 60 + "\n")
