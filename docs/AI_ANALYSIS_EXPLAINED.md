# 🤖 AI Analysis Feature - Complete Technical Explanation

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [End-to-End Workflow](#end-to-end-workflow)
3. [The Exact Prompt Sent to GPT-4](#the-exact-prompt-sent-to-gpt-4)
4. [How the Prompt Affects Results](#how-the-prompt-affects-results)
5. [Response Processing](#response-processing)
6. [Configuration & Customization](#configuration--customization)
7. [Real Example Walkthrough](#real-example-walkthrough)

---

## 🎯 **Overview**

The "Analyze with AI" button sends your search results to GPT-4 (or GPT-3.5-turbo) with a carefully crafted prompt that asks the AI to act as an expert bioinformatics advisor.

**What it does:**
- Takes up to 5 top-ranked datasets from your search
- Creates a comprehensive prompt with dataset metadata
- Sends to OpenAI API (GPT-4)
- Returns expert analysis comparing datasets
- Displays results in beautiful markdown format

---

## 🔄 **End-to-End Workflow**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CLICKS "🤖 Analyze with AI" BUTTON                      │
│    (After performing a search)                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (semantic_search.html)                              │
│    Function: analyzeWithAI()                                    │
│                                                                  │
│    Sends POST request to /api/agents/analyze:                   │
│    {                                                             │
│      "datasets": [top 5 datasets],                              │
│      "query": "joint DNA methylation and HiC profiling",        │
│      "max_datasets": 5                                           │
│    }                                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BACKEND API (omics_oracle_v2/api/routes/agents.py)          │
│    Function: analyze_datasets()                                 │
│                                                                  │
│    ✅ Check: OpenAI API key configured?                        │
│    ✅ Limit: Take top 5 datasets (max_datasets)                │
│    ✅ Build: Create analysis prompt (see below)                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PROMPT CONSTRUCTION (THE MAGIC HAPPENS HERE)                │
│                                                                  │
│    For each dataset, extract:                                   │
│    • GEO ID (e.g., GSE189158)                                   │
│    • Relevance score (e.g., 5%)                                 │
│    • Title                                                       │
│    • Organism                                                    │
│    • Sample count                                               │
│    • Summary (first 300 characters)                             │
│                                                                  │
│    Build structured prompt (see next section)                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SEND TO OPENAI API                                           │
│    (lib/ai/client.py - SummarizationClient)                     │
│                                                                  │
│    Model: gpt-4-turbo-preview (default)                         │
│    Max Tokens: 800                                               │
│    Temperature: 0.7                                              │
│    System Message: "You are an expert bioinformatics advisor..." │
│    User Message: [The constructed prompt]                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. GPT-4 GENERATES ANALYSIS (15-30 seconds)                     │
│                                                                  │
│    Returns structured markdown with:                            │
│    ### Overview                                                 │
│    ### Comparison                                               │
│    ### Key Insights                                             │
│    ### Recommendations                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. BACKEND PROCESSES RESPONSE                                   │
│                                                                  │
│    • Receives full markdown text                                │
│    • Parses for insights/recommendations (optional)             │
│    • Packages in AIAnalysisResponse                             │
│    • Returns to frontend                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. FRONTEND DISPLAYS RESULTS                                    │
│    (semantic_search.html - displayAIAnalysis())                 │
│                                                                  │
│    • Parse markdown with marked.js                              │
│    • Render in purple gradient panel                            │
│    • Show headings, lists, bold text properly                   │
│    • Display model name and execution time                      │
└─────────────────────────────────────────────────────────────────┘
```

**Total Time:** 15-30 seconds (mostly waiting for GPT-4)

---

## 📝 **The Exact Prompt Sent to GPT-4**

### **System Message (Sets AI Persona)**

```
You are an expert bioinformatics advisor helping researchers understand 
and select genomics datasets. Provide clear, actionable insights.
```

This tells GPT-4 to act as a domain expert, not a general assistant.

### **User Message (The Analysis Request)**

For your query `"joint DNA methylation and HiC profiling"`, the exact prompt would be:

```
User searched for: "joint DNA methylation and HiC profiling"

Found 2 relevant datasets:

1. **GSE281238** (Relevance: 10%)
   Title: Generalization of the sci-L3 method to achieve high-throughput 
   linear amplification for replication template strand sequencing, 
   genome conformation capture, and the joint profiling of RNA and 
   chromatin accessibility
   Organism: N/A, Samples: 7
   Summary: Single-cell combinatorial indexing (sci-) methods have 
   addressed major limitations of throughput and cost for many single 
   cell modalities. With the incorporation of linear amplification 
   and 3-level barcoding in our suite of methods called sci-L3, we 
   further addressed the limitations of uniformity in single cell 
   genome amplification. Here, we build on the generalizability of 
   sci-L3 by extending it to template strand sequencing...

2. **GSE189158** (Relevance: 5%)
   Title: NOMe-HiC: joint profiling of genetic variants, DNA 
   methylation, chromatin accessibility, and 3D genome in the same 
   DNA molecule
   Organism: N/A, Samples: 12
   Summary: Cis-regulatory elements coordinate the regulation of 
   their targeted genes' expression. However, the joint measurement 
   of cis-regulatory elements' activities and their interactions in 
   spatial proximity is limited by the current sequencing approaches. 
   We describe a method, NOMe-HiC, which simultaneously captures 
   single nucleotide polymorphisms, DNA methylation, chromatin 
   accessibility (GpC methyltransferase footprints), and chromosome 
   conformation changes from the same DNA molecule...

Analyze these datasets and provide:

1. **Overview**: Which datasets are most relevant to the user's query and why?
2. **Comparison**: How do these datasets differ in methodology and scope?
3. **Key Insights**: What are the main scientific findings or approaches?
4. **Recommendations**: Which dataset(s) would you recommend for:
   - Basic understanding of the topic
   - Advanced analysis
   - Method development

Write for a researcher who wants expert guidance on which datasets to use.
Be specific and cite dataset IDs (GSE numbers).
```

---

## 🎨 **How the Prompt Affects Results**

### **1. Query Context Matters**

**Your Query:** `"joint DNA methylation and HiC profiling"`

GPT-4 uses this to:
- ✅ Understand what you're looking for
- ✅ Assess relevance of each dataset to YOUR specific needs
- ✅ Focus analysis on DNA methylation + Hi-C aspects
- ✅ Ignore irrelevant parts of datasets

**Example Impact:**
- For query "cancer genomics" → AI focuses on cancer relevance
- For query "single cell RNA-seq" → AI focuses on scRNA-seq methods
- For query "epigenetics" → AI focuses on methylation, histone marks

### **2. Relevance Scores Influence AI**

```
GSE281238 (Relevance: 10%)
GSE189158 (Relevance: 5%)
```

**BUT** - GPT-4 can disagree with the scores!

In your case:
- **Search ranked GSE281238 higher (10%)**
- **GPT-4 concluded GSE189158 is MORE relevant**

Why? GPT-4 understands semantic meaning:
- GSE189158 title literally says "joint profiling... DNA methylation... 3D genome"
- GSE281238 focuses on sci-L3 method, not specifically DNA methylation + Hi-C

**This is POWERFUL** - AI provides a second opinion on relevance!

### **3. Dataset Summaries Provide Scientific Context**

The 300-character summaries give GPT-4 enough context to understand:
- Methodology (NOMe-HiC vs sci-L3)
- Biological focus (cis-regulatory elements vs single-cell)
- Technical approach (linear amplification vs simultaneous capture)

**Without summaries:** AI would only have titles (superficial analysis)
**With summaries:** AI understands the science (deep analysis)

### **4. Structured Request Guides Response Format**

The prompt explicitly asks for:
1. **Overview** → AI starts with "which is most relevant"
2. **Comparison** → AI creates methodology section
3. **Key Insights** → AI extracts scientific findings
4. **Recommendations** → AI suggests use cases

This structure ensures **consistent, actionable answers** every time.

### **5. Max Tokens Limit (800) Controls Length**

```python
max_tokens=800
```

**Effect:**
- Prevents overly long responses ($$$)
- Forces AI to be concise and focused
- Typically produces 600-800 words (perfect length)

If you need longer analysis, increase to 1200-1500 tokens.

---

## 🔬 **Response Processing**

### **What Comes Back from GPT-4**

```json
{
  "analysis": "### Overview\n\nBased on your query...\n\n### Comparison\n\n...",
  "model_used": "gpt-4-turbo-preview",
  "execution_time_ms": 14864
}
```

### **Frontend Rendering**

1. **Markdown Parsing** (marked.js):
   ```javascript
   const analysisHtml = marked.parse(data.analysis);
   ```

2. **Converts:**
   - `### Overview` → `<h3>Overview</h3>`
   - `**bold**` → `<strong>bold</strong>`
   - `- list item` → `<li>list item</li>`

3. **Displays** in purple gradient panel with proper styling

---

## ⚙️ **Configuration & Customization**

### **Environment Variables**

```bash
# Required
export OMICS_AI_OPENAI_API_KEY="sk-..."

# Optional (defaults shown)
export OMICS_AI_MODEL="gpt-4-turbo-preview"  # or "gpt-3.5-turbo"
export OMICS_AI_MAX_TOKENS="1000"
export OMICS_AI_TEMPERATURE="0.7"  # 0=deterministic, 1=creative
```

### **Customizing the Prompt**

**File:** `omics_oracle_v2/api/routes/agents.py`

**To add more context:**
```python
analysis_prompt = f"""
User searched for: "{request.query}"
User's research area: Epigenomics  # ← ADD THIS
User's expertise level: Advanced    # ← ADD THIS

Found {len(datasets_to_analyze)} relevant datasets:
...
```

**To change analysis focus:**
```python
Analyze these datasets and provide:

1. **Statistical Power**: Which has better sample size?
2. **Reproducibility**: Which has published code?
3. **Data Availability**: Which has SRA data?
4. **Citation Impact**: Which is more cited?
```

**To adjust tone:**
```python
system_message = (
    "You are a friendly bioinformatics tutor explaining datasets to a "
    "graduate student. Use simple language and provide examples."
)
```

### **Model Comparison**

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| **gpt-4-turbo-preview** | 15-30s | $0.03/analysis | ⭐⭐⭐⭐⭐ | Production, accuracy critical |
| **gpt-4** | 20-40s | $0.06/analysis | ⭐⭐⭐⭐⭐ | Maximum quality |
| **gpt-3.5-turbo** | 3-8s | $0.002/analysis | ⭐⭐⭐ | Testing, high volume |

---

## 🔍 **Real Example Walkthrough**

### **Your Query:** `"joint DNA methylation and HiC profiling"`

### **Step 1: Search finds 2 datasets**

```
GSE281238 (10% relevance) - sci-L3 method
GSE189158 (5% relevance) - NOMe-HiC method
```

### **Step 2: Prompt is constructed**

```
User searched for: "joint DNA methylation and HiC profiling"

Found 2 datasets:
[Full metadata for GSE281238 and GSE189158]

Analyze and provide: Overview, Comparison, Insights, Recommendations
```

### **Step 3: GPT-4 analyzes**

**GPT-4's reasoning (internal, not shown):**
1. User wants DNA methylation + Hi-C together
2. GSE189158 title explicitly mentions both
3. GSE189158 summary describes "simultaneous captures"
4. GSE281238 focuses on sci-L3 amplification method
5. GSE281238 doesn't emphasize methylation + Hi-C combo
6. **Conclusion:** GSE189158 is MORE relevant despite lower search score

### **Step 4: GPT-4 generates structured response**

```markdown
### Overview

Based on your query for "joint DNA methylation and HiC profiling," 
the most relevant dataset is **GSE189158**. This dataset directly 
addresses the simultaneous profiling of DNA methylation, chromatin 
accessibility, and 3D genome organization...

### Comparison

**GSE281238** employs the sci-L3 method, which is an advancement in 
single-cell combinatorial indexing strategies...

**GSE189158**, on the other hand, introduces NOMe-HiC, a novel 
methodology specifically designed for the concurrent examination...

### Key Insights

- **GSE281238** highlights the versatility and efficiency of the 
  sci-L3 method in capturing a wide range of genomic information...

- **GSE189158** provides critical insights into the interplay 
  between cis-regulatory elements and gene expression...

### Recommendations

**For Basic Understanding of the Topic:**
**GSE189158** is recommended...

**For Advanced Analysis:**
**GSE189158** would again be the go-to dataset...

**For Method Development:**
Both datasets offer valuable insights...
```

### **Step 5: Frontend renders as beautiful HTML**

With proper:
- `<h3>` headers for sections
- `<strong>` for dataset IDs
- `<p>` for paragraphs
- `<ul><li>` for bullet points

---

## 💡 **Key Insights**

### **What Makes This Powerful**

1. **Semantic Understanding**
   - Search uses keywords (basic matching)
   - AI understands scientific concepts (deep understanding)
   - AI can catch nuances humans might miss

2. **Expert Guidance**
   - Not just "here are datasets"
   - But "USE THIS ONE because..."
   - Actionable recommendations

3. **Comparative Analysis**
   - Highlights methodology differences
   - Explains tradeoffs
   - Helps choose the right dataset

4. **Research Context**
   - Understands why you're searching
   - Tailors advice to your needs
   - Provides use-case specific recommendations

### **Limitations to Be Aware Of**

1. **Cost:** ~$0.03 per analysis with GPT-4
2. **Speed:** 15-30 seconds (can't be instant)
3. **API Dependency:** Needs OpenAI key + internet
4. **Accuracy:** AI can hallucinate (rare with good prompts)
5. **Token Limits:** Can't analyze 100 datasets at once

---

## 🚀 **Future Improvements**

Ideas for enhancing the AI analysis:

1. **Add Paper Abstracts**
   - Fetch from PubMed
   - Give AI full publication context
   - Even better scientific understanding

2. **Include User Feedback**
   - "I'm looking for cancer-specific..."
   - "I need high sample count..."
   - Personalized recommendations

3. **Multi-Stage Analysis**
   - First pass: Which datasets are relevant?
   - Second pass: Deep dive on top 2
   - Third pass: Suggest analysis pipelines

4. **Citation Network**
   - "Dataset A is cited by Dataset B"
   - "These papers use similar methods"
   - Build knowledge graph

5. **Code Generation**
   - "Here's Python code to download GSE189158"
   - "Here's an analysis pipeline for NOMe-HiC data"
   - End-to-end guidance

---

## 📚 **Code References**

| Component | File | Line | Purpose |
|-----------|------|------|---------|
| Frontend Button | `semantic_search.html` | ~1262 | "Analyze with AI" button |
| Frontend JS | `semantic_search.html` | ~2430 | `analyzeWithAI()` function |
| API Endpoint | `api/routes/agents.py` | 545-673 | `analyze_datasets()` |
| Prompt Building | `api/routes/agents.py` | 587-611 | Constructs analysis prompt |
| OpenAI Call | `lib/ai/client.py` | ~180 | `_call_llm()` method |
| Markdown Parsing | `semantic_search.html` | ~2477 | `marked.parse()` |
| CSS Styling | `semantic_search.html` | ~1062 | Markdown element styles |

---

## 🎓 **Summary**

**The "Analyze with AI" feature is a research assistant that:**

1. Takes your search results
2. Understands your scientific question
3. Reads dataset metadata like a human expert
4. Compares methodologies and findings
5. Recommends the best dataset for your needs
6. Explains reasoning in clear language

**It's like having a senior bioinformatician review your search results!**

---

**Questions or want to customize? Check the code references above!** 🚀
