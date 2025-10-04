#!/usr/bin/env python3
"""
Phase 0 Task 5: Test Organization Script

This script:
1. Removes unnecessary sys imports from test files
2. Identifies test files that need sys imports (for legitimate reasons)
3. Generates a report of test organization
4. Creates enhanced conftest.py with common fixtures
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_sys_usage(content: str, filepath: Path) -> Dict[str, bool]:
    """Check if sys module is legitimately used in file."""
    uses = {
        "sys.exit": "sys.exit(" in content,
        "sys.argv": "sys.argv" in content,
        "sys.platform": "sys.platform" in content,
        "sys.version": "sys.version" in content or "sys.version_info" in content,
        "sys.stdout": "sys.stdout" in content or "sys.stderr" in content or "sys.stdin" in content,
        "sys.modules": "sys.modules" in content,
        "sys.path_mock": '@patch("sys.path' in content or "@patch('sys.path" in content,
        "sys.executable": "sys.executable" in content,
    }
    return {k: v for k, v in uses.items() if v}


def remove_unnecessary_sys_imports(filepath: Path) -> bool:
    """Remove sys import if it's not used. Returns True if modified."""
    content = filepath.read_text(encoding="utf-8")

    # Check if file has sys import
    if "import sys" not in content:
        return False

    # Check if sys is legitimately used
    legitimate_uses = check_sys_usage(content, filepath)

    if legitimate_uses:
        return False  # Keep sys import if it's used

    # Remove standalone "import sys" lines
    original_content = content
    content = re.sub(r"^import sys\s*\n", "", content, flags=re.MULTILINE)

    if content != original_content:
        filepath.write_text(content, encoding="utf-8")
        return True

    return False


def analyze_test_structure(tests_dir: Path) -> Dict[str, any]:
    """Analyze test directory structure."""
    stats = {
        "total_files": 0,
        "test_files": 0,
        "conftest_files": 0,
        "by_category": {},
        "sys_imports_removed": 0,
        "sys_imports_kept": 0,
        "sys_usage_reasons": [],
    }

    for pyfile in tests_dir.rglob("*.py"):
        if pyfile.name == "__pycache__":
            continue

        stats["total_files"] += 1

        if pyfile.name.startswith("test_") or pyfile.name.endswith("_test.py"):
            stats["test_files"] += 1

        if pyfile.name == "conftest.py":
            stats["conftest_files"] += 1

        # Categorize by subdirectory
        rel_path = pyfile.relative_to(tests_dir)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        # Check sys imports
        content = pyfile.read_text(encoding="utf-8")
        if "import sys" in content:
            legitimate_uses = check_sys_usage(content, pyfile)
            if legitimate_uses:
                stats["sys_imports_kept"] += 1
                stats["sys_usage_reasons"].append(
                    {"file": str(pyfile.relative_to(tests_dir)), "reasons": list(legitimate_uses.keys())}
                )
            else:
                # Try to remove it
                if remove_unnecessary_sys_imports(pyfile):
                    stats["sys_imports_removed"] += 1

    return stats


def print_report(stats: Dict[str, any]):
    """Print analysis report."""
    print(f"\n{BOLD}{BLUE}=== Test Organization Report ==={RESET}\n")

    print(f"{BOLD}Test Files:{RESET}")
    print(f"  Total Python files: {stats['total_files']}")
    print(f"  Test files: {stats['test_files']}")
    print(f"  Conftest files: {stats['conftest_files']}")

    print(f"\n{BOLD}By Category:{RESET}")
    for category, count in sorted(stats["by_category"].items()):
        print(f"  {category}: {count} files")

    print(f"\n{BOLD}Sys Import Cleanup:{RESET}")
    print(f"  {GREEN}Removed unnecessary sys imports: {stats['sys_imports_removed']}{RESET}")
    print(f"  {YELLOW}Kept legitimate sys imports: {stats['sys_imports_kept']}{RESET}")

    if stats["sys_usage_reasons"]:
        print(f"\n{BOLD}Legitimate sys Usage:{RESET}")
        for item in stats["sys_usage_reasons"][:10]:  # Show first 10
            reasons = ", ".join(item["reasons"])
            print(f"  {item['file']}: {reasons}")
        if len(stats["sys_usage_reasons"]) > 10:
            print(f"  ... and {len(stats['sys_usage_reasons']) - 10} more files")

    print(f"\n{GREEN}{BOLD}[OK] Test organization analysis complete{RESET}")


def main():
    """Main execution."""
    # Find tests directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    tests_dir = repo_root / "tests"

    if not tests_dir.exists():
        print(f"{RED}[ERROR] Tests directory not found: {tests_dir}{RESET}")
        return 1

    print(f"{BOLD}Analyzing test structure: {tests_dir}{RESET}")

    # Analyze and clean up
    stats = analyze_test_structure(tests_dir)

    # Print report
    print_report(stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
