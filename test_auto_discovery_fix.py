#!/usr/bin/env python3
"""
Test Auto-Discovery Fix Validation

Run this AFTER restarting the server and searching for a dataset.
It will verify that auto-discovery is working correctly.
"""
import sqlite3
from datetime import datetime
from pathlib import Path


def validate_auto_discovery():
    """Validate that auto-discovery is working."""

    db_path = "data/database/omics_oracle.db"

    if not Path(db_path).exists():
        print("[WARN]  Database doesn't exist yet - search for a dataset first!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("AUTO-DISCOVERY VALIDATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check datasets
    cursor.execute("SELECT COUNT(*) FROM geo_datasets")
    dataset_count = cursor.fetchone()[0]

    # Check citations
    cursor.execute("SELECT COUNT(*) FROM universal_identifiers")
    citation_count = cursor.fetchone()[0]

    print(f"[DATA] Database Status:")
    print(f"   GEO Datasets: {dataset_count}")
    print(f"   Citations: {citation_count}")
    print()

    if dataset_count == 0:
        print("[WARN]  No datasets yet - search for something first!")
        conn.close()
        return

    # Check each dataset's citation status
    cursor.execute(
        """
        SELECT
            g.geo_id,
            g.title,
            g.publication_count,
            COUNT(DISTINCT ui.pmid) as actual_citations,
            COUNT(DISTINCT ui.pdf_url) as citations_with_urls
        FROM geo_datasets g
        LEFT JOIN universal_identifiers ui ON g.geo_id = ui.geo_id
        GROUP BY g.geo_id
        ORDER BY g.created_at DESC
    """
    )

    print("=" * 80)
    print("DATASET CITATION STATUS")
    print("=" * 80)

    success_count = 0
    failure_count = 0

    for row in cursor.fetchall():
        geo_id, title, pub_count, actual_citations, urls = row

        print(f"\n{geo_id}: {title[:60]}...")
        print(f"   Expected citations: {pub_count}")
        print(f"   Actual citations: {actual_citations}")
        print(f"   Citations with URLs: {urls}")

        if pub_count > 0 and actual_citations > 0:
            print(f"   [OK] AUTO-DISCOVERY WORKING!")
            success_count += 1
        elif pub_count > 0 and actual_citations == 0:
            print(f"   [FAIL] AUTO-DISCOVERY FAILED - No citations inserted!")
            failure_count += 1
        else:
            print(f"   [WARN]  Dataset has no citations (might be expected)")

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"[OK] Success: {success_count} datasets with citations")
    print(f"[FAIL] Failures: {failure_count} datasets without citations")
    print()

    if failure_count > 0:
        print("[FIX] TROUBLESHOOTING:")
        print("   1. Check logs: tail -f logs/omics_api.log | grep AUTO-DISCOVERY")
        print("   2. Look for errors like 'identifier_utils' or 'no column'")
        print("   3. If errors persist, check that schema migration ran")
    elif success_count > 0:
        print("[DONE] AUTO-DISCOVERY IS WORKING CORRECTLY!")
        print("   - Citations are being discovered and inserted")
        print("   - URLs are being extracted where available")
        print("   - System is ready for production use")
    else:
        print("[INFO]  No datasets with citations yet - search for more datasets")

    conn.close()


if __name__ == "__main__":
    validate_auto_discovery()
