#!/usr/bin/env python
"""Quick test of Google Scholar client - just one search."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.config import GoogleScholarConfig

print("="*70)
print("QUICK GOOGLE SCHOLAR TEST")
print("="*70)

try:
    # Create config
    config = GoogleScholarConfig(enable=True, rate_limit_seconds=3.0)
    print("✅ Config created")
    
    # Create client
    client = GoogleScholarClient(config)
    print(f"✅ Client initialized (source: {client.source_name})")
    
    # Quick search
    query = "CRISPR"
    print(f"\n🔍 Searching for: '{query}' (max 3 results)")
    print("   This will take ~10 seconds...")
    
    results = client.search(query, max_results=3)
    
    print(f"\n✅ SUCCESS! Found {len(results)} publications")
    
    for i, pub in enumerate(results, 1):
        print(f"\n{i}. {pub.title[:60]}...")
        print(f"   Citations: {pub.citations or 0}")
        print(f"   Year: {pub.publication_date.year if pub.publication_date else 'N/A'}")
        print(f"   Source: {pub.source}")
    
    print("\n" + "="*70)
    print("✅ GOOGLE SCHOLAR CLIENT IS WORKING!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
