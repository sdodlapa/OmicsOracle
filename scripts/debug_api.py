#!/usr/bin/env python3
"""
Debug API Server Startup
Run this to see the actual error that's killing the API server.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("DEBUG: Starting API Server")
print("=" * 60)

try:
    print("\n[1/5] Importing modules...")
    from omics_oracle_v2.api.main import app

    print("✓ Imports successful")

    print("\n[2/5] Checking settings...")
    from omics_oracle_v2.core import Settings

    settings = Settings()
    print(f"✓ Settings loaded")
    print(f"  - Environment: {settings.environment}")
    print(f"  - NCBI Email: {settings.geo.ncbi_email}")

    print("\n[3/5] Checking API config...")
    from omics_oracle_v2.api.config import APISettings

    api_settings = APISettings()
    print(f"✓ API Settings loaded")
    print(f"  - Host: {api_settings.host}")
    print(f"  - Port: {api_settings.port}")

    print("\n[4/5] Testing app creation...")
    print(f"✓ FastAPI app created: {app.title}")

    print("\n[5/5] Starting server...")
    import uvicorn

    uvicorn.run(app, host=api_settings.host, port=api_settings.port, log_level="debug")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nFull traceback:")
    import traceback

    traceback.print_exc()
    sys.exit(1)
