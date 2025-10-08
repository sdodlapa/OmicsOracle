#!/usr/bin/env python3
"""
Data Integrity Analyzer for OmicsOracle

This script analyzes the OmicsOracle codebase for potential data integrity issues:
1. Hardcoded GSE IDs that might be causing data mismatches
2. Static fallback data patterns that might be displayed instead of real data
3. Mock data structures that might be persisting in production code
4. Cache overriding or manipulation that could affect data integrity

Usage:
    python analyze_data_integrity.py --scan-all
    python analyze_data_integrity.py --check-file path/to/file.py
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data_integrity_analysis.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("data_integrity_analyzer")


class DataIntegrityAnalyzer:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.path.dirname(os.path.abspath(__file__))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = "integrity_reports"
        os.makedirs(self.output_dir, exist_ok=True)

        # Problematic patterns to search for
        self.patterns = {
            "hardcoded_gse": {
                # Look for explicit GSE IDs in code
                "regex": r'["\']GSE\d{4,8}["\']',
                "description": "Hardcoded GSE ID",
            },
            "mock_data": {
                # Patterns suggesting mock data
                "regex": r"(?:mock|fake|dummy|sample|placeholder|test)_(?:data|response|result|api)",
                "description": "Mock data reference",
            },
            "fallback_data": {
                # Look for fallback data structures
                "regex": r"(?:fallback|default)_(?:data|response|result|content)",
                "description": "Fallback data structure",
            },
            "cache_manipulation": {
                # Patterns for cache operations that might affect data integrity
                "regex": r"(?:override|manipulate|insert|modify)_cache|cache\.(?:set|update|store)",
                "description": "Cache manipulation",
            },
            "hardcoded_title": {
                # Look for hardcoded titles that might be displayed instead of real ones
                "regex": r'title\s*=\s*["\'][^"\']+COVID[^"\']*["\']',
                "description": "Hardcoded title with COVID reference",
            },
        }

        # File patterns to include in the scan
        self.include_patterns = [
            "*.py",  # Python files
            "*.js",  # JavaScript files
            "*.json",  # JSON data files
            "*.html",  # HTML templates
            "*.jsx",  # React files
            "*.ts",  # TypeScript files
            "*.tsx",  # React TypeScript files
        ]

        # Directories to exclude
        self.exclude_dirs = [
            "__pycache__",
            "node_modules",
            "venv",
            ".git",
            ".env",
            "tests",
            "test",
        ]

        logger.info(f"Data Integrity Analyzer initialized at {self.root_dir}")

    def scan_all(self) -> Dict[str, Any]:
        """
        Scan the entire codebase for problematic patterns
        """
        logger.info("Starting full codebase scan")

        all_findings = {
            "timestamp": self.timestamp,
            "root_dir": self.root_dir,
            "findings": [],
            "statistics": {
                "files_scanned": 0,
                "files_with_issues": 0,
                "total_issues": 0,
                "issues_by_type": {},
            },
        }

        # Initialize issue counters
        for pattern_type in self.patterns.keys():
            all_findings["statistics"]["issues_by_type"][pattern_type] = 0

        # Walk through the directory structure
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                # Check if file matches any include pattern
                if any(file.endswith(p.replace("*", "")) for p in self.include_patterns):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.root_dir)

                    # Scan the file
                    logger.debug(f"Scanning {rel_path}")
                    file_findings = self.scan_file(file_path)
                    all_findings["statistics"]["files_scanned"] += 1

                    if file_findings["issues"]:
                        all_findings["findings"].append(
                            {
                                "file": rel_path,
                                "issues": file_findings["issues"],
                            }
                        )

                        # Update statistics
                        all_findings["statistics"]["files_with_issues"] += 1
                        all_findings["statistics"]["total_issues"] += len(file_findings["issues"])

                        # Update issue type counts
                        for issue in file_findings["issues"]:
                            issue_type = issue["type"]
                            all_findings["statistics"]["issues_by_type"][issue_type] += 1

        # Generate a summary
        all_findings["summary"] = self.generate_summary(all_findings)

        # Save the report
        self.save_report(all_findings)

        return all_findings

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single file for problematic patterns
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            findings = {"file": file_path, "issues": []}

            # Check each pattern
            for pattern_type, pattern_info in self.patterns.items():
                matches = re.finditer(pattern_info["regex"], content, re.IGNORECASE)

                for match in matches:
                    # Get line number and context
                    line_number = content[: match.start()].count("\n") + 1

                    # Get context (the full line)
                    start_of_line = content.rfind("\n", 0, match.start()) + 1
                    end_of_line = content.find("\n", match.start())
                    if end_of_line == -1:  # End of file
                        end_of_line = len(content)

                    context = content[start_of_line:end_of_line].strip()

                    findings["issues"].append(
                        {
                            "type": pattern_type,
                            "description": pattern_info["description"],
                            "line": line_number,
                            "match": match.group(0),
                            "context": context,
                        }
                    )

            return findings

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
            return {"file": file_path, "issues": [], "error": str(e)}

    def generate_summary(self, findings: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of findings
        """
        stats = findings["statistics"]

        summary = [
            f"DATA INTEGRITY ANALYSIS SUMMARY",
            f"------------------------------",
            f"Files scanned: {stats['files_scanned']}",
            f"Files with issues: {stats['files_with_issues']} ({stats['files_with_issues']/stats['files_scanned']*100:.1f}% of scanned files)",
            f"Total issues found: {stats['total_issues']}",
            f"",
            f"ISSUES BY TYPE:",
        ]

        # Add issue type breakdown
        for issue_type, count in stats["issues_by_type"].items():
            if count > 0:
                summary.append(f"- {issue_type}: {count} issues")

        # Add critical file list (files with multiple issues)
        if findings["findings"]:
            critical_files = sorted(
                findings["findings"],
                key=lambda x: len(x["issues"]),
                reverse=True,
            )[
                :5
            ]  # Top 5 most problematic files

            summary.append(f"\nMOST PROBLEMATIC FILES:")
            for file_info in critical_files:
                summary.append(f"- {file_info['file']}: {len(file_info['issues'])} issues")

        return "\n".join(summary)

    def save_report(self, findings: Dict[str, Any]) -> None:
        """
        Save findings to a JSON file
        """
        filename = f"{self.output_dir}/integrity_analysis_{self.timestamp}.json"
        with open(filename, "w") as f:
            json.dump(findings, f, indent=2)

        logger.info(f"Data integrity analysis saved to {filename}")

        # Also save a summary file
        summary_filename = f"{self.output_dir}/integrity_analysis_summary_{self.timestamp}.txt"
        with open(summary_filename, "w") as f:
            f.write(findings["summary"])

        logger.info(f"Summary saved to {summary_filename}")

    def print_summary(self, findings: Dict[str, Any]) -> None:
        """
        Print the summary to the console
        """
        print("\n" + "=" * 80)
        print(findings["summary"])
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Analyze OmicsOracle codebase for data integrity issues")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan-all", action="store_true", help="Scan the entire codebase")
    group.add_argument("--check-file", help="Check a specific file")

    parser.add_argument("--root-dir", help="Root directory to scan (default: current directory)")

    args = parser.parse_args()

    analyzer = DataIntegrityAnalyzer(root_dir=args.root_dir)

    if args.scan_all:
        findings = analyzer.scan_all()
        analyzer.print_summary(findings)
    elif args.check_file:
        file_findings = analyzer.scan_file(args.check_file)

        if file_findings["issues"]:
            print(f"\nIssues found in {args.check_file}:")
            for issue in file_findings["issues"]:
                print(f"Line {issue['line']}: {issue['description']} - {issue['match']}")
                print(f"  Context: {issue['context']}")
                print()
        else:
            print(f"No issues found in {args.check_file}")


if __name__ == "__main__":
    main()
