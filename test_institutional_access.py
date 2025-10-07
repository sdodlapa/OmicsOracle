#!/usr/bin/env python3
"""Quick test of institutional access functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
from omics_oracle_v2.lib.publications.clients.institutional_access import InstitutionalAccessManager, InstitutionType
from datetime import datetime

print("\n" + "=" * 80)
print(" INSTITUTIONAL ACCESS TEST")
print("=" * 80 + "\n")

# Create test publication
pub = Publication(
    title="CRISPR-Cas9 genome editing",
    authors=["Zhang, F."],
    abstract="Test",
    publication_date=datetime(2014, 1, 1),
    journal="Nature Biotechnology",
    doi="10.1038/nbt.2808",
    source=PublicationSource.PUBMED,
)

print(f"Publication: {pub.title}")
print(f"DOI: {pub.doi}\n")

# Test institutional access
manager = InstitutionalAccessManager(institution=InstitutionType.GEORGIA_TECH)
access_status = manager.check_access_status(pub)
access_url = manager.get_access_url(pub)

print(f"Access Status: {access_status}")
print(f"Access URL: {access_url}\n")

# Enrich metadata
pub.metadata["access_status"] = access_status
pub.metadata["has_access"] = any(access_status.values())
pub.metadata["access_url"] = access_url

print("✅ Institutional access working!")
print(f"✅ EZProxy URL generated: {access_url[:50]}...")
print(f"✅ Metadata enriched: has_access={pub.metadata['has_access']}\n")
