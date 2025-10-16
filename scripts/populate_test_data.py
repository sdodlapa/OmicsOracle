"""
Populate UnifiedDB with test data for benchmarking.
Quick script to insert sample GEO datasets for validation.
"""
import asyncio
from datetime import datetime, timezone
from omics_oracle_v2.lib.pipelines.storage import UnifiedDatabase, GEODataset, UniversalIdentifier

async def populate_test_data():
    """Insert test GEO datasets into UnifiedDB."""
    db = UnifiedDatabase("data/database/omics_oracle.db")
    
    test_datasets = [
        {
            "geo_id": "GSE234968",
            "title": "RNA-seq analysis of cancer immunotherapy response",
            "summary": "Transcriptomic profiling of tumor samples treated with immunotherapy",
            "organism": "Homo sapiens",
            "platform": "Illumina NovaSeq 6000",
            "sample_count": 48,
            "submission_date": "2023-01-15",
            "publication_date": "2023-06-20",
            "relevance_score": 0.95,
            "match_reasons": ["cancer", "immunotherapy", "RNA-seq"]
        },
        {
            "geo_id": "GSE184471",
            "title": "Single-cell RNA-seq of immune cells in melanoma",
            "summary": "scRNA-seq analysis of tumor-infiltrating lymphocytes",
            "organism": "Homo sapiens",
            "platform": "10x Genomics",
            "sample_count": 24,
            "submission_date": "2022-08-10",
            "publication_date": "2023-02-15",
            "relevance_score": 0.88,
            "match_reasons": ["cancer", "immune cells", "single-cell"]
        },
        {
            "geo_id": "GSE189158",
            "title": "Bulk RNA-seq of breast cancer patients",
            "summary": "Transcriptome analysis of breast cancer tumor biopsies",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 4000",
            "sample_count": 120,
            "submission_date": "2022-11-05",
            "publication_date": "2023-04-12",
            "relevance_score": 0.82,
            "match_reasons": ["breast cancer", "RNA-seq", "tumor"]
        },
    ]
    
    print("=" * 60)
    print("Populating UnifiedDB with test data...")
    print("=" * 60)
    
    for data in test_datasets:
        # Create GEO dataset
        dataset = GEODataset(
            geo_id=data["geo_id"],
            title=data["title"],
            summary=data["summary"],
            organism=data["organism"],
            platform=data["platform"],
            publication_count=1,
            pdfs_downloaded=0,
            pdfs_extracted=0,
            avg_extraction_quality=0.0,
            created_at=datetime.now(timezone.utc).isoformat(),
            last_processed_at=datetime.now(timezone.utc).isoformat(),
            status="active"
        )
        
        # Insert into database
        db.insert_geo_dataset(dataset)
        print(f"✅ Inserted: {data['geo_id']} - {data['title'][:50]}...")
        
        # Add sample publication link
        pub = UniversalIdentifier(
            geo_id=data["geo_id"],
            pmid=f"3{data['geo_id'][3:]}",  # Fake PMID for testing
            title=data["title"],
            doi=f"10.1234/{data['geo_id'].lower()}",
            authors='["Smith J", "Jones A"]',  # JSON string
            journal="Nature Methods",
            publication_year=2023,
            first_discovered_at=datetime.now(timezone.utc).isoformat(),
            last_updated_at=datetime.now(timezone.utc).isoformat()
        )
        db.insert_universal_identifier(pub)
        print(f"   + Linked publication: PMID {pub.pmid}")
    
    # Verify insertion
    stats = db.get_database_statistics()
    print("\n" + "=" * 60)
    print("Database Statistics:")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    print("✅ Test data population complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(populate_test_data())
