#!/usr/bin/env python3
"""
Test Google Scholar availability and citation access.
Run this periodically to check if Scholar has unblocked.
"""

import os
import ssl
import time
from datetime import datetime

# Disable SSL verification
os.environ["PYTHONHTTPSVERIFY"] = "0"
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from scholarly import scholarly

    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    print("❌ scholarly library not installed")
    print("   Install: pip install scholarly")
    exit(1)

print("=" * 60)
print("  Google Scholar Availability Test")
print("=" * 60)
print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test 1: Simple search
print("Test 1: Basic search...")
try:
    search_query = scholarly.search_pubs("cancer", year_low=2024)
    result = next(search_query)

    print("✅ Google Scholar is WORKING!")
    print(f"\nSample result:")
    print(f"  Title: {result['bib']['title'][:60]}...")
    print(f"  Year: {result['bib'].get('pub_year', 'N/A')}")
    print(f"  Citations: {result.get('num_citations', 0)}")

    scholar_working = True

except StopIteration:
    print("⚠️  Search returned no results (possibly blocked)")
    scholar_working = False

except Exception as e:
    error_msg = str(e)
    if "Cannot Fetch" in error_msg:
        print("❌ Google Scholar is BLOCKED")
        print("   Error: Cannot Fetch from Google Scholar")
    else:
        print(f"❌ Error: {error_msg}")
    scholar_working = False

print("\n" + "-" * 60)

# Test 2: Get citation count
if scholar_working:
    print("\nTest 2: Citation extraction...")
    try:
        search_query = scholarly.search_pubs("deep learning", year_low=2020)
        result = next(search_query)

        citations = result.get("num_citations", 0)
        print(f"✅ Citation count: {citations}")

        if citations > 0:
            print("✅ Citation metrics are available!")
        else:
            print("⚠️  No citations (may be recent paper)")

    except Exception as e:
        print(f"❌ Citation test failed: {e}")

print("\n" + "=" * 60)

# Summary
if scholar_working:
    print("\n🎉 SUCCESS! Google Scholar is accessible!")
    print("\nNext steps:")
    print("1. Enable Scholar in dashboard:")
    print("   - Check ✓ Google Scholar box")
    print("   - Search will include citations")
    print("\n2. Search example:")
    print("   Query: cancer genomics")
    print("   Expected: Citations > 0")

else:
    print("\n⏰ Google Scholar is still blocked.")
    print("\nOptions:")
    print("1. Wait 15-30 more minutes, then run this script again")
    print("2. Slow down rate limit to 10 seconds (see GOOGLE_SCHOLAR_CITATION_GUIDE.md)")
    print("3. Use proxy service (ScraperAPI - $49/mo)")
    print("4. Use alternative: Semantic Scholar API (free)")
    print("\nRun this script again in 30 minutes:")
    print(f"  python {__file__}")

print("\n" + "=" * 60 + "\n")
