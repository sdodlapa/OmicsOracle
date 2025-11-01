# MiniMax-M2 Integration Technical Specification

**Project:** OmicsOracle v3.0 - Automated Genomics Data Analysis Agent  
**Document Version:** 1.0  
**Date:** November 1, 2025  
**Status:** Design Phase  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Model Specifications](#model-specifications)
4. [Infrastructure Requirements](#infrastructure-requirements)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Component Design](#component-design)
7. [API Design](#api-design)
8. [Code Generation Pipeline](#code-generation-pipeline)
9. [Execution Sandbox](#execution-sandbox)
10. [Security & Safety](#security--safety)
11. [Error Handling & Recovery](#error-handling--recovery)
12. [Performance Optimization](#performance-optimization)
13. [Testing Strategy](#testing-strategy)
14. [Deployment Architecture](#deployment-architecture)
15. [Cost Analysis](#cost-analysis)
16. [Implementation Roadmap](#implementation-roadmap)
17. [Appendices](#appendices)

---

## Executive Summary

### Objective

Integrate MiniMax-M2 (230B parameter MoE model) as an autonomous coding agent within OmicsOracle to automatically:
1. Discover and download genomics data from GEO/SRA/ArrayExpress
2. Generate analysis pipelines (preprocessing, QC, statistical analysis)
3. Execute code in sandboxed environments
4. Generate publication-quality visualizations
5. Produce comprehensive analysis reports

### Key Benefits

- **Automation:** Transform "GSE ID → Results" from manual process to single API call
- **Cost Efficiency:** Self-hosted model eliminates recurring GPT-4 API costs (~$10-30 per analysis)
- **Privacy:** On-premise deployment for sensitive genomics data
- **Reproducibility:** Auto-generated code pipelines with version control
- **Scale:** Handle 100+ concurrent analyses with 4-8× H100 GPUs

### Success Metrics

- **Code Quality:** >90% executable pipelines without manual intervention
- **Analysis Accuracy:** Match or exceed manual bioinformatics workflows
- **Performance:** <30 seconds from GSE ID to executable code
- **Reliability:** >95% uptime with auto-recovery from failures
- **Cost:** ROI in 6-12 months for active research usage

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         OmicsOracle v3.0                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐     ┌──────────────┐  │
│  │   Web UI /   │─────▶│  FastAPI     │────▶│   Analysis   │  │
│  │   Dashboard  │      │  Gateway     │     │   Service    │  │
│  └──────────────┘      └──────────────┘     └──────┬───────┘  │
│                                                     │          │
│                        ┌────────────────────────────┘          │
│                        ▼                                       │
│              ┌──────────────────────┐                         │
│              │  MiniMax-M2 Agent    │                         │
│              │  Orchestrator        │                         │
│              └──────────┬───────────┘                         │
│                        │                                       │
│         ┌──────────────┼──────────────┐                       │
│         ▼              ▼              ▼                       │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │   Data     │ │   Code     │ │ Execution  │               │
│  │ Discovery  │ │ Generator  │ │  Sandbox   │               │
│  │   Agent    │ │   Agent    │ │   Runner   │               │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘               │
│        │              │              │                       │
└────────┼──────────────┼──────────────┼───────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    External Services                          │
├──────────────────────────────────────────────────────────────┤
│  GEO FTP    │  SRA DB    │  MiniMax-M2  │  Results    │     │
│  Servers    │  (NCBI)    │  Inference   │  Storage    │     │
│             │            │  Cluster     │  (S3/Local) │     │
└──────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request (GSE239603, "Compare APOE4 vs control")
    │
    ▼
API Gateway (FastAPI)
    │
    ├─→ Validate Request (GSE ID format, analysis type)
    ├─→ Check Cache (has this been analyzed before?)
    ├─→ Create Analysis Job (UUID, status tracking)
    │
    ▼
Analysis Service Coordinator
    │
    ├─→ Step 1: GEO Metadata Fetch
    │   └─→ Use existing GEO service
    │
    ├─→ Step 2: Data Discovery Agent (M2)
    │   ├─→ Browse GEO web interface
    │   ├─→ Identify data type (RNA-seq, microarray, etc.)
    │   ├─→ Extract FTP/HTTP download links
    │   └─→ Parse sample metadata (conditions, replicates)
    │
    ├─→ Step 3: Code Generation Agent (M2)
    │   ├─→ Context: Platform, data type, user query
    │   ├─→ Generate download code (FTP, HTTP, streaming)
    │   ├─→ Generate preprocessing code (QC, normalization)
    │   ├─→ Generate analysis code (DE, enrichment)
    │   ├─→ Generate visualization code (plots, heatmaps)
    │   └─→ Return complete pipeline with dependencies
    │
    ├─→ Step 4: Sandbox Execution (Docker)
    │   ├─→ Create isolated environment
    │   ├─→ Install dependencies (pip, conda, R packages)
    │   ├─→ Execute pipeline step-by-step
    │   ├─→ Capture outputs (data, plots, logs)
    │   ├─→ Handle errors → M2 debugging loop
    │   └─→ Cleanup sandbox
    │
    └─→ Step 5: Results Packaging
        ├─→ Store generated code (GitHub/S3)
        ├─→ Store analysis results (DB)
        ├─→ Store visualizations (S3/CDN)
        ├─→ Generate summary report
        └─→ Return to user
```

---

## Model Specifications

### MiniMax-M2 Technical Details

**Model Architecture:**
- **Type:** Mixture of Experts (MoE) Transformer
- **Total Parameters:** 230 billion
- **Active Parameters:** 10 billion per forward pass
- **Context Length:** 128,000 tokens
- **Architecture:** Custom MiniMax architecture with interleaved thinking

**Supported Precisions:**
- FP32 (full precision, not recommended for inference)
- BF16 (brain float 16, recommended for quality)
- FP8 (8-bit floating point, H100 optimized)
- INT4 (4-bit quantized, community models)

**Training Data:**
- Code: GitHub, StackOverflow, documentation
- Scientific: PubMed, arXiv, bioRxiv
- Reasoning: Chain-of-thought, tool-use datasets
- Cut-off: September 2024

**Special Features:**
- **Interleaved Thinking:** Uses `<think>...</think>` tags for reasoning
- **Tool Calling:** Native support for function calling
- **Multi-turn Context:** Maintains conversation history
- **Code Execution Awareness:** Understands compile-run-fix loops

### Inference Serving Options

**Option A: SGLang (Recommended)**
```bash
# Fastest inference, best throughput
# 4× H100 80GB, FP8 precision

python -m sglang.launch_server \
    --model-path MiniMaxAI/MiniMax-M2 \
    --tp-size 4 \
    --dtype fp8 \
    --mem-fraction-static 0.85 \
    --port 8080
```

**Performance:**
- Latency: 15-25ms per token (first token: 100-150ms)
- Throughput: 50-100 tokens/sec per request
- Concurrent Users: 15-20 (4× H100)
- Context Window: 128K tokens supported

**Option B: vLLM**
```bash
# Good inference, excellent batching
# 4× H100 80GB, FP8 precision

python -m vllm.entrypoints.openai.api_server \
    --model MiniMaxAI/MiniMax-M2 \
    --tensor-parallel-size 4 \
    --dtype float8 \
    --max-model-len 128000 \
    --port 8080
```

**Performance:**
- Latency: 20-30ms per token
- Throughput: 40-80 tokens/sec per request
- Batch Size: Up to 256 concurrent requests
- Context Window: 128K tokens

**Option C: MLX (Apple Silicon, Development Only)**
```bash
# For local development on Mac
# M2 Ultra/Max recommended

mlx_lm.server \
    --model MiniMaxAI/MiniMax-M2 \
    --port 8080
```

---

## Infrastructure Requirements

### GPU Cluster Specifications

**Production Deployment (Recommended):**

**Configuration:** 4× NVIDIA H100 80GB (SXM or PCIe)

```yaml
Hardware Specifications:
  GPUs:
    - Model: NVIDIA H100 SXM5 or PCIe
    - Memory: 80GB HBM3 per GPU (320GB total)
    - Quantity: 4
    - Interconnect: NVLink 4.0 (SXM) or PCIe 5.0
    - TDP: 700W per GPU (SXM) or 350W (PCIe)
  
  CPU:
    - Model: AMD EPYC 9654 or Intel Xeon Platinum 8480+
    - Cores: 96+ (24 per GPU minimum)
    - RAM: 512GB DDR5 (128GB per GPU minimum)
  
  Storage:
    - NVMe SSD: 8TB (for model weights, cache, temp data)
    - HDD/NAS: 50TB (for analysis results, datasets)
    - Network: 100Gbps for data transfer
  
  Network:
    - Internal: 200Gbps InfiniBand or RoCE
    - External: 10Gbps fiber (for GEO/SRA downloads)
    - Firewall: Hardware firewall for sandbox isolation

Power & Cooling:
  - Power: 3-4 kW total (4× H100 SXM + system)
  - Cooling: Liquid cooling or high-CFM air cooling
  - UPS: 10kVA for continuous operation
```

**Cost Estimate:**
- Hardware: $80,000 - $120,000 (4× H100 + server)
- Infrastructure: $10,000 - $20,000 (network, cooling)
- Annual Operating: $5,000 - $10,000 (power, maintenance)
- **Total First Year:** ~$100,000 - $150,000

**Alternative Configurations:**

**Budget Option:** 2× H100 80GB (INT4 quantization)
- Cost: ~$50,000
- Performance: 60% of full deployment
- Concurrent Users: 5-8
- Use Case: Development, small labs

**Premium Option:** 8× H100 80GB (BF16, high throughput)
- Cost: ~$200,000
- Performance: 2× production throughput
- Concurrent Users: 40-50
- Use Case: Large institutions, commercial service

### Cloud vs On-Premise Comparison

**Cloud (AWS/GCP/Azure):**
```yaml
AWS p5.48xlarge (8× H100):
  - Cost: $98.32/hour = $2,360/day = $70,800/month
  - Storage: S3 ($0.023/GB/month)
  - Network: Data transfer costs
  - Total Monthly: ~$75,000 - $80,000

Break-even vs On-premise: 2-3 months
```

**On-Premise (Recommended):**
```yaml
Initial Investment: $100,000 - $150,000
Monthly Operating: $500 - $1,000
Break-even: After 2-3 months of cloud usage
```

**Recommendation:** On-premise for >6 months usage, cloud for experimentation

---

## Data Flow Architecture

### End-to-End Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Input                                                │
├─────────────────────────────────────────────────────────────┤
│  - GEO ID: GSE239603                                         │
│  - Analysis Type: Differential Expression                    │
│  - Query: "Compare APOE4 vs control microglia"              │
│  - Parameters: padj < 0.05, |log2FC| > 1                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Metadata Discovery (Existing OmicsOracle Service)         │
├─────────────────────────────────────────────────────────────┤
│  GEO SOFT Parser:                                            │
│    - Platform: GPL24676 (Illumina NovaSeq 6000)             │
│    - Type: Expression profiling by high throughput seq      │
│    - Organism: Homo sapiens                                 │
│    - Samples: 24 (12 APOE4, 12 control)                     │
│    - PubMed ID: 37749326                                    │
│                                                              │
│  Output:                                                     │
│    {                                                         │
│      "geo_id": "GSE239603",                                 │
│      "title": "APOE4 impairs microglial response...",      │
│      "platform": "GPL24676",                                │
│      "type": "rna_seq",                                     │
│      "samples": [                                           │
│        {"name": "APOE4_rep1", "condition": "APOE4", ...},  │
│        {"name": "Control_rep1", "condition": "WT", ...}     │
│      ],                                                      │
│      "ftp_base": "ftp://ftp.ncbi.nlm.nih.gov/geo/..."      │
│    }                                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Data Discovery Agent (MiniMax-M2)                         │
├─────────────────────────────────────────────────────────────┤
│  M2 Agent Task:                                              │
│    "Browse GEO page for GSE239603 and find all data files"  │
│                                                              │
│  M2 Actions:                                                 │
│    1. HTTP GET https://www.ncbi.nlm.nih.gov/geo/...         │
│    2. Parse HTML to find FTP links                          │
│    3. List FTP directory contents                           │
│    4. Identify file types and sizes                         │
│                                                              │
│  M2 Output:                                                  │
│    {                                                         │
│      "data_files": [                                        │
│        {                                                     │
│          "type": "series_matrix",                           │
│          "url": "ftp://.../GSE239603_series_matrix.txt.gz", │
│          "size_mb": 2.4                                     │
│        },                                                    │
│        {                                                     │
│          "type": "raw_counts",                              │
│          "url": "ftp://.../GSE239603_counts.txt.gz",        │
│          "size_mb": 15.8                                    │
│        },                                                    │
│        {                                                     │
│          "type": "supplementary",                           │
│          "url": "ftp://.../GSE239603_RAW.tar",              │
│          "size_mb": 4500.0,                                 │
│          "note": "Individual FASTQ files, not needed"       │
│        }                                                     │
│      ],                                                      │
│      "recommended": "raw_counts",                           │
│      "reasoning": "Counts matrix is preprocessed and..."    │
│    }                                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Code Generation Agent (MiniMax-M2)                        │
├─────────────────────────────────────────────────────────────┤
│  M2 Prompt Template:                                         │
│    """                                                       │
│    You are an expert bioinformatics programmer.             │
│    Generate a complete Python pipeline to:                  │
│                                                              │
│    Dataset: GSE239603                                       │
│    Type: RNA-seq (Illumina NovaSeq)                         │
│    Data: Count matrix (genes × samples)                     │
│    Analysis: Differential expression (APOE4 vs control)     │
│    Conditions: 12 APOE4 samples vs 12 control samples       │
│    Thresholds: padj < 0.05, |log2FC| > 1                    │
│                                                              │
│    Requirements:                                             │
│    1. Download count matrix from FTP                        │
│    2. Quality control (filter low-count genes)              │
│    3. Normalization (TPM or DESeq2)                         │
│    4. Differential expression analysis                      │
│    5. Multiple testing correction (Benjamini-Hochberg)      │
│    6. Visualization:                                        │
│       - Volcano plot                                        │
│       - Heatmap (top 50 genes)                              │
│       - PCA plot (sample clustering)                        │
│    7. Gene list export (CSV with stats)                     │
│                                                              │
│    Generate modular, well-documented code with error        │
│    handling and progress reporting.                         │
│    """                                                       │
│                                                              │
│  M2 Output: Complete Python pipeline (see Appendix A)       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Code Validation & Safety Check                           │
├─────────────────────────────────────────────────────────────┤
│  Static Analysis:                                            │
│    ✓ No system calls (os.system, subprocess with shell)     │
│    ✓ No file operations outside /workspace                  │
│    ✓ No network access except approved domains              │
│    ✓ No infinite loops or recursion bombs                   │
│    ✓ Memory limits respected                                │
│                                                              │
│  AST Parsing:                                                │
│    - Extract imports                                        │
│    - Identify external dependencies                         │
│    - Check for dangerous functions                          │
│                                                              │
│  If unsafe → Reject and log                                 │
│  If safe → Proceed to sandbox                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Sandbox Execution (Docker Container)                     │
├─────────────────────────────────────────────────────────────┤
│  Container Specs:                                            │
│    - Image: bioinformatics-base:latest                      │
│    - CPU: 8 cores                                           │
│    - RAM: 32GB                                              │
│    - Disk: 100GB (ephemeral)                                │
│    - Network: Restricted (FTP/HTTP whitelist)               │
│    - Timeout: 30 minutes                                    │
│                                                              │
│  Execution Steps:                                            │
│    1. Create container: docker run --rm --cpus=8 ...        │
│    2. Install dependencies: pip install -r requirements.txt │
│    3. Copy generated code to /workspace/pipeline.py         │
│    4. Execute: python /workspace/pipeline.py                │
│    5. Monitor:                                              │
│       - stdout/stderr streaming                             │
│       - Resource usage (CPU, RAM, disk)                     │
│       - Progress indicators                                 │
│    6. On completion:                                        │
│       - Copy outputs to persistent storage                  │
│       - Extract generated plots/files                       │
│       - Cleanup container                                   │
│                                                              │
│  Error Handling:                                             │
│    - If error → capture traceback                           │
│    - Send to M2 for debugging                               │
│    - M2 generates fixed code                                │
│    - Retry execution (max 3 attempts)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Results Processing & Storage                             │
├─────────────────────────────────────────────────────────────┤
│  Generated Artifacts:                                        │
│    - data/deg_results.csv (2,500 genes, stats)              │
│    - plots/volcano_plot.png (1200×900, 300dpi)              │
│    - plots/heatmap_top50.png (1500×2000, 300dpi)            │
│    - plots/pca_samples.png (1000×800, 300dpi)               │
│    - logs/execution.log (timestamped operations)            │
│    - code/generated_pipeline.py (reproducible code)         │
│                                                              │
│  Storage Locations:                                          │
│    - S3: s3://omics-results/GSE239603/analysis_uuid/        │
│    - Database: PostgreSQL (metadata, stats summary)         │
│    - CDN: CloudFront (plots for fast delivery)              │
│                                                              │
│  Database Schema:                                            │
│    analyses:                                                 │
│      - id (UUID)                                            │
│      - geo_id (GSE239603)                                   │
│      - user_id                                              │
│      - status (completed)                                   │
│      - created_at, completed_at                             │
│      - execution_time_seconds (245)                         │
│      - code_s3_path                                         │
│      - results_s3_path                                      │
│                                                              │
│    differential_expression_results:                         │
│      - analysis_id (FK)                                     │
│      - gene_id                                              │
│      - gene_name                                            │
│      - log2_fold_change                                     │
│      - pvalue                                               │
│      - adjusted_pvalue                                      │
│      - base_mean                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Report Generation (MiniMax-M2)                            │
├─────────────────────────────────────────────────────────────┤
│  M2 Task: Generate natural language report                  │
│                                                              │
│  Input Context:                                              │
│    - Analysis parameters                                    │
│    - Summary statistics                                     │
│    - Top significant genes                                  │
│    - Plot descriptions                                      │
│    - Original GEO metadata                                  │
│    - PubMed paper abstract (if available)                   │
│                                                              │
│  M2 Generated Report:                                        │
│    """                                                       │
│    # Analysis Report: GSE239603                             │
│                                                              │
│    ## Dataset Overview                                      │
│    This RNA-seq study examined gene expression differences  │
│    between APOE4 and wild-type microglia in the context    │
│    of Alzheimer's disease (PMID: 37749326).                │
│                                                              │
│    ## Methods                                               │
│    - Platform: Illumina NovaSeq 6000                        │
│    - Samples: 12 APOE4 vs 12 control microglia              │
│    - Analysis: Differential expression using DESeq2-style   │
│    - Thresholds: FDR < 0.05, |log2FC| > 1                   │
│                                                              │
│    ## Results                                               │
│    - Total genes analyzed: 18,542                           │
│    - Differentially expressed genes: 2,489 (13.4%)          │
│    - Upregulated in APOE4: 1,245 genes                      │
│    - Downregulated in APOE4: 1,244 genes                    │
│                                                              │
│    ## Key Findings                                          │
│    Top upregulated genes in APOE4 microglia include:        │
│    - APOE (log2FC: 3.2, padj: 1.2e-45)                      │
│    - CLU (log2FC: 2.1, padj: 4.5e-32)                       │
│    - TREM2 (log2FC: 1.8, padj: 2.3e-28)                     │
│                                                              │
│    These results suggest enhanced lipid metabolism and      │
│    inflammatory response in APOE4-expressing microglia.     │
│                                                              │
│    ## Visualizations                                        │
│    See attached plots for:                                  │
│    - Volcano plot showing genome-wide expression changes    │
│    - Heatmap of top 50 differentially expressed genes       │
│    - PCA demonstrating clear separation between groups      │
│    """                                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. User Response                                             │
├─────────────────────────────────────────────────────────────┤
│  API Response:                                               │
│    {                                                         │
│      "analysis_id": "a1b2c3d4-...",                         │
│      "status": "completed",                                 │
│      "execution_time": 245,                                 │
│      "summary": {                                           │
│        "total_genes": 18542,                                │
│        "deg_count": 2489,                                   │
│        "upregulated": 1245,                                 │
│        "downregulated": 1244                                │
│      },                                                      │
│      "top_genes": [...],                                    │
│      "plots": {                                             │
│        "volcano": "https://cdn.../volcano.png",             │
│        "heatmap": "https://cdn.../heatmap.png",             │
│        "pca": "https://cdn.../pca.png"                      │
│      },                                                      │
│      "downloads": {                                         │
│        "results_csv": "https://s3.../results.csv",          │
│        "code": "https://s3.../pipeline.py",                 │
│        "report": "https://s3.../report.md"                  │
│      },                                                      │
│      "report": "# Analysis Report...",                      │
│      "reproducible_code": "import pandas as pd..."          │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. MiniMax-M2 Agent Orchestrator

**Purpose:** Coordinate multi-agent tasks (data discovery, code generation, debugging)

**File:** `omics_oracle_v2/agents/m2_orchestrator.py`

```python
"""
MiniMax-M2 Agent Orchestrator

Manages the lifecycle of M2 agent tasks including:
- Connection pool to M2 inference servers
- Task queue management
- Context management (conversation history)
- Tool calling coordination
- Error recovery
"""

from typing import List, Dict, Optional, AsyncGenerator
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

class AgentRole(Enum):
    """Different agent roles for specialized tasks"""
    DATA_DISCOVERY = "data_discovery"
    CODE_GENERATOR = "code_generator"
    DEBUGGER = "debugger"
    REPORT_WRITER = "report_writer"

@dataclass
class M2Message:
    """Single message in conversation with M2"""
    role: str  # "user", "assistant", "system"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[List[Dict]] = None

@dataclass
class M2AgentConfig:
    """Configuration for M2 agent"""
    inference_url: str = "http://localhost:8080/v1/chat/completions"
    model: str = "MiniMaxAI/MiniMax-M2"
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 40
    max_tokens: int = 8192
    timeout_seconds: int = 300
    retry_attempts: int = 3

class MiniMaxM2Orchestrator:
    """
    Orchestrates MiniMax-M2 agent interactions for genomics analysis.
    
    Features:
    - Connection pooling for multiple concurrent requests
    - Conversation history management
    - Tool calling support
    - Automatic retry with exponential backoff
    - Streaming response support
    """
    
    def __init__(self, config: M2AgentConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.conversation_history: Dict[str, List[M2Message]] = {}
    
    async def initialize(self):
        """Initialize HTTP session for M2 inference"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def chat(
        self,
        messages: List[M2Message],
        role: AgentRole,
        stream: bool = False,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Send chat request to M2 and get response.
        
        Args:
            messages: Conversation history
            role: Agent role for specialized behavior
            stream: Stream response token-by-token
            tools: Available tools for function calling
        
        Returns:
            Assistant response text
        """
        # Build request payload
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ],
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_tokens": self.config.max_tokens,
            "stream": stream
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        # Add system prompt based on role
        system_prompt = self._get_system_prompt(role)
        payload["messages"].insert(0, {
            "role": "system",
            "content": system_prompt
        })
        
        # Execute request with retry
        for attempt in range(self.config.retry_attempts):
            try:
                if stream:
                    return await self._stream_request(payload)
                else:
                    return await self._standard_request(payload)
            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
    
    async def _standard_request(self, payload: Dict) -> str:
        """Execute standard (non-streaming) request"""
        async with self.session.post(
            self.config.inference_url,
            json=payload
        ) as response:
            if response.status != 200:
                raise Exception(f"M2 API error: {response.status}")
            
            result = await response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _stream_request(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Execute streaming request"""
        async with self.session.post(
            self.config.inference_url,
            json=payload
        ) as response:
            if response.status != 200:
                raise Exception(f"M2 API error: {response.status}")
            
            async for line in response.content:
                if line:
                    # Parse SSE format
                    if line.startswith(b"data: "):
                        data = line[6:]
                        if data != b"[DONE]":
                            import json
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
    
    def _get_system_prompt(self, role: AgentRole) -> str:
        """Get specialized system prompt for agent role"""
        prompts = {
            AgentRole.DATA_DISCOVERY: """
You are a genomics data discovery expert. Your task is to:
1. Browse GEO/SRA/ArrayExpress databases
2. Identify available data files (FTP links, file types, sizes)
3. Determine the best data source for analysis
4. Extract sample metadata and experimental conditions

Be thorough but efficient. Prefer preprocessed data over raw files.
""",
            AgentRole.CODE_GENERATOR: """
You are an expert bioinformatics programmer. Generate production-quality Python code for:
- RNA-seq differential expression analysis
- Microarray data processing
- Data visualization (matplotlib, seaborn)
- Statistical testing and multiple testing correction

Requirements:
- Modular, well-documented functions
- Error handling and validation
- Progress reporting
- Memory-efficient processing
- Reproducible results

Use standard packages: pandas, numpy, scipy, matplotlib, seaborn.
For specialized tasks, use: GEOparse, scanpy, DESeq2 (via rpy2).
""",
            AgentRole.DEBUGGER: """
You are a Python debugging expert specializing in bioinformatics code.
Analyze errors and generate fixed code.

When you receive an error:
1. Identify the root cause
2. Explain the issue clearly
3. Generate corrected code
4. Add safeguards to prevent similar errors
""",
            AgentRole.REPORT_WRITER: """
You are a scientific writer specializing in genomics research.
Generate clear, accurate analysis reports with:
- Dataset description
- Methods summary
- Key results and statistics
- Biological interpretation
- References to relevant literature

Use appropriate scientific terminology. Be concise but comprehensive.
"""
        }
        
        return prompts[role]
    
    async def generate_analysis_code(
        self,
        geo_id: str,
        platform: str,
        data_type: str,
        analysis_type: str,
        user_query: str,
        data_files: List[Dict]
    ) -> str:
        """
        Generate complete analysis pipeline code.
        
        Args:
            geo_id: GEO dataset ID
            platform: Sequencing/array platform
            data_type: rna_seq, microarray, etc.
            analysis_type: differential_expression, etc.
            user_query: Natural language query
            data_files: Available data files with URLs
        
        Returns:
            Complete Python code for analysis
        """
        # Build detailed prompt
        prompt = f"""
Generate a complete Python analysis pipeline for:

Dataset: {geo_id}
Platform: {platform}
Data Type: {data_type}
Analysis: {analysis_type}
User Query: {user_query}

Available Data Files:
{self._format_data_files(data_files)}

Requirements:
1. Download data from FTP (with retry and validation)
2. Quality control and filtering
3. Normalization (appropriate for data type)
4. Statistical analysis ({analysis_type})
5. Multiple testing correction
6. Visualizations:
   - Volcano plot (if DE analysis)
   - Heatmap (top genes)
   - PCA/MDS (sample clustering)
7. Export results to CSV
8. Generate summary statistics

Code must be:
- Complete and executable
- Well-documented with docstrings
- Modular with functions
- Error-handling throughout
- Progress indicators
- Memory-efficient

Return ONLY the Python code, no explanations.
"""
        
        messages = [M2Message(role="user", content=prompt)]
        
        code = await self.chat(
            messages=messages,
            role=AgentRole.CODE_GENERATOR,
            stream=False
        )
        
        # Extract code from markdown if present
        code = self._extract_code_from_markdown(code)
        
        return code
    
    def _format_data_files(self, files: List[Dict]) -> str:
        """Format file list for prompt"""
        lines = []
        for f in files:
            lines.append(
                f"- {f['type']}: {f['url']} ({f['size_mb']:.1f} MB)"
            )
        return "\n".join(lines)
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Extract Python code from markdown code blocks"""
        if "```python" in text:
            # Extract code between ```python and ```
            start = text.find("```python") + 9
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            # Generic code block
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        else:
            # Return as-is
            return text.strip()
```

### 2. Data Discovery Agent

**Purpose:** Browse GEO/SRA to find download links and file information

**File:** `omics_oracle_v2/agents/data_discovery_agent.py`

```python
"""
Data Discovery Agent

Uses MiniMax-M2 with web browsing capabilities to:
- Navigate GEO/SRA websites
- Extract FTP links and file metadata
- Determine optimal data files for analysis
- Parse sample information and experimental design
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup

@dataclass
class DataFile:
    """Represents a downloadable data file"""
    file_type: str  # "series_matrix", "raw_counts", "suppl", etc.
    url: str
    filename: str
    size_mb: float
    format: str  # "txt.gz", "tar", "CEL.gz", etc.
    recommended: bool = False
    notes: Optional[str] = None

class DataDiscoveryAgent:
    """
    Agent for discovering genomics data files on public repositories.
    
    Supports:
    - GEO (Gene Expression Omnibus)
    - SRA (Sequence Read Archive)
    - ArrayExpress (EBI)
    """
    
    def __init__(self, m2_orchestrator):
        self.m2 = m2_orchestrator
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
    
    async def discover_geo_files(
        self,
        geo_id: str,
        platform: str,
        data_type: str
    ) -> List[DataFile]:
        """
        Discover all available files for a GEO dataset.
        
        Strategy:
        1. Check FTP directory structure
        2. Parse GEO web page for supplementary files
        3. Use M2 to determine best files for analysis
        
        Args:
            geo_id: GEO accession (e.g., GSE239603)
            platform: Platform ID (e.g., GPL24676)
            data_type: rna_seq, microarray, etc.
        
        Returns:
            List of available data files with recommendations
        """
        # Step 1: Get FTP directory listing
        ftp_files = await self._list_ftp_directory(geo_id)
        
        # Step 2: Scrape GEO web page for additional info
        web_files = await self._scrape_geo_page(geo_id)
        
        # Step 3: Merge and deduplicate
        all_files = self._merge_file_lists(ftp_files, web_files)
        
        # Step 4: Ask M2 to recommend best files
        recommended = await self._get_m2_recommendations(
            geo_id, platform, data_type, all_files
        )
        
        return recommended
    
    async def _list_ftp_directory(self, geo_id: str) -> List[DataFile]:
        """List files in GEO FTP directory"""
        import ftplib
        
        files = []
        
        # Determine FTP path
        series_prefix = geo_id[:7] + "nnn"  # GSE239603 -> GSE239nnn
        ftp_path = f"/geo/series/{series_prefix}/{geo_id}"
        
        try:
            ftp = ftplib.FTP("ftp.ncbi.nlm.nih.gov")
            ftp.login()
            
            # Check matrix directory
            try:
                ftp.cwd(f"{ftp_path}/matrix")
                matrix_files = []
                ftp.retrlines("LIST", matrix_files.append)
                
                for line in matrix_files:
                    file_info = self._parse_ftp_line(line, "matrix")
                    if file_info:
                        files.append(file_info)
            except:
                pass  # Directory doesn't exist
            
            # Check suppl directory
            try:
                ftp.cwd(f"{ftp_path}/suppl")
                suppl_files = []
                ftp.retrlines("LIST", suppl_files.append)
                
                for line in suppl_files:
                    file_info = self._parse_ftp_line(line, "suppl")
                    if file_info:
                        files.append(file_info)
            except:
                pass
            
            ftp.quit()
        
        except Exception as e:
            # Log error but don't fail - web scraping might still work
            print(f"FTP listing failed: {e}")
        
        return files
    
    def _parse_ftp_line(self, line: str, directory: str) -> Optional[DataFile]:
        """Parse FTP LIST output line"""
        # FTP LIST format: permissions links owner group size month day time filename
        parts = line.split()
        if len(parts) < 9:
            return None
        
        size_bytes = int(parts[4])
        size_mb = size_bytes / (1024 * 1024)
        filename = parts[-1]
        
        # Determine file type
        if "series_matrix" in filename:
            file_type = "series_matrix"
        elif "RAW" in filename:
            file_type = "raw_archive"
        elif "counts" in filename or "fpkm" in filename or "tpm" in filename:
            file_type = "expression_matrix"
        else:
            file_type = "supplementary"
        
        # Construct FTP URL
        geo_id = filename.split("_")[0]
        series_prefix = geo_id[:7] + "nnn"
        url = f"ftp://ftp.ncbi.nlm.nih.gov/geo/series/{series_prefix}/{geo_id}/{directory}/{filename}"
        
        return DataFile(
            file_type=file_type,
            url=url,
            filename=filename,
            size_mb=size_mb,
            format=filename.split(".")[-1] if "." in filename else "unknown"
        )
    
    async def _scrape_geo_page(self, geo_id: str) -> List[DataFile]:
        """Scrape GEO web page for file links"""
        url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={geo_id}"
        
        async with self.session.get(url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, "html.parser")
        files = []
        
        # Find supplementary file links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # Look for FTP links
            if "ftp.ncbi.nlm.nih.gov" in href:
                filename = href.split("/")[-1]
                
                # Try to get size from page
                size_text = link.parent.get_text()
                size_mb = self._extract_file_size(size_text)
                
                files.append(DataFile(
                    file_type="supplementary",
                    url=href,
                    filename=filename,
                    size_mb=size_mb,
                    format=filename.split(".")[-1] if "." in filename else "unknown"
                ))
        
        return files
    
    def _extract_file_size(self, text: str) -> float:
        """Extract file size from text (e.g., '2.4 Mb' -> 2.4)"""
        match = re.search(r"(\d+\.?\d*)\s*([KMG]b)", text, re.IGNORECASE)
        if match:
            size = float(match.group(1))
            unit = match.group(2).upper()
            
            if unit == "KB":
                return size / 1024
            elif unit == "MB":
                return size
            elif unit == "GB":
                return size * 1024
        
        return 0.0
    
    def _merge_file_lists(
        self,
        ftp_files: List[DataFile],
        web_files: List[DataFile]
    ) -> List[DataFile]:
        """Merge and deduplicate file lists"""
        seen_urls = set()
        merged = []
        
        for file in ftp_files + web_files:
            if file.url not in seen_urls:
                seen_urls.add(file.url)
                merged.append(file)
        
        return merged
    
    async def _get_m2_recommendations(
        self,
        geo_id: str,
        platform: str,
        data_type: str,
        files: List[DataFile]
    ) -> List[DataFile]:
        """
        Use M2 to analyze files and recommend best ones for analysis.
        """
        # Build prompt
        file_list = "\n".join([
            f"{i+1}. {f.file_type}: {f.filename} ({f.size_mb:.1f} MB, {f.format})"
            for i, f in enumerate(files)
        ])
        
        prompt = f"""
Analyze these data files for genomics analysis:

Dataset: {geo_id}
Platform: {platform}
Data Type: {data_type}

Available Files:
{file_list}

For {data_type} analysis, which file(s) should we use?
Consider:
- Preprocessed data is better than raw data
- Count matrices are ideal for RNA-seq
- Avoid downloading huge raw archives (FASTQ, BAM) unless necessary
- Series matrix files contain sample metadata

Respond in JSON format:
{{
  "recommended_files": [1, 3],  // List of file numbers
  "reasoning": "Explanation of why these files were chosen",
  "avoid_files": [5],  // Files to avoid
  "notes": "Any important considerations"
}}
"""
        
        from omics_oracle_v2.agents.m2_orchestrator import M2Message, AgentRole
        
        messages = [M2Message(role="user", content=prompt)]
        response = await self.m2.chat(
            messages=messages,
            role=AgentRole.DATA_DISCOVERY
        )
        
        # Parse JSON response
        import json
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            recommendations = json.loads(json_str)
            
            # Mark recommended files
            for idx in recommendations["recommended_files"]:
                files[idx - 1].recommended = True
                files[idx - 1].notes = recommendations["reasoning"]
        
        except Exception as e:
            # If parsing fails, mark first suitable file as recommended
            for f in files:
                if f.file_type in ["expression_matrix", "series_matrix"]:
                    f.recommended = True
                    break
        
        return files
```

### 3. Code Execution Sandbox

**Purpose:** Safely execute generated code in isolated Docker containers

**File:** `omics_oracle_v2/agents/execution_sandbox.py`

```python
"""
Code Execution Sandbox

Provides secure, isolated environment for running M2-generated analysis code.

Security Features:
- Docker containerization
- Resource limits (CPU, RAM, disk)
- Network restrictions (whitelist only)
- Read-only filesystem (except /workspace)
- Execution timeout
- User namespace isolation
"""

import asyncio
import docker
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    # Resource limits
    cpu_cores: int = 8
    memory_mb: int = 32000
    disk_mb: int = 102400  # 100GB
    
    # Time limits
    timeout_seconds: int = 1800  # 30 minutes
    
    # Network
    network_mode: str = "bridge"
    allowed_domains: List[str] = None
    
    # Docker
    base_image: str = "omicsoracle/bioinformatics-base:latest"
    remove_on_exit: bool = True
    
    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = [
                "ftp.ncbi.nlm.nih.gov",
                "ftp-trace.ncbi.nlm.nih.gov",
                "www.ncbi.nlm.nih.gov",
                "pypi.org",
                "files.pythonhosted.org",
                "conda.anaconda.org"
            ]

@dataclass
class ExecutionResult:
    """Result of code execution"""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    output_files: List[Path]
    error_traceback: Optional[str] = None
    resource_usage: Optional[Dict] = None

class ExecutionSandbox:
    """
    Manages Docker-based code execution sandbox.
    
    Usage:
        sandbox = ExecutionSandbox(config)
        await sandbox.initialize()
        result = await sandbox.execute(code, requirements)
        await sandbox.cleanup()
    """
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.docker_client: Optional[docker.DockerClient] = None
        self.container: Optional[docker.models.containers.Container] = None
        self.workspace_dir: Optional[Path] = None
    
    async def initialize(self):
        """Initialize Docker client and workspace"""
        self.docker_client = docker.from_env()
        
        # Create temporary workspace
        self.workspace_dir = Path(tempfile.mkdtemp(prefix="omics_sandbox_"))
        logger.info(f"Created workspace: {self.workspace_dir}")
    
    async def execute(
        self,
        code: str,
        requirements: Optional[List[str]] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute Python code in sandbox.
        
        Args:
            code: Python code to execute
            requirements: List of pip packages to install
            environment_vars: Environment variables for execution
        
        Returns:
            Execution result with outputs
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Write code to workspace
            code_file = self.workspace_dir / "pipeline.py"
            code_file.write_text(code)
            
            # Write requirements if provided
            if requirements:
                req_file = self.workspace_dir / "requirements.txt"
                req_file.write_text("\n".join(requirements))
            
            # Create container
            self.container = self._create_container(environment_vars)
            
            # Install dependencies if needed
            if requirements:
                await self._install_dependencies()
            
            # Execute code
            exit_code, output = await self._run_code()
            
            # Collect outputs
            output_files = await self._collect_outputs()
            
            # Get resource usage
            resource_usage = await self._get_resource_usage()
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Parse stdout/stderr
            stdout, stderr = self._parse_output(output)
            
            # Check for errors
            error_traceback = None
            if exit_code != 0:
                error_traceback = self._extract_traceback(stderr)
            
            return ExecutionResult(
                success=(exit_code == 0),
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                output_files=output_files,
                error_traceback=error_traceback,
                resource_usage=resource_usage
            )
        
        except asyncio.TimeoutError:
            logger.error("Execution timeout")
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Execution timeout exceeded",
                execution_time=self.config.timeout_seconds,
                output_files=[],
                error_traceback="TimeoutError: Execution exceeded maximum time limit"
            )
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                output_files=[],
                error_traceback=str(e)
            )
    
    def _create_container(
        self,
        environment_vars: Optional[Dict[str, str]]
    ) -> docker.models.containers.Container:
        """Create Docker container with security restrictions"""
        
        # Build volume mounts
        volumes = {
            str(self.workspace_dir): {
                'bind': '/workspace',
                'mode': 'rw'
            }
        }
        
        # Build environment
        env = environment_vars or {}
        env.update({
            'PYTHONUNBUFFERED': '1',
            'MPLBACKEND': 'Agg',  # Non-interactive matplotlib
        })
        
        # Resource limits
        mem_limit = f"{self.config.memory_mb}m"
        cpu_quota = self.config.cpu_cores * 100000  # CPU quota in microseconds
        
        container = self.docker_client.containers.create(
            image=self.config.base_image,
            command="sleep infinity",  # Keep container running
            detach=True,
            remove=self.config.remove_on_exit,
            volumes=volumes,
            environment=env,
            working_dir="/workspace",
            
            # Resource limits
            mem_limit=mem_limit,
            memswap_limit=mem_limit,  # Disable swap
            cpu_quota=cpu_quota,
            cpu_period=100000,
            
            # Security options
            security_opt=['no-new-privileges'],
            cap_drop=['ALL'],
            cap_add=['CHOWN', 'DAC_OVERRIDE', 'SETUID', 'SETGID'],
            read_only=False,  # Need write access to /workspace
            
            # Network
            network_mode=self.config.network_mode,
            
            # Prevent privilege escalation
            user='1000:1000',  # Non-root user
        )
        
        container.start()
        logger.info(f"Container created: {container.id[:12]}")
        
        return container
    
    async def _install_dependencies(self) -> None:
        """Install Python dependencies in container"""
        cmd = "pip install --no-cache-dir -r requirements.txt"
        
        exit_code, output = self.container.exec_run(
            cmd,
            workdir="/workspace",
            demux=True
        )
        
        if exit_code != 0:
            stderr = output[1].decode() if output[1] else ""
            raise Exception(f"Failed to install dependencies: {stderr}")
        
        logger.info("Dependencies installed successfully")
    
    async def _run_code(self) -> Tuple[int, bytes]:
        """Execute the Python code with timeout"""
        cmd = "python pipeline.py"
        
        # Execute with timeout
        exec_instance = self.docker_client.api.exec_create(
            self.container.id,
            cmd,
            workdir="/workspace"
        )
        
        # Start execution
        exec_stream = self.docker_client.api.exec_start(
            exec_instance['Id'],
            stream=True,
            demux=True
        )
        
        # Collect output with timeout
        output_chunks = []
        try:
            timeout_at = asyncio.get_event_loop().time() + self.config.timeout_seconds
            
            for chunk in exec_stream:
                if asyncio.get_event_loop().time() > timeout_at:
                    self.container.kill()
                    raise asyncio.TimeoutError()
                
                output_chunks.append(chunk)
                
                # Yield to event loop periodically
                await asyncio.sleep(0)
        
        except asyncio.TimeoutError:
            raise
        
        # Get exit code
        exec_info = self.docker_client.api.exec_inspect(exec_instance['Id'])
        exit_code = exec_info['ExitCode']
        
        # Combine output
        output = b''.join(
            chunk for chunk in output_chunks if chunk
        )
        
        return exit_code, output
    
    async def _collect_outputs(self) -> List[Path]:
        """Collect generated output files from workspace"""
        output_files = []
        
        # Common output patterns
        patterns = [
            "*.png", "*.jpg", "*.pdf", "*.svg",  # Plots
            "*.csv", "*.tsv", "*.txt",  # Data
            "*.html", "*.md",  # Reports
            "*.h5", "*.h5ad",  # Single-cell data
        ]
        
        for pattern in patterns:
            for file_path in self.workspace_dir.glob(pattern):
                if file_path.is_file():
                    output_files.append(file_path)
        
        logger.info(f"Collected {len(output_files)} output files")
        return output_files
    
    async def _get_resource_usage(self) -> Dict:
        """Get container resource usage statistics"""
        try:
            stats = self.container.stats(stream=False)
            
            # Parse CPU usage
            cpu_delta = (
                stats['cpu_stats']['cpu_usage']['total_usage'] -
                stats['precpu_stats']['cpu_usage']['total_usage']
            )
            system_delta = (
                stats['cpu_stats']['system_cpu_usage'] -
                stats['precpu_stats']['system_cpu_usage']
            )
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
            
            # Parse memory usage
            memory_usage_mb = stats['memory_stats']['usage'] / (1024 * 1024)
            memory_limit_mb = stats['memory_stats']['limit'] / (1024 * 1024)
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage_mb, 2),
                'memory_limit_mb': round(memory_limit_mb, 2),
                'memory_percent': round((memory_usage_mb / memory_limit_mb) * 100, 2)
            }
        
        except Exception as e:
            logger.warning(f"Failed to get resource usage: {e}")
            return {}
    
    def _parse_output(self, output: bytes) -> Tuple[str, str]:
        """Parse stdout and stderr from exec output"""
        try:
            # Docker exec returns tuple of (stdout, stderr)
            if isinstance(output, tuple):
                stdout = output[0].decode('utf-8', errors='replace') if output[0] else ""
                stderr = output[1].decode('utf-8', errors='replace') if output[1] else ""
            else:
                # Single stream
                decoded = output.decode('utf-8', errors='replace')
                stdout = decoded
                stderr = ""
            
            return stdout, stderr
        
        except Exception as e:
            logger.error(f"Failed to parse output: {e}")
            return "", str(e)
    
    def _extract_traceback(self, stderr: str) -> str:
        """Extract Python traceback from stderr"""
        lines = stderr.split('\n')
        traceback_lines = []
        in_traceback = False
        
        for line in lines:
            if line.startswith('Traceback'):
                in_traceback = True
            
            if in_traceback:
                traceback_lines.append(line)
        
        return '\n'.join(traceback_lines) if traceback_lines else stderr
    
    async def cleanup(self):
        """Cleanup container and workspace"""
        try:
            if self.container:
                try:
                    self.container.stop(timeout=5)
                    logger.info("Container stopped")
                except:
                    self.container.kill()
                    logger.info("Container killed")
                
                if not self.config.remove_on_exit:
                    self.container.remove(force=True)
        
        except Exception as e:
            logger.error(f"Container cleanup error: {e}")
        
        try:
            if self.workspace_dir and self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
                logger.info("Workspace cleaned up")
        
        except Exception as e:
            logger.error(f"Workspace cleanup error: {e}")
```

### 4. Code Safety Validator

**Purpose:** Static analysis to detect dangerous code patterns before execution

**File:** `omics_oracle_v2/agents/code_safety_validator.py`

```python
"""
Code Safety Validator

Performs static analysis on M2-generated code to detect:
- Dangerous system calls
- File operations outside /workspace
- Network access to non-whitelisted domains
- Resource abuse (infinite loops, fork bombs)
- Code injection attempts
"""

import ast
import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    """Security risk levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityIssue:
    """Detected security issue"""
    level: RiskLevel
    category: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str

class CodeSafetyValidator:
    """
    Validates Python code for security issues before execution.
    
    Uses AST (Abstract Syntax Tree) analysis to detect:
    - Dangerous imports
    - System calls
    - File operations
    - Network operations
    - Eval/exec usage
    - Infinite loops
    """
    
    # Dangerous modules
    BANNED_MODULES = {
        'os': ['system', 'popen', 'execv', 'execl', 'spawn'],
        'subprocess': ['call', 'Popen', 'run'],
        'commands': '*',  # Deprecated, always dangerous
        'pty': '*',
        'shlex': ['split'],  # Can enable injection
        '__builtin__': ['eval', 'exec', 'compile'],
        'builtins': ['eval', 'exec', 'compile'],
    }
    
    # Allowed modules for bioinformatics
    ALLOWED_MODULES = {
        # Data science
        'pandas', 'numpy', 'scipy', 'sklearn', 'statsmodels',
        # Visualization
        'matplotlib', 'seaborn', 'plotly',
        # Bioinformatics
        'Bio', 'pysam', 'scanpy', 'anndata', 'GEOparse',
        # Utilities
        'requests', 'urllib', 'ftplib', 'gzip', 'tarfile', 'zipfile',
        'json', 'csv', 'pickle', 'pathlib', 'logging',
        # Math
        'math', 'statistics', 'random',
        # R integration
        'rpy2',
    }
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.code_lines: List[str] = []
    
    def validate(self, code: str) -> Tuple[bool, List[SecurityIssue]]:
        """
        Validate Python code for security issues.
        
        Args:
            code: Python code to validate
        
        Returns:
            (is_safe, issues_found)
        """
        self.issues = []
        self.code_lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.issues.append(SecurityIssue(
                level=RiskLevel.CRITICAL,
                category="syntax_error",
                line_number=e.lineno or 0,
                code_snippet=e.text or "",
                description=f"Syntax error: {e.msg}",
                recommendation="Fix syntax errors before execution"
            ))
            return False, self.issues
        
        # Run all checks
        self._check_imports(tree)
        self._check_dangerous_calls(tree)
        self._check_file_operations(tree)
        self._check_network_operations(tree)
        self._check_eval_exec(tree)
        self._check_infinite_loops(tree)
        self._check_resource_abuse(tree)
        
        # Determine if code is safe
        has_critical = any(i.level == RiskLevel.CRITICAL for i in self.issues)
        has_high = any(i.level == RiskLevel.HIGH for i in self.issues)
        
        is_safe = not (has_critical or has_high)
        
        return is_safe, self.issues
    
    def _check_imports(self, tree: ast.AST) -> None:
        """Check for dangerous imports"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._validate_import(alias.name, node.lineno)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    self._validate_import(
                        f"{module}.{alias.name}",
                        node.lineno
                    )
    
    def _validate_import(self, import_path: str, line_number: int) -> None:
        """Validate a single import"""
        base_module = import_path.split('.')[0]
        
        # Check if banned
        if base_module in self.BANNED_MODULES:
            banned_attrs = self.BANNED_MODULES[base_module]
            
            if banned_attrs == '*':
                self.issues.append(SecurityIssue(
                    level=RiskLevel.CRITICAL,
                    category="banned_import",
                    line_number=line_number,
                    code_snippet=self.code_lines[line_number - 1],
                    description=f"Import of banned module: {base_module}",
                    recommendation=f"Remove import of {base_module}"
                ))
            
            else:
                # Check specific attributes
                for part in import_path.split('.'):
                    if part in banned_attrs:
                        self.issues.append(SecurityIssue(
                            level=RiskLevel.CRITICAL,
                            category="banned_import",
                            line_number=line_number,
                            code_snippet=self.code_lines[line_number - 1],
                            description=f"Import of banned function: {import_path}",
                            recommendation=f"Remove import of {import_path}"
                        ))
    
    def _check_dangerous_calls(self, tree: ast.AST) -> None:
        """Check for dangerous function calls"""
        dangerous_patterns = [
            ('os.system', RiskLevel.CRITICAL),
            ('subprocess.', RiskLevel.CRITICAL),
            ('eval(', RiskLevel.CRITICAL),
            ('exec(', RiskLevel.CRITICAL),
            ('compile(', RiskLevel.HIGH),
            ('__import__(', RiskLevel.HIGH),
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else ""
                
                for pattern, level in dangerous_patterns:
                    if pattern in call_str:
                        self.issues.append(SecurityIssue(
                            level=level,
                            category="dangerous_call",
                            line_number=node.lineno,
                            code_snippet=self.code_lines[node.lineno - 1],
                            description=f"Dangerous function call: {call_str}",
                            recommendation="Use safer alternatives"
                        ))
    
    def _check_file_operations(self, tree: ast.AST) -> None:
        """Check file operations stay within /workspace"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check open() calls
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    if node.args:
                        # Try to extract filename
                        filename_node = node.args[0]
                        if isinstance(filename_node, ast.Constant):
                            filename = filename_node.value
                            if isinstance(filename, str):
                                if filename.startswith('/') and not filename.startswith('/workspace'):
                                    self.issues.append(SecurityIssue(
                                        level=RiskLevel.HIGH,
                                        category="file_access",
                                        line_number=node.lineno,
                                        code_snippet=self.code_lines[node.lineno - 1],
                                        description=f"File access outside /workspace: {filename}",
                                        recommendation="Only access files in /workspace directory"
                                    ))
    
    def _check_network_operations(self, tree: ast.AST) -> None:
        """Check network operations use whitelisted domains"""
        # This is a basic check - in practice, runtime enforcement is better
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else ""
                
                # Flag network operations for review
                if any(pattern in call_str for pattern in ['requests.', 'urllib.', 'http.client']):
                    self.issues.append(SecurityIssue(
                        level=RiskLevel.LOW,
                        category="network_access",
                        line_number=node.lineno,
                        code_snippet=self.code_lines[node.lineno - 1],
                        description=f"Network operation detected: {call_str}",
                        recommendation="Ensure only whitelisted domains are accessed"
                    ))
    
    def _check_eval_exec(self, tree: ast.AST) -> None:
        """Check for eval/exec usage"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        self.issues.append(SecurityIssue(
                            level=RiskLevel.CRITICAL,
                            category="code_injection",
                            line_number=node.lineno,
                            code_snippet=self.code_lines[node.lineno - 1],
                            description=f"Use of {node.func.id}() enables code injection",
                            recommendation=f"Remove {node.func.id}() call"
                        ))
    
    def _check_infinite_loops(self, tree: ast.AST) -> None:
        """Check for potential infinite loops"""
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check for 'while True:' without break
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = any(
                        isinstance(n, ast.Break)
                        for n in ast.walk(node)
                    )
                    
                    if not has_break:
                        self.issues.append(SecurityIssue(
                            level=RiskLevel.MEDIUM,
                            category="infinite_loop",
                            line_number=node.lineno,
                            code_snippet=self.code_lines[node.lineno - 1],
                            description="Infinite loop without break statement",
                            recommendation="Add break condition or timeout"
                        ))
    
    def _check_resource_abuse(self, tree: ast.AST) -> None:
        """Check for potential resource abuse"""
        # Check for fork bombs or recursive spawning
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function calls itself recursively without clear termination
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id == node.name:
                                # Recursive call - flag for review
                                self.issues.append(SecurityIssue(
                                    level=RiskLevel.LOW,
                                    category="recursion",
                                    line_number=child.lineno,
                                    code_snippet=self.code_lines[child.lineno - 1],
                                    description=f"Recursive call in {node.name}()",
                                    recommendation="Ensure recursion has proper termination"
```

---

## API Design

### REST API Endpoints

**File:** `omics_oracle_v2/api/routes/agent_analysis.py`

```python
"""
Agent Analysis API Routes

Endpoints for MiniMax-M2 automated genomics analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/api/v3/agent", tags=["agent-analysis"])

# Request/Response Models

class AnalysisType(str, Enum):
    """Supported analysis types"""
    DIFFERENTIAL_EXPRESSION = "differential_expression"
    GENE_ONTOLOGY = "gene_ontology"
    PATHWAY_ENRICHMENT = "pathway_enrichment"
    CLUSTERING = "clustering"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"
    CUSTOM = "custom"

class AnalysisStatus(str, Enum):
    """Analysis job status"""
    QUEUED = "queued"
    DISCOVERING_DATA = "discovering_data"
    GENERATING_CODE = "generating_code"
    VALIDATING_CODE = "validating_code"
    EXECUTING = "executing"
    DEBUGGING = "debugging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentAnalysisRequest(BaseModel):
    """Request to start agent-driven analysis"""
    
    geo_id: str = Field(
        ...,
        description="GEO dataset accession (e.g., GSE239603)",
        regex=r"^GSE\d+$"
    )
    
    analysis_type: AnalysisType = Field(
        default=AnalysisType.DIFFERENTIAL_EXPRESSION,
        description="Type of analysis to perform"
    )
    
    query: str = Field(
        ...,
        description="Natural language description of analysis (e.g., 'Compare APOE4 vs control')",
        min_length=10,
        max_length=1000
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Analysis-specific parameters",
        example={
            "padj_threshold": 0.05,
            "log2fc_threshold": 1.0,
            "top_genes": 50
        }
    )
    
    priority: int = Field(
        default=1,
        description="Job priority (1=low, 5=high)",
        ge=1,
        le=5
    )
    
    notify_on_completion: Optional[str] = Field(
        default=None,
        description="Email address for completion notification"
    )
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate parameters based on analysis type"""
        if v is None:
            return {}
        
        analysis_type = values.get('analysis_type')
        
        if analysis_type == AnalysisType.DIFFERENTIAL_EXPRESSION:
            # Validate DE parameters
            if 'padj_threshold' in v:
                assert 0 < v['padj_threshold'] <= 1, "padj_threshold must be (0, 1]"
            if 'log2fc_threshold' in v:
                assert v['log2fc_threshold'] >= 0, "log2fc_threshold must be >= 0"
        
        return v

class AgentAnalysisResponse(BaseModel):
    """Response after starting analysis"""
    
    analysis_id: UUID = Field(
        ...,
        description="Unique analysis job ID"
    )
    
    status: AnalysisStatus = Field(
        ...,
        description="Current status"
    )
    
    created_at: datetime
    
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    
    status_url: str = Field(
        ...,
        description="URL to check status"
    )

class AnalysisStatusResponse(BaseModel):
    """Analysis status response"""
    
    analysis_id: UUID
    status: AnalysisStatus
    progress_percent: int = Field(ge=0, le=100)
    
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    current_step: str
    steps_completed: List[str]
    
    error_message: Optional[str] = None
    
    # Results (populated when status=COMPLETED)
    results: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Complete analysis results"""
    
    analysis_id: UUID
    geo_id: str
    analysis_type: AnalysisType
    
    status: AnalysisStatus
    execution_time_seconds: float
    
    # Summary statistics
    summary: Dict[str, Any] = Field(
        ...,
        description="Summary statistics",
        example={
            "total_genes": 18542,
            "deg_count": 2489,
            "upregulated": 1245,
            "downregulated": 1244
        }
    )
    
    # Top results
    top_results: List[Dict[str, Any]] = Field(
        ...,
        description="Top genes/features",
        example=[
            {
                "gene": "APOE",
                "log2fc": 3.2,
                "pvalue": 1.2e-45,
                "padj": 1.5e-43
            }
        ]
    )
    
    # Visualizations
    plots: Dict[str, str] = Field(
        ...,
        description="URLs to generated plots",
        example={
            "volcano": "https://cdn.omicsoracle.com/plots/analysis_id/volcano.png",
            "heatmap": "https://cdn.omicsoracle.com/plots/analysis_id/heatmap.png",
            "pca": "https://cdn.omicsoracle.com/plots/analysis_id/pca.png"
        }
    )
    
    # Downloads
    downloads: Dict[str, str] = Field(
        ...,
        description="Downloadable files",
        example={
            "results_csv": "https://s3.../results.csv",
            "code": "https://s3.../pipeline.py",
            "report": "https://s3.../report.md"
        }
    )
    
    # Generated report
    report: str = Field(
        ...,
        description="Natural language analysis report"
    )
    
    # Reproducible code
    code: str = Field(
        ...,
        description="Generated Python code for reproducibility"
    )

# API Endpoints

@router.post("/analyze", response_model=AgentAnalysisResponse)
async def start_agent_analysis(
    request: AgentAnalysisRequest,
    background_tasks: BackgroundTasks,
    # user: User = Depends(get_current_user)  # Authentication
):
    """
    Start automated genomics analysis with MiniMax-M2 agent.
    
    The agent will:
    1. Discover and download data from GEO
    2. Generate analysis code
    3. Execute code in sandbox
    4. Generate visualizations and report
    
    Returns immediately with analysis_id for status checking.
    """
    
    # Create analysis job
    analysis_id = uuid4()
    
    # TODO: Store in database
    # await db.analyses.insert({
    #     "id": analysis_id,
    #     "user_id": user.id,
    #     "geo_id": request.geo_id,
    #     "analysis_type": request.analysis_type,
    #     "query": request.query,
    #     "parameters": request.parameters,
    #     "status": AnalysisStatus.QUEUED,
    #     "created_at": datetime.utcnow()
    # })
    
    # Queue background task
    background_tasks.add_task(
        execute_agent_analysis,
        analysis_id=analysis_id,
        geo_id=request.geo_id,
        analysis_type=request.analysis_type,
        query=request.query,
        parameters=request.parameters or {}
    )
    
    return AgentAnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.QUEUED,
        created_at=datetime.utcnow(),
        estimated_completion=None,  # TODO: Calculate based on queue
        status_url=f"/api/v3/agent/status/{analysis_id}"
    )

@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: UUID):
    """
    Get status of an analysis job.
    
    Use this endpoint to poll for progress updates.
    """
    
    # TODO: Fetch from database
    # analysis = await db.analyses.find_one({"id": analysis_id})
    # if not analysis:
    #     raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Mock response for now
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.EXECUTING,
        progress_percent=45,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        current_step="Executing analysis code",
        steps_completed=[
            "Data discovery",
            "Code generation",
            "Code validation"
        ]
    )

@router.get("/results/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_results(analysis_id: UUID):
    """
    Get complete results for a completed analysis.
    
    Returns 404 if not found, 425 if not yet completed.
    """
    
    # TODO: Fetch from database
    # analysis = await db.analyses.find_one({"id": analysis_id})
    # if not analysis:
    #     raise HTTPException(status_code=404, detail="Analysis not found")
    # 
    # if analysis["status"] != AnalysisStatus.COMPLETED:
    #     raise HTTPException(
    #         status_code=425,
    #         detail=f"Analysis not complete. Current status: {analysis['status']}"
    #     )
    
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/cancel/{analysis_id}")
async def cancel_analysis(analysis_id: UUID):
    """
    Cancel a running analysis.
    
    Stops execution and cleans up resources.
    """
    
    # TODO: Implement cancellation
    # 1. Update status in database
    # 2. Kill Docker container if running
    # 3. Cleanup workspace
    
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/queue")
async def get_analysis_queue():
    """
    Get current analysis queue status.
    
    Shows queued, running, and recently completed jobs.
    """
    
    # TODO: Fetch from database
    return {
        "queued": 3,
        "running": 2,
        "completed_last_hour": 15,
        "jobs": []
    }

# Background Task

async def execute_agent_analysis(
    analysis_id: UUID,
    geo_id: str,
    analysis_type: AnalysisType,
    query: str,
    parameters: Dict[str, Any]
):
    """
    Execute agent-driven analysis in background.
    
    This is the main orchestration function that coordinates:
    1. Data discovery
    2. Code generation
    3. Code validation
    4. Sandbox execution
    5. Results storage
    6. Report generation
    """
    
    from omics_oracle_v2.agents.m2_orchestrator import MiniMaxM2Orchestrator, M2AgentConfig
    from omics_oracle_v2.agents.data_discovery_agent import DataDiscoveryAgent
    from omics_oracle_v2.agents.execution_sandbox import ExecutionSandbox, SandboxConfig
    from omics_oracle_v2.agents.code_safety_validator import CodeSafetyValidator
    
    try:
        # Update status: DISCOVERING_DATA
        await update_analysis_status(analysis_id, AnalysisStatus.DISCOVERING_DATA)
        
        # Step 1: Discover data files
        m2_config = M2AgentConfig()
        m2 = MiniMaxM2Orchestrator(m2_config)
        await m2.initialize()
        
        discovery_agent = DataDiscoveryAgent(m2)
        await discovery_agent.initialize()
        
        # Get GEO metadata (use existing service)
        # geo_metadata = await get_geo_metadata(geo_id)
        
        # Discover data files
        # data_files = await discovery_agent.discover_geo_files(
        #     geo_id=geo_id,
        #     platform=geo_metadata["platform"],
        #     data_type=geo_metadata["type"]
        # )
        
        # Update status: GENERATING_CODE
        await update_analysis_status(analysis_id, AnalysisStatus.GENERATING_CODE)
        
        # Step 2: Generate analysis code
        # code = await m2.generate_analysis_code(
        #     geo_id=geo_id,
        #     platform=geo_metadata["platform"],
        #     data_type=geo_metadata["type"],
        #     analysis_type=analysis_type.value,
        #     user_query=query,
        #     data_files=data_files
        # )
        
        # Update status: VALIDATING_CODE
        await update_analysis_status(analysis_id, AnalysisStatus.VALIDATING_CODE)
        
        # Step 3: Validate code safety
        # validator = CodeSafetyValidator()
        # is_safe, issues = validator.validate(code)
        # 
        # if not is_safe:
        #     await update_analysis_status(
        #         analysis_id,
        #         AnalysisStatus.FAILED,
        #         error="Generated code failed safety validation"
        #     )
        #     return
        
        # Update status: EXECUTING
        await update_analysis_status(analysis_id, AnalysisStatus.EXECUTING)
        
        # Step 4: Execute in sandbox
        # sandbox_config = SandboxConfig()
        # sandbox = ExecutionSandbox(sandbox_config)
        # await sandbox.initialize()
        # 
        # result = await sandbox.execute(
        #     code=code,
        #     requirements=extract_requirements(code)
        # )
        # 
        # # If execution failed, try debugging
        # if not result.success and result.error_traceback:
        #     await update_analysis_status(analysis_id, AnalysisStatus.DEBUGGING)
        #     
        #     # Use M2 to debug and fix code
        #     fixed_code = await m2.debug_code(
        #         original_code=code,
        #         error_traceback=result.error_traceback,
        #         stdout=result.stdout,
        #         stderr=result.stderr
        #     )
        #     
        #     # Retry execution
        #     result = await sandbox.execute(code=fixed_code)
        # 
        # await sandbox.cleanup()
        
        # Step 5: Store results
        # await store_analysis_results(analysis_id, result)
        
        # Update status: COMPLETED
        await update_analysis_status(analysis_id, AnalysisStatus.COMPLETED)
        
        # Cleanup
        await discovery_agent.close()
        await m2.close()
    
    except Exception as e:
        # Update status: FAILED
        await update_analysis_status(
            analysis_id,
            AnalysisStatus.FAILED,
            error=str(e)
        )

async def update_analysis_status(
    analysis_id: UUID,
    status: AnalysisStatus,
    error: Optional[str] = None
):
    """Update analysis status in database"""
    # TODO: Implement database update
    pass
```

### WebSocket API for Real-time Updates

**File:** `omics_oracle_v2/api/websockets/agent_progress.py`

```python
"""
WebSocket API for Real-time Analysis Progress

Provides live updates during analysis execution:
- Status changes
- Progress percentage
- Log streaming
- Partial results
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from uuid import UUID
import asyncio
import json

class AnalysisProgressManager:
    """
    Manages WebSocket connections for analysis progress updates.
    
    Clients connect with analysis_id and receive real-time updates.
    """
    
    def __init__(self):
        # Maps analysis_id -> set of websocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, analysis_id: UUID, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = set()
        
        self.active_connections[analysis_id].add(websocket)
    
    def disconnect(self, analysis_id: UUID, websocket: WebSocket):
        """Remove WebSocket connection"""
        if analysis_id in self.active_connections:
            self.active_connections[analysis_id].discard(websocket)
            
            # Cleanup if no more connections
            if not self.active_connections[analysis_id]:
                del self.active_connections[analysis_id]
    
    async def broadcast(self, analysis_id: UUID, message: dict):
        """Send message to all connected clients for this analysis"""
        if analysis_id not in self.active_connections:
            return
        
        # Send to all connections
        disconnected = set()
        
        for websocket in self.active_connections[analysis_id]:
            try:
                await websocket.send_json(message)
            except:
                disconnected.add(websocket)
        
        # Cleanup disconnected clients
        for websocket in disconnected:
            self.disconnect(analysis_id, websocket)

# Global manager instance
progress_manager = AnalysisProgressManager()

# WebSocket endpoint
async def websocket_analysis_progress(
    websocket: WebSocket,
    analysis_id: UUID
):
    """
    WebSocket endpoint for analysis progress.
    
    Usage (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v3/agent/ws/{analysis_id}');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data.progress_percent);
        console.log('Status:', data.status);
    };
    ```
    """
    
    await progress_manager.connect(analysis_id, websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "analysis_id": str(analysis_id),
            "message": "Connected to analysis progress stream"
        })
        
        # Keep connection alive
        while True:
            # Receive ping/pong to detect disconnection
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Echo pings
                if data == "ping":
                    await websocket.send_text("pong")
            
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        progress_manager.disconnect(analysis_id, websocket)

# Helper function to send progress updates
async def send_progress_update(
    analysis_id: UUID,
    status: str,
    progress_percent: int,
    current_step: str,
    details: Optional[Dict] = None
):
    """
    Send progress update to all connected clients.
    
    Call this from the background analysis task.
    """
    
    message = {
        "type": "progress",
        "analysis_id": str(analysis_id),
        "status": status,
        "progress_percent": progress_percent,
        "current_step": current_step,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        message["details"] = details
    
    await progress_manager.broadcast(analysis_id, message)
```

---

## Security & Safety

### Multi-Layer Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation (API Layer)                       │
├─────────────────────────────────────────────────────────────┤
│  ✓ GEO ID format validation (regex)                         │
│  ✓ Query length limits (10-1000 chars)                      │
│  ✓ Parameter type checking                                  │
│  ✓ Rate limiting per user                                   │
│  ✓ Authentication & authorization                           │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Static Code Analysis (Pre-Execution)               │
├─────────────────────────────────────────────────────────────┤
│  ✓ AST parsing for dangerous patterns                       │
│  ✓ Import whitelist enforcement                             │
│  ✓ File path validation (/workspace only)                   │
│  ✓ Network domain whitelist                                 │
│  ✓ Resource limit checks                                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Container Isolation (Runtime)                      │
├─────────────────────────────────────────────────────────────┤
│  ✓ Docker containerization                                  │
│  ✓ Non-root user (UID 1000)                                 │
│  ✓ Read-only root filesystem                                │
│  ✓ CPU/memory limits enforced                               │
│  ✓ Network isolation (bridge mode)                          │
│  ✓ Capability dropping (no CAP_SYS_ADMIN)                   │
│  ✓ Seccomp/AppArmor profiles                                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Runtime Monitoring (Active Execution)              │
├─────────────────────────────────────────────────────────────┤
│  ✓ Resource usage monitoring (CPU, RAM, disk)               │
│  ✓ Network traffic inspection                               │
│  ✓ Execution timeout enforcement                            │
│  ✓ Process tree monitoring                                  │
│  ✓ Anomaly detection                                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Output Validation (Post-Execution)                 │
├─────────────────────────────────────────────────────────────┤
│  ✓ File type validation (PNG, CSV, etc.)                    │
│  ✓ Size limits enforcement                                  │
│  ✓ Malware scanning (ClamAV)                                │
│  ✓ Data sanitization                                        │
└─────────────────────────────────────────────────────────────┘
```

### Docker Security Configuration

**File:** `docker/bioinformatics-base.Dockerfile`

```dockerfile
# Base image for secure code execution
FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 -s /bin/bash bioinformatics

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install common bioinformatics packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create workspace directory
RUN mkdir /workspace && chown bioinformatics:bioinformatics /workspace

# Switch to non-root user
USER bioinformatics
WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    HOME=/home/bioinformatics

# Default command
CMD ["/bin/bash"]
```

**File:** `docker/requirements.txt`

```
# Data science
pandas==2.1.0
numpy==1.24.3
scipy==1.11.2
scikit-learn==1.3.0
statsmodels==0.14.0

# Visualization
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.16.1

# Bioinformatics
biopython==1.81
pysam==0.21.0
scanpy==1.9.5
anndata==0.10.0
GEOparse==2.0.3

# Utilities
requests==2.31.0
aiohttp==3.8.5
ftplib3==0.0.1
tqdm==4.66.1

# R integration (optional)
rpy2==3.5.13
```

### Network Security

**File:** `omics_oracle_v2/security/network_policy.py`

```python
"""
Network Security Policy

Whitelist-based network access control for sandboxed execution.
"""

from typing import Set
import re

class NetworkPolicy:
    """
    Enforces network access policies for sandboxed code.
    
    Only whitelisted domains can be accessed.
    """
    
    # Allowed domains
    WHITELIST: Set[str] = {
        # NCBI services
        "ftp.ncbi.nlm.nih.gov",
        "ftp-trace.ncbi.nlm.nih.gov",
        "www.ncbi.nlm.nih.gov",
        "eutils.ncbi.nlm.nih.gov",
        
        # EBI services
        "ftp.ebi.ac.uk",
        "www.ebi.ac.uk",
        
        # Package repositories
        "pypi.org",
        "files.pythonhosted.org",
        "conda.anaconda.org",
        "repo.anaconda.com",
        
        # Bioconductor
        "bioconductor.org",
        "master.bioconductor.org",
    }
    
    @classmethod
    def is_allowed(cls, url: str) -> bool:
        """Check if URL is allowed"""
        # Extract domain
        domain_match = re.search(
            r'(?:https?://)?([^/:]+)',
            url
        )
        
        if not domain_match:
            return False
        
        domain = domain_match.group(1)
        
        # Check whitelist
        return domain in cls.WHITELIST
    
    @classmethod
    def validate_urls(cls, code: str) -> tuple[bool, list[str]]:
        """
        Extract and validate all URLs in code.
        
        Returns:
            (all_allowed, disallowed_urls)
        """
        # Extract URLs from code
        url_pattern = r'https?://[^\s\'"<>]+'
        urls = re.findall(url_pattern, code)
        
        # Check each URL
        disallowed = []
        for url in urls:
            if not cls.is_allowed(url):
                disallowed.append(url)
        
        return (len(disallowed) == 0, disallowed)
```

---

## Error Handling & Recovery

### Automatic Debugging Loop

```
Code Generation
      │
      ▼
   Execute
      │
      ├─→ Success ─→ Done
      │
      └─→ Error
            │
            ▼
      Extract Traceback
            │
            ▼
      Send to M2 Debugger
            │
            ▼
      M2 Analyzes Error
            │
            ▼
      Generate Fixed Code
            │
            ▼
      Validate Fix
            │
            ├─→ Safe ─→ Execute (Retry)
            │
            └─→ Unsafe ─→ Fail
                  │
                  └─→ Max Retries? ─→ Final Fail
```

**File:** `omics_oracle_v2/agents/error_recovery.py`

```python
"""
Error Recovery System

Automatic debugging and error recovery using MiniMax-M2.
"""

from typing import Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class DebugContext:
    """Context for debugging failed code"""
    original_code: str
    error_traceback: str
    stdout: str
    stderr: str
    attempt_number: int
    previous_fixes: list[str]

class ErrorRecoveryAgent:
    """
    Uses MiniMax-M2 to debug and fix failed code execution.
    
    Capabilities:
    - Parse Python tracebacks
    - Identify root cause (missing import, wrong API, logic error)
    - Generate fixed code
    - Learn from previous failures
    """
    
    MAX_RETRY_ATTEMPTS = 3
    
    def __init__(self, m2_orchestrator):
        self.m2 = m2_orchestrator
        self.fix_history = []
    
    async def debug_and_fix(
        self,
        context: DebugContext
    ) -> Tuple[bool, Optional[str], str]:
        """
        Attempt to debug and fix failed code.
        
        Args:
            context: Debug context with error information
        
        Returns:
            (success, fixed_code, explanation)
        """
        
        # Check retry limit
        if context.attempt_number >= self.MAX_RETRY_ATTEMPTS:
            return False, None, "Maximum retry attempts exceeded"
        
        # Analyze error type
        error_category = self._categorize_error(context.error_traceback)
        
        # Build debugging prompt
        prompt = self._build_debug_prompt(context, error_category)
        
        # Ask M2 to fix
        from omics_oracle_v2.agents.m2_orchestrator import M2Message, AgentRole
        
        messages = [M2Message(role="user", content=prompt)]
        response = await self.m2.chat(
            messages=messages,
            role=AgentRole.DEBUGGER
        )
        
        # Extract fixed code and explanation
        fixed_code, explanation = self._parse_debug_response(response)
        
        # Validate fix
        from omics_oracle_v2.agents.code_safety_validator import CodeSafetyValidator
        validator = CodeSafetyValidator()
        is_safe, issues = validator.validate(fixed_code)
        
        if not is_safe:
            return False, None, "Fixed code failed safety validation"
        
        # Store fix for learning
        self.fix_history.append({
            'error_category': error_category,
            'original_error': context.error_traceback,
            'fix': explanation
        })
        
        return True, fixed_code, explanation
    
    def _categorize_error(self, traceback: str) -> str:
        """Categorize error type from traceback"""
        
        if "ModuleNotFoundError" in traceback or "ImportError" in traceback:
            return "missing_import"
        
        elif "KeyError" in traceback:
            return "key_error"
        
        elif "FileNotFoundError" in traceback:
            return "file_not_found"
        
        elif "MemoryError" in traceback:
            return "memory_error"
        
        elif "TypeError" in traceback:
            return "type_error"
        
        elif "ValueError" in traceback:
            return "value_error"
        
        elif "AttributeError" in traceback:
            return "attribute_error"
        
        elif "IndexError" in traceback:
            return "index_error"
        
        elif "ZeroDivisionError" in traceback:
            return "zero_division"
        
        elif "URLError" in traceback or "ConnectionError" in traceback:
            return "network_error"
        
        else:
            return "unknown"
    
    def _build_debug_prompt(
        self,
        context: DebugContext,
        error_category: str
    ) -> str:
        """Build prompt for M2 debugger"""
        
        prompt = f"""
You are debugging Python code that failed during execution.

Error Category: {error_category}
Attempt: {context.attempt_number + 1} / {self.MAX_RETRY_ATTEMPTS}

ORIGINAL CODE:
```python
{context.original_code}
```

ERROR TRACEBACK:
```
{context.error_traceback}
```

STDOUT:
```
{context.stdout}
```

STDERR:
```
{context.stderr}
```
"""
        
        # Add context from previous fixes
        if context.previous_fixes:
            prompt += "\n\nPREVIOUS FIX ATTEMPTS:\n"
            for i, fix in enumerate(context.previous_fixes, 1):
                prompt += f"{i}. {fix}\n"
        
        # Add guidance based on error category
        prompt += self._get_category_guidance(error_category)
        
        prompt += """

Analyze the error and provide:
1. Root cause explanation
2. Fixed Python code
3. What was changed and why

Format your response as:
```analysis
[Your analysis of the root cause]
```

```python
[Fixed code here]
```

```explanation
[What you changed and why]
```
"""
        
        return prompt
    
    def _get_category_guidance(self, error_category: str) -> str:
        """Get category-specific debugging guidance"""
        
        guidance = {
            "missing_import": """
GUIDANCE:
- Check if the required package is in requirements.txt
- Verify correct import syntax
- Consider alternative packages if import is not available
""",
            "key_error": """
GUIDANCE:
- Check if key exists before accessing (use .get())
- Verify data structure matches expectations
- Add defensive checks
""",
            "file_not_found": """
GUIDANCE:
- Verify file path is correct
- Check if file needs to be downloaded first
- Add file existence check before access
""",
            "memory_error": """
GUIDANCE:
- Process data in chunks instead of loading all at once
- Use generators or iterators
- Delete intermediate variables
- Consider using mmap for large files
""",
            "network_error": """
GUIDANCE:
- Add retry logic with exponential backoff
- Check if URL is accessible
- Verify network permissions
- Add timeout parameters
""",
            "type_error": """
GUIDANCE:
- Check data types before operations
- Add type conversions where needed
- Verify function arguments match expected types
""",
        }
        
        return guidance.get(error_category, "")
    
    def _parse_debug_response(self, response: str) -> Tuple[str, str]:
        """Parse fixed code and explanation from M2 response"""
        
        # Extract code block
        code_pattern = r'```python\n(.*?)\n```'
        code_match = re.search(code_pattern, response, re.DOTALL)
        
        if code_match:
            fixed_code = code_match.group(1)
        else:
            # Fallback: try generic code block
            code_pattern = r'```\n(.*?)\n```'
            code_match = re.search(code_pattern, response, re.DOTALL)
            fixed_code = code_match.group(1) if code_match else ""
        
        # Extract explanation
        expl_pattern = r'```explanation\n(.*?)\n```'
        expl_match = re.search(expl_pattern, response, re.DOTALL)
        
        if expl_match:
            explanation = expl_match.group(1)
        else:
            # Fallback: use full response
            explanation = response
        
        return fixed_code.strip(), explanation.strip()

### Common Error Patterns and Solutions

| Error Type | Common Cause | Automated Fix |
|------------|-------------|---------------|
| **ModuleNotFoundError** | Missing package | Add to requirements.txt |
| **KeyError** | Missing dict key | Use `.get()` with default |
| **FileNotFoundError** | Download not completed | Add retry with `time.sleep()` |
| **MemoryError** | Loading full dataset | Switch to chunked processing |
| **URLError** | Network timeout | Add retry with backoff |
| **ValueError** | Invalid parameter | Add validation/conversion |
| **AttributeError** | Wrong API usage | Fix method/attribute name |
| **IndexError** | Empty array access | Add length check |
| **ZeroDivisionError** | Division by zero | Add denominator check |
| **TimeoutError** | Slow download | Increase timeout, add progress |
```

---

## Performance Optimization

### Caching Strategy

```python
"""
Multi-level caching for performance optimization.

Cache Levels:
1. GEO metadata cache (Redis)
2. Generated code cache (PostgreSQL)
3. Analysis results cache (S3 + DB)
4. M2 inference cache (in-memory)
"""

from typing import Optional, Any
import hashlib
import json
from redis import asyncio as aioredis
from datetime import timedelta

class AnalysisCache:
    """
    Caches analysis results to avoid redundant computation.
    
    Cache Key Strategy:
    - GEO ID + analysis type + parameters hash
    - Invalidation: 30 days or on new data
    """
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = timedelta(days=30)
    
    def _compute_cache_key(
        self,
        geo_id: str,
        analysis_type: str,
        parameters: dict
    ) -> str:
        """Compute deterministic cache key"""
        
        # Sort parameters for consistent hashing
        params_str = json.dumps(parameters, sort_keys=True)
        
        # Create hash
        content = f"{geo_id}:{analysis_type}:{params_str}"
        hash_hex = hashlib.sha256(content.encode()).hexdigest()
        
        return f"analysis:{hash_hex}"
    
    async def get(
        self,
        geo_id: str,
        analysis_type: str,
        parameters: dict
    ) -> Optional[dict]:
        """Get cached analysis result"""
        
        key = self._compute_cache_key(geo_id, analysis_type, parameters)
        
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        return None
    
    async def set(
        self,
        geo_id: str,
        analysis_type: str,
        parameters: dict,
        result: dict
    ):
        """Cache analysis result"""
        
        key = self._compute_cache_key(geo_id, analysis_type, parameters)
        
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(result)
        )

class CodeCache:
    """
    Caches generated code for similar analyses.
    
    Benefits:
    - Skip code generation for identical requests
    - Learn from successful patterns
    - Faster response times
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_similar_code(
        self,
        geo_id: str,
        platform: str,
        data_type: str,
        analysis_type: str
    ) -> Optional[str]:
        """Find similar successful analysis code"""
        
        # Query for similar analyses
        query = """
        SELECT code, parameters, success_rate
        FROM code_cache
        WHERE platform = $1
          AND data_type = $2
          AND analysis_type = $3
          AND success_rate > 0.9
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        results = await self.db.fetch(
            query,
            platform,
            data_type,
            analysis_type
        )
        
        if results:
            # Return most recent successful code
            return results[0]['code']
        
        return None
    
    async def store_successful_code(
        self,
        geo_id: str,
        platform: str,
        data_type: str,
        analysis_type: str,
        code: str,
        parameters: dict
    ):
        """Store successful code for reuse"""
        
        query = """
        INSERT INTO code_cache
        (geo_id, platform, data_type, analysis_type, code, parameters, success_rate)
        VALUES ($1, $2, $3, $4, $5, $6, 1.0)
        ON CONFLICT (geo_id, analysis_type)
        DO UPDATE SET
            code = EXCLUDED.code,
            success_rate = 1.0,
            updated_at = NOW()
        """
        
        await self.db.execute(
            query,
            geo_id,
            platform,
            data_type,
            analysis_type,
            code,
            json.dumps(parameters)
        )
```

### Parallel Processing

```python
"""
Parallel processing for improved throughput.
"""

import asyncio
from typing import List
from concurrent.futures import ProcessPoolExecutor

class ParallelAnalysisExecutor:
    """
    Execute multiple analyses in parallel.
    
    Strategies:
    1. Queue-based job distribution
    2. GPU sharing across analyses
    3. Container pool management
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = asyncio.Queue()
        self.active_analyses: dict = {}
    
    async def submit(self, analysis_request: dict) -> str:
        """Submit analysis to queue"""
        
        analysis_id = str(uuid4())
        await self.queue.put((analysis_id, analysis_request))
        
        return analysis_id
    
    async def worker(self, worker_id: int):
        """Worker that processes analyses from queue"""
        
        while True:
            # Get next analysis
            analysis_id, request = await self.queue.get()
            
            try:
                # Execute analysis
                result = await execute_agent_analysis(
                    analysis_id=analysis_id,
                    **request
                )
                
                # Store result
                self.active_analyses[analysis_id] = result
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
            
            finally:
                self.queue.task_done()
    
    async def start_workers(self):
        """Start worker pool"""
        
        workers = [
            asyncio.create_task(self.worker(i))
            for i in range(self.max_workers)
        ]
        
        await asyncio.gather(*workers)
```

### M2 Inference Optimization

```python
"""
Optimize M2 inference performance.
"""

class M2InferenceOptimizer:
    """
    Optimizations for MiniMax-M2 inference:
    1. Batching multiple requests
    2. KV cache reuse
    3. Speculative decoding
    4. Quantization (FP8)
    """
    
    def __init__(self):
        self.request_batch = []
        self.batch_size = 8
        self.batch_timeout = 0.1  # 100ms
    
    async def optimized_inference(
        self,
        prompt: str,
        config: dict
    ) -> str:
        """
        Batched inference with optimizations.
        
        Groups multiple requests together for better GPU utilization.
        """
        
        # Add to batch
        self.request_batch.append((prompt, config))
        
        # Wait for batch or timeout
        if len(self.request_batch) >= self.batch_size:
            return await self._process_batch()
        
        else:
            await asyncio.sleep(self.batch_timeout)
            return await self._process_batch()
    
    async def _process_batch(self) -> List[str]:
        """Process batched requests"""
        
        if not self.request_batch:
            return []
        
        # Extract prompts
        prompts = [req[0] for req in self.request_batch]
        
        # Batch inference (pseudocode)
        # responses = await m2_client.batch_generate(prompts)
        
        # Clear batch
        self.request_batch = []
        
        return responses  # type: ignore
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/unit/test_m2_orchestrator.py`

```python
"""
Unit tests for M2 Orchestrator.
"""

import pytest
from omics_oracle_v2.agents.m2_orchestrator import (
    MiniMaxM2Orchestrator,
    M2AgentConfig,
    M2Message,
    AgentRole
)

@pytest.fixture
async def orchestrator():
    """Create test orchestrator"""
    config = M2AgentConfig(
        inference_url="http://localhost:8080/v1/chat/completions"
    )
    orch = MiniMaxM2Orchestrator(config)
    await orch.initialize()
    yield orch
    await orch.close()

@pytest.mark.asyncio
async def test_code_extraction_from_markdown(orchestrator):
    """Test extracting code from markdown response"""
    
    markdown = """
Here's the code:

```python
import pandas as pd

def analyze():
    return "result"
```

That should work!
"""
    
    code = orchestrator._extract_code_from_markdown(markdown)
    
    assert "import pandas as pd" in code
    assert "def analyze():" in code
    assert "That should work!" not in code

@pytest.mark.asyncio
async def test_system_prompt_selection(orchestrator):
    """Test correct system prompts for different roles"""
    
    prompt_gen = orchestrator._get_system_prompt(AgentRole.CODE_GENERATOR)
    prompt_debug = orchestrator._get_system_prompt(AgentRole.DEBUGGER)
    
    assert "bioinformatics programmer" in prompt_gen.lower()
    assert "debugging" in prompt_debug.lower()
    assert prompt_gen != prompt_debug
```

**File:** `tests/unit/test_code_safety_validator.py`

```python
"""
Unit tests for Code Safety Validator.
"""

import pytest
from omics_oracle_v2.agents.code_safety_validator import (
    CodeSafetyValidator,
    RiskLevel
)

def test_detect_dangerous_import():
    """Test detection of dangerous imports"""
    
    code = """
import os
import pandas as pd

os.system("ls -la")
"""
    
    validator = CodeSafetyValidator()
    is_safe, issues = validator.validate(code)
    
    assert not is_safe
    assert len(issues) > 0
    assert any(i.level == RiskLevel.CRITICAL for i in issues)
    assert any("os.system" in i.description for i in issues)

def test_allow_safe_imports():
    """Test allowing safe bioinformatics imports"""
    
    code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

df = pd.read_csv('data.csv')
"""
    
    validator = CodeSafetyValidator()
    is_safe, issues = validator.validate(code)
    
    # Should have no critical/high issues
    critical_issues = [
        i for i in issues
        if i.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
    ]
    
    assert len(critical_issues) == 0

def test_detect_eval_exec():
    """Test detection of eval/exec"""
    
    code = """
user_input = "malicious code"
eval(user_input)
"""
    
    validator = CodeSafetyValidator()
    is_safe, issues = validator.validate(code)
    
    assert not is_safe
    assert any("eval" in i.description for i in issues)

def test_detect_file_access_outside_workspace():
    """Test detection of file access outside /workspace"""
    
    code = """
with open('/etc/passwd', 'r') as f:
    data = f.read()
"""
    
    validator = CodeSafetyValidator()
    is_safe, issues = validator.validate(code)
    
    assert not is_safe
    assert any("/etc/passwd" in i.description for i in issues)
```

### Integration Tests

**File:** `tests/integration/test_end_to_end_analysis.py`

```python
"""
Integration tests for end-to-end analysis pipeline.
"""

import pytest
import asyncio
from uuid import UUID

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_analysis_workflow():
    """
    Test complete workflow from API request to results.
    
    Steps:
    1. Submit analysis request
    2. Poll for status
    3. Verify completion
    4. Check results
    """
    
    from omics_oracle_v2.api.routes.agent_analysis import (
        start_agent_analysis,
        get_analysis_status,
        get_analysis_results
    )
    
    # Step 1: Submit request
    request = {
        "geo_id": "GSE239603",
        "analysis_type": "differential_expression",
        "query": "Compare APOE4 vs control",
        "parameters": {
            "padj_threshold": 0.05,
            "log2fc_threshold": 1.0
        }
    }
    
    response = await start_agent_analysis(request)
    analysis_id = response.analysis_id
    
    assert isinstance(analysis_id, UUID)
    
    # Step 2: Poll for completion (with timeout)
    max_wait = 300  # 5 minutes
    poll_interval = 5
    elapsed = 0
    
    while elapsed < max_wait:
        status = await get_analysis_status(analysis_id)
        
        if status.status == "completed":
            break
        elif status.status == "failed":
            pytest.fail(f"Analysis failed: {status.error_message}")
        
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    
    assert status.status == "completed", "Analysis did not complete in time"
    
    # Step 3: Get results
    results = await get_analysis_results(analysis_id)
    
    # Verify results structure
    assert results.geo_id == "GSE239603"
    assert results.summary is not None
    assert "total_genes" in results.summary
    assert len(results.plots) > 0
    assert "volcano" in results.plots
    assert len(results.code) > 0

@pytest.mark.integration
async def test_error_recovery():
    """
    Test automatic error recovery.
    
    Inject an error and verify M2 can debug and fix it.
    """
    
    from omics_oracle_v2.agents.error_recovery import ErrorRecoveryAgent, DebugContext
    
    # Deliberately broken code
    broken_code = """
import pandas as pd

# Typo in function name
df = pd.read_csv("data.csv")
result = df.groupby("condition").meann()  # 'meann' should be 'mean'
"""
    
    # Simulate execution error
    error_traceback = """
Traceback (most recent call last):
  File "pipeline.py", line 5, in <module>
    result = df.groupby("condition").meann()
AttributeError: 'DataFrameGroupBy' object has no attribute 'meann'
"""
    
    context = DebugContext(
        original_code=broken_code,
        error_traceback=error_traceback,
        stdout="",
        stderr=error_traceback,
        attempt_number=0,
        previous_fixes=[]
    )
    
    # Test error recovery
    recovery_agent = ErrorRecoveryAgent(m2_orchestrator)
    success, fixed_code, explanation = await recovery_agent.debug_and_fix(context)
    
    assert success
    assert fixed_code is not None
    assert ".mean()" in fixed_code
    assert "meann" not in fixed_code
```

### Load Testing

**File:** `tests/load/test_concurrent_analyses.py`

```python
"""
Load tests for concurrent analysis execution.
"""

import pytest
import asyncio
from typing import List

@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_analyses():
    """
    Test system under load with multiple concurrent analyses.
    
    Target: 10 concurrent analyses without degradation
    """
    
    async def submit_analysis(geo_id: str) -> dict:
        """Submit single analysis"""
        # Implementation here
        pass
    
    # Submit 10 concurrent analyses
    geo_ids = [f"GSE{100000 + i}" for i in range(10)]
    
    tasks = [submit_analysis(geo_id) for geo_id in geo_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check success rate
    successful = [r for r in results if not isinstance(r, Exception)]
    success_rate = len(successful) / len(results)
    
    assert success_rate >= 0.9, f"Success rate {success_rate} below threshold"

@pytest.mark.load
async def test_gpu_utilization():
    """
    Test GPU utilization under load.
    
    Target: >80% GPU utilization with 4+ concurrent requests
    """
    
    # Monitor GPU usage during concurrent analyses
    # Verify efficient batching and resource usage
    pass
```

---

## Deployment Architecture

### Kubernetes Deployment

**File:** `k8s/m2-inference-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minimax-m2-inference
  namespace: omicsoracle
spec:
  replicas: 1  # Single replica for 4× H100
  selector:
    matchLabels:
      app: m2-inference
  template:
    metadata:
      labels:
        app: m2-inference
    spec:
      # GPU node selector
      nodeSelector:
        gpu-type: h100
        gpu-count: "4"
      
      # Tolerations for GPU nodes
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      
      containers:
      - name: m2-server
        image: omicsoracle/minimax-m2:latest
        
        # Resource requests/limits
        resources:
          requests:
            nvidia.com/gpu: 4
            memory: "256Gi"
            cpu: "48"
          limits:
            nvidia.com/gpu: 4
            memory: "512Gi"
            cpu: "96"
        
        # Environment variables
        env:
        - name: MODEL_PATH
          value: "/models/MiniMax-M2"
        - name: TENSOR_PARALLEL_SIZE
          value: "4"
        - name: DTYPE
          value: "fp8"
        - name: MAX_MODEL_LEN
          value: "128000"
        
        # Ports
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        
        # Volume mounts
        volumeMounts:
        - name: model-cache
          mountPath: /models
        
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 120
          periodSeconds: 30
        
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
      
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: model-cache-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: m2-inference-service
  namespace: omicsoracle
spec:
  selector:
    app: m2-inference
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
```

**File:** `k8s/analysis-worker-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analysis-workers
  namespace: omicsoracle
spec:
  replicas: 4  # 4 worker pods
  selector:
    matchLabels:
      app: analysis-worker
  template:
    metadata:
      labels:
        app: analysis-worker
    spec:
      containers:
      - name: worker
        image: omicsoracle/analysis-worker:latest
        
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
          limits:
            memory: "32Gi"
            cpu: "8"
        
        env:
        - name: M2_INFERENCE_URL
          value: "http://m2-inference-service:8080"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: postgres-url
        - name: MAX_CONCURRENT_JOBS
          value: "2"
        
        # Docker-in-Docker for sandbox execution
        volumeMounts:
        - name: docker-sock
          mountPath: /var/run/docker.sock
        - name: workspace
          mountPath: /workspace
      
      volumes:
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
      - name: workspace
        emptyDir:
          sizeLimit: 200Gi
```

### Docker Compose (Development)

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # MiniMax-M2 Inference Server
  m2-inference:
    image: omicsoracle/minimax-m2:latest
    container_name: m2-inference
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0,1,2,3
      - MODEL_PATH=/models/MiniMax-M2
      - TENSOR_PARALLEL_SIZE=4
      - DTYPE=fp8
    volumes:
      - ./models:/models
    ports:
      - "8080:8080"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 4
              capabilities: [gpu]
  
  # Analysis Worker
  analysis-worker:
    image: omicsoracle/analysis-worker:latest
    container_name: analysis-worker
    depends_on:
      - m2-inference
      - redis
      - postgres
    environment:
      - M2_INFERENCE_URL=http://m2-inference:8080
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/omics
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./workspace:/workspace
  
  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
  
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    environment:
      - POSTGRES_USER=omics
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=omicsoracle
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  # FastAPI Backend
  api-server:
    image: omicsoracle/api:latest
    container_name: api-server
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://omics:secure_password@postgres:5432/omicsoracle
      - REDIS_URL=redis://redis:6379
      - M2_WORKER_URL=http://analysis-worker:8000
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data

volumes:
  redis-data:
  postgres-data:
  model-cache:
```

### Monitoring & Observability

**File:** `monitoring/prometheus-config.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  # M2 Inference Metrics
  - job_name: 'm2-inference'
    static_configs:
      - targets: ['m2-inference:8080']
    metrics_path: /metrics
  
  # Analysis Worker Metrics
  - job_name: 'analysis-workers'
    static_configs:
      - targets: ['analysis-worker:9090']
  
  # GPU Metrics
  - job_name: 'nvidia-dcgm'
    static_configs:
      - targets: ['dcgm-exporter:9400']

  # Node Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

**File:** `monitoring/grafana-dashboard.json`

```json
{
  "dashboard": {
    "title": "OmicsOracle M2 Analysis",
    "panels": [
      {
        "title": "Analysis Throughput",
        "targets": [
          {
            "expr": "rate(analysis_completed_total[5m])"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "DCGM_FI_DEV_GPU_UTIL"
          }
        ]
      },
      {
        "title": "M2 Inference Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(m2_inference_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Analyses",
        "targets": [
          {
            "expr": "analysis_active_jobs"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(analysis_errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## Cost Analysis

### Hardware Costs (On-Premise)

**Initial Investment:**

| Component | Specification | Quantity | Unit Cost | Total |
|-----------|--------------|----------|-----------|-------|
| **GPU** | NVIDIA H100 SXM 80GB | 4 | $25,000 | $100,000 |
| **Server** | Dual EPYC 9654, 512GB RAM | 1 | $15,000 | $15,000 |
| **Storage** | 10TB NVMe SSD | 1 | $3,000 | $3,000 |
| **Networking** | 100Gbps NIC, Switch | 1 | $5,000 | $5,000 |
| **Cooling** | Liquid cooling system | 1 | $8,000 | $8,000 |
| **Rack & Power** | 42U rack, PDU, UPS | 1 | $10,000 | $10,000 |
| **Installation** | Setup, cabling, testing | 1 | $5,000 | $5,000 |
| **Total Initial** | | | | **$146,000** |

**Annual Operating Costs:**

| Item | Calculation | Annual Cost |
|------|------------|-------------|
| **Electricity** | 3.5 kW × 24h × 365d × $0.12/kWh | $3,679 |
| **Cooling** | 1.2× power cost | $4,415 |
| **Maintenance** | 5% of hardware cost | $7,300 |
| **Network** | Dedicated 10Gbps line | $12,000 |
| **Staff Time** | 20% FTE DevOps ($150k salary) | $30,000 |
| **Total Annual** | | **$57,394** |

**5-Year Total Cost of Ownership:** $146,000 + ($57,394 × 5) = **$432,970**

### Cloud Costs (AWS)

**Compute (p5.48xlarge - 8× H100):**
- On-Demand: $98.32/hour = $2,360/day = $70,800/month = **$849,600/year**
- Spot: ~$30-50/hour = $900/day = $27,000/month = **$324,000/year** (65% savings)

**Storage (S3 + EBS):**
- Results Storage: 10TB × $0.023/GB/month = $230/month = **$2,760/year**
- EBS Volumes: 5TB × $0.08/GB/month = $400/month = **$4,800/year**

**Data Transfer:**
- Genomics data downloads: ~5TB/month × $0.09/GB = $450/month = **$5,400/year**

**Total Cloud Annual Cost (On-Demand):** **$862,560**  
**Total Cloud Annual Cost (Spot):** **$336,960**

### Cost Comparison

| Deployment | Year 1 | Year 2 | Year 3 | Year 5 |
|------------|--------|--------|--------|--------|
| **On-Premise** | $203,394 | $260,788 | $318,182 | $432,970 |
| **Cloud (On-Demand)** | $862,560 | $1,725,120 | $2,587,680 | $4,312,800 |
| **Cloud (Spot)** | $336,960 | $673,920 | $1,010,880 | $1,684,800 |

**Break-Even Analysis:**
- vs On-Demand: **2.8 months**
- vs Spot Instances: **7.3 months**

**Recommendation:** On-premise deployment for >6 months continuous usage

### ROI Analysis

**Value Generated per Analysis:**

Assuming M2 enables automated analysis that would otherwise require:
- 4 hours of bioinformatician time ($75/hour) = $300
- Or eliminates need for $100 GPT-4 API costs

**Usage Scenarios:**

| Usage | Analyses/Month | Value/Month | Annual Value |
|-------|----------------|-------------|--------------|
| **Light** (Academic Lab) | 50 | $15,000 | $180,000 |
| **Medium** (Core Facility) | 200 | $60,000 | $720,000 |
| **Heavy** (Biotech Company) | 1000 | $300,000 | $3,600,000 |

**Payback Period:**

- **Light Usage:** $146,000 / $15,000 = **9.7 months**
- **Medium Usage:** $146,000 / $60,000 = **2.4 months**
- **Heavy Usage:** $146,000 / $300,000 = **0.5 months** (2 weeks!)

**5-Year ROI:**

- **Light:** ($180,000 × 5) - $432,970 = **$467,030** (108% ROI)
- **Medium:** ($720,000 × 5) - $432,970 = **$3,167,030** (732% ROI)
- **Heavy:** ($3,600,000 × 5) - $432,970 = **$17,567,030** (4058% ROI)

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Objectives:**
- Set up infrastructure
- Implement basic M2 integration
- Create minimal viable pipeline

**Tasks:**

| Week | Task | Deliverable |
|------|------|-------------|
| **Week 1** | Hardware procurement & setup | 4× H100 server operational |
| | Install base software stack | CUDA, Docker, K8s ready |
| | Deploy M2 inference server | SGLang serving M2 at 8080 |
| **Week 2** | Implement M2 Orchestrator | `m2_orchestrator.py` complete |
| | Build API endpoints | `/api/v3/agent/*` endpoints |
| | Set up database schema | PostgreSQL tables created |
| **Week 3** | Implement Code Safety Validator | AST-based validation working |
| | Create Docker sandbox | Secure execution environment |
| | Build basic data discovery | FTP/GEO scraping functional |
| **Week 4** | Integration testing | End-to-end pipeline works |
| | Performance benchmarking | Latency & throughput metrics |
| | Documentation | API docs, deployment guide |

**Success Criteria:**
- ✅ M2 responding to API calls with <2s latency
- ✅ Complete analysis for simple dataset (GSE239603)
- ✅ Code validation catching dangerous patterns
- ✅ Docker sandbox executing code safely

### Phase 2: Enhancement (Weeks 5-8)

**Objectives:**
- Add error recovery
- Implement caching
- Improve code generation quality

**Tasks:**

| Week | Task | Deliverable |
|------|------|-------------|
| **Week 5** | Implement Error Recovery Agent | Automatic debugging loop |
| | Add retry logic | 3-attempt retry with fixes |
| | Improve prompts | Fine-tuned prompts for M2 |
| **Week 6** | Add Redis caching | Analysis result caching |
| | Implement code cache | Reuse successful patterns |
| | Optimize M2 inference | Batching, KV cache reuse |
| **Week 7** | Add more analysis types | GO enrichment, clustering |
| | Enhance visualizations | Interactive plots, heatmaps |
| | Improve report generation | Scientific writing quality |
| **Week 8** | Comprehensive testing | 100+ test datasets |
| | Load testing | 10 concurrent analyses |
| | Bug fixes & polish | Address all critical issues |

**Success Criteria:**
- ✅ 90%+ success rate on diverse datasets
- ✅ Error recovery fixes 80% of failures
- ✅ Cache hit rate >40% for common analyses
- ✅ Handle 10 concurrent analyses

### Phase 3: Production (Weeks 9-12)

**Objectives:**
- Production hardening
- Monitoring & alerting
- User documentation

**Tasks:**

| Week | Task | Deliverable |
|------|------|-------------|
| **Week 9** | Set up monitoring | Prometheus + Grafana |
| | Implement logging | Structured logs, tracing |
| | Add alerting | PagerDuty integration |
| **Week 10** | Security audit | Penetration testing |
| | Performance tuning | Optimize bottlenecks |
| | Scalability testing | 50+ concurrent analyses |
| **Week 11** | User documentation | Tutorials, examples |
| | API documentation | OpenAPI spec, Postman |
| | Admin documentation | Deployment, maintenance |
| **Week 12** | Beta testing | 10 external users |
| | Feedback iteration | Address user feedback |
| | Launch preparation | Marketing, announcements |

**Success Criteria:**
- ✅ 99.5% uptime over 1 week
- ✅ No critical security vulnerabilities
- ✅ Complete documentation
- ✅ Positive beta user feedback

### Phase 4: Scale & Optimization (Months 4-6)

**Objectives:**
- Scale to 100+ concurrent users
- Add advanced features
- Cost optimization

**Tasks:**

| Month | Focus Area | Deliverables |
|-------|-----------|--------------|
| **Month 4** | Horizontal Scaling | Multi-GPU cluster (8× H100) |
| | Load balancing | Smart request routing |
| | Auto-scaling | Dynamic resource allocation |
| **Month 5** | Advanced Features | Custom analysis workflows |
| | R integration | DESeq2, limma support |
| | Single-cell analysis | Scanpy, Seurat integration |
| **Month 6** | Cost Optimization | Spot instance usage |
| | Model optimization | INT4 quantization trials |
| | Efficiency improvements | Reduce compute per analysis |

**Success Criteria:**
- ✅ Support 100+ concurrent analyses
- ✅ <30s average analysis time
- ✅ 50% cost reduction through optimization
- ✅ Advanced analysis types working

### Milestones & Metrics

**Month 1 (MVP):**
- Analyses completed: 10
- Success rate: 70%
- Avg time: 120s

**Month 3 (Production):**
- Analyses completed: 500
- Success rate: 90%
- Avg time: 60s
- Concurrent capacity: 10

**Month 6 (Scale):**
- Analyses completed: 5,000
- Success rate: 95%
- Avg time: 30s
- Concurrent capacity: 100

**Month 12 (Mature):**
- Analyses completed: 50,000
- Success rate: 98%
- Avg time: 20s
- Concurrent capacity: 200

---

## Appendices

### Appendix A: Complete Code Example

**Generated Pipeline for GSE239603 Differential Expression**

```python
#!/usr/bin/env python3
"""
Automated Analysis Pipeline for GSE239603
Generated by MiniMax-M2 Agent

Dataset: APOE4 vs Control Microglia RNA-seq
Platform: Illumina NovaSeq 6000
Analysis: Differential Expression
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection
import ftplib
import gzip
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Analysis parameters
GEO_ID = "GSE239603"
FTP_SERVER = "ftp.ncbi.nlm.nih.gov"
DATA_URL = f"/geo/series/GSE239nnn/{GEO_ID}/suppl/{GEO_ID}_counts.txt.gz"
PADJ_THRESHOLD = 0.05
LOG2FC_THRESHOLD = 1.0
TOP_GENES = 50

def download_data(output_file="counts.txt.gz"):
    """Download count matrix from GEO FTP"""
    logger.info(f"Downloading data from {FTP_SERVER}...")
    
    try:
        ftp = ftplib.FTP(FTP_SERVER)
        ftp.login()
        
        with open(output_file, 'wb') as f:
            ftp.retrbinary(f'RETR {DATA_URL}', f.write)
        
        ftp.quit()
        logger.info(f"Download complete: {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def load_and_preprocess(counts_file):
    """Load and preprocess count matrix"""
    logger.info("Loading count matrix...")
    
    # Decompress if needed
    if counts_file.endswith('.gz'):
        with gzip.open(counts_file, 'rb') as f_in:
            with open('counts.txt', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        counts_file = 'counts.txt'
    
    # Load data
    df = pd.read_csv(counts_file, sep='\t', index_col=0)
    logger.info(f"Loaded {df.shape[0]} genes × {df.shape[1]} samples")
    
    # Extract sample metadata from column names
    conditions = []
    for col in df.columns:
        if 'APOE4' in col or 'apoe4' in col.lower():
            conditions.append('APOE4')
        else:
            conditions.append('Control')
    
    metadata = pd.DataFrame({
        'sample': df.columns,
        'condition': conditions
    })
    
    logger.info(f"Conditions: {metadata['condition'].value_counts().to_dict()}")
    
    # Filter low-count genes (at least 10 reads in 3+ samples)
    keep = (df >= 10).sum(axis=1) >= 3
    df_filtered = df[keep]
    logger.info(f"Retained {df_filtered.shape[0]} genes after filtering")
    
    return df_filtered, metadata

def normalize_counts(df):
    """TPM normalization"""
    logger.info("Normalizing counts (TPM)...")
    
    # Calculate size factors (total counts per sample)
    size_factors = df.sum(axis=0) / 1e6
    
    # Normalize
    df_norm = df.div(size_factors, axis=1)
    
    return df_norm

def differential_expression(df, metadata):
    """Perform differential expression analysis"""
    logger.info("Running differential expression analysis...")
    
    # Split by condition
    apoe4_samples = metadata[metadata['condition'] == 'APOE4']['sample']
    control_samples = metadata[metadata['condition'] == 'Control']['sample']
    
    apoe4_data = df[apoe4_samples]
    control_data = df[control_samples]
    
    # Calculate statistics for each gene
    results = []
    
    for gene in df.index:
        apoe4_vals = apoe4_data.loc[gene].values
        control_vals = control_data.loc[gene].values
        
        # Skip if all zeros
        if (apoe4_vals == 0).all() or (control_vals == 0).all():
            continue
        
        # Calculate fold change (add pseudocount)
        apoe4_mean = np.mean(apoe4_vals) + 1
        control_mean = np.mean(control_vals) + 1
        fold_change = apoe4_mean / control_mean
        log2fc = np.log2(fold_change)
        
        # T-test
        t_stat, pvalue = stats.ttest_ind(apoe4_vals, control_vals)
        
        results.append({
            'gene': gene,
            'baseMean': np.mean([apoe4_mean, control_mean]),
            'log2FoldChange': log2fc,
            'pvalue': pvalue,
            'APOE4_mean': apoe4_mean - 1,
            'Control_mean': control_mean - 1
        })
    
    # Create results dataframe
    res_df = pd.DataFrame(results)
    
    # Multiple testing correction
    _, padj = fdrcorrection(res_df['pvalue'])
    res_df['padj'] = padj
    
    # Sort by adjusted p-value
    res_df = res_df.sort_values('padj')
    
    logger.info(f"Analyzed {len(res_df)} genes")
    
    # Filter significant genes
    sig = res_df[
        (res_df['padj'] < PADJ_THRESHOLD) &
        (np.abs(res_df['log2FoldChange']) > LOG2FC_THRESHOLD)
    ]
    
    logger.info(f"Found {len(sig)} differentially expressed genes")
    logger.info(f"  Upregulated: {(sig['log2FoldChange'] > 0).sum()}")
    logger.info(f"  Downregulated: {(sig['log2FoldChange'] < 0).sum()}")
    
    return res_df, sig

def plot_volcano(res_df, output='volcano_plot.png'):
    """Generate volcano plot"""
    logger.info("Generating volcano plot...")
    
    plt.figure(figsize=(12, 9))
    
    # Prepare data
    x = res_df['log2FoldChange']
    y = -np.log10(res_df['padj'].replace(0, 1e-300))
    
    # Color by significance
    colors = []
    for _, row in res_df.iterrows():
        if row['padj'] < PADJ_THRESHOLD and abs(row['log2FoldChange']) > LOG2FC_THRESHOLD:
            if row['log2FoldChange'] > 0:
                colors.append('red')
            else:
                colors.append('blue')
        else:
            colors.append('gray')
    
    # Scatter plot
    plt.scatter(x, y, c=colors, alpha=0.5, s=10)
    
    # Add threshold lines
    plt.axhline(-np.log10(PADJ_THRESHOLD), color='black', linestyle='--', alpha=0.5)
    plt.axvline(LOG2FC_THRESHOLD, color='black', linestyle='--', alpha=0.5)
    plt.axvline(-LOG2FC_THRESHOLD, color='black', linestyle='--', alpha=0.5)
    
    # Labels
    plt.xlabel('log2 Fold Change', fontsize=14)
    plt.ylabel('-log10 Adjusted P-value', fontsize=14)
    plt.title(f'{GEO_ID}: APOE4 vs Control', fontsize=16)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Upregulated'),
        Patch(facecolor='blue', label='Downregulated'),
        Patch(facecolor='gray', label='Not significant')
    ]
    plt.legend(handles=legend_elements)
    
    plt.tight_layout()
    plt.savefig(output, dpi=300)
    logger.info(f"Volcano plot saved: {output}")

def plot_heatmap(df, sig, metadata, output='heatmap_top50.png'):
    """Generate heatmap of top genes"""
    logger.info("Generating heatmap...")
    
    # Get top genes
    top_genes = sig.head(TOP_GENES)['gene'].tolist()
    df_top = df.loc[top_genes]
    
    # Z-score normalize
    df_zscore = df_top.apply(lambda x: (x - x.mean()) / x.std(), axis=1)
    
    # Create column colors
    col_colors = metadata.set_index('sample')['condition'].map({
        'APOE4': 'red',
        'Control': 'blue'
    })
    
    # Plot
    g = sns.clustermap(
        df_zscore,
        cmap='RdBu_r',
        center=0,
        col_colors=col_colors,
        figsize=(15, 20),
        cbar_kws={'label': 'Z-score'},
        yticklabels=True
    )
    
    g.fig.suptitle(f'Top {TOP_GENES} Differentially Expressed Genes', y=0.98)
    plt.savefig(output, dpi=300, bbox_inches='tight')
    logger.info(f"Heatmap saved: {output}")

def plot_pca(df, metadata, output='pca_samples.png'):
    """Generate PCA plot"""
    logger.info("Generating PCA plot...")
    
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    
    # Transpose (samples as rows)
    df_t = df.T
    
    # Standardize
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_t)
    
    # PCA
    pca = PCA(n_components=2)
    pcs = pca.fit_transform(df_scaled)
    
    # Plot
    plt.figure(figsize=(10, 8))
    
    for condition in metadata['condition'].unique():
        mask = metadata['condition'] == condition
        plt.scatter(
            pcs[mask, 0],
            pcs[mask, 1],
            label=condition,
            s=100,
            alpha=0.7
        )
    
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', fontsize=12)
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', fontsize=12)
    plt.title('PCA: Sample Clustering', fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=300)
    logger.info(f"PCA plot saved: {output}")

def save_results(res_df, sig, output='deg_results.csv'):
    """Save results to CSV"""
    logger.info("Saving results...")
    
    res_df.to_csv(output, index=False)
    sig.to_csv('significant_genes.csv', index=False)
    
    logger.info(f"Results saved: {output}")

def generate_summary(res_df, sig):
    """Generate analysis summary"""
    summary = f"""
# Analysis Summary: {GEO_ID}

## Parameters
- Adjusted p-value threshold: {PADJ_THRESHOLD}
- log2 Fold Change threshold: {LOG2FC_THRESHOLD}

## Results
- Total genes analyzed: {len(res_df)}
- Significant genes: {len(sig)}
- Upregulated (APOE4 > Control): {(sig['log2FoldChange'] > 0).sum()}
- Downregulated (APOE4 < Control): {(sig['log2FoldChange'] < 0).sum()}

## Top 10 Upregulated Genes
{sig[sig['log2FoldChange'] > 0].head(10)[['gene', 'log2FoldChange', 'padj']].to_string(index=False)}

## Top 10 Downregulated Genes
{sig[sig['log2FoldChange'] < 0].head(10)[['gene', 'log2FoldChange', 'padj']].to_string(index=False)}
"""
    
    with open('analysis_summary.txt', 'w') as f:
        f.write(summary)
    
    logger.info("Summary saved: analysis_summary.txt")
    print(summary)

def main():
    """Main analysis pipeline"""
    logger.info(f"Starting analysis for {GEO_ID}")
    
    # Download data
    counts_file = download_data()
    
    # Load and preprocess
    df, metadata = load_and_preprocess(counts_file)
    
    # Normalize
    df_norm = normalize_counts(df)
    
    # Differential expression
    res_df, sig = differential_expression(df_norm, metadata)
    
    # Visualizations
    plot_volcano(res_df)
    plot_heatmap(df_norm, sig, metadata)
    plot_pca(df_norm, metadata)
    
    # Save results
    save_results(res_df, sig)
    
    # Generate summary
    generate_summary(res_df, sig)
    
    logger.info("Analysis complete!")

if __name__ == "__main__":
    main()
```

### Appendix B: Database Schema

```sql
-- Analysis Jobs Table
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    geo_id VARCHAR(20) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    query TEXT NOT NULL,
    parameters JSONB,
    
    status VARCHAR(20) NOT NULL,
    progress_percent INTEGER DEFAULT 0,
    current_step TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    execution_time_seconds FLOAT,
    error_message TEXT,
    
    code_s3_path TEXT,
    results_s3_path TEXT,
    
    INDEX idx_user_id (user_id),
    INDEX idx_geo_id (geo_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Differential Expression Results
CREATE TABLE differential_expression_results (
    id BIGSERIAL PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    
    gene_id VARCHAR(50),
    gene_name VARCHAR(100),
    log2_fold_change FLOAT,
    pvalue DOUBLE PRECISION,
    adjusted_pvalue DOUBLE PRECISION,
    base_mean FLOAT,
    
    INDEX idx_analysis_id (analysis_id),
    INDEX idx_gene_name (gene_name),
    INDEX idx_padj (adjusted_pvalue)
);

-- Code Cache
CREATE TABLE code_cache (
    id SERIAL PRIMARY KEY,
    geo_id VARCHAR(20),
    platform VARCHAR(100),
    data_type VARCHAR(50),
    analysis_type VARCHAR(50),
    
    code TEXT NOT NULL,
    parameters JSONB,
    success_rate FLOAT DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(geo_id, analysis_type)
);

-- Analysis Metrics
CREATE TABLE analysis_metrics (
    id BIGSERIAL PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id),
    
    metric_name VARCHAR(100),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_analysis_id (analysis_id),
    INDEX idx_metric_name (metric_name)
);
```

### Appendix C: Configuration Files

**File:** `config/m2_config.yaml`

```yaml
# MiniMax-M2 Configuration

inference:
  url: "http://localhost:8080/v1/chat/completions"
  model: "MiniMaxAI/MiniMax-M2"
  timeout_seconds: 300
  retry_attempts: 3

generation:
  temperature: 1.0
  top_p: 0.95
  top_k: 40
  max_tokens: 8192

sandbox:
  base_image: "omicsoracle/bioinformatics-base:latest"
  cpu_cores: 8
  memory_mb: 32000
  disk_mb: 102400
  timeout_seconds: 1800
  remove_on_exit: true

security:
  allowed_domains:
    - "ftp.ncbi.nlm.nih.gov"
    - "www.ncbi.nlm.nih.gov"
    - "pypi.org"
    - "files.pythonhosted.org"
  
  max_file_size_mb: 5000
  max_output_files: 100

caching:
  redis_url: "redis://localhost:6379"
  analysis_ttl_days: 30
  code_ttl_days: 90

database:
  url: "postgresql://user:pass@localhost:5432/omics"
  pool_size: 20
  max_overflow: 10

storage:
  type: "s3"  # or "local"
  s3_bucket: "omicsoracle-results"
  s3_region: "us-east-1"
  local_path: "/data/results"
```

---

## Conclusion

This technical specification provides a complete blueprint for integrating MiniMax-M2 as an autonomous coding agent within OmicsOracle. The system enables fully automated genomics data analysis from GEO accession to publication-ready results.

**Key Takeaways:**

1. **Architecture**: Multi-layer security, Docker isolation, agent orchestration
2. **Infrastructure**: 4× H100 GPUs, on-premise deployment, <2s latency
3. **Cost**: $146k initial, 2-10 month payback depending on usage
4. **Timeline**: 12 weeks to production, 6 months to scale
5. **ROI**: 108-4058% over 5 years depending on usage level

**Next Steps:**

1. Secure hardware procurement approval
2. Begin Phase 1 implementation (Week 1)
3. Recruit DevOps engineer for deployment
4. Identify beta testing partners

**Document Version:** 1.0  
**Last Updated:** November 1, 2025  
**Total Pages:** ~75 equivalent pages  
**Word Count:** ~15,000 words