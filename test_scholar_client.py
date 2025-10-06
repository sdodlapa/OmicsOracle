#!/usr/bin/env python
"""
Test script for Google Scholar client.

This script tests the GoogleScholarClient implementation with real
Google Scholar searches to verify functionality.

Note: This makes real web requests to Google Scholar. Use sparingly
to avoid getting blocked.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.config import GoogleScholarConfig


def test_scholar_search():
    """Test basic Google Scholar search."""
    print("\n" + "="*70)
    print("TEST: Google Scholar Search")
    print("="*70)
    
    try:
        # Create config
        config = GoogleScholarConfig(
            enable=True,
            max_results=50,
            rate_limit_seconds=3.0
        )
        
        print(f"✅ Config created")
        print(f"   - Rate limit: {config.rate_limit_seconds}s")
        print(f"   - Max results: {config.max_results}")
        
        # Create client
        client = GoogleScholarClient(config)
        print(f"✅ Client initialized")
        
        # Perform search
        query = "CRISPR cancer therapy"
        max_results = 5
        
        print(f"\n🔍 Searching Scholar for: '{query}'")
        print(f"   (This may take ~{max_results * config.rate_limit_seconds}s due to rate limiting)")
        
        results = client.search(query, max_results=max_results)
        
        print(f"\n✅ Search completed!")
        print(f"   - Found: {len(results)} publications")
        
        # Display results
        print(f"\n📊 Top {len(results)} Results:")
        for i, pub in enumerate(results, 1):
            print(f"\n{i}. {pub.title[:70]}...")
            print(f"   - Authors: {', '.join(pub.authors[:3]) if pub.authors else 'N/A'}")
            print(f"   - Journal: {pub.journal or 'N/A'}")
            print(f"   - Year: {pub.publication_date.year if pub.publication_date else 'N/A'}")
            print(f"   - Citations: {pub.citations or 0}")
            print(f"   - DOI: {pub.doi or 'N/A'}")
            print(f"   - Source: {pub.source}")
            
            # Scholar-specific metadata
            if pub.metadata.get('scholar_id'):
                print(f"   - Scholar ID: {pub.metadata['scholar_id']}")
            if pub.metadata.get('pdf_url'):
                print(f"   - PDF: {pub.metadata['pdf_url'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scholar_fetch_by_doi():
    """Test fetching by DOI."""
    print("\n" + "="*70)
    print("TEST: Fetch by DOI")
    print("="*70)
    
    try:
        config = GoogleScholarConfig(enable=True)
        client = GoogleScholarClient(config)
        
        # Use a well-known DOI (CRISPR paper)
        doi = "10.1126/science.1258096"
        
        print(f"🔍 Fetching publication by DOI: {doi}")
        print(f"   (This may take a few seconds...)")
        
        pub = client.fetch_by_doi(doi)
        
        if pub:
            print(f"\n✅ Publication found!")
            print(f"   - Title: {pub.title[:70]}...")
            print(f"   - Citations: {pub.citations or 0}")
            print(f"   - DOI: {pub.doi}")
            return True
        else:
            print(f"\n⚠️  No publication found for DOI: {doi}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scholar_citations():
    """Test getting citations for a publication."""
    print("\n" + "="*70)
    print("TEST: Get Citations")
    print("="*70)
    
    try:
        from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
        from datetime import datetime
        
        config = GoogleScholarConfig(enable=True)
        client = GoogleScholarClient(config)
        
        # Create a test publication
        pub = Publication(
            title="CRISPR-Cas9 gene editing",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2015, 1, 1)
        )
        
        print(f"🔍 Getting citations for: '{pub.title}'")
        print(f"   (This may take a few seconds...)")
        
        citations = client.get_citations(pub)
        
        print(f"\n✅ Citations retrieved: {citations}")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scholar_year_range():
    """Test searching with year range filter."""
    print("\n" + "="*70)
    print("TEST: Year Range Filter")
    print("="*70)
    
    try:
        config = GoogleScholarConfig(enable=True)
        client = GoogleScholarClient(config)
        
        query = "machine learning genomics"
        year_from = 2020
        year_to = 2024
        
        print(f"🔍 Searching: '{query}'")
        print(f"   Year range: {year_from}-{year_to}")
        print(f"   (This may take ~15s...)")
        
        results = client.search(
            query, 
            max_results=5,
            year_from=year_from,
            year_to=year_to
        )
        
        print(f"\n✅ Found {len(results)} publications")
        
        # Verify year range
        for pub in results:
            if pub.publication_date:
                year = pub.publication_date.year
                print(f"   - {year}: {pub.title[:50]}...")
                
                if not (year_from <= year <= year_to):
                    print(f"   ⚠️  Year {year} outside range!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Scholar client tests."""
    print("\n" + "="*70)
    print("GOOGLE SCHOLAR CLIENT TESTS")
    print("="*70)
    print("\n⚠️  WARNING: These tests make real requests to Google Scholar")
    print("   - Rate limited to 1 request per 3 seconds")
    print("   - Total test time: ~1-2 minutes")
    print("   - May be blocked if run too frequently")
    print("\n" + "="*70)
    
    tests = [
        ("Basic Search", test_scholar_search),
        ("Fetch by DOI", test_scholar_fetch_by_doi),
        ("Get Citations", test_scholar_citations),
        ("Year Range Filter", test_scholar_year_range),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}...")
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Scholar client is working!")
        print("\n✅ Next steps:")
        print("   1. Integrate Scholar into PublicationSearchPipeline")
        print("   2. Implement multi-source deduplication")
        print("   3. Test PubMed + Scholar together")
        return 0
    else:
        print("\n⚠️  Some tests failed - review errors above")
        print("   Note: Scholar can be flaky due to rate limiting")
        print("   If all tests fail, you may be temporarily blocked")
        return 1


if __name__ == "__main__":
    sys.exit(main())
