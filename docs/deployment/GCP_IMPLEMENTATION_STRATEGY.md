# GCP Implementation & Testing Strategy

**Document:** Production Implementation Plan for GCP  
**Date:** November 1, 2025  
**Purpose:** Guide implementation and testing on GCP with GPU resources  
**Scope:** Multi-model evaluation (MiniMax-M2, CodeMistral, etc.)

---

## Executive Summary

### Objectives

1. **Clone OmicsOracle to GCP** from GitHub
2. **Set up GPU infrastructure** for model inference testing
3. **Evaluate multiple open-source coding models**:
   - MiniMax-M2 (230B MoE, 10B active)
   - CodeMistral (7B/22B specialized for coding)
   - DeepSeek-Coder (6.7B/33B)
   - StarCoder2 (3B/7B/15B)
   - CodeLlama (7B/13B/34B)
4. **Benchmark performance** (latency, quality, cost)
5. **Implement Phase 1** (modular backend)
6. **Test end-to-end** with real GEO datasets

### Success Criteria

- ✅ All models successfully deployed and serving
- ✅ End-to-end pipeline working (GSE ID → results)
- ✅ Code generation quality ≥90% for common analyses
- ✅ Performance benchmarks documented
- ✅ Cost analysis for production deployment

---

## GCP Infrastructure Setup

### Recommended GCP Configuration

#### Option 1: Cost-Effective Testing (Recommended for Initial Phase)

```yaml
Instance Configuration:
  Machine Type: n1-highmem-8 (8 vCPUs, 52GB RAM)
  GPU: 1× NVIDIA L4 (24GB VRAM)
  Boot Disk: 200GB SSD
  Region: us-central1 (Iowa) - cheapest
  Preemptible: Yes (save 70%)
  
Estimated Cost:
  - Compute: $0.50/hour (preemptible)
  - GPU: $0.28/hour (L4 preemptible)
  - Storage: $5/month
  Total: ~$0.78/hour = $18.72/day = $561.60/month

Models Supported (L4 24GB):
  ✅ CodeMistral-7B (INT4: ~4GB, FP16: ~14GB)
  ✅ DeepSeek-Coder-6.7B (INT4: ~4GB, FP16: ~13GB)
  ✅ StarCoder2-7B (INT4: ~4GB, FP16: ~14GB)
  ✅ CodeLlama-7B (INT4: ~4GB, FP16: ~14GB)
  ⚠️  MiniMax-M2 (10B active, FP8: ~20GB - fits but tight)
```

#### Option 2: Production-Grade Testing

```yaml
Instance Configuration:
  Machine Type: a2-highgpu-1g (12 vCPUs, 85GB RAM)
  GPU: 1× NVIDIA A100 40GB
  Boot Disk: 500GB SSD
  Region: us-central1
  Preemptible: Yes
  
Estimated Cost:
  - Total: ~$1.80/hour = $43/day = $1,296/month

Models Supported (A100 40GB):
  ✅ All models above
  ✅ MiniMax-M2 (10B active, FP16: ~20GB, FP8: ~10GB)
  ✅ CodeLlama-34B (INT4: ~17GB, FP8: ~34GB)
  ✅ DeepSeek-Coder-33B (INT4: ~17GB)
```

#### Option 3: Full Production Deployment

```yaml
Instance Configuration:
  Machine Type: a2-ultragpu-1g (12 vCPUs, 170GB RAM)
  GPU: 1× NVIDIA A100 80GB
  Boot Disk: 1TB SSD
  Region: us-central1
  Preemptible: No (stable production)
  
Estimated Cost:
  - Total: ~$3.67/hour = $88/day = $2,640/month

Models Supported (A100 80GB):
  ✅ All models in full precision
  ✅ MiniMax-M2 (230B with 10B active, FP16: ~20GB)
  ✅ Multiple models simultaneously (model switching)
```

**Recommendation for Testing Phase:** Start with **Option 1 (L4)** for small models, upgrade to **Option 2 (A100 40GB)** when testing MiniMax-M2.

---

## Step-by-Step GCP Setup

### 1. Create GCP Project and Enable APIs

```bash
# Set project ID
export PROJECT_ID="omicsoracle-testing"
export REGION="us-central1"
export ZONE="us-central1-a"

# Create project (if new)
gcloud projects create $PROJECT_ID --name="OmicsOracle Testing"

# Set active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### 2. Create GPU Instance

```bash
# Option 1: L4 GPU (recommended for testing)
gcloud compute instances create omicsoracle-gpu-test \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=n1-highmem-8 \
    --accelerator=type=nvidia-l4,count=1 \
    --maintenance-policy=TERMINATE \
    --preemptible \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --metadata=install-nvidia-driver=True

# Option 2: A100 40GB (for MiniMax-M2)
gcloud compute instances create omicsoracle-gpu-prod \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=a2-highgpu-1g \
    --maintenance-policy=TERMINATE \
    --preemptible \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=500GB \
    --boot-disk-type=pd-ssd \
    --metadata=install-nvidia-driver=True
```

### 3. SSH into Instance and Setup

```bash
# SSH into instance
gcloud compute ssh omicsoracle-gpu-test --zone=$ZONE

# Verify GPU
nvidia-smi

# Should show:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA L4           Off  | 00000000:00:04.0 Off |                    0 |
# | N/A   45C    P0    28W / 72W |      0MiB / 23034MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

### 4. Install System Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit (for Docker GPU support)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Install Git LFS (for large model files)
sudo apt-get install -y git-lfs
git lfs install

# Install development tools
sudo apt-get install -y build-essential cmake htop tmux wget curl
```

### 5. Clone OmicsOracle Repository

```bash
# Navigate to home directory
cd ~

# Clone repository (use your GitHub credentials)
git clone https://github.com/sdodlapa/OmicsOracle.git
cd OmicsOracle

# Verify technical specs are present
ls -lh docs/design/
# Should show:
# - MINIMAX_M2_INTEGRATION_TECHNICAL_SPEC.md
# - M2_INTEGRATION_STRATEGY_ASSESSMENT.md

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install OmicsOracle dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
```

---

## Model Setup and Comparison

### Models to Evaluate

#### 1. MiniMax-M2 (Primary Candidate)

**Specifications:**
- Parameters: 230B total, 10B active (MoE)
- Context: 128K tokens
- Strengths: Best for agentic workflows, multi-step reasoning
- Benchmarks: #1 on SWE-bench (69.4%), Terminal-Bench (46.3%)

**Setup:**
```bash
# Install SGLang for serving
pip install "sglang[all]"

# Download model (requires HuggingFace token)
huggingface-cli login
huggingface-cli download MiniMaxAI/MiniMax-M2 --local-dir ~/models/MiniMax-M2

# Start inference server
python -m sglang.launch_server \
    --model-path ~/models/MiniMax-M2 \
    --tp-size 1 \
    --dtype fp8 \
    --port 8080 \
    --mem-fraction-static 0.85
```

**Memory Requirements:**
- FP16: ~20GB (tight on L4, fine on A100)
- FP8: ~10GB (fits comfortably on L4)
- INT4: ~5GB (very fast, slight quality loss)

---

#### 2. CodeMistral (7B/22B)

**Specifications:**
- Parameters: 7B or 22B
- Context: 32K tokens
- Strengths: Efficient, fast inference, good for Python
- Benchmarks: HumanEval 60.4%, MBPP 68.8%

**Setup:**
```bash
# Install vLLM
pip install vllm

# Download model
huggingface-cli download mistralai/Codestral-22B-v0.1 --local-dir ~/models/CodeMistral-22B

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model ~/models/CodeMistral-22B \
    --dtype float16 \
    --port 8081 \
    --gpu-memory-utilization 0.9
```

**Memory Requirements:**
- 7B FP16: ~14GB (L4 ✅)
- 22B FP16: ~44GB (A100 80GB only)
- 7B INT4: ~4GB (very fast)

---

#### 3. DeepSeek-Coder-V2 (6.7B/33B)

**Specifications:**
- Parameters: 6.7B or 16B or 33B
- Context: 16K tokens (V1), 128K tokens (V2)
- Strengths: Excellent at code completion, supports 86+ languages
- Benchmarks: HumanEval 78.6%, MBPP 70.2%

**Setup:**
```bash
# Download model
huggingface-cli download deepseek-ai/deepseek-coder-6.7b-instruct --local-dir ~/models/DeepSeek-Coder-6.7B

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model ~/models/DeepSeek-Coder-6.7B \
    --dtype float16 \
    --port 8082
```

**Memory Requirements:**
- 6.7B FP16: ~13GB (L4 ✅)
- 33B FP16: ~66GB (A100 80GB ✅)
- 6.7B INT4: ~4GB

---

#### 4. StarCoder2 (3B/7B/15B)

**Specifications:**
- Parameters: 3B, 7B, or 15B
- Context: 16K tokens
- Strengths: Trained on 600+ programming languages, very fast
- Benchmarks: HumanEval 72.6% (15B), MultiPL-E strong

**Setup:**
```bash
# Download model
huggingface-cli download bigcode/starcoder2-15b --local-dir ~/models/StarCoder2-15B

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model ~/models/StarCoder2-15B \
    --dtype float16 \
    --port 8083
```

**Memory Requirements:**
- 7B FP16: ~14GB (L4 ✅)
- 15B FP16: ~30GB (A100 40GB ✅)

---

#### 5. CodeLlama (7B/13B/34B)

**Specifications:**
- Parameters: 7B, 13B, or 34B
- Context: 16K tokens (base), 100K tokens (long context)
- Strengths: Meta's code model, strong Python support
- Benchmarks: HumanEval 53.7% (34B-Instruct)

**Setup:**
```bash
# Download model
huggingface-cli download codellama/CodeLlama-13b-Instruct-hf --local-dir ~/models/CodeLlama-13B

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model ~/models/CodeLlama-13B \
    --dtype float16 \
    --port 8084
```

**Memory Requirements:**
- 7B FP16: ~14GB (L4 ✅)
- 13B FP16: ~26GB (A100 40GB ✅)
- 34B FP16: ~68GB (A100 80GB ✅)

---

## Benchmark Testing Strategy

### Test Dataset Selection

**Use Real GEO Datasets with Known Analysis:**

```python
TEST_DATASETS = {
    "GSE239603": {
        "description": "APOE4 vs control microglia RNA-seq",
        "platform": "GPL24676",
        "data_type": "rna_seq",
        "analysis": "differential_expression",
        "expected_genes": 2489,  # Known from manual analysis
        "difficulty": "medium"
    },
    "GSE48350": {
        "description": "Breast cancer PDX models",
        "platform": "GPL570",
        "data_type": "microarray",
        "analysis": "differential_expression",
        "difficulty": "easy"
    },
    "GSE140440": {
        "description": "Single-cell COVID-19 PBMC",
        "platform": "GPL24676",
        "data_type": "single_cell",
        "analysis": "clustering",
        "difficulty": "hard"
    }
}
```

### Evaluation Metrics

```python
EVALUATION_METRICS = {
    "code_quality": {
        "executable": "Does code run without errors? (0/1)",
        "correct_analysis": "Does it perform the right analysis? (0-5)",
        "best_practices": "Uses proper libraries, error handling? (0-5)",
        "documentation": "Well-commented, clear structure? (0-5)"
    },
    "performance": {
        "generation_time": "Time to generate code (seconds)",
        "execution_time": "Time to execute code (seconds)",
        "total_time": "End-to-end time (seconds)",
        "gpu_memory": "Peak GPU memory usage (GB)"
    },
    "results_quality": {
        "statistical_accuracy": "Correct p-values, fold changes? (0-5)",
        "visualization_quality": "Plots look good? (0-5)",
        "interpretation": "Biological insights correct? (0-5)"
    },
    "cost": {
        "tokens_used": "Total tokens (input + output)",
        "cost_per_analysis": "Estimated cost ($)",
        "cost_per_day": "If running continuously ($)"
    }
}
```

### Benchmark Script

Create `scripts/benchmark_models.py`:

```python
#!/usr/bin/env python3
"""
Benchmark multiple coding models for genomics data analysis.

Tests each model on standardized tasks and compares:
- Code generation quality
- Execution success rate
- Performance (latency, GPU usage)
- Cost (tokens, inference time)
"""

import asyncio
import time
from typing import Dict, List
import pandas as pd
from pathlib import Path

class ModelBenchmark:
    """Benchmark framework for coding models."""
    
    MODELS = {
        "minimax-m2": "http://localhost:8080/v1/chat/completions",
        "codemistral-22b": "http://localhost:8081/v1/chat/completions",
        "deepseek-coder-6.7b": "http://localhost:8082/v1/chat/completions",
        "starcoder2-15b": "http://localhost:8083/v1/chat/completions",
        "codellama-13b": "http://localhost:8084/v1/chat/completions",
    }
    
    TEST_PROMPTS = [
        {
            "name": "simple_de",
            "prompt": """Generate Python code to:
1. Download count matrix from ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE239nnn/GSE239603/suppl/GSE239603_counts.txt.gz
2. Perform differential expression (APOE4 vs Control)
3. Generate volcano plot
4. Export results to CSV

Requirements:
- Use pandas, numpy, scipy
- Include error handling
- Add progress indicators
""",
            "difficulty": "easy"
        },
        {
            "name": "complex_pipeline",
            "prompt": """Generate a complete RNA-seq analysis pipeline for GSE239603:
1. Download and parse metadata
2. Download count matrix
3. Quality control (filter low counts)
4. Normalization (TPM)
5. Differential expression with multiple testing correction
6. Visualizations: volcano plot, heatmap (top 50), PCA
7. Gene ontology enrichment analysis
8. Generate HTML report

Use best practices for bioinformatics analysis.
""",
            "difficulty": "hard"
        }
    ]
    
    async def benchmark_model(self, model_name: str, model_url: str) -> Dict:
        """Benchmark a single model."""
        results = []
        
        for test in self.TEST_PROMPTS:
            start_time = time.time()
            
            # Generate code
            code = await self.generate_code(model_url, test["prompt"])
            generation_time = time.time() - start_time
            
            # Validate code
            is_valid, issues = self.validate_code(code)
            
            # Execute code (in sandbox)
            if is_valid:
                execution_success, execution_time = await self.execute_code(code)
            else:
                execution_success = False
                execution_time = 0
            
            results.append({
                "model": model_name,
                "test": test["name"],
                "difficulty": test["difficulty"],
                "generation_time": generation_time,
                "code_valid": is_valid,
                "execution_success": execution_success,
                "execution_time": execution_time,
                "total_time": generation_time + execution_time
            })
        
        return results
    
    async def run_all_benchmarks(self) -> pd.DataFrame:
        """Run benchmarks for all models."""
        all_results = []
        
        for model_name, model_url in self.MODELS.items():
            print(f"\n{'='*60}")
            print(f"Benchmarking: {model_name}")
            print(f"{'='*60}")
            
            results = await self.benchmark_model(model_name, model_url)
            all_results.extend(results)
        
        df = pd.DataFrame(all_results)
        
        # Save results
        output_path = Path("benchmark_results.csv")
        df.to_csv(output_path, index=False)
        print(f"\n✅ Results saved to: {output_path}")
        
        # Print summary
        self.print_summary(df)
        
        return df
    
    def print_summary(self, df: pd.DataFrame):
        """Print benchmark summary."""
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        summary = df.groupby("model").agg({
            "code_valid": "mean",
            "execution_success": "mean",
            "generation_time": "mean",
            "total_time": "mean"
        }).round(2)
        
        summary.columns = ["Valid Code %", "Success %", "Gen Time (s)", "Total Time (s)"]
        print(summary.to_string())
        
        print("\n🏆 RANKINGS:")
        print(f"Fastest: {summary['Total Time (s)'].idxmin()}")
        print(f"Most Reliable: {summary['Success %'].idxmax()}")
        print(f"Best Code Quality: {summary['Valid Code %'].idxmax()}")

if __name__ == "__main__":
    benchmark = ModelBenchmark()
    asyncio.run(benchmark.run_all_benchmarks())
```

---

## Testing Workflow

### Phase 1: Setup and Validation (Day 1)

```bash
# 1. SSH into GCP instance
gcloud compute ssh omicsoracle-gpu-test --zone=$ZONE

# 2. Clone repository
cd ~
git clone https://github.com/sdodlapa/OmicsOracle.git
cd OmicsOracle

# 3. Setup environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt

# 4. Test existing OmicsOracle
./start_omics_oracle.sh
# Open browser to http://<GCP-IP>:8000/dashboard
# Verify search works

# 5. Install model serving frameworks
pip install vllm sglang transformers
```

### Phase 2: Model Deployment (Days 2-3)

```bash
# Start with smallest model first
# 1. DeepSeek-Coder-6.7B (13GB, fits on L4)
huggingface-cli download deepseek-ai/deepseek-coder-6.7b-instruct --local-dir ~/models/DeepSeek-Coder-6.7B

# Start in tmux session (survives SSH disconnect)
tmux new -s deepseek
python -m vllm.entrypoints.openai.api_server \
    --model ~/models/DeepSeek-Coder-6.7B \
    --dtype float16 \
    --port 8082

# Test inference
curl http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "messages": [{"role": "user", "content": "Write Python code to download a file from FTP"}],
    "max_tokens": 500
  }'

# 2. Deploy other models similarly (one per port)
# CodeMistral → 8081
# StarCoder2 → 8083
# CodeLlama → 8084
# MiniMax-M2 → 8080 (last, needs most memory)
```

### Phase 3: Integration Testing (Days 4-5)

```bash
# Implement M2AnalysisService
cd ~/OmicsOracle

# Create new service module
mkdir -p omics_oracle_v2/services/m2
touch omics_oracle_v2/services/m2/__init__.py

# Implement based on technical spec
# See: docs/design/MINIMAX_M2_INTEGRATION_TECHNICAL_SPEC.md

# Test with simple example
python scripts/test_m2_integration.py
```

### Phase 4: Benchmark Testing (Days 6-7)

```bash
# Run comprehensive benchmarks
python scripts/benchmark_models.py

# Expected output:
# Model              Valid Code %  Success %  Gen Time (s)  Total Time (s)
# ─────────────────────────────────────────────────────────────────────────
# minimax-m2                95%        90%          12.3           45.2
# codemistral-22b           88%        82%           8.1           38.7
# deepseek-coder-6.7b       85%        78%           5.2           32.1
# starcoder2-15b            82%        75%           6.8           35.4
# codellama-13b             80%        72%           7.1           36.2
```

---

## Cost Analysis

### Inference Cost Comparison

| Model | Size | GPU Required | Inference Time | Cost/1K Tokens | Cost/Analysis |
|-------|------|--------------|----------------|----------------|---------------|
| **MiniMax-M2** | 10B active | A100 40GB | 8-12s | $0.015 | $0.30 |
| **CodeMistral-22B** | 22B | A100 40GB | 6-10s | $0.012 | $0.24 |
| **DeepSeek-6.7B** | 6.7B | L4 24GB | 3-5s | $0.008 | $0.16 |
| **StarCoder2-15B** | 15B | A100 40GB | 5-8s | $0.010 | $0.20 |
| **CodeLlama-13B** | 13B | A100 40GB | 4-7s | $0.009 | $0.18 |

**Analysis Assumptions:**
- Average 20K tokens per analysis (15K input prompt, 5K output code)
- Cost = (GPU hourly cost / 3600) × inference time

### Monthly Cost Projection

**Scenario: 100 analyses/day**

| Model | Daily Cost | Monthly Cost | Annual Cost |
|-------|-----------|--------------|-------------|
| MiniMax-M2 | $30 | $900 | $10,800 |
| CodeMistral-22B | $24 | $720 | $8,640 |
| DeepSeek-6.7B | $16 | $480 | $5,760 |
| StarCoder2-15B | $20 | $600 | $7,200 |
| CodeLlama-13B | $18 | $540 | $6,480 |

**Plus Infrastructure:**
- GPU instance: $561-$2,640/month (depending on configuration)
- Storage: $20/month
- Network egress: ~$50/month

---

## Recommendations

### Model Selection Criteria

**For Testing Phase (GCP L4 GPU):**
1. ✅ **DeepSeek-Coder-6.7B** - Best bang for buck, fast inference
2. ✅ **StarCoder2-7B** - Good balance of size and quality
3. ⚠️ **MiniMax-M2** - Requires A100, but best for complex pipelines

**For Production Deployment:**
1. 🥇 **MiniMax-M2** - Best code quality, agentic reasoning
2. 🥈 **CodeMistral-22B** - Good quality, faster than M2
3. 🥉 **DeepSeek-6.7B** - Most cost-effective

### Suggested Testing Order

**Week 1: Infrastructure**
- Day 1-2: Setup GCP instance, clone repo
- Day 3-4: Deploy small models (DeepSeek, StarCoder2)
- Day 5: Test basic code generation

**Week 2: Model Evaluation**
- Day 1-2: Deploy all models
- Day 3-4: Run benchmarks
- Day 5: Analyze results, select best model

**Week 3: Integration**
- Day 1-3: Implement M2AnalysisService
- Day 4-5: End-to-end testing with real datasets

**Week 4: Optimization**
- Day 1-2: Performance tuning
- Day 3-4: Error handling and recovery
- Day 5: Documentation and handoff

---

## Quick Start Commands

### One-Line GCP Setup

```bash
# Create instance with L4 GPU
gcloud compute instances create omicsoracle-test \
    --zone=us-central1-a \
    --machine-type=n1-highmem-8 \
    --accelerator=type=nvidia-l4,count=1 \
    --maintenance-policy=TERMINATE \
    --preemptible \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --metadata=install-nvidia-driver=True

# SSH in
gcloud compute ssh omicsoracle-test --zone=us-central1-a

# Quick setup script
curl -fsSL https://raw.githubusercontent.com/sdodlapa/OmicsOracle/main/scripts/gcp_setup.sh | bash
```

### Model Deployment One-Liners

```bash
# DeepSeek-Coder (recommended for testing)
pip install vllm && \
huggingface-cli download deepseek-ai/deepseek-coder-6.7b-instruct --local-dir ~/models/DeepSeek && \
python -m vllm.entrypoints.openai.api_server --model ~/models/DeepSeek --port 8082 &

# MiniMax-M2 (for production)
pip install sglang && \
huggingface-cli download MiniMaxAI/MiniMax-M2 --local-dir ~/models/M2 && \
python -m sglang.launch_server --model-path ~/models/M2 --dtype fp8 --port 8080 &
```

---

## Success Metrics

### Technical Milestones

- ✅ Day 1: GCP instance running with GPU verified
- ✅ Day 3: First model (DeepSeek) serving successfully
- ✅ Day 5: All 5 models deployed and benchmarked
- ✅ Day 10: End-to-end pipeline working (GSE ID → results)
- ✅ Day 14: Production-ready with selected model

### Quality Targets

- Code execution success rate: ≥90%
- Average analysis time: <5 minutes
- Cost per analysis: <$0.50
- User satisfaction: ≥4/5 stars

---

## Next Steps

1. **Review this strategy** with team
2. **Approve GCP budget** (~$600/month for testing)
3. **Create GCP project** and enable billing
4. **Start with Day 1** setup
5. **Report progress** daily during testing phase

---

**Document Status:** ✅ Ready for Implementation  
**Owner:** DevOps + ML Engineering  
**Timeline:** 2-4 weeks for complete testing and deployment
