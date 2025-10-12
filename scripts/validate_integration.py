#!/usr/bin/env python3
"""
Validate End-to-End Integration Status

Tests that UnifiedSearchPipeline is properly integrated and working.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_1_search_agent_uses_unified_pipeline():
    """Test 1: Verify SearchAgent uses UnifiedSearchPipeline by default."""
    print("\n" + "=" * 60)
    print("TEST 1: SearchAgent Integration")
    print("=" * 60)

    try:
        from omics_oracle_v2.agents import SearchAgent
        from omics_oracle_v2.core import Settings

        settings = Settings()
        agent = SearchAgent(settings=settings)

        # Check feature flag
        if hasattr(agent, "_use_unified_pipeline"):
            if agent._use_unified_pipeline:
                print("✅ SearchAgent._use_unified_pipeline = True")
                print("   SearchAgent IS using UnifiedSearchPipeline")
                return True
            else:
                print("❌ SearchAgent._use_unified_pipeline = False")
                print("   SearchAgent is using LEGACY implementation")
                return False
        else:
            print("⚠️  SearchAgent._use_unified_pipeline attribute not found")
            print("   Cannot determine which implementation is active")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_2_unified_pipeline_config():
    """Test 2: Verify UnifiedSearchPipeline configuration."""
    print("\n" + "=" * 60)
    print("TEST 2: UnifiedSearchPipeline Configuration")
    print("=" * 60)

    try:
        from omics_oracle_v2.agents import SearchAgent
        from omics_oracle_v2.core import Settings

        settings = Settings()
        agent = SearchAgent(settings=settings)

        if hasattr(agent, "_unified_pipeline_config"):
            config = agent._unified_pipeline_config
            print(f"✅ UnifiedSearchConfig found:")
            print(f"   - enable_geo_search: {config.enable_geo_search}")
            print(f"   - enable_publication_search: {config.enable_publication_search}")
            print(f"   - enable_caching: {config.enable_caching}")
            print(f"   - enable_query_optimization: {config.enable_query_optimization}")
            print(f"   - enable_ner: {config.enable_ner}")
            print(f"   - enable_sapbert: {config.enable_sapbert}")
            print(f"   - max_geo_results: {config.max_geo_results}")
            return True
        else:
            print("❌ UnifiedSearchConfig not found")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_3_search_agent_execution():
    """Test 3: Execute SearchAgent and verify it uses unified pipeline."""
    print("\n" + "=" * 60)
    print("TEST 3: SearchAgent Execution (Live Test)")
    print("=" * 60)

    try:
        from omics_oracle_v2.agents import SearchAgent
        from omics_oracle_v2.agents.models.search import SearchInput
        from omics_oracle_v2.core import Settings

        settings = Settings()
        agent = SearchAgent(settings=settings)

        # Create search input
        search_input = SearchInput(
            search_terms=["diabetes"],
            original_query="diabetes",
            max_results=3,
        )

        print(f"Executing search: 'diabetes' (max 3 results)")

        # Execute
        result = agent.execute(search_input)

        if result.success:
            print(f"✅ Search succeeded:")
            print(f"   - Total found: {result.output.total_found}")
            print(f"   - Datasets returned: {len(result.output.datasets)}")

            # Check filters_applied for pipeline indicators
            filters = result.output.filters_applied
            if "search_mode" in filters:
                print(f"   - Search mode: {filters['search_mode']}")
            if "cache_hit" in filters:
                print(f"   - Cache hit: {filters['cache_hit']}")
            if "optimized" in filters:
                print(f"   - Query optimized: {filters['optimized']}")

            # Show first result
            if result.output.datasets:
                first = result.output.datasets[0]
                print(f"\n   First result:")
                print(f"   - GEO ID: {first.dataset.geo_id}")
                print(f"   - Title: {first.dataset.title[:80]}...")
                print(f"   - Relevance: {first.relevance_score:.2f}")

            # Check execution context for implementation type
            if hasattr(result, "context"):
                context = result.context
                if "implementation" in context.metrics:
                    impl = context.metrics["implementation"]
                    if impl == "unified_pipeline":
                        print(f"\n✅ CONFIRMED: Used UnifiedSearchPipeline")
                        return True
                    else:
                        print(f"\n⚠️  Used implementation: {impl}")
                        return False

            return True
        else:
            print(f"❌ Search failed: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_4_unified_pipeline_direct():
    """Test 4: Test UnifiedSearchPipeline directly."""
    print("\n" + "=" * 60)
    print("TEST 4: Direct UnifiedSearchPipeline Test")
    print("=" * 60)

    try:
        from omics_oracle_v2.lib.pipelines.unified_search_pipeline import (
            OmicsSearchPipeline,
            UnifiedSearchConfig,
        )

        config = UnifiedSearchConfig(
            enable_geo_search=True,
            enable_publication_search=False,
            enable_caching=False,  # Disable cache for clean test
            max_geo_results=3,
        )

        pipeline = OmicsSearchPipeline(config)
        print("✅ OmicsSearchPipeline initialized")

        async def run_search():
            result = await pipeline.search(query="diabetes", max_geo_results=3)
            return result

        print("Executing direct pipeline search...")
        result = asyncio.run(run_search())

        print(f"✅ Direct pipeline search succeeded:")
        print(f"   - Query type: {result.query_type}")
        print(f"   - Total results: {result.total_results}")
        print(f"   - GEO datasets: {len(result.geo_datasets)}")
        print(f"   - Search time: {result.search_time_ms:.2f}ms")
        print(f"   - Cache hit: {result.cache_hit}")

        if result.geo_datasets:
            first = result.geo_datasets[0]
            print(f"\n   First result:")
            print(f"   - GEO ID: {first.geo_id}")
            print(f"   - Title: {first.title[:80]}...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_5_dashboard_pipeline_check():
    """Test 5: Check what pipeline the dashboard is using."""
    print("\n" + "=" * 60)
    print("TEST 5: Dashboard Pipeline Check")
    print("=" * 60)

    try:
        dashboard_path = project_root / "omics_oracle_v2" / "lib" / "dashboard" / "app.py"

        if not dashboard_path.exists():
            print(f"❌ Dashboard not found at: {dashboard_path}")
            return False

        # Read dashboard code
        with open(dashboard_path, "r") as f:
            content = f.read()

        # Check for pipeline imports
        has_publication_pipeline = "PublicationSearchPipeline" in content
        has_unified_pipeline = "UnifiedSearchPipeline" in content or "OmicsSearchPipeline" in content
        has_search_agent = "SearchAgent" in content

        print(f"Dashboard file: {dashboard_path}")
        print(f"\nImport analysis:")
        print(f"   - PublicationSearchPipeline: {'✅ FOUND' if has_publication_pipeline else '❌ Not found'}")
        print(f"   - UnifiedSearchPipeline: {'✅ FOUND' if has_unified_pipeline else '❌ Not found'}")
        print(f"   - SearchAgent: {'✅ FOUND' if has_search_agent else '❌ Not found'}")

        if has_publication_pipeline and not has_unified_pipeline and not has_search_agent:
            print(f"\n❌ ISSUE: Dashboard uses OLD PublicationSearchPipeline")
            print(f"   Dashboard needs update to use UnifiedSearchPipeline or SearchAgent")
            return False
        elif has_unified_pipeline or has_search_agent:
            print(f"\n✅ Dashboard uses new implementation")
            return True
        else:
            print(f"\n⚠️  Cannot determine dashboard pipeline")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("OMICSORACLE END-TO-END INTEGRATION VALIDATION")
    print("=" * 60)
    print("\nTesting UnifiedSearchPipeline integration...")

    results = {
        "SearchAgent Feature Flag": test_1_search_agent_uses_unified_pipeline(),
        "UnifiedSearchPipeline Config": test_2_unified_pipeline_config(),
        "SearchAgent Execution": test_3_search_agent_execution(),
        "Direct Pipeline Test": test_4_unified_pipeline_direct(),
        "Dashboard Pipeline Check": test_5_dashboard_pipeline_check(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Integration is working correctly!")
        return 0
    elif failed == 1 and not results["Dashboard Pipeline Check"]:
        print("\n⚠️  API integration working, Dashboard needs update")
        print("   See: docs/development/END_TO_END_INTEGRATION_STATUS.md")
        return 1
    else:
        print("\n❌ INTEGRATION ISSUES DETECTED")
        print("   See: docs/development/END_TO_END_INTEGRATION_STATUS.md")
        return 2


if __name__ == "__main__":
    sys.exit(main())
