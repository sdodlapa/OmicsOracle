#!/usr/bin/env python3
"""
Fix Import Structure - Phase 0, Task 2
Remove all sys.path manipulations and ensure proper imports.
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Patterns to match sys.path manipulations
SYS_PATH_PATTERNS = [
    r"sys\.path\.insert\([^)]+\)",
    r"sys\.path\.append\([^)]+\)",
]

# Import statement to add where needed
PROPER_IMPORT_SETUP = """
# Standard imports - no sys.path manipulation needed
# Package is installed in development mode: pip install -e .
"""


def find_python_files() -> List[Path]:
    """Find all Python files that need fixing."""
    python_files = []

    # Search in key directories
    search_dirs = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "scripts",
    ]

    for search_dir in search_dirs:
        if search_dir.exists():
            for py_file in search_dir.rglob("*.py"):
                # Skip __pycache__ and venv
                if "__pycache__" in str(py_file) or "venv" in str(py_file):
                    continue
                python_files.append(py_file)

    # Also check root-level test files
    for py_file in PROJECT_ROOT.glob("test_*.py"):
        python_files.append(py_file)

    return python_files


def has_sys_path_manipulation(content: str) -> bool:
    """Check if file has sys.path manipulations."""
    for pattern in SYS_PATH_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


def remove_sys_path_lines(content: str) -> Tuple[str, int]:
    """Remove sys.path manipulation lines."""
    lines = content.split("\n")
    new_lines = []
    removed_count = 0
    skip_next_blank = False

    for i, line in enumerate(lines):
        # Check if this line contains sys.path manipulation
        is_sys_path_line = False
        for pattern in SYS_PATH_PATTERNS:
            if re.search(pattern, line):
                is_sys_path_line = True
                removed_count += 1
                skip_next_blank = True
                break

        # Skip project_root definition lines that are only used for sys.path
        if "project_root" in line and "Path(__file__)" in line:
            # Check if next few lines use project_root for sys.path
            next_lines = lines[i + 1 : min(i + 5, len(lines))]
            uses_for_sys_path = any("sys.path" in nl and "project_root" in nl for nl in next_lines)
            if uses_for_sys_path:
                is_sys_path_line = True
                removed_count += 1
                skip_next_blank = True

        # Skip import sys if it's only used for sys.path
        if line.strip() == "import sys":
            # Look ahead to see if sys is only used for sys.path
            rest_of_file = "\n".join(lines[i + 1 :])
            # Remove sys.path references temporarily to check other uses
            temp_content = re.sub(r"sys\.path\.[^)]+\)", "", rest_of_file)
            if "sys." not in temp_content and "sys," not in temp_content:
                is_sys_path_line = True
                removed_count += 1
                skip_next_blank = True

        if is_sys_path_line:
            continue

        # Skip blank line immediately after removed sys.path line
        if skip_next_blank and line.strip() == "":
            skip_next_blank = False
            continue

        skip_next_blank = False
        new_lines.append(line)

    return "\n".join(new_lines), removed_count


def fix_file(file_path: Path) -> Tuple[bool, int]:
    """Fix a single file."""
    try:
        content = file_path.read_text()

        if not has_sys_path_manipulation(content):
            return False, 0

        new_content, removed_count = remove_sys_path_lines(content)

        # Write back
        file_path.write_text(new_content)

        return True, removed_count

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False, 0


def main():
    """Main execution."""
    print("=" * 70)
    print("PHASE 0 - TASK 2: FIX IMPORT STRUCTURE")
    print("=" * 70)
    print()

    # Find all Python files
    print("Finding Python files...")
    python_files = find_python_files()
    print(f"Found {len(python_files)} Python files")
    print()

    # Fix each file
    print("Removing sys.path manipulations...")
    fixed_files = []
    total_removed = 0

    for py_file in python_files:
        was_fixed, removed_count = fix_file(py_file)
        if was_fixed:
            fixed_files.append((py_file, removed_count))
            total_removed += removed_count
            relative_path = py_file.relative_to(PROJECT_ROOT)
            print(f"  [OK] {relative_path} ({removed_count} lines removed)")

    print()
    print("=" * 70)
    print(f"SUMMARY")
    print("=" * 70)
    print(f"Files fixed: {len(fixed_files)}")
    print(f"Total sys.path lines removed: {total_removed}")
    print()

    if fixed_files:
        print("[SUCCESS] All sys.path manipulations removed!")
        print()
        print("Next steps:")
        print("1. Ensure package is installed: pip install -e .")
        print("2. Run tests to verify imports work")
        print("3. Commit changes")
    else:
        print("No sys.path manipulations found!")


if __name__ == "__main__":
    main()
