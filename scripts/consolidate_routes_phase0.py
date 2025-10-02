#!/usr/bin/env python3
"""
Route Consolidation Script - Phase 0, Task 3
Consolidates 7 route files into 4 organized files with clear API versioning.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

OLD_ROUTES = [
    "src/omics_oracle/presentation/web/routes/v1.py",
    "src/omics_oracle/presentation/web/routes/v2.py",
    "src/omics_oracle/presentation/web/routes/search.py",
    "src/omics_oracle/presentation/web/routes/analysis.py",
    "src/omics_oracle/presentation/web/routes/enhanced_search.py",
    "src/omics_oracle/presentation/web/routes/futuristic_search.py",
]

NEW_ROUTES = [
    "src/omics_oracle/presentation/web/routes/api_v1.py",
    "src/omics_oracle/presentation/web/routes/api_v2.py",
    "src/omics_oracle/presentation/web/routes/health.py",
    "src/omics_oracle/presentation/web/routes/ui.py",
]


def print_consolidation_summary():
    """Print consolidation summary."""
    print("=" * 70)
    print("ROUTE CONSOLIDATION SUMMARY")
    print("=" * 70)
    print()
    print("OLD STRUCTURE (7 files):")
    print("-" * 70)
    for route in OLD_ROUTES:
        route_path = PROJECT_ROOT / route
        status = "EXISTS" if route_path.exists() else "MISSING"
        print(f"  [{status}] {route}")
    print()
    print("NEW STRUCTURE (4 files):")
    print("-" * 70)
    for route in NEW_ROUTES:
        route_path = PROJECT_ROOT / route
        status = "CREATED" if route_path.exists() else "MISSING"
        print(f"  [{status}] {route}")
    print()
    print("CONSOLIDATION MAPPING:")
    print("-" * 70)
    print("  v1.py + search.py + analysis.py")
    print("    -> api_v1.py (All v1 endpoints + legacy compatibility)")
    print()
    print("  v2.py + enhanced_search.py + futuristic_search.py")
    print("    -> api_v2.py (Enhanced search + real-time + AI features)")
    print()
    print("  health.py (enhanced)")
    print("    -> health.py (Consolidated health/monitoring endpoints)")
    print()
    print("  __init__.py dashboard routes")
    print("    -> ui.py (All UI/dashboard serving logic)")
    print()
    print("BENEFITS:")
    print("-" * 70)
    print("  - Clear API versioning strategy (v1 vs v2)")
    print("  - Eliminated duplicate health check endpoints")
    print("  - Separated concerns (API, health, UI)")
    print("  - Reduced route file count from 7 to 4")
    print("  - Better maintainability and discoverability")
    print("  - Cleaner import structure")
    print()
    print("NEXT STEPS:")
    print("-" * 70)
    print("  1. Verify all routes work correctly")
    print("  2. Run tests to ensure no regressions")
    print("  3. Remove old route files (marked as deprecated)")
    print("  4. Update documentation")
    print("=" * 70)


if __name__ == "__main__":
    print_consolidation_summary()
