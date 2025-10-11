#!/usr/bin/env python3
"""
Code Usage Verification Tool

Analyzes codebase to find:
- Orphaned files (never imported)
- Duplicate implementations
- Unused code candidates for archiving
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CodeAnalyzer:
    """Analyze code dependencies and usage"""

    def __init__(self, root_dir: str = "omics_oracle_v2"):
        self.root_dir = Path(root_dir)
        self.all_python_files = list(self.root_dir.rglob("*.py"))
        self.import_graph = defaultdict(set)  # file -> set of imports
        self.reverse_graph = defaultdict(set)  # module -> set of files that import it

    def find_all_imports(self, file_path: Path) -> Set[str]:
        """Parse file and extract all imports"""
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}", file=sys.stderr)
            return set()

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_import = f"{module}.{alias.name}" if module else alias.name
                    imports.add(full_import)

        return imports

    def build_dependency_graph(self):
        """Build full dependency graph"""
        print("📊 Building dependency graph...")

        for py_file in self.all_python_files:
            if "archive" in str(py_file):
                continue  # Skip already archived code

            imports = self.find_all_imports(py_file)

            # Filter to only omics_oracle_v2 imports
            internal_imports = {imp for imp in imports if imp.startswith("omics_oracle_v2")}

            self.import_graph[str(py_file)] = internal_imports

            # Build reverse graph
            for imp in internal_imports:
                self.reverse_graph[imp].add(str(py_file))

        print(f"✅ Analyzed {len(self.all_python_files)} files")
        print(f"✅ Found {len(self.reverse_graph)} unique imports")

    def find_orphaned_files(self) -> List[Tuple[Path, str]]:
        """Find files never imported by anything"""
        orphaned = []

        for py_file in self.all_python_files:
            if "archive" in str(py_file) or "__init__.py" in str(py_file):
                continue

            # Convert file path to module path
            module_path = str(py_file.relative_to(Path(".")))
            module_path = module_path.replace("/", ".").replace(".py", "")

            # Check if this module is imported anywhere
            is_imported = False
            for importing_file, imports in self.import_graph.items():
                for imp in imports:
                    if module_path in imp or imp in module_path:
                        is_imported = True
                        break
                if is_imported:
                    break

            if not is_imported:
                # Double-check: grep for any mention
                reason = self._check_usage(py_file)
                orphaned.append((py_file, reason))

        return orphaned

    def _check_usage(self, file_path: Path) -> str:
        """Check if file is used in examples, tests, or docs"""
        filename = file_path.stem

        usage = []

        # Check tests
        test_files = list(Path("tests").rglob("*.py"))
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    if filename in f.read():
                        usage.append(f"test: {test_file.name}")
            except:
                pass

        # Check examples
        example_files = list(Path("examples").rglob("*.py"))
        for example_file in example_files:
            try:
                with open(example_file) as f:
                    if filename in f.read():
                        usage.append(f"example: {example_file.name}")
            except:
                pass

        if usage:
            return f"Possibly used in: {', '.join(usage)}"
        return "No usage found"

    def find_duplicate_implementations(self) -> List[Tuple[str, List[Path]]]:
        """Find files with similar class/function names (potential duplicates)"""
        class_names = defaultdict(list)

        for py_file in self.all_python_files:
            if "archive" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_names[node.name].append(py_file)
            except:
                pass

        # Find duplicates
        duplicates = [(name, files) for name, files in class_names.items() if len(files) > 1]

        return duplicates

    def analyze_file(self, file_path: str):
        """Detailed analysis of a specific file"""
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        print(f"\n{'='*80}")
        print(f"📄 ANALYSIS: {file_path}")
        print(f"{'='*80}\n")

        # 1. What does it import?
        imports = self.find_all_imports(file_path)
        print(f"📥 IMPORTS ({len(imports)}):")
        for imp in sorted(imports):
            if imp.startswith("omics_oracle_v2"):
                print(f"  • {imp}")

        # 2. What imports it?
        module_path = str(file_path.relative_to(Path("."))).replace("/", ".").replace(".py", "")
        importers = []
        for importing_file, file_imports in self.import_graph.items():
            for imp in file_imports:
                if module_path in imp or imp in module_path:
                    importers.append(importing_file)
                    break

        print(f"\n📤 IMPORTED BY ({len(importers)}):")
        if importers:
            for importer in sorted(set(importers))[:10]:
                print(f"  • {importer}")
            if len(importers) > 10:
                print(f"  ... and {len(importers) - 10} more")
        else:
            print("  ⚠️  NOT IMPORTED BY ANY FILE")

        # 3. Check usage in tests/examples
        print(f"\n🧪 USAGE CHECK:")
        usage_info = self._check_usage(file_path)
        print(f"  {usage_info}")

        # 4. Extract classes/functions
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
            ]

            print(f"\n📦 CONTENTS:")
            if classes:
                print(f"  Classes: {', '.join(classes)}")
            if functions:
                print(f"  Public functions: {', '.join(functions[:10])}")
                if len(functions) > 10:
                    print(f"    ... and {len(functions) - 10} more")
        except:
            pass

        # 5. Recommendation
        print(f"\n💡 RECOMMENDATION:")
        if not importers:
            print("  ⚠️  CANDIDATE FOR ARCHIVING - Not imported anywhere")
        elif len(importers) < 3:
            print("  🔍 LOW USAGE - Verify if still needed")
        else:
            print("  ✅ ACTIVELY USED - Keep in codebase")

        print()


def main():
    """Main entry point"""
    analyzer = CodeAnalyzer()
    analyzer.build_dependency_graph()

    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            # Check specific file
            if len(sys.argv) < 3:
                print("Usage: python verify_code_usage.py check <file_path>")
                sys.exit(1)
            analyzer.analyze_file(sys.argv[2])

        elif sys.argv[1] == "orphans":
            # Find orphaned files
            print("\n🔍 Finding orphaned files...\n")
            orphaned = analyzer.find_orphaned_files()

            if orphaned:
                print(f"Found {len(orphaned)} potentially orphaned files:\n")
                for file_path, reason in sorted(orphaned):
                    print(f"📄 {file_path}")
                    print(f"   └─ {reason}\n")
            else:
                print("✅ No orphaned files found!")

        elif sys.argv[1] == "duplicates":
            # Find duplicate implementations
            print("\n🔍 Finding duplicate implementations...\n")
            duplicates = analyzer.find_duplicate_implementations()

            if duplicates:
                print(f"Found {len(duplicates)} classes with multiple implementations:\n")
                for class_name, files in sorted(duplicates):
                    print(f"🔄 {class_name} ({len(files)} implementations):")
                    for file_path in files:
                        print(f"   • {file_path}")
                    print()
            else:
                print("✅ No duplicate class names found!")

        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python verify_code_usage.py [orphans|duplicates|check <file>]")
            sys.exit(1)

    else:
        # Run all checks
        print("\n" + "=" * 80)
        print("🔍 FULL CODE ANALYSIS")
        print("=" * 80 + "\n")

        # 1. Orphaned files
        print("1️⃣  ORPHANED FILES:")
        orphaned = analyzer.find_orphaned_files()
        print(f"   Found {len(orphaned)} candidates for archiving\n")

        # 2. Duplicates
        print("2️⃣  DUPLICATE IMPLEMENTATIONS:")
        duplicates = analyzer.find_duplicate_implementations()
        print(f"   Found {len(duplicates)} classes with multiple implementations\n")

        print("\nRun with specific commands for details:")
        print("  python verify_code_usage.py orphans")
        print("  python verify_code_usage.py duplicates")
        print("  python verify_code_usage.py check <file_path>")


if __name__ == "__main__":
    main()
