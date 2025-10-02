#!/usr/bin/env python3
"""
Test configuration loading with the updated API keys and settings.
"""

import os
import sys
from pathlib import Path

# Add src to Python path


def test_config_loading():
    """Test that all configurations load correctly with the new API keys."""

    print("🧪 Testing Configuration Loading...")
    print("=" * 50)

    try:
        # Load environment variables from .env.development
        from dotenv import load_dotenv

        env_file = Path(".env.development")
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment from: {env_file}")
        else:
            print("⚠️  .env.development not found, using system environment")

        # Import and test configuration
        from omics_oracle.infrastructure.configuration.config import AppConfig

        print("\n🔧 Creating application configuration...")
        config = AppConfig()

        print(f"📧 NCBI Email: {config.geo.email}")
        print(f"🔑 NCBI API Key: {'Set' if config.geo.api_key else 'Not set'}")
        print(f"🤖 OpenAI API Key: {'Set' if config.openai.api_key else 'Not set'}")
        print(f"🎯 OpenAI Model: {config.openai.model}")
        print(f"🌡️  OpenAI Temperature: {config.openai.temperature}")
        print(f"📊 Max Tokens: {config.openai.max_tokens}")

        print(f"\n🏗️  Environment: {config.environment}")
        print(f"🐛 Debug Mode: {config.debug}")
        print(f"🚀 App Version: {config.app_version}")
        print(f"🌐 Host: {config.host}:{config.port}")

        # Test validation
        print("\n✅ Configuration validation passed!")

        # Check feature flags
        print(f"\n🎛️  Feature Flags:")
        print(f"   - Caching: {config.enable_caching}")
        print(f"   - AI Summarization: {config.enable_ai_summarization}")
        print(f"   - WebSockets: {config.enable_websockets}")
        print(f"   - Batch Processing: {config.enable_batch_processing}")

        # Check sub-configurations
        print(f"\n⚙️  Sub-configurations:")
        print(f"   - Database: {config.database.url}")
        print(f"   - Redis: {config.redis.url}")
        print(f"   - Logging Level: {config.logging.level}")
        print(f"   - Rate Limit: {config.security.rate_limit_per_minute}/min")

        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)
