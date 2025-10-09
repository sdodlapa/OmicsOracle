#!/usr/bin/env python3
"""
Test email configuration for OpenAlex and PubMed.

This verifies that your email (sdodl001@odu.edu) is properly configured
for the "polite pool" which gives 10x faster rate limits.
"""

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

def test_email_config():
    """Test that email is properly configured."""
    print("="*80)
    print("Testing Email Configuration for Polite Pool")
    print("="*80)
    
    # Create default config
    config = PublicationSearchConfig()
    
    print("\n✓ Default Configuration Created")
    print(f"  PubMed email: {config.pubmed_config.email}")
    
    # Create pipeline
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()
    
    print("\n✓ Pipeline Initialized")
    
    # Check OpenAlex client
    if pipeline.openalex_client:
        openalex_email = pipeline.openalex_client.config.email
        rate_limit = pipeline.openalex_client.config.rate_limit_per_second
        
        print(f"\n✓ OpenAlex Client Configured")
        print(f"  Email: {openalex_email}")
        print(f"  Rate Limit: {rate_limit} requests/second")
        
        if openalex_email:
            print(f"\n🎉 SUCCESS! Using polite pool with {rate_limit}x faster rate limits!")
            print(f"  - Without email: 1 request/second")
            print(f"  - With email ({openalex_email}): {rate_limit} requests/second")
            print(f"  - Daily limit: 10,000 requests/day")
        else:
            print("\n⚠️  WARNING: No email configured - using slower rate limits")
            print("  - Current: 1 request/second")
            print("  - With email: 10 requests/second (10x faster!)")
    else:
        print("\n❌ OpenAlex client not initialized")
    
    # Check PubMed client
    if pipeline.pubmed_client:
        pubmed_email = pipeline.pubmed_client.config.email
        print(f"\n✓ PubMed Client Configured")
        print(f"  Email: {pubmed_email}")
    
    pipeline.cleanup()
    
    print("\n" + "="*80)
    print("Configuration Test Complete")
    print("="*80)

if __name__ == "__main__":
    test_email_config()
