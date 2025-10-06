"""Test if settings are loading from .env file."""

from omics_oracle_v2.core.config import get_settings

settings = get_settings()

print("=" * 80)
print("SETTINGS LOADED:")
print("=" * 80)
print(f"Debug: {settings.debug}")
print(f"Environment: {getattr(settings, 'environment', 'NOT SET')}")
print()
print("GEO Settings:")
print(f"  ncbi_email: {settings.geo.ncbi_email}")
print(f"  ncbi_api_key: {settings.geo.ncbi_api_key}")
print(f"  rate_limit: {settings.geo.rate_limit}")
print(f"  verify_ssl: {settings.geo.verify_ssl}")
print()
print("=" * 80)

if settings.geo.ncbi_email:
    print("[OK] NCBI email is configured!")
else:
    print("[ERROR] NCBI email is NOT configured!")
    print()
    print("Check:")
    print("  1. Is .env file present?")
    print("  2. Does it have OMICS_GEO_NCBI_EMAIL=your@email.com?")
    print("  3. Is python-dotenv installed?")
