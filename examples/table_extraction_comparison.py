"""
Advanced PDF Table Extraction Demo

Compares three approaches:
1. PyMuPDF (fitz) - Fast but basic
2. pdfplumber - Good for simple tables
3. camelot - Best for complex scientific tables

Shows when to use each tool.
"""

import sys
from pathlib import Path
import json

# PDF extraction libraries
import fitz  # PyMuPDF
import pdfplumber
import camelot
import pandas as pd


def test_pymupdf_tables(pdf_path: Path):
    """
    PyMuPDF approach: Extract text blocks and try to identify tables.
    
    Pros: Very fast
    Cons: No structured table extraction, manual parsing needed
    """
    print("\n" + "=" * 80)
    print("1. PyMuPDF (fitz) - Fast but requires manual table parsing")
    print("=" * 80)
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(min(3, len(doc))):  # First 3 pages
        page = doc[page_num]
        
        # Get text as blocks
        blocks = page.get_text("dict")["blocks"]
        text_blocks = [b for b in blocks if b["type"] == 0]
        
        print(f"\nPage {page_num + 1}:")
        print(f"  Text blocks: {len(text_blocks)}")
        
        # Try to identify potential tables (heuristic: blocks with multiple lines)
        potential_tables = [
            b for b in text_blocks
            if len(b.get("lines", [])) > 3
        ]
        print(f"  Potential table blocks: {len(potential_tables)}")
        
        if potential_tables:
            # Show first potential table
            table_block = potential_tables[0]
            lines = table_block.get("lines", [])
            print(f"  First table-like block ({len(lines)} lines):")
            
            # Extract text from first few lines
            for i, line in enumerate(lines[:3]):
                spans = line.get("spans", [])
                line_text = " ".join(span.get("text", "") for span in spans)
                print(f"    Line {i+1}: {line_text[:80]}")
    
    doc.close()
    
    print("\n  ⚠️  Verdict: Can detect table-like regions but NO structured extraction")
    print("     Need manual parsing of text blocks")
    return False  # No structured tables


def test_pdfplumber_tables(pdf_path: Path):
    """
    pdfplumber approach: Uses text positioning to detect tables.
    
    Pros: Good for simple/moderate tables, easy to use
    Cons: Struggles with complex layouts, merged cells
    """
    print("\n" + "=" * 80)
    print("2. pdfplumber - Good for simple tables")
    print("=" * 80)
    
    tables_found = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:5]):  # First 5 pages
            tables = page.extract_tables()
            
            if tables:
                print(f"\nPage {page_num + 1}: Found {len(tables)} table(s)")
                
                for i, table in enumerate(tables):
                    if table:
                        rows = len(table)
                        cols = len(table[0]) if table else 0
                        print(f"  Table {i+1}: {rows} rows × {cols} cols")
                        
                        # Show first few rows
                        print(f"  First 3 rows:")
                        for row_idx, row in enumerate(table[:3]):
                            print(f"    {row}")
                        
                        tables_found.append({
                            'page': page_num + 1,
                            'rows': rows,
                            'cols': cols,
                            'data': table[:5]  # First 5 rows
                        })
    
    if tables_found:
        print(f"\n  ✅ Verdict: Found {len(tables_found)} table(s)")
        print("     Good for simple tables with clear boundaries")
        return True
    else:
        print(f"\n  ⚠️  Verdict: No tables detected")
        print("     May need different settings or table structure too complex")
        return False


def test_camelot_tables(pdf_path: Path):
    """
    Camelot approach: Uses computer vision + text positioning.
    
    Pros: Best for complex scientific tables, exports to multiple formats
    Cons: Slower, requires Ghostscript for some features
    
    Two methods:
    - Stream: Text-based (like pdfplumber)
    - Lattice: Line-based (detects table borders)
    """
    print("\n" + "=" * 80)
    print("3. Camelot - Best for complex scientific tables")
    print("=" * 80)
    
    results = {
        'stream': [],
        'lattice': []
    }
    
    # Try Stream method (text-based)
    print("\n📊 Method A: Stream (text-based detection)")
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='1-5',  # First 5 pages
            flavor='stream',
            edge_tol=50,
            row_tol=10
        )
        
        print(f"   Found {len(tables)} table(s)")
        
        for i, table in enumerate(tables):
            print(f"\n   Table {i+1}:")
            print(f"     Page: {table.page}")
            print(f"     Shape: {table.df.shape[0]} rows × {table.df.shape[1]} cols")
            print(f"     Accuracy: {table.accuracy:.1f}%")
            print(f"     First 3 rows:")
            print(table.df.head(3).to_string(index=False))
            
            results['stream'].append({
                'table_num': i + 1,
                'page': table.page,
                'shape': table.df.shape,
                'accuracy': table.accuracy,
                'dataframe': table.df
            })
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Try Lattice method (line-based)
    print("\n📊 Method B: Lattice (line-based detection)")
    try:
        tables = camelot.read_pdf(
            str(pdf_path),
            pages='1-5',  # First 5 pages
            flavor='lattice',
            line_scale=40
        )
        
        print(f"   Found {len(tables)} table(s)")
        
        for i, table in enumerate(tables):
            print(f"\n   Table {i+1}:")
            print(f"     Page: {table.page}")
            print(f"     Shape: {table.df.shape[0]} rows × {table.df.shape[1]} cols")
            print(f"     Accuracy: {table.accuracy:.1f}%")
            print(f"     First 3 rows:")
            print(table.df.head(3).to_string(index=False))
            
            results['lattice'].append({
                'table_num': i + 1,
                'page': table.page,
                'shape': table.df.shape,
                'accuracy': table.accuracy,
                'dataframe': table.df
            })
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    total_stream = len(results['stream'])
    total_lattice = len(results['lattice'])
    
    print(f"\n  ✅ Verdict:")
    print(f"     Stream method: {total_stream} table(s)")
    print(f"     Lattice method: {total_lattice} table(s)")
    
    if total_stream > 0 or total_lattice > 0:
        print("     Camelot can extract structured tables with high accuracy")
        print("     Can export to: CSV, Excel, JSON, HTML, SQLite")
        return True, results
    else:
        print("     No tables detected (may be text-only PDF)")
        return False, results


def export_camelot_tables(results: dict, output_dir: Path):
    """Export camelot tables to various formats."""
    if not results:
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 80)
    print("EXPORTING CAMELOT TABLES")
    print("=" * 80)
    
    for method, tables in results.items():
        if not tables:
            continue
        
        print(f"\n{method.upper()} method tables:")
        
        for table_info in tables:
            table_num = table_info['table_num']
            page = table_info['page']
            df = table_info['dataframe']
            
            # Export to CSV
            csv_file = output_dir / f"table_{method}_p{page}_t{table_num}.csv"
            df.to_csv(csv_file, index=False)
            print(f"  ✅ {csv_file.name}")
            
            # Export to Excel
            excel_file = output_dir / f"table_{method}_p{page}_t{table_num}.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"  ✅ {excel_file.name}")
            
            # Export to JSON
            json_file = output_dir / f"table_{method}_p{page}_t{table_num}.json"
            df.to_json(json_file, orient='records', indent=2)
            print(f"  ✅ {json_file.name}")
    
    print(f"\n  📁 Exported to: {output_dir}")


def comparison_summary():
    """Print final comparison."""
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    summary = """
╔═══════════════╦═════════════╦═════════════╦═════════════╗
║   Feature     ║   PyMuPDF   ║ pdfplumber  ║   Camelot   ║
╠═══════════════╬═════════════╬═════════════╬═════════════╣
║ Speed         ║    ⭐⭐⭐⭐⭐    ║     ⭐⭐⭐     ║     ⭐⭐      ║
║ Accuracy      ║     ⭐⭐      ║    ⭐⭐⭐⭐     ║   ⭐⭐⭐⭐⭐    ║
║ Ease of Use   ║    ⭐⭐⭐⭐     ║   ⭐⭐⭐⭐⭐    ║    ⭐⭐⭐⭐     ║
║ Simple Tables ║     ❌       ║     ✅      ║     ✅      ║
║ Complex Tables║     ❌       ║     ⚠️      ║     ✅      ║
║ Merged Cells  ║     ❌       ║     ❌      ║     ✅      ║
║ Multi-column  ║     ❌       ║     ⚠️      ║     ✅      ║
║ Export Formats║     ❌       ║   Manual    ║  CSV/Excel/ ║
║               ║             ║             ║  JSON/HTML  ║
╚═══════════════╩═════════════╩═════════════╩═════════════╝

RECOMMENDATIONS:

1. For SIMPLE tables (clean borders, single column):
   → Use pdfplumber (fast, easy, good enough)

2. For COMPLEX scientific tables (merged cells, multi-column):
   → Use Camelot with 'lattice' method (most accurate)

3. For TEXT-BASED tables (no visible borders):
   → Use Camelot with 'stream' method

4. For GENERAL text extraction (no tables needed):
   → Use PyMuPDF (fastest)

5. For COMBINED approach (recommended):
   → Try pdfplumber first (fast)
   → Fall back to Camelot if pdfplumber fails
   → Use 'lattice' for tables with borders
   → Use 'stream' for tables without borders

WHEN TO USE EACH METHOD:
━━━━━━━━━━━━━━━━━━━━━━━━
PyMuPDF:    Extract text, images, metadata (not tables)
pdfplumber: Simple tables in well-formatted PDFs
Camelot:    Complex scientific tables with high accuracy needs
PMC XML:    ALWAYS prefer this over PDF when available!
"""
    print(summary)


def main():
    """Run comprehensive table extraction comparison."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "PDF TABLE EXTRACTION COMPARISON" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Find a PDF with potential tables
    pdf_files = list(Path("data/fulltext/pdf/arxiv").glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ No PDF files found in data/fulltext/pdf/arxiv/")
        print("   Run the PDF download demo first!")
        return
    
    # Test on first PDF
    pdf_path = pdf_files[0]
    print(f"\n📄 Testing PDF: {pdf_path.name}")
    print(f"   Size: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Test all three methods
        pymupdf_result = test_pymupdf_tables(pdf_path)
        pdfplumber_result = test_pdfplumber_tables(pdf_path)
        camelot_success, camelot_results = test_camelot_tables(pdf_path)
        
        # Export camelot tables if found
        if camelot_success:
            output_dir = Path("data/fulltext/tables_extracted")
            export_camelot_tables(camelot_results, output_dir)
        
        # Show comparison
        comparison_summary()
        
        print("\n" + "=" * 80)
        print("✅ COMPARISON COMPLETE")
        print("=" * 80)
        print("\nKEY TAKEAWAY:")
        print("  • PMC XML > Camelot > pdfplumber > PyMuPDF (for tables)")
        print("  • Always use PMC XML when available!")
        print("  • Use Camelot for complex PDF tables")
        print("  • Use pdfplumber for simple PDF tables")
        print("  • PyMuPDF is best for text/images, not tables\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
