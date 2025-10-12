"""
Demo script for validating downloaded full-text files.

This script demonstrates:
1. Validating PMC XML files
2. Validating PDF files
3. Generating validation reports
4. Quality scoring

Usage:
    python examples/fulltext_validation_demo.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.fulltext.validators import (
    ContentValidator,
    validate_xml_file,
    validate_pdf_file,
)


def validate_xml_files():
    """Validate all downloaded PMC XML files."""
    print("\n" + "=" * 80)
    print("PMC XML VALIDATION")
    print("=" * 80)

    xml_dir = Path("data/fulltext/xml/pmc")

    if not xml_dir.exists():
        print("❌ No XML directory found")
        return

    xml_files = sorted(xml_dir.glob("*.nxml"))

    if not xml_files:
        print("❌ No XML files found")
        return

    print(f"\n✓ Found {len(xml_files)} XML files\n")

    results = []

    for xml_file in xml_files:
        print(f"\n{'─' * 80}")
        print(f"📄 {xml_file.name}")
        print(f"{'─' * 80}")

        # Validate with default thresholds
        is_valid, report = validate_xml_file(xml_file)

        # Display results
        print(f"{'Valid:':<20} {'✅ YES' if is_valid else '❌ NO'}")
        print(f"{'Size:':<20} {report['size']:,} bytes")

        if "quality_score" in report:
            quality = report["quality_score"]
            quality_emoji = "🟢" if quality > 0.7 else "🟡" if quality > 0.4 else "🔴"
            print(f"{'Quality Score:':<20} {quality_emoji} {quality:.2%}")

        if "found_elements" in report:
            print(f"\n{'Found Elements:':<20}")
            for elem, text in report["found_elements"].items():
                preview = text[:60] + "..." if len(text) > 60 else text
                print(f"  • {elem}: {preview}")

        if "missing_elements" in report:
            missing = report["missing_elements"]
            if missing:
                print(f"\n{'Missing Elements:':<20} {', '.join(missing)}")

        if "error" in report:
            print(f"\n{'Error:':<20} {report['error']}")

        results.append(
            {
                "file": xml_file.name,
                "valid": is_valid,
                "size": report["size"],
                "quality": report.get("quality_score", 0),
            }
        )

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total files:     {len(results)}")
    print(f"Valid files:     {sum(1 for r in results if r['valid'])}")
    print(f"Invalid files:   {sum(1 for r in results if not r['valid'])}")
    print(
        f"Avg quality:     {sum(r['quality'] for r in results) / len(results):.2%}"
    )


def validate_pdf_files():
    """Validate all downloaded PDF files."""
    print("\n" + "=" * 80)
    print("PDF VALIDATION")
    print("=" * 80)

    pdf_dir = Path("data/fulltext/pdf/arxiv")

    if not pdf_dir.exists():
        print("❌ No PDF directory found")
        return

    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDF files found")
        return

    print(f"\n✓ Found {len(pdf_files)} PDF files\n")

    results = []

    for pdf_file in pdf_files:
        print(f"\n{'─' * 80}")
        print(f"📄 {pdf_file.name}")
        print(f"{'─' * 80}")

        # Validate
        is_valid, report = validate_pdf_file(pdf_file)

        # Display results
        print(f"{'Valid:':<20} {'✅ YES' if is_valid else '❌ NO'}")
        print(f"{'Size:':<20} {report['size'] / 1024 / 1024:.2f} MB")

        if "pdf_version" in report:
            print(f"{'PDF Version:':<20} {report['pdf_version']}")

        if "encrypted" in report:
            encrypted = report["encrypted"]
            print(f"{'Encrypted:':<20} {'⚠️  YES' if encrypted else '✅ NO'}")

        if "sha256" in report:
            print(f"{'SHA256:':<20} {report['sha256'][:16]}...")

        if "error" in report:
            print(f"\n{'Error:':<20} {report['error']}")

        # Check for metadata JSON
        json_file = pdf_file.with_suffix(".json")
        if json_file.exists():
            print(f"\n{'Metadata File:':<20} ✅ Found")
            with open(json_file) as f:
                metadata = json.load(f)
            print(f"{'Source:':<20} {metadata.get('source', 'unknown')}")
            print(f"{'Identifier:':<20} {metadata.get('source_identifier', 'unknown')}")
        else:
            print(f"\n{'Metadata File:':<20} ❌ Not found")

        results.append(
            {
                "file": pdf_file.name,
                "valid": is_valid,
                "size_mb": report["size"] / 1024 / 1024,
            }
        )

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total files:     {len(results)}")
    print(f"Valid files:     {sum(1 for r in results if r['valid'])}")
    print(f"Invalid files:   {sum(1 for r in results if not r['valid'])}")
    print(f"Total size:      {sum(r['size_mb'] for r in results):.2f} MB")


def cross_validate_with_content_validator():
    """Cross-validate using ContentValidator for both XML and PDF."""
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION WITH ContentValidator")
    print("=" * 80)

    validator = ContentValidator()

    # Check one XML file
    xml_files = list(Path("data/fulltext/xml/pmc").glob("*.nxml"))
    if xml_files:
        xml_file = xml_files[0]
        print(f"\n📄 Testing XML: {xml_file.name}")

        with open(xml_file, "rb") as f:
            content = f.read()

        is_valid, report = validator.validate_and_report(content, "xml", xml_file.stem)

        print(f"  Valid: {'✅' if is_valid else '❌'}")
        print(f"  Quality: {report.get('quality_score', 0):.2%}")

    # Check one PDF file
    pdf_files = list(Path("data/fulltext/pdf/arxiv").glob("*.pdf"))
    if pdf_files:
        pdf_file = pdf_files[0]
        print(f"\n📄 Testing PDF: {pdf_file.name}")

        with open(pdf_file, "rb") as f:
            content = f.read()

        is_valid, report = validator.validate_and_report(content, "pdf", pdf_file.stem)

        print(f"  Valid: {'✅' if is_valid else '❌'}")
        print(f"  Version: {report.get('pdf_version', 'unknown')}")
        print(f"  Encrypted: {report.get('encrypted', 'unknown')}")


def main():
    """Run all validation demos."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "FULL-TEXT VALIDATION DEMO" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Validate XML files
        validate_xml_files()

        # Validate PDF files
        validate_pdf_files()

        # Cross-validate
        cross_validate_with_content_validator()

        print("\n" + "=" * 80)
        print("✅ VALIDATION DEMO COMPLETE")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
