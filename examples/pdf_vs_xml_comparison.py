"""
PDF vs PMC XML Comparison Demo

This demonstrates why PMC XML is superior to PDF extraction,
and when you might need PDF extraction anyway.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber


def analyze_pmc_xml():
    """Show what we get from PMC XML (structured, accurate)."""
    print("\n" + "=" * 80)
    print("PMC XML ANALYSIS (Structured, Clean)")
    print("=" * 80)

    xml_file = Path("data/fulltext/xml/pmc/3166277.nxml")
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract structured content
    title = root.find(".//article-title")
    abstract = root.find(".//abstract")
    figures = root.findall(".//fig")
    tables = root.findall(".//table-wrap")
    refs = root.findall(".//ref")

    print(f"\n📄 Article: {xml_file.stem}")
    print(f"   Title: {title.text if title is not None else 'N/A'}")
    print(f"   Abstract: {len(abstract.text) if abstract is not None and abstract.text else 0} chars")
    print(f"   Figures: {len(figures)}")
    print(f"   Tables: {len(tables)}")
    print(f"   References: {len(refs)}")

    # Show table structure
    if tables:
        print("\n📊 FIRST TABLE STRUCTURE (from XML):")
        tbl_wrap = tables[0]
        table = tbl_wrap.find(".//table")

        if table is not None:
            rows = table.findall(".//tr")
            print(f"   Total rows: {len(rows)}")

            # First row (headers)
            if rows:
                first_row = rows[0]
                headers = first_row.findall(".//th")
                print(f"   Headers: {[h.text for h in headers if h.text]}")

                # Second row (data)
                if len(rows) > 1:
                    second_row = rows[1]
                    cells = second_row.findall(".//td")
                    print(f"   Sample row: {[c.text for c in cells[:4] if c.text]}")

    # Show figure references
    if figures:
        print("\n🖼️  FIGURE REFERENCES (from XML):")
        for i, fig in enumerate(figures[:2], 1):
            label = fig.find(".//label")
            graphic = fig.find(".//graphic")
            caption = fig.find(".//caption")

            print(f"   Figure {i}:")
            print(f"      Label: {label.text if label is not None and label.text else 'N/A'}")
            if graphic is not None:
                href = graphic.get("{http://www.w3.org/1999/xlink}href")
                print(f"      Image file: {href}")
            if caption is not None:
                cap_text = "".join(caption.itertext())
                print(f"      Caption: {cap_text[:100]}...")


def analyze_pdf_with_pymupdf():
    """Show what we can extract from PDF using PyMuPDF."""
    print("\n" + "=" * 80)
    print("PDF ANALYSIS - PyMuPDF (Fast, images+text)")
    print("=" * 80)

    pdf_file = list(Path("data/fulltext/pdf/arxiv").glob("*.pdf"))[0]
    doc = fitz.open(pdf_file)

    print(f"\n📄 PDF: {pdf_file.name}")
    print(f"   Pages: {len(doc)}")
    print(f"   Metadata: {doc.metadata.get('title', 'N/A')}")

    # First page analysis
    page = doc[0]
    text = page.get_text()
    images = page.get_images()

    print(f"\n📝 First page:")
    print(f"   Text length: {len(text)} chars")
    print(f"   Text preview: {text[:200].replace(chr(10), ' ')}...")
    print(f"   Images: {len(images)}")

    # Image extraction capability
    total_images = sum(len(p.get_images()) for p in doc)
    print(f"\n🖼️  Total images in PDF: {total_images}")
    print(f"   Can extract: ✅ YES (as PNG/JPG)")

    # Table detection (basic - looks for text blocks)
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [b for b in blocks if b["type"] == 0]
    print(f"\n📊 Text blocks (potential tables): {len(text_blocks)}")
    print(f"   Table extraction: ⚠️  MODERATE (needs manual parsing)")

    doc.close()


def analyze_pdf_with_pdfplumber():
    """Show what we can extract from PDF using pdfplumber (best for tables)."""
    print("\n" + "=" * 80)
    print("PDF ANALYSIS - pdfplumber (Best for tables)")
    print("=" * 80)

    pdf_file = list(Path("data/fulltext/pdf/arxiv").glob("*.pdf"))[0]

    with pdfplumber.open(pdf_file) as pdf:
        print(f"\n📄 PDF: {pdf_file.name}")
        print(f"   Pages: {len(pdf.pages)}")

        # First page
        page = pdf.pages[0]
        text = page.extract_text()

        print(f"\n📝 First page:")
        print(f"   Text length: {len(text) if text else 0} chars")

        # Table detection
        tables = page.extract_tables()
        print(f"\n📊 Tables detected: {len(tables)}")

        if tables:
            print(f"   First table rows: {len(tables[0])}")
            print(f"   First table cols: {len(tables[0][0]) if tables[0] else 0}")
            print(f"   Sample row: {tables[0][0][:3] if tables[0] else 'N/A'}")

        # Image detection (metadata only)
        images = page.images
        print(f"\n🖼️  Images detected: {len(images)}")
        print(f"   Can extract pixels: ❌ NO (metadata only)")


def comparison_summary():
    """Print a comparison summary."""
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    comparison = """
Feature                    | PMC XML        | PyMuPDF        | pdfplumber
---------------------------|----------------|----------------|----------------
Text extraction            | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐⭐⭐ Good     | ⭐⭐⭐⭐ Good
Structure preservation     | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐ Poor       | ⭐⭐⭐ Moderate
Table extraction           | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐ Poor       | ⭐⭐⭐⭐ Very Good
Figure captions            | ⭐⭐⭐⭐⭐ Perfect | ❌ None        | ❌ None
Image extraction           | ⭐⭐ References  | ⭐⭐⭐⭐⭐ Perfect | ❌ Metadata only
References (citations)     | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐ Poor       | ⭐⭐ Poor
Author metadata            | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐ Limited    | ⭐⭐ Limited
Speed                      | ⭐⭐⭐⭐⭐ Instant | ⭐⭐⭐⭐⭐ Fast   | ⭐⭐⭐ Moderate
Accuracy                   | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐⭐ Good     | ⭐⭐⭐⭐ Very Good

RECOMMENDATION:
1. Use PMC XML when available (90% of recent papers) ✅
2. Use PyMuPDF for PDF fallback (arXiv, older papers) ⚠️
3. Use pdfplumber for table extraction from PDFs ⚠️
4. Consider camelot-py for complex scientific tables ⚠️

WHY PMC XML WINS:
- Structured by publishers (no parsing errors)
- Includes semantic information (sections, roles, etc.)
- Table structure preserved (rows, columns, headers)
- Citation metadata complete
- No OCR needed
- Faster processing

WHEN YOU NEED PDF EXTRACTION:
- arXiv papers (no PMC XML)
- Publisher PDFs (Elsevier, Springer, Nature, etc.)
- Older papers not in PMC
- Need actual image files (not just references)
- Scanned papers (need OCR)
"""
    print(comparison)


def main():
    """Run all analyses."""
    try:
        analyze_pmc_xml()
        analyze_pdf_with_pymupdf()
        analyze_pdf_with_pdfplumber()
        comparison_summary()

        print("\n" + "=" * 80)
        print("✅ COMPARISON COMPLETE")
        print("=" * 80)
        print("\nCONCLUSION: PMC XML provides superior structured content.")
        print("PDF extraction is needed only when XML unavailable or for images.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
