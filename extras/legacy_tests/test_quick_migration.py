"""
Quick validation test - just import and initialize.
"""
import sys

print("Testing SearchAgent migration...")

try:
    from omics_oracle_v2.agents.search_agent import SearchAgent
    from omics_oracle_v2.core.config import Settings

    print("✓ Imports successful")

    # Create agent
    settings = Settings()
    agent = SearchAgent(
        settings=settings,
        enable_semantic=True,
        enable_publications=True,
    )

    print("✓ SearchAgent initialized")
    print(f"✓ Unified pipeline enabled: {agent._use_unified_pipeline}")
    print(f"✓ Config created: {agent._unified_pipeline_config is not None}")

    print("\n🎉 Migration structure validated successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
