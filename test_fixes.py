#!/usr/bin/env python3
"""
Quick test: Verify PDF download and data persistence fixes

Run after server restart and searching for GSE570
"""
import sqlite3
from pathlib import Path

print("=" * 80)
print("TESTING FIXES")
print("=" * 80)

# Test 1: Database Persistence
print("\n1. DATABASE PERSISTENCE TEST")
db_path = Path("data/database/omics_oracle.db")
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM geo_datasets")
    datasets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM universal_identifiers")
    citations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pdf_acquisition")
    pdfs = cursor.fetchone()[0]

    print(f"   geo_datasets: {datasets} rows")
    print(f"   universal_identifiers: {citations} rows")
    print(f"   pdf_acquisition: {pdfs} rows")

    if datasets > 0:
        print("   [OK] Datasets persisted to database")
        cursor.execute("SELECT geo_id, title, publication_count FROM geo_datasets")
        for row in cursor.fetchall():
            print(f"     - {row[0]}: {row[2]} citations")
    else:
        print("   [FAIL] No datasets persisted (search first)")

    conn.close()
else:
    print("   [FAIL] Database doesn't exist")

# Test 2: PDF Downloads
print("\n2. PDF DOWNLOAD TEST")
pdf_dir = Path("data/pdfs")
if pdf_dir.exists():
    pdf_folders = list(pdf_dir.glob("GSE*"))
    if pdf_folders:
        for folder in pdf_folders[:3]:
            pdfs = list(folder.glob("*.pdf"))
            print(f"   {folder.name}: {len(pdfs)} PDFs")
        print("   [OK] PDFs downloaded")
    else:
        print("   [WARN] No PDF folders (click 'Download Papers' first)")
else:
    print("   [WARN] PDF directory doesn't exist yet")

# Test 3: Server Status
print("\n3. NEXT STEPS")
print("   1. Search for 'GSE570' in dashboard")
print("   2. Click 'Download Papers' button")
print("   3. Re-run this script to verify both fixes")
print("   4. Restart server and search again (should be instant from DB)")

print("=" * 80)
