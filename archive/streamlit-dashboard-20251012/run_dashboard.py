#!/usr/bin/env python3
"""
Run OmicsOracle Dashboard.

Usage:
    pytho    print("\n" + "=" * 60)
    print("Starting OmicsOracle Dashboard")
    print("=" * 60)
    print(f"URL: http://{args.host}:{args.port}")
    print("Features Enabled:")ripts/run_dashboard.py [--config CONFIG_NAME]

Config options:
    - default: Standard configuration
    - minimal: Minimal features
    - research: Full research features
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run dashboard application."""
    parser = argparse.ArgumentParser(description="Run OmicsOracle Dashboard")
    parser.add_argument(
        "--config",
        choices=["default", "minimal", "research"],
        default="default",
        help="Dashboard configuration preset",
    )
    parser.add_argument("--port", type=int, default=8501, help="Port to run on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")

    args = parser.parse_args()

    # Import here to check for streamlit
    try:
        import streamlit.web.cli as stcli
    except ImportError:
        print("ERROR: Streamlit is not installed.")
        print("Install it with: pip install streamlit")
        sys.exit(1)

    # Get config
    from omics_oracle_v2.lib.dashboard.config import DEFAULT_CONFIG, MINIMAL_CONFIG, RESEARCH_CONFIG

    config_map = {
        "default": DEFAULT_CONFIG,
        "minimal": MINIMAL_CONFIG,
        "research": RESEARCH_CONFIG,
    }

    config = config_map[args.config]

    # Set environment variable for config
    import os

    os.environ["DASHBOARD_CONFIG"] = args.config

    # Run streamlit
    dashboard_path = project_root / "omics_oracle_v2" / "lib" / "dashboard" / "app.py"

    sys.argv = [
        "streamlit",
        "run",
        str(dashboard_path),
        f"--server.port={args.port}",
        f"--server.address={args.host}",
        "--server.headless=true",
    ]

    print(f"\n🧬 Starting OmicsOracle Dashboard ({args.config} config)")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"⚙️  Features: ", end="")
    features = []
    if config.enable_search:
        features.append("Search")
    if config.enable_visualizations:
        features.append("Visualizations")
    if config.enable_analytics:
        features.append("Analytics")
    print(", ".join(features))
    print("\n🚀 Press Ctrl+C to stop\n")

    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
