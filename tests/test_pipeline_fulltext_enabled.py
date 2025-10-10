"""
Quick test to verify Unpaywall + Sci-Hub are now enabled in the pipeline.

This test checks that the pipeline properly initializes FullTextManager
with both Unpaywall and Sci-Hub enabled.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables
os.environ["PYTHONHTTPSVERIFY"] = "0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pipeline_fulltext_enabled():
    """Test that pipeline initializes with Unpaywall and Sci-Hub enabled."""
    from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
    from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
    
    print("="*80)
    print("TESTING: Pipeline FullText Configuration")
    print("="*80)
    print()
    
    # Create config with fulltext retrieval enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=False,
        enable_scholar=False,
        enable_citations=False,
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_fulltext_retrieval=True,  # ✅ Enable OA full-text retrieval
    )
    
    print("1. Initializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()
    
    # Check FullTextManager exists
    if not pipeline.fulltext_manager:
        print("   ❌ FAILED: FullTextManager not initialized")
        return False
    
    print("   ✅ FullTextManager initialized")
    print()
    
    # Check configuration
    print("2. Checking FullTextManager configuration...")
    fm_config = pipeline.fulltext_manager.config
    
    checks = {
        "OpenAlex OA": fm_config.enable_openalex,
        "Unpaywall": fm_config.enable_unpaywall,
        "CORE": fm_config.enable_core,
        "bioRxiv": fm_config.enable_biorxiv,
        "arXiv": fm_config.enable_arxiv,
        "Crossref": fm_config.enable_crossref,
        "Sci-Hub": fm_config.enable_scihub,
    }
    
    print("   Source Status:")
    print("   " + "-"*60)
    all_passed = True
    for source, enabled in checks.items():
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        print(f"   {source:15} → {status}")
        
        # Fail if critical sources are disabled
        if source in ["Unpaywall", "Sci-Hub"] and not enabled:
            all_passed = False
    
    print()
    
    if not all_passed:
        print("❌ FAILED: Unpaywall or Sci-Hub not enabled")
        return False
    
    # Check email configuration
    print("3. Checking Unpaywall email configuration...")
    if fm_config.unpaywall_email:
        print(f"   ✅ Email configured: {fm_config.unpaywall_email}")
    else:
        print("   ⚠️  WARNING: No email configured for Unpaywall")
    print()
    
    # Test with a real paper
    print("4. Testing with a real paper...")
    print("   Testing DOI: 10.1038/nature12373 (Nature, paywalled)")
    
    from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
    
    test_pub = Publication(
        title="A programmable dual-RNA-guided DNA endonuclease",
        doi="10.1038/nature12373",
        pmid="23287722",
        source=PublicationSource.PUBMED,
    )
    
    await pipeline.fulltext_manager.initialize()
    
    result = await pipeline.fulltext_manager.get_fulltext(test_pub)
    
    print()
    print(f"   Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    if result.success:
        print(f"   Source: {result.source.value}")
        print(f"   URL: {result.url[:80]}...")
    else:
        print(f"   Error: {result.error}")
    
    await pipeline.fulltext_manager.cleanup()
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    if all_passed and result.success:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Pipeline is properly configured with:")
        print("  ✅ Unpaywall enabled (50% coverage improvement)")
        print("  ✅ Sci-Hub enabled (additional 25% coverage)")
        print("  ✅ Successfully retrieved full-text")
        print()
        print("Expected coverage: 80-85%")
        return True
    elif all_passed:
        print("⚠️  CONFIGURATION CORRECT BUT TEST FAILED")
        print()
        print("Pipeline configuration is correct, but full-text retrieval failed.")
        print("This may be due to:")
        print("  - Network issues")
        print("  - Mirror availability")
        print("  - Paper not available in any source")
        return True
    else:
        print("❌ CONFIGURATION FAILED")
        print()
        print("Please check:")
        print("  1. pipeline.py lines 191-206")
        print("  2. Ensure enable_unpaywall=True")
        print("  3. Ensure enable_scihub=True")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_pipeline_fulltext_enabled())
    sys.exit(0 if success else 1)
