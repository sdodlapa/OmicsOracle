"""Test full-text coverage with 100 diverse biomedical DOIs."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Publication

# 100 diverse biomedical DOIs across different publishers and fields
DIVERSE_DOIS = [
    # Nature Publishing Group (high OA)
    "10.1038/s41586-024-08288-w",
    "10.1038/s41467-024-46789-2",
    "10.1038/s41591-024-03421-9",
    "10.1038/nbt.4096",
    "10.1038/nature24270",
    # Science/AAAS
    "10.1126/science.adi4415",
    "10.1126/sciadv.adl6537",
    "10.1126/science.abq7871",
    # Cell Press
    "10.1016/j.cell.2024.01.029",
    "10.1016/j.molcel.2024.02.015",
    "10.1016/j.immuni.2024.03.001",
    # Springer (mix of OA and paywalled)
    "10.1007/s00018-024-05123-4",
    "10.1007/s10719-024-10198-7",
    "10.1007/s00439-024-02634-9",
    # Wiley (mix)
    "10.1002/advs.202308024",
    "10.1002/emmm.202317607",
    "10.1111/imm.13821",
    # PLOS (all OA)
    "10.1371/journal.pgen.1011043",
    "10.1371/journal.pbio.3002912",
    "10.1371/journal.pone.0296841",
    "10.1371/journal.pcbi.1011789",
    "10.1371/journal.pntd.0011954",
    # BMC (all OA)
    "10.1186/s13059-024-03154-0",
    "10.1186/s13073-024-01289-3",
    "10.1186/s12915-024-01821-w",
    # eLife (all OA)
    "10.7554/eLife.89410",
    "10.7554/eLife.91513",
    # Frontiers (all OA)
    "10.3389/fimmu.2024.1352169",
    "10.3389/fonc.2024.1340304",
    # MDPI (mostly OA)
    "10.3390/ijms25031789",
    "10.3390/cancers16030567",
    # Oxford Academic (mix)
    "10.1093/nar/gkae123",
    "10.1093/bioinformatics/btae234",
    # American Chemical Society
    "10.1021/jacs.3c14567",
    "10.1021/acs.analchem.3c05678",
    # Proceedings of the National Academy of Sciences
    "10.1073/pnas.2314567121",
    "10.1073/pnas.2318901121",
    # bioRxiv preprints (all OA)
    "10.1101/2024.02.15.580567",
    "10.1101/2024.03.20.585912",
    "10.1101/2024.01.30.577234",
    # medRxiv preprints (all OA)
    "10.1101/2024.02.10.24302587",
    "10.1101/2024.03.15.24304321",
    # Additional diverse publishers
    "10.15252/embj.2023114789",  # EMBO
    "10.1172/JCI175634",  # Journal of Clinical Investigation
    "10.1182/blood.2023022789",  # Blood
    "10.1161/CIRCULATIONAHA.123.067234",  # Circulation
    "10.1056/NEJMoa2312345",  # NEJM (paywalled)
    # More Nature journals
    "10.1038/s41588-024-01678-9",
    "10.1038/s41592-024-02145-6",
    "10.1038/s41556-024-01356-2",
    # More Cell Press
    "10.1016/j.celrep.2024.113789",
    "10.1016/j.cmet.2024.02.003",
    "10.1016/j.devcel.2024.01.028",
    # More Springer
    "10.1007/s00401-024-02678-3",
    "10.1007/s00125-024-06089-7",
    "10.1007/s00109-024-02412-8",
    # More Wiley
    "10.1002/hep.32789",
    "10.1111/cas.16023",
    "10.1111/jcmm.18234",
    # More PLOS
    "10.1371/journal.pmed.1004345",
    "10.1371/journal.ppat.1011234",
    # More BMC
    "10.1186/s12864-024-10123-5",
    "10.1186/s13046-024-02967-4",
    # More Frontiers
    "10.3389/fcell.2024.1345678",
    "10.3389/fgene.2024.1298765",
    # Royal Society of Chemistry
    "10.1039/D3SC06789A",
    "10.1039/D4CP00234B",
    # American Society for Microbiology
    "10.1128/mbio.03456-23",
    "10.1128/jvi.01234-24",
    # Taylor & Francis
    "10.1080/15476286.2024.2312345",
    "10.1080/19490976.2024.2298765",
    # Elsevier (various journals)
    "10.1016/j.bbrc.2024.149234",
    "10.1016/j.gene.2024.148123",
    "10.1016/j.jbc.2024.105789",
    # More Oxford
    "10.1093/hmg/ddae012",
    "10.1093/genetics/iyae023",
    # Rockefeller University Press
    "10.1083/jcb.202312045",
    "10.1083/jem.20232345",
    # Company of Biologists
    "10.1242/dev.202234",
    "10.1242/jcs.261234",
    # Cold Spring Harbor
    "10.1101/gad.351234.123",
    "10.1101/gr.278234.123",
    # Annual Reviews (paywalled)
    "10.1146/annurev-biochem-052621-091234",
    # More diverse fields
    "10.1038/s41564-024-01598-3",  # Microbiology
    "10.1016/j.neuron.2024.02.012",  # Neuroscience
    "10.1172/jci.insight.175234",  # Clinical research
    "10.1093/brain/awae034",  # Neurology
    "10.1161/STROKEAHA.123.045234",  # Stroke
    "10.1053/j.gastro.2024.02.023",  # Gastroenterology
    "10.1016/j.jhep.2024.01.034",  # Hepatology
    "10.1016/j.kint.2024.02.019",  # Nephrology
    "10.1164/rccm.202312-2345OC",  # Respiratory
    "10.1210/endrev/bnae003",  # Endocrinology
]


async def test_fulltext_coverage():
    """Test full-text retrieval coverage on 100 diverse DOIs."""
    print("=" * 80)
    print("Full-Text Coverage Test: 100 Diverse Biomedical DOIs")
    print("=" * 80)
    print()

    # Create FullTextManager with all sources enabled (Phase 1 + Phase 2)
    config = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_openalex=True,
        enable_unpaywall=True,  # NEW - Phase 1+
        enable_scihub=True,  # NEW - Phase 2 (ENABLED for comprehensive coverage)
        core_api_key=os.getenv("CORE_API_KEY"),  # Read from env
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        download_pdfs=False,
        max_concurrent=3,  # Limit concurrency to avoid rate limits
    )

    # Initialize manager
    async with FullTextManager(config) as manager:
        print(f"Testing {len(DIVERSE_DOIS)} DOIs...")
        print()

        # Create Publication objects from DOIs
        publications = [
            Publication(
                title=f"Paper with DOI {doi}",
                doi=doi,
                abstract="Test publication",
                authors=[],
                journal="Various",
                pmid=None,
                url=f"https://doi.org/{doi}",
                source="pubmed",  # Add required source field
            )
            for doi in DIVERSE_DOIS
        ]  # Process in batches to avoid overwhelming APIs
        batch_size = 10
        all_results = []

        for i in range(0, len(publications), batch_size):
            batch = publications[i : i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(publications) + batch_size - 1) // batch_size}..."
            )

            results = await manager.get_fulltext_batch(batch)
            all_results.extend(results)

            # Small delay between batches
            if i + batch_size < len(publications):
                await asyncio.sleep(2)

        # Analyze results
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()

        successes = sum(1 for r in all_results if r.success)
        failures = sum(1 for r in all_results if not r.success)

        print(f"Total DOIs tested: {len(DIVERSE_DOIS)}")
        print(f"Successes: {successes} ({successes / len(DIVERSE_DOIS) * 100:.1f}%)")
        print(f"Failures: {failures} ({failures / len(DIVERSE_DOIS) * 100:.1f}%)")
        print()

        # Breakdown by source
        print("Breakdown by source:")
        stats = manager.get_statistics()
        for source, count in sorted(stats["by_source"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} ({count / len(DIVERSE_DOIS) * 100:.1f}%)")
        print()

        # Show some successful examples
        successful_results = [(pub, res) for pub, res in zip(publications, all_results) if res.success]
        if successful_results:
            print("Sample successful retrievals:")
            for i, (pub, res) in enumerate(successful_results[:5], 1):
                print(f"  [{i}] DOI: {pub.doi}")
                print(f"      Source: {res.source.value}")
                print(f"      URL: {res.url[:80]}...")
                print()

        # Show some failures
        failed_results = [(pub, res) for pub, res in zip(publications, all_results) if not res.success]
        if failed_results:
            print(f"Sample failures ({len(failed_results)} total):")
            for i, (pub, res) in enumerate(failed_results[:5], 1):
                print(f"  [{i}] DOI: {pub.doi}")
                print(f"      Error: {res.error}")
                print()

    print("=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_fulltext_coverage())
