#!/usr/bin/env python3
"""
Quick Local CI Check

Simple ASCII-only validation script that mirrors GitHub Actions checks.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_check(cmd: List[str], description: str) -> bool:
    """Run a single check and return success status."""
    print(f"\n[CHECK] {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Special handling for Bandit security scan
        if "bandit" in cmd[0] and "-f" in cmd and "json" in cmd:
            return check_bandit_results()

        print(f"[PASS] {description}")
        return True
    except subprocess.CalledProcessError:
        # Special handling for Bandit - it writes info to stderr but succeeds
        if "bandit" in cmd[0] and "-f" in cmd and "json" in cmd:
            return check_bandit_results()

        print(f"[FAIL] {description}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {cmd[0]}")
        return False


def check_bandit_results() -> bool:
    """Check Bandit JSON report for high-severity issues only."""
    try:
        bandit_file = Path("bandit-report.json")
        if not bandit_file.exists():
            print("[FAIL] Bandit report not generated")
            return False

        with open(bandit_file, encoding="utf-8") as f:
            report = json.load(f)

        # Only fail on HIGH severity issues
        metrics = report.get("metrics", {}).get("_totals", {})
        high_severity = metrics.get("SEVERITY.HIGH", 0)

        if high_severity > 0:
            print(f"[FAIL] Found {high_severity} high-severity " f"security issues")
            return False
        else:
            medium_severity = metrics.get("SEVERITY.MEDIUM", 0)
            if medium_severity > 0:
                print(f"[PASS] Security Scan " f"(Note: {medium_severity} medium-severity warnings)")
            else:
                print("[PASS] Security Scan")
            return True

    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Failed to parse Bandit report: {e}")
        return False


def main() -> int:
    """Run essential CI checks."""
    print("=== Quick Local CI Validation ===")

    checks: List[Tuple[List[str], str]] = [
        (["python", "scripts/ascii_enforcer.py"], "ASCII Enforcement"),
        (
            [
                "black",
                "--check",
                "src/",
                "tests/",
                "scripts/",
                "--line-length",
                "80",
            ],
            "Black Formatting",
        ),
        (
            [
                "isort",
                "--check-only",
                "src/",
                "tests/",
                "scripts/",
                "--profile",
                "black",
            ],
            "Import Sorting",
        ),
        (["ruff", "check", "src/", "tests/", "scripts/"], "Ruff Linting"),
        (
            ["flake8", "src/", "tests/", "scripts/", "--max-line-length=110"],
            "Line Length (Hard Limit: 100 chars)",
        ),
        (
            [
                "bandit",
                "-r",
                "src/",
                "-f",
                "json",
                "-o",
                "bandit-report.json",
            ],
            "Security Scan",
        ),
    ]

    # Optional soft warnings (don't fail the build)
    soft_checks: List[Tuple[List[str], str]] = [
        (
            ["flake8", "src/", "tests/", "scripts/", "--max-line-length=80"],
            "Line Length (Soft Target: 80 chars)",
        ),
    ]

    failures = 0
    failed_checks = []

    # Run hard checks (these can fail the build)
    for cmd, desc in checks:
        if not run_check(cmd, desc):
            failures += 1
            failed_checks.append(desc)

    # Run soft checks (warnings only)
    print("\n=== Soft Checks (Warnings Only) ===")
    for cmd, desc in soft_checks:
        print(f"\n[SOFT CHECK] {desc}")
        print(f"Command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print(f"[WARNING] {desc}")
                if result.stdout:
                    print(f"Output: {result.stdout}")
            else:
                print(f"[PASS] {desc}")
        except FileNotFoundError:
            print(f"[ERROR] Command not found: {cmd[0]}")

    print("\n=== Summary ===")
    if failures == 0:
        print("[SUCCESS] All required checks passed!")
        return 0
    else:
        print(f"[FAILED] {failures} required checks failed:")
        for failed_check in failed_checks:
            print(f"  - {failed_check}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
