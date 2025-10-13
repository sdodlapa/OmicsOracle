"""Debug deduplication issue."""

from datetime import datetime

from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Create two pubs with same DOI
pub1 = Publication(
    pmid="12345678",
    doi="10.1234/test1",
    title="CRISPR gene editing in cancer therapy",
    abstract="Study on CRISPR for cancer treatment",
    authors=["Smith J", "Jones A"],
    journal="Nature",
    publication_date=datetime(2023, 1, 15),
    source=PublicationSource.PUBMED,
)

pub2 = Publication(
    doi="10.1234/test1",  # Same DOI
    title="CRISPR gene editing in cancer therapy",
    abstract="Study on CRISPR for cancer treatment",
    authors=["Smith J", "Jones A"],
    journal="Nature",
    publication_date=datetime(2023, 1, 15),
    source=PublicationSource.GOOGLE_SCHOLAR,
    citation_count=150,
)

print(f"Pub1 primary_id: {pub1.primary_id}")
print(f"Pub2 primary_id: {pub2.primary_id}")
print(f"Are they equal? {pub1.primary_id == pub2.primary_id}")
print(f"Pub1 == Pub2? {pub1 == pub2}")

# Test deduplication
publications = [pub1, pub2]
seen_ids = set()
unique_pubs = []

for pub in publications:
    pub_id = pub.primary_id
    print(f"\nChecking {pub.source}: primary_id={pub_id}")
    if pub_id not in seen_ids:
        print("  -> Adding to unique list")
        seen_ids.add(pub_id)
        unique_pubs.append(pub)
    else:
        print("  -> Already seen, skipping")

print("\nOriginal count:", len(publications))
print("Unique count:", len(unique_pubs))
print("Deduplication working:", len(unique_pubs) == 1)
