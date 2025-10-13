"""
Debug script to test PMID 39997216 download step-by-step
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_step_by_step():
    print("\n" + "="*80)
    print("DEBUGGING PMID 39997216 (PMC11851118)")
    print("="*80)

    # Step 1: Fetch metadata from PubMed
    print("\n[STEP 1] Fetching metadata from PubMed...")
    from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig

    pubmed_client = PubMedClient(PubMedConfig(email="test@omicsoracle.ai"))
    pub = pubmed_client.fetch_by_id("39997216")

    if pub:
        print(f"✅ Metadata fetched successfully!")
        print(f"   - Title: {pub.title[:80]}...")
        print(f"   - DOI: {pub.doi}")
        print(f"   - PMC ID: {pub.pmcid}")
        print(f"   - Journal: {pub.journal}")
        print(f"   - Authors: {pub.authors[:3] if pub.authors else []}")
    else:
        print("❌ Failed to fetch metadata!")
        return

    # Step 2: Convert PMID to PMC ID
    print("\n[STEP 2] Checking PMC ID from metadata...")
    if pub.pmcid:
        print(f"✅ PMC ID found in metadata: {pub.pmcid}")
        print(f"   No need for E-utilities conversion!")
    else:
        print(f"⚠️ No PMC ID in metadata, would need E-utilities")
        print(f"   (Skipping E-utilities test due to SSL issues in test script)")

    # Step 3: Try PMC download
    print("\n[STEP 3] Testing PMC download...")
    from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
    from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

    config = FullTextManagerConfig(
        enable_institutional=False,
        enable_pmc=True,
        enable_unpaywall=False,
        enable_core=False,
        enable_scihub=False,
        timeout_per_source=30
    )

    manager = FullTextManager(config)
    await manager.initialize()

    # Use the full publication object
    result = await manager._try_pmc(pub)

    print(f"\n📊 PMC Result:")
    print(f"   - Success: {result.success}")
    print(f"   - Source: {result.source}")
    print(f"   - URL: {result.url}")
    print(f"   - PDF Path: {result.pdf_path}")
    print(f"   - Error: {result.error}")
    print(f"   - Metadata: {result.metadata}")

    # Step 4: Full waterfall test
    print("\n[STEP 4] Testing full waterfall (all sources)...")
    config_full = FullTextManagerConfig(
        enable_institutional=True,
        enable_pmc=True,
        enable_unpaywall=True,
        enable_core=True,
        enable_scihub=True,
        timeout_per_source=30
    )

    manager_full = FullTextManager(config_full)
    await manager_full.initialize()

    result_full = await manager_full.get_fulltext(pub)

    print(f"\n📊 Full Waterfall Result:")
    print(f"   - Success: {result_full.success}")
    print(f"   - Source: {result_full.source}")
    print(f"   - URL: {result_full.url}")
    print(f"   - PDF Path: {result_full.pdf_path}")
    print(f"   - Error: {result_full.error}")

    # Step 5: Test the actual service endpoint
    print("\n[STEP 5] Testing FullTextService (what the API uses)...")
    from omics_oracle_v2.services.fulltext_service import FullTextService
    from omics_oracle_v2.api.models.responses import DatasetResponse

    service = FullTextService()

    dataset = DatasetResponse(
        geo_id="GSE_TEST",
        title="Test Dataset",
        summary="Test",
        organism="Homo sapiens",
        pubmed_ids=["39997216"],
        relevance_score=1.0
    )

    enriched = await service.enrich_dataset_with_fulltext(dataset, max_papers=1)

    print(f"\n📊 Service Result:")
    print(f"   - Status: {enriched.fulltext_status}")
    print(f"   - Count: {enriched.fulltext_count}")
    print(f"   - Fulltext: {enriched.fulltext}")

    if enriched.fulltext_count > 0:
        print(f"\n🎉 SUCCESS! Paper downloaded via {result_full.source}")
    else:
        print(f"\n❌ FAILED! Status: {enriched.fulltext_status}")


if __name__ == "__main__":
    asyncio.run(test_step_by_step())
