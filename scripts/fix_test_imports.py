#!/usr/bin/env python3
"""
Fix old src.omics_oracle imports in test files

Changes:
    from src.omics_oracle.X -> from omics_oracle.X
    import src.omics_oracle.X -> import omics_oracle.X
"""

import re
from pathlib import Path


def fix_imports_in_file(filepath: Path) -> bool:
    """Fix src.omics_oracle imports in a single file."""
    content = filepath.read_text(encoding="utf-8")
    original_content = content

    # Pattern 1: from src.omics_oracle.XXX import YYY
    content = re.sub(r"from src\.omics_oracle\.", "from omics_oracle.", content)

    # Pattern 2: import src.omics_oracle.XXX
    content = re.sub(r"import src\.omics_oracle\.", "import omics_oracle.", content)

    # Pattern 3: import src.omics_oracle
    content = re.sub(r"import src\.omics_oracle\b", "import omics_oracle", content)

    if content != original_content:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """Fix imports in all test files."""
    tests_dir = Path(__file__).parent.parent / "tests"

    fixed = 0
    for pyfile in tests_dir.rglob("*.py"):
        if pyfile.name == "__pycache__":
            continue

        if fix_imports_in_file(pyfile):
            print(f"[OK] Fixed: {pyfile.relative_to(tests_dir)}")
            fixed += 1

    print(f"\n[OK] Fixed {fixed} test files")
    return 0


if __name__ == "__main__":
    exit(main())
