#!/usr/bin/env python3
"""
Verify NCBI and OpenAI configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from: {env_file}\n")
    else:
        print(f"❌ .env file not found at: {env_file}\n")
except ImportError:
    print("⚠️  python-dotenv not installed\n")

from omics_oracle_v2.core.config import get_settings

print("=" * 70)
print(" " * 20 + "CONFIGURATION VERIFICATION")
print("=" * 70)

settings = get_settings()

print("\n🔍 NCBI/GEO Configuration:")
print(f"  Email: {settings.geo.ncbi_email or '❌ NOT SET'}")
if settings.geo.ncbi_email:
    print(f"  ✅ Email configured: {settings.geo.ncbi_email}")
else:
    print("  ❌ Email NOT configured - searches will fail!")

if settings.geo.ncbi_api_key:
    masked = f"{settings.geo.ncbi_api_key[:10]}...{settings.geo.ncbi_api_key[-4:]}"
    print(f"  ✅ API Key configured: {masked}")
    print(f"  Rate Limit: {settings.geo.rate_limit} req/sec")
else:
    print("  ⚠️  API Key not configured - using default rate limit (3 req/sec)")

print("\n🤖 OpenAI Configuration:")
if settings.ai.openai_api_key:
    masked = f"{settings.ai.openai_api_key[:10]}...{settings.ai.openai_api_key[-10:]}"
    print(f"  ✅ API Key configured: {masked}")
    print(f"  Model: {settings.ai.model}")
    print(f"  Max Tokens: {settings.ai.max_tokens}")
else:
    print("  ❌ API Key NOT configured - AI features will not work!")

print("\n📊 Database Configuration:")
print(f"  URL: {settings.database.url}")

print("\n" + "=" * 70)

if settings.geo.ncbi_email and settings.ai.openai_api_key:
    print("✅ CONFIGURATION COMPLETE - All systems ready!")
elif settings.geo.ncbi_email:
    print("⚠️  PARTIAL - NCBI configured, OpenAI missing")
elif settings.ai.openai_api_key:
    print("⚠️  PARTIAL - OpenAI configured, NCBI missing")
else:
    print("❌ INCOMPLETE - Both NCBI and OpenAI need configuration")

print("=" * 70)
print()

# Exit with appropriate code
exit(0 if (settings.geo.ncbi_email and settings.ai.openai_api_key) else 1)
