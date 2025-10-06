"""
Create sample GEO datasets for testing visualization features.

This script populates the database with realistic sample datasets
so you can test the semantic search UI without needing to fetch
real data from GEO.

Usage:
    python -m omics_oracle_v2.scripts.create_sample_data
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from omics_oracle_v2.database import async_session_maker
from omics_oracle_v2.models.geo_dataset import GEODataset

SAMPLE_DATASETS = [
    {
        "geo_id": "GSE12345",
        "title": "Comprehensive Molecular Portraits of Human Breast Tumors",
        "summary": "We conducted a comprehensive characterization of 825 breast tumors using DNA, RNA, and protein analysis platforms. This integrated genomic analysis revealed four main breast cancer classes when combining data from five platforms, each of which shows significant molecular heterogeneity. Somatic mutations in only three genes (TP53, PIK3CA, and GATA3) occurred at >10% incidence across all breast cancers.",
        "organism": "Homo sapiens",
        "sample_count": 825,
        "platform": "GPL570",
        "submission_date": datetime(2012, 3, 15),
        "last_update_date": datetime(2012, 10, 1),
        "pubmed_id": "23000897",
        "series_type": "Expression profiling by array",
        "contributor": "The Cancer Genome Atlas Network",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345",
    },
    {
        "geo_id": "GSE67890",
        "title": "Gene Expression Profiling of Breast Cancer Molecular Subtypes",
        "summary": "Microarray analysis of 150 breast cancer samples classified into molecular subtypes (Luminal A, Luminal B, HER2-enriched, and Basal-like). RNA was extracted from frozen tumor samples and hybridized to Affymetrix arrays. This study identifies distinct gene expression patterns associated with each subtype and potential therapeutic targets.",
        "organism": "Homo sapiens",
        "sample_count": 150,
        "platform": "GPL570",
        "submission_date": datetime(2015, 5, 20),
        "last_update_date": datetime(2015, 11, 15),
        "series_type": "Expression profiling by array",
        "contributor": "Memorial Sloan Kettering Cancer Center",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE67890",
    },
    {
        "geo_id": "GSE11111",
        "title": "RNA-seq Analysis of Tumor-Infiltrating Lymphocytes in Breast Cancer",
        "summary": "High-throughput RNA sequencing of tumor-infiltrating lymphocytes (TILs) from 200 breast cancer patients. This study characterizes the immune landscape of breast tumors and identifies prognostic immune gene signatures. Results show that high TIL infiltration is associated with better outcomes in triple-negative breast cancer.",
        "organism": "Homo sapiens",
        "sample_count": 200,
        "platform": "GPL24676",
        "submission_date": datetime(2019, 8, 10),
        "last_update_date": datetime(2020, 2, 5),
        "pubmed_id": "31234567",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "Dana-Farber Cancer Institute",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE11111",
    },
    {
        "geo_id": "GSE22222",
        "title": "Single-Cell RNA-seq of Breast Cancer Metastases",
        "summary": "Single-cell transcriptomic profiling of metastatic breast cancer cells from brain, bone, liver, and lung metastases. Over 50,000 cells were analyzed to identify metastasis-specific cell populations and signaling pathways. This dataset reveals organ-specific adaptations and potential vulnerabilities in metastatic cells.",
        "organism": "Homo sapiens",
        "sample_count": 75,
        "platform": "GPL24676",
        "submission_date": datetime(2021, 3, 25),
        "last_update_date": datetime(2021, 9, 10),
        "pubmed_id": "34567890",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "Stanford University",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE22222",
    },
    {
        "geo_id": "GSE33333",
        "title": "Epigenomic Landscape of Breast Cancer Progression",
        "summary": "Genome-wide DNA methylation profiling of breast cancer progression from ductal carcinoma in situ (DCIS) to invasive ductal carcinoma (IDC). ChIP-seq and ATAC-seq were used to map histone modifications and chromatin accessibility across 120 samples. Identifies epigenetic drivers of breast cancer progression and potential therapeutic targets.",
        "organism": "Homo sapiens",
        "sample_count": 120,
        "platform": "GPL20795",
        "submission_date": datetime(2020, 11, 5),
        "last_update_date": datetime(2021, 4, 20),
        "pubmed_id": "33456789",
        "series_type": "Genome binding/occupancy profiling by high throughput sequencing",
        "contributor": "University of Cambridge",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE33333",
    },
    {
        "geo_id": "GSE44444",
        "title": "Immune Response to Viral Infection in Lung Epithelial Cells",
        "summary": "Time-course RNA-seq analysis of human lung epithelial cells infected with influenza A virus. Samples collected at 0, 6, 12, 24, and 48 hours post-infection to characterize temporal dynamics of antiviral response. Identifies interferon-stimulated genes and potential therapeutic targets for viral pneumonia.",
        "organism": "Homo sapiens",
        "sample_count": 60,
        "platform": "GPL16791",
        "submission_date": datetime(2018, 7, 15),
        "last_update_date": datetime(2018, 12, 1),
        "pubmed_id": "30123456",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "University of Washington",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE44444",
    },
    {
        "geo_id": "GSE55555",
        "title": "Alzheimer's Disease Brain Transcriptomics Study",
        "summary": "RNA-seq analysis of post-mortem brain tissue from Alzheimer's disease patients and age-matched controls. Samples from hippocampus, prefrontal cortex, and entorhinal cortex (n=300 total). Identifies dysregulated pathways in neurodegeneration including synaptic function, inflammation, and protein aggregation.",
        "organism": "Homo sapiens",
        "sample_count": 300,
        "platform": "GPL24676",
        "submission_date": datetime(2017, 2, 10),
        "last_update_date": datetime(2017, 8, 25),
        "pubmed_id": "28901234",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "NIH/NIA",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE55555",
    },
    {
        "geo_id": "GSE66666",
        "title": "Pancreatic Cancer Organoid Drug Screening",
        "summary": "Patient-derived organoid models from pancreatic ductal adenocarcinoma tested against 140 FDA-approved drugs. RNA-seq before and after drug treatment to identify biomarkers of response. This dataset enables precision medicine approaches for pancreatic cancer treatment.",
        "organism": "Homo sapiens",
        "sample_count": 85,
        "platform": "GPL20301",
        "submission_date": datetime(2019, 4, 5),
        "last_update_date": datetime(2019, 10, 20),
        "pubmed_id": "31789012",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "MD Anderson Cancer Center",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE66666",
    },
    {
        "geo_id": "GSE77777",
        "title": "T Cell Exhaustion in Chronic Viral Infection",
        "summary": "Single-cell RNA-seq of CD8+ T cells during chronic LCMV infection in mice. Characterizes the transcriptional program of T cell exhaustion and identifies reversible vs. irreversible exhaustion states. Findings have implications for cancer immunotherapy and chronic viral infections.",
        "organism": "Mus musculus",
        "sample_count": 45,
        "platform": "GPL19057",
        "submission_date": datetime(2016, 9, 12),
        "last_update_date": datetime(2017, 1, 30),
        "pubmed_id": "27345678",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "Emory University",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE77777",
    },
    {
        "geo_id": "GSE88888",
        "title": "Gut Microbiome and Host Gene Expression in IBD",
        "summary": "Paired metatranscriptomics and host RNA-seq from intestinal biopsies of inflammatory bowel disease patients. Correlates microbial gene expression with host immune response. Identifies dysbiotic bacteria and host-microbe interactions driving intestinal inflammation.",
        "organism": "Homo sapiens",
        "sample_count": 180,
        "platform": "GPL18573",
        "submission_date": datetime(2020, 6, 18),
        "last_update_date": datetime(2021, 1, 5),
        "pubmed_id": "32567890",
        "series_type": "Expression profiling by high throughput sequencing",
        "contributor": "Broad Institute",
        "web_link": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE88888",
    },
]


async def create_sample_datasets():
    """Create sample GEO datasets in the database."""
    print("Creating sample GEO datasets...")

    async with async_session_maker() as session:
        # Check if datasets already exist
        result = await session.execute(select(GEODataset).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("WARNING: Database already contains datasets.")
            print("   Clear the database first if you want to recreate samples.")
            return

        # Create datasets
        created_count = 0
        for dataset_data in SAMPLE_DATASETS:
            dataset = GEODataset(**dataset_data)
            session.add(dataset)
            created_count += 1

        await session.commit()

        print(f"SUCCESS: Created {created_count} sample datasets")
        print("\nDatasets:")
        for ds in SAMPLE_DATASETS:
            print(f"  - {ds['geo_id']}: {ds['title'][:60]}...")

        print("\nNow you can:")
        print("  1. Visit http://localhost:8000/search")
        print("  2. Search for: 'breast cancer RNA-seq'")
        print("  3. Test visualizations with real data!")


async def clear_sample_datasets():
    """Clear all sample datasets from the database."""
    print("Clearing sample datasets...")

    async with async_session_maker() as session:
        # Delete all datasets
        result = await session.execute(select(GEODataset))
        datasets = result.scalars().all()

        for dataset in datasets:
            await session.delete(dataset)

        await session.commit()
        print(f"SUCCESS: Cleared {len(datasets)} datasets")


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear_sample_datasets()
    else:
        await create_sample_datasets()


if __name__ == "__main__":
    asyncio.run(main())
