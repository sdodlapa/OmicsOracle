#!/usr/bin/env python3
"""
PDF Reader script for OmicsOracle project documents.
This script reads PDF documents and extracts their content for analysis.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    import fitz  # pymupdf
    import pdfplumber
    import PyPDF2

    PDF_LIBRARIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PDF libraries not available: {e}")
    PDF_LIBRARIES_AVAILABLE = False


class PDFReader:
    """Enhanced PDF reader with multiple extraction methods."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def extract_with_pdfplumber(self) -> str:
        """Extract text using pdfplumber - best for structured text."""
        try:
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            return text.strip()
        except Exception as e:
            print(f"Error with pdfplumber: {e}")
            return ""

    def extract_with_pymupdf(self) -> str:
        """Extract text using PyMuPDF - good for complex layouts."""
        try:
            text = ""
            doc = fitz.open(self.pdf_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text() + "\n\n"
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error with PyMuPDF: {e}")
            return ""

    def extract_with_pypdf2(self) -> str:
        """Extract text using PyPDF2 - fallback method."""
        try:
            text = ""
            with open(self.pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
            return text.strip()
        except Exception as e:
            print(f"Error with PyPDF2: {e}")
            return ""

    def extract_text(self) -> str:
        """Extract text using the best available method."""
        print(f"Reading PDF: {self.pdf_path.name}")

        # Try pdfplumber first (usually best results)
        text = self.extract_with_pdfplumber()
        if text and len(text) > 100:
            print(f"[OK] Extracted {len(text)} characters with pdfplumber")
            return text

        # Try PyMuPDF as fallback
        text = self.extract_with_pymupdf()
        if text and len(text) > 100:
            print(f"[OK] Extracted {len(text)} characters with PyMuPDF")
            return text

        # Try PyPDF2 as last resort
        text = self.extract_with_pypdf2()
        if text and len(text) > 100:
            print(f"[OK] Extracted {len(text)} characters with PyPDF2")
            return text

        print("[FAIL] Failed to extract meaningful text from PDF")
        return ""

    def get_metadata(self) -> Dict:
        """Extract PDF metadata."""
        try:
            doc = fitz.open(self.pdf_path)
            metadata = doc.metadata
            doc.close()
            return metadata
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}


def read_all_pdfs(directory: str) -> Dict[str, Dict]:
    """Read all PDF files in a directory."""
    pdf_dir = Path(directory)
    results = {}

    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {directory}")

    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_file.name}")
        print(f"{'='*60}")

        reader = PDFReader(pdf_file)
        text = reader.extract_text()
        metadata = reader.get_metadata()

        results[pdf_file.name] = {
            "text": text,
            "metadata": metadata,
            "path": str(pdf_file),
            "word_count": len(text.split()) if text else 0,
            "char_count": len(text) if text else 0,
        }

        print(f"Word count: {results[pdf_file.name]['word_count']}")
        print(f"Character count: {results[pdf_file.name]['char_count']}")

        # Show first 200 characters as preview
        if text:
            preview = text[:200].replace("\n", " ")
            print(f"Preview: {preview}...")

    return results


def save_extracted_text(results: Dict[str, Dict], output_dir: str = "extracted_docs"):
    """Save extracted text to individual files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for filename, data in results.items():
        if data["text"]:
            # Create output filename
            base_name = Path(filename).stem
            output_file = output_path / f"{base_name}_extracted.txt"

            # Write content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Extracted from: {filename}\n")
                f.write(f"# Word count: {data['word_count']}\n")
                f.write(f"# Character count: {data['char_count']}\n")
                f.write(f"# Extraction date: {datetime.now().isoformat()}\n\n")
                f.write(data["text"])

            print(f"[OK] Saved extracted text to: {output_file}")


def main():
    """Main function to read OmicsOracle PDF documents."""
    print("[SEARCH] OmicsOracle PDF Document Reader")
    print("=" * 50)

    # Get the directory containing the PDFs
    pdf_directory = "/Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle"

    # Read all PDFs
    results = read_all_pdfs(pdf_directory)

    # Save extracted text
    save_extracted_text(results)

    # Summary
    print("\n[DATA] SUMMARY:")
    print(f"Total PDFs processed: {len(results)}")
    successful_extractions = sum(1 for r in results.values() if r["text"])
    print(f"Successful extractions: {successful_extractions}")
    total_words = sum(r["word_count"] for r in results.values())
    print(f"Total words extracted: {total_words}")

    # List files with content
    print("\n[FILE] Files with extracted content:")
    for filename, data in results.items():
        if data["text"]:
            print(f"  [OK] {filename} ({data['word_count']} words)")
        else:
            print(f"  [FAIL] {filename} (extraction failed)")

    return results


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)
