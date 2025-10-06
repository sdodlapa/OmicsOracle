#!/usr/bin/env python3
"""
Quick script to create sample GEO datasets for embedding.

This creates a small set of realistic GEO datasets for testing semantic search.
"""

import json
from pathlib import Path

# Sample biomedical datasets
SAMPLE_DATASETS = [
    {
        "id": "GSE123456",
        "accession": "GSE123456",
        "title": "ATAC-seq analysis of chromatin accessibility in cancer cells",
        "summary": "We performed ATAC-seq to profile chromatin accessibility changes in breast cancer cell lines treated with epigenetic drugs. Results reveal widespread chromatin remodeling and identify potential therapeutic targets.",
        "organism": "Homo sapiens",
        "sample_count": 24,
        "platform": "GPL20301",
        "keywords": ["ATAC-seq", "chromatin accessibility", "breast cancer", "epigenetics"],
    },
    {
        "id": "GSE234567",
        "accession": "GSE234567",
        "title": "RNA-seq profiling of T cell differentiation states",
        "summary": "Single-cell RNA-seq of CD4+ T cells during differentiation into Th1, Th2, and Th17 subtypes. Analysis identifies transcription factors and signaling pathways driving lineage specification.",
        "organism": "Mus musculus",
        "sample_count": 48,
        "platform": "GPL24247",
        "keywords": ["RNA-seq", "T cells", "differentiation", "scRNA-seq"],
    },
    {
        "id": "GSE345678",
        "accession": "GSE345678",
        "title": "ChIP-seq mapping of histone modifications in stem cells",
        "summary": "Genome-wide ChIP-seq profiling of H3K4me3, H3K27me3, and H3K27ac in embryonic stem cells and differentiated neurons. Data reveals dynamic changes in chromatin states during neuronal differentiation.",
        "organism": "Homo sapiens",
        "sample_count": 36,
        "platform": "GPL20795",
        "keywords": ["ChIP-seq", "histone modifications", "stem cells", "differentiation"],
    },
    {
        "id": "GSE456789",
        "accession": "GSE456789",
        "title": "Microbiome analysis of gut bacteria in inflammatory bowel disease",
        "summary": "16S rRNA sequencing of gut microbiome samples from IBD patients and healthy controls. Results show significant dysbiosis with reduced diversity and altered metabolic pathways in IBD.",
        "organism": "human gut metagenome",
        "sample_count": 120,
        "platform": "GPL19293",
        "keywords": ["microbiome", "16S rRNA", "IBD", "gut bacteria"],
    },
    {
        "id": "GSE567890",
        "accession": "GSE567890",
        "title": "Proteomics analysis of Alzheimer disease brain tissue",
        "summary": "Mass spectrometry-based proteomics of hippocampal tissue from Alzheimer patients and age-matched controls. Identifies protein aggregation signatures and potential biomarkers for early diagnosis.",
        "organism": "Homo sapiens",
        "sample_count": 60,
        "platform": "GPL28019",
        "keywords": ["proteomics", "Alzheimer", "brain tissue", "mass spectrometry"],
    },
    {
        "id": "GSE678901",
        "accession": "GSE678901",
        "title": "Methylation profiling of tumor suppressor genes in lung cancer",
        "summary": "Genome-wide DNA methylation analysis using WGBS in lung adenocarcinoma samples. Identifies hypermethylated promoters of tumor suppressor genes correlating with poor prognosis.",
        "organism": "Homo sapiens",
        "sample_count": 80,
        "platform": "GPL24676",
        "keywords": ["methylation", "lung cancer", "WGBS", "tumor suppressors"],
    },
    {
        "id": "GSE789012",
        "accession": "GSE789012",
        "title": "Single-cell transcriptomics of pancreatic islet cells in diabetes",
        "summary": "scRNA-seq analysis of pancreatic islets from type 2 diabetes patients. Reveals heterogeneity in beta cell populations and identifies stress response signatures associated with dysfunction.",
        "organism": "Homo sapiens",
        "sample_count": 15,
        "platform": "GPL24676",
        "keywords": ["scRNA-seq", "diabetes", "pancreatic islets", "beta cells"],
    },
    {
        "id": "GSE890123",
        "accession": "GSE890123",
        "title": "Hi-C mapping of 3D genome organization in developmental stages",
        "summary": "Hi-C chromosome conformation capture in embryonic stem cells, neural progenitors, and differentiated neurons. Maps changes in chromatin loops and TAD boundaries during development.",
        "organism": "Mus musculus",
        "sample_count": 18,
        "platform": "GPL21103",
        "keywords": ["Hi-C", "3D genome", "development", "chromatin organization"],
    },
    {
        "id": "GSE901234",
        "accession": "GSE901234",
        "title": "CRISPR screen identifies regulators of immune checkpoint expression",
        "summary": "Genome-wide CRISPR-Cas9 knockout screen in melanoma cells identifies genes regulating PD-L1 expression. Validates targets that enhance immunotherapy response in mouse models.",
        "organism": "Homo sapiens",
        "sample_count": 96,
        "platform": "GPL24676",
        "keywords": ["CRISPR", "immunotherapy", "PD-L1", "melanoma"],
    },
    {
        "id": "GSE012345",
        "accession": "GSE012345",
        "title": "Metabolomics profiling of cancer cell metabolism under hypoxia",
        "summary": "LC-MS metabolomics analysis of cancer cells cultured under normoxic and hypoxic conditions. Identifies metabolic reprogramming and potential vulnerabilities for therapeutic targeting.",
        "organism": "Homo sapiens",
        "sample_count": 32,
        "platform": "GPL28019",
        "keywords": ["metabolomics", "cancer metabolism", "hypoxia", "LC-MS"],
    },
]


def create_sample_datasets(output_dir: str = "data/cache/geo_samples"):
    """Create sample GEO datasets for testing."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save as individual JSON files
    for dataset in SAMPLE_DATASETS:
        filename = f"{dataset['accession']}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(dataset, f, indent=2)

        print(f"✅ Created {filename}")

    # Also save as single combined file
    combined_path = output_path / "all_datasets.json"
    with open(combined_path, "w") as f:
        json.dump(SAMPLE_DATASETS, f, indent=2)

    print(f"\n✅ Created {len(SAMPLE_DATASETS)} sample datasets in {output_dir}/")
    print(f"✅ Combined file: {combined_path}")

    return SAMPLE_DATASETS


if __name__ == "__main__":
    datasets = create_sample_datasets()
    print(f"\nDatasets ready for embedding!")
    print(f"Total: {len(datasets)} datasets")
    print(
        f"Topics: ATAC-seq, RNA-seq, ChIP-seq, microbiome, proteomics, methylation, scRNA-seq, Hi-C, CRISPR, metabolomics"
    )
