# Ollama Installation Guide for OmicsOracle

## What is Ollama?

Ollama is a local LLM runtime that allows you to run open-source language models on your own hardware:
- ✅ **Free**: No API costs
- ✅ **Private**: Data stays on your machine
- ✅ **Fast**: GPU acceleration support
- ✅ **Easy**: One command to install and use

## Installation

### macOS (Current System)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Alternative: Using Homebrew
brew install ollama
```

### Verification

```bash
# Check installation
ollama --version

# Should output something like: ollama version 0.1.x
```

## Installing BioMistral 7B

### Step 1: Download Model

```bash
# Pull BioMistral 7B model (~4GB download)
ollama pull biomistral

# This may take 5-10 minutes depending on internet speed
```

### Step 2: Test Model

```bash
# Test basic inference
ollama run biomistral "What is BRCA1?"

# Expected output: Biomedical explanation of BRCA1 gene
```

### Step 3: Test with OmicsOracle

```bash
# Run validation test with LLM
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
PYTHONPATH=src:$PYTHONPATH python scripts/validate_llm_for_citations.py --llm --provider ollama
```

## Alternative Models

If BioMistral is not available, alternatives:

### Llama 3.1 8B (General Purpose)
```bash
ollama pull llama3.1:8b
```

### Mixtral 8x7B (Higher Quality)
```bash
ollama pull mixtral:8x7b
```

### Llama 3.1 70B (Highest Quality, Requires Strong GPU)
```bash
ollama pull llama3.1:70b
```

## Hardware Requirements

### Minimum (CPU Only)
- RAM: 8GB
- Storage: 10GB
- Speed: Slow (2-5 min per paper)

### Recommended (GPU)
- GPU: NVIDIA RTX 3060+ or M1/M2 Mac
- RAM: 16GB+
- Storage: 10GB
- Speed: Fast (5-15 sec per paper)

### Optimal (High Performance)
- GPU: NVIDIA RTX 4090 or Apple M2 Max/Ultra
- RAM: 32GB+
- Storage: 20GB
- Speed: Very fast (2-5 sec per paper)

## Configuration in OmicsOracle

### Environment Variables

```bash
# Set Ollama as default provider
export LLM_PROVIDER=ollama
export LLM_MODEL=biomistral
export OLLAMA_HOST=http://localhost:11434  # Default Ollama server
```

### Python Configuration

```python
from omics_oracle_v2.lib.llm.client import LLMClient

# Use Ollama with BioMistral
llm = LLMClient(provider="ollama", model="biomistral")

# Test
response = llm.chat([{"role": "user", "content": "What is TCGA?"}])
print(response)
```

## Troubleshooting

### Issue: "ollama: command not found"

**Solution:**
```bash
# macOS: Add to PATH
export PATH="/usr/local/bin:$PATH"

# Or reinstall
curl https://ollama.ai/install.sh | sh
```

### Issue: "Model 'biomistral' not found"

**Solution:**
```bash
# List available models
ollama list

# Pull BioMistral
ollama pull biomistral

# If BioMistral doesn't exist, use alternative
ollama pull llama3.1:8b
```

### Issue: "Connection refused to localhost:11434"

**Solution:**
```bash
# Start Ollama server
ollama serve

# In another terminal, test
ollama run biomistral "test"
```

### Issue: Very slow on CPU

**Solution:**
```bash
# Use smaller model
ollama pull llama3.1:8b

# Or use cloud provider instead
export LLM_PROVIDER=anthropic  # Requires API key
export ANTHROPIC_API_KEY=your_key_here
```

### Issue: Out of memory

**Solution:**
```bash
# Use smaller model
ollama pull llama3.1:7b

# Or adjust context window
export OLLAMA_NUM_CTX=2048  # Reduce from default 4096
```

## Performance Optimization

### GPU Acceleration (NVIDIA)

```bash
# Check GPU is detected
nvidia-smi

# Ollama will automatically use GPU if available
```

### GPU Acceleration (Apple Silicon)

```bash
# M1/M2 Macs automatically use Metal acceleration
# No additional configuration needed
```

### Batch Processing

```python
# Process multiple papers efficiently
from omics_oracle_v2.lib.llm.client import LLMClient

llm = LLMClient(provider="ollama", model="biomistral", cache_enabled=True)

# Cache will avoid re-analyzing same papers
for paper in papers:
    result = llm_analyzer.analyze_citation_context(...)
```

## Cost Analysis

### Ollama (Local) - BioMistral 7B
- **Setup Cost:** $0
- **Per Paper:** $0
- **100 Papers:** $0
- **Hardware:** Use existing Mac/PC
- **Privacy:** ✅ All local

### Comparison: Cloud Providers

**OpenAI (GPT-4 Turbo)**
- Per Paper: ~$0.10
- 100 Papers: ~$10
- Privacy: ❌ Data sent to OpenAI

**Anthropic (Claude 3.5 Sonnet)**
- Per Paper: ~$0.05
- 100 Papers: ~$5
- Privacy: ❌ Data sent to Anthropic

**Ollama Savings:** $5-10 per 100 papers

## Next Steps

After installation:

1. ✅ Verify Ollama installed: `ollama --version`
2. ✅ Download BioMistral: `ollama pull biomistral`
3. ✅ Test model: `ollama run biomistral "What is TCGA?"`
4. ✅ Run validation test:
   ```bash
   cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
   PYTHONPATH=src:$PYTHONPATH python scripts/validate_llm_for_citations.py --llm --provider ollama
   ```
5. ✅ Compare results: Baseline (62.5%) vs LLM (target: >85%)
6. ✅ Make decision: GO/HYBRID/NO-GO

## Additional Resources

- Ollama Documentation: https://ollama.ai/
- BioMistral Paper: https://arxiv.org/abs/2402.10373
- Model Library: https://ollama.ai/library
- OmicsOracle LLM Strategy: `docs/LLM_STRATEGY.md`
