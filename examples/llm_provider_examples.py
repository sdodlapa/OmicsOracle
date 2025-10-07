"""
Example: How to switch between LLM providers in OmicsOracle.

This demonstrates the provider-agnostic architecture.
ALL examples below produce identical results!
"""

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations import CitationAnalyzer, LLMCitationAnalyzer

# =============================================================================
# EXAMPLE 1: Using OpenAI (GPT-4 Turbo)
# =============================================================================

print("=" * 80)
print("OPTION 1: OpenAI GPT-4 Turbo")
print("=" * 80)

# Initialize with OpenAI
llm_openai = LLMClient(
    provider="openai",
    model="gpt-4-turbo-preview",  # Or "gpt-4", "gpt-3.5-turbo"
    temperature=0.1,  # Deterministic
    cache_enabled=True,  # Save costs
)

# Create citation analyzer
analyzer_openai = LLMCitationAnalyzer(llm_openai)

# Use it (same code for all providers!)
# analysis = analyzer_openai.analyze_citation_context(context, cited, citing)

print("✓ Using OpenAI GPT-4 Turbo")
print("  Quality: Highest")
print("  Cost: ~$10-15 per 100 papers")
print("  Setup: export OPENAI_API_KEY=sk-...")
print()

# =============================================================================
# EXAMPLE 2: Using Anthropic (Claude 3.5 Sonnet)
# =============================================================================

print("=" * 80)
print("OPTION 2: Anthropic Claude 3.5 Sonnet")
print("=" * 80)

# Initialize with Anthropic
llm_anthropic = LLMClient(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",  # Or "claude-3-opus", "claude-3-haiku"
    temperature=0.1,
    cache_enabled=True,
)

# Create citation analyzer
analyzer_anthropic = LLMCitationAnalyzer(llm_anthropic)

# Use it (IDENTICAL code!)
# analysis = analyzer_anthropic.analyze_citation_context(context, cited, citing)

print("✓ Using Anthropic Claude 3.5 Sonnet")
print("  Quality: Excellent (comparable to GPT-4)")
print("  Cost: ~$5-10 per 100 papers")
print("  Setup: export ANTHROPIC_API_KEY=sk-ant-...")
print()

# =============================================================================
# EXAMPLE 3: Using Ollama (Local Llama 3.1)
# =============================================================================

print("=" * 80)
print("OPTION 3: Ollama Local (Llama 3.1)")
print("=" * 80)

# Initialize with Ollama (local)
llm_ollama = LLMClient(
    provider="ollama",
    model="llama3.1",  # Or "llama3", "mixtral", "phi-3"
    temperature=0.1,
    cache_enabled=True,
)

# Create citation analyzer
analyzer_ollama = LLMCitationAnalyzer(llm_ollama)

# Use it (IDENTICAL code!)
# analysis = analyzer_ollama.analyze_citation_context(context, cited, citing)

print("✓ Using Ollama Llama 3.1 (Local)")
print("  Quality: Good")
print("  Cost: FREE ($0)")
print("  Setup: Install Ollama + pull model")
print()

# =============================================================================
# EXAMPLE 4: Hybrid Strategy (Best of Both Worlds)
# =============================================================================

print("=" * 80)
print("OPTION 4: Hybrid Strategy")
print("=" * 80)

# Fast classification with cheap model
llm_classifier = LLMClient(provider="openai", model="gpt-3.5-turbo")

# Deep analysis with quality model
llm_analyzer = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")


def analyze_paper_hybrid(paper, citing_papers):
    """Hybrid approach: fast classification + deep analysis."""

    # Step 1: Quick classification (cheap)
    classifier = LLMCitationAnalyzer(llm_classifier)
    quick_check = classifier.analyze_citation_context(paper, citing_papers[0], paper)

    # Step 2: Deep analysis only if needed (expensive)
    if quick_check.dataset_reused:
        analyzer = LLMCitationAnalyzer(llm_analyzer)
        deep_analysis = analyzer.synthesize_dataset_impact(paper, citing_papers)
        return deep_analysis
    else:
        return None


print("✓ Hybrid: GPT-3.5 for classification + Claude for deep analysis")
print("  Quality: High where it matters")
print("  Cost: ~70% reduction vs all GPT-4")
print()

# =============================================================================
# EXAMPLE 5: Configuration via Environment Variables
# =============================================================================

print("=" * 80)
print("OPTION 5: Environment-Based Configuration")
print("=" * 80)

import os

# Read from environment
provider = os.getenv("LLM_PROVIDER", "anthropic")  # Default to Anthropic
model = os.getenv("LLM_MODEL", None)  # Use provider defaults

llm = LLMClient(provider=provider, model=model)

print(f"✓ Provider: {provider}")
print(f"  Model: {model or 'default'}")
print("  Usage: export LLM_PROVIDER=anthropic")
print()

# =============================================================================
# EXAMPLE 6: Runtime Provider Switching
# =============================================================================

print("=" * 80)
print("OPTION 6: Switch Providers at Runtime")
print("=" * 80)


def analyze_with_fallback(citation_context, cited, citing):
    """Try cloud API, fallback to local on failure."""

    try:
        # Try Anthropic first (fast + cheap)
        llm = LLMClient(provider="anthropic", cache_enabled=True)
        analyzer = LLMCitationAnalyzer(llm)
        return analyzer.analyze_citation_context(citation_context, cited, citing)

    except Exception as e:
        print(f"Anthropic failed: {e}, falling back to Ollama...")

        # Fallback to local model (free but slower)
        llm = LLMClient(provider="ollama")
        analyzer = LLMCitationAnalyzer(llm)
        return analyzer.analyze_citation_context(citation_context, cited, citing)


print("✓ Automatic failover: Cloud → Local")
print("  Reliability: High (always works)")
print("  Cost: Minimal (uses local only on failure)")
print()

# =============================================================================
# KEY TAKEAWAY
# =============================================================================

print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print(
    """
The beauty of our architecture:

1. Write code ONCE
2. Works with ANY LLM provider
3. Switch providers with ONE line change
4. No vendor lock-in
5. Future-proof

Current Status: Infrastructure ready, LLM choice NOT decided yet.

Recommendation: Test all 3 on Day 16, then decide based on:
  - Quality requirements
  - Budget constraints
  - Privacy needs
  - Scale projections
"""
)
print("=" * 80)
