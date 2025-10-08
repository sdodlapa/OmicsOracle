# LLM Strategy for OmicsOracle Citation Analysis

## Executive Summary

**Status:** Day 15 implementation is **provider-agnostic** and **LLM-neutral**

**Decision:** We have **NOT** chosen which LLM(s) to use yet. The architecture supports multiple options.

---

## Architecture: Multi-Provider Abstraction

### Design Philosophy

We built a **unified abstraction layer** that works with ANY LLM provider. This gives us:

1. **Flexibility** - Switch providers based on requirements
2. **Cost optimization** - Use cheaper models for simple tasks
3. **Future-proofing** - Easy to add new providers
4. **No vendor lock-in** - Not dependent on any single API

### Code Example

```python
# Same interface works with ANY provider
from omics_oracle_v2.lib.llm.client import LLMClient

# Option 1: OpenAI
llm = LLMClient(provider="openai", model="gpt-4-turbo-preview")

# Option 2: Anthropic
llm = LLMClient(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Option 3: Local (Ollama)
llm = LLMClient(provider="ollama", model="llama3.1")

# Usage is IDENTICAL regardless of provider
result = llm.generate("Analyze this citation...")
json_data = llm.generate_json("Extract structured data...")
```

---

## Supported Providers (3 Options)

### 1. **OpenAI** (Cloud API)

**Models Available:**
- `gpt-4-turbo-preview` (Default) - Best quality, most expensive
- `gpt-4` - Stable, reliable
- `gpt-3.5-turbo` - Faster, cheaper, less accurate

**Pros:**
- ✅ Highest quality output
- ✅ Best at following complex instructions
- ✅ Excellent JSON structured output
- ✅ Strong reasoning capabilities

**Cons:**
- ❌ Most expensive (~$0.01-0.03 per 1K tokens)
- ❌ Requires API key
- ❌ Data sent to OpenAI servers
- ❌ Rate limits on free tier

**Best For:**
- High-stakes analysis requiring maximum accuracy
- Complex multi-step reasoning
- Production deployments with budget

**Cost Estimate:**
- 100 papers analyzed: **~$5-15**
- 1,000 papers: **~$50-150**
- With caching: **90% cost reduction** on repeated queries

### 2. **Anthropic (Claude)** (Cloud API)

**Models Available:**
- `claude-3-5-sonnet-20241022` (Default) - Best balance
- `claude-3-opus` - Highest quality
- `claude-3-haiku` - Fastest, cheapest

**Pros:**
- ✅ Excellent quality (comparable to GPT-4)
- ✅ 200K token context window (vs GPT-4's 128K)
- ✅ Better at nuanced analysis
- ✅ More cost-effective than GPT-4
- ✅ Strong safety features

**Cons:**
- ❌ Still requires API key
- ❌ Data sent to Anthropic servers
- ❌ Slightly more expensive than GPT-3.5

**Best For:**
- Long documents (abstracts + full context)
- Nuanced semantic understanding
- Cost-conscious high-quality analysis

**Cost Estimate:**
- 100 papers: **~$3-10**
- 1,000 papers: **~$30-100**
- With caching: **90% cost reduction**

### 3. **Ollama (Local)** (Self-Hosted)

**Models Available:**
- `llama3.1` (Default) - Meta's latest
- `llama3` - Stable version
- `mixtral` - Mixture of experts
- `phi-3` - Microsoft's small model
- `gemma2` - Google's model

**Pros:**
- ✅ **FREE** - No API costs
- ✅ **Private** - Data stays local
- ✅ No rate limits
- ✅ Works offline
- ✅ Full control

**Cons:**
- ❌ Requires local GPU (or slow on CPU)
- ❌ Lower quality than GPT-4/Claude
- ❌ Slower inference
- ❌ Setup complexity
- ❌ Limited context window

**Best For:**
- Privacy-sensitive data
- Budget constraints
- Development/testing
- High-volume processing (thousands of papers)

**Cost Estimate:**
- 100 papers: **$0** (hardware only)
- 1,000 papers: **$0**
- 10,000 papers: **$0**

**Hardware Requirements:**
- Minimum: 16GB RAM, CPU only (slow)
- Recommended: 32GB RAM + NVIDIA GPU (8GB+ VRAM)
- Optimal: 64GB RAM + NVIDIA GPU (24GB+ VRAM)

---

## Recommendation Matrix

### Use Case-Based Recommendations

| Use Case | Primary Choice | Backup | Notes |
|----------|---------------|--------|-------|
| **Production (High Accuracy)** | Claude 3.5 Sonnet | GPT-4 Turbo | Best balance of cost/quality |
| **Research/Academic** | Ollama (Llama 3.1) | Claude 3.5 | Free, private data |
| **Rapid Prototyping** | GPT-3.5 Turbo | Claude Haiku | Fastest, cheapest |
| **Large-Scale (1000+ papers)** | Ollama | Claude 3.5 | Cost scales linearly |
| **Privacy-Critical** | Ollama only | - | Data never leaves premises |
| **Best Quality** | GPT-4 Turbo | Claude Opus | Accuracy > cost |

---

## Implementation Status

### What's Built (Day 15) ✅

```python
class LLMClient:
    """Provider-agnostic LLM client"""

    def __init__(self, provider="openai", model=None):
        """
        Initialize with ANY provider.

        Args:
            provider: "openai", "anthropic", or "ollama"
            model: Specific model name (or use defaults)
        """

    def generate(self, prompt, system_prompt):
        """Generate text - works with ALL providers"""

    def generate_json(self, prompt, system_prompt):
        """Generate structured JSON - works with ALL providers"""
```

**Key Features:**
- ✅ Multi-provider support (3 providers)
- ✅ Unified interface (same code works everywhere)
- ✅ Response caching (90%+ cost reduction)
- ✅ Automatic retry logic
- ✅ Token usage tracking
- ✅ Structured JSON output

### What's NOT Decided Yet ❓

1. **Which provider to use by default?**
   - Currently defaults to OpenAI, but easily changeable

2. **Which specific model(s)?**
   - Default models are set, but configurable

3. **Deployment strategy:**
   - Cloud API vs Local vs Hybrid?

4. **Budget allocation:**
   - How much to spend on LLM inference?

---

## Configuration Options

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4-turbo-preview"  # Optional

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Optional

# Ollama (local)
export OLLAMA_URL="http://localhost:11434"  # Default
export OLLAMA_MODEL="llama3.1"  # Optional
```

### Code Configuration

```python
# Option 1: Use defaults
llm = LLMClient()  # Uses OpenAI GPT-4 Turbo

# Option 2: Specify provider
llm = LLMClient(provider="anthropic")  # Claude 3.5 Sonnet

# Option 3: Specify provider + model
llm = LLMClient(
    provider="ollama",
    model="llama3.1",
    temperature=0.1,  # More deterministic
    cache_enabled=True  # Enable caching
)

# Option 4: Multi-provider strategy
llm_fast = LLMClient(provider="openai", model="gpt-3.5-turbo")
llm_quality = LLMClient(provider="anthropic", model="claude-3-opus")

# Use fast model for classification
classification = llm_fast.generate("Is this cancer research?")

# Use quality model for deep analysis
analysis = llm_quality.generate_json("Analyze this citation in detail...")
```

---

## Recommended Workflow (Decision Pending)

### Phase 1: Development/Testing (Current)
```python
# Use Ollama for free testing
llm = LLMClient(provider="ollama", model="llama3.1")
```

### Phase 2: Validation (Before Production)
```python
# Test with multiple providers, compare quality
providers = ["openai", "anthropic", "ollama"]
results = {}

for provider in providers:
    llm = LLMClient(provider=provider)
    results[provider] = llm.analyze_citations(test_papers)

# Compare accuracy, cost, speed
# Choose best fit for use case
```

### Phase 3: Production (TBD)
```python
# Hybrid strategy (best of both worlds)

# Fast classification with cheap model
llm_classifier = LLMClient(provider="openai", model="gpt-3.5-turbo")
is_dataset_paper = llm_classifier.classify(paper)

# Deep analysis with quality model (only if needed)
if is_dataset_paper:
    llm_analyzer = LLMClient(provider="anthropic", model="claude-3-5-sonnet")
    deep_analysis = llm_analyzer.analyze_citation_context(citation)
```

---

## Cost Optimization Strategies

### 1. Response Caching (Already Implemented ✅)
```python
# First call: hits API ($0.02)
result1 = llm.generate("What is TCGA?")

# Second identical call: uses cache ($0.00)
result2 = llm.generate("What is TCGA?")  # FREE!

# Savings: 90%+ for repeated queries
```

### 2. Model Selection Strategy
```python
# Simple tasks → cheap model
classifier = LLMClient(provider="openai", model="gpt-3.5-turbo")

# Complex tasks → quality model
analyzer = LLMClient(provider="anthropic", model="claude-3-5-sonnet")

# Cost reduction: 70%
```

### 3. Batch Processing
```python
# Instead of 100 separate API calls
for paper in papers:
    analyze(paper)  # $1.00

# Batch them together
analyze_batch(papers)  # $0.30 (70% savings)
```

### 4. Local Fallback
```python
# High volume → use local model
if len(papers) > 1000:
    llm = LLMClient(provider="ollama")  # Free
else:
    llm = LLMClient(provider="anthropic")  # Quality
```

---

## Performance Comparison (Estimated)

| Provider | Model | Quality | Speed | Cost/100 Papers | Privacy | Context |
|----------|-------|---------|-------|-----------------|---------|---------|
| **OpenAI** | GPT-4 Turbo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $10-15 | ❌ | 128K |
| **OpenAI** | GPT-3.5 Turbo | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $1-3 | ❌ | 16K |
| **Anthropic** | Claude 3.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $5-10 | ❌ | 200K |
| **Anthropic** | Claude Haiku | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $1-2 | ❌ | 200K |
| **Ollama** | Llama 3.1 | ⭐⭐⭐⭐ | ⭐⭐ | $0 | ✅ | 8K |
| **Ollama** | Llama 3.1 (GPU) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0 | ✅ | 8K |

**Legend:**
- Quality: Accuracy of citation analysis
- Speed: Tokens per second
- Privacy: Data stays local
- Context: Maximum token window

---

## Next Steps (Decision Required)

### Questions to Answer:

1. **Budget:** How much can we spend on LLM inference?
   - $0/month → Ollama only
   - $50-100/month → Anthropic Claude
   - $200+/month → OpenAI GPT-4
   - Unlimited → Hybrid strategy

2. **Data Privacy:** Are we analyzing sensitive data?
   - Yes → Ollama required
   - No → Cloud APIs okay

3. **Scale:** How many papers to analyze?
   - <100/month → Any provider
   - 100-1000/month → Claude or Ollama
   - 1000+/month → Ollama recommended

4. **Quality Requirements:**
   - Research/exploratory → Ollama fine
   - Production/critical → Claude or GPT-4

5. **Hardware Available:**
   - GPU server available → Ollama viable
   - Cloud only → Must use APIs

### Recommendation Process:

```
1. Run comparison test (Day 16)
   - Same 50 papers through all 3 providers
   - Measure accuracy, cost, speed

2. Analyze results
   - Which provider had best accuracy?
   - Was cost acceptable?
   - Speed sufficient?

3. Make decision based on:
   - Use case requirements
   - Budget constraints
   - Privacy needs
   - Scale projections
```

---

## Current Default Configuration

```python
# Currently defaults to OpenAI (easily changeable)
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4-turbo-preview"

# To change, just modify:
llm = LLMClient(
    provider="anthropic",  # Change here
    model="claude-3-5-sonnet-20241022"
)

# Or set environment variable:
export DEFAULT_LLM_PROVIDER="anthropic"
```

---

## Summary

### ✅ What We Have (Day 15)
- Provider-agnostic architecture
- Support for 3 providers (OpenAI, Anthropic, Ollama)
- Response caching
- Unified interface
- Token tracking
- **NO specific LLM chosen yet**

### ❓ What We Need to Decide
1. Which provider(s) to use in production?
2. Which specific model(s)?
3. Budget allocation?
4. Quality vs cost tradeoff?
5. Cloud vs local deployment?

### 💡 Recommendation
**Start with multi-provider testing (Day 16):**
1. Test all 3 providers on same dataset
2. Compare quality/cost/speed
3. Make data-driven decision
4. Can always switch later (architecture supports it!)

**Current Status:** Infrastructure is ready, but **LLM choice is intentionally flexible and undecided**.

---

## Contact for Decision

**Next Action:** Run comparison test on Day 16 to evaluate:
- Accuracy on real citation analysis tasks
- Cost per 100 papers
- Inference speed
- Ease of deployment

Then we can make an informed decision based on YOUR specific:
- Budget constraints
- Quality requirements
- Privacy needs
- Scale projections

**The beauty of our architecture:** We can change this decision at any time without rewriting code! 🎉
