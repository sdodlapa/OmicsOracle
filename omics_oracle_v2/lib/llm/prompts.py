"""
Prompt templates for LLM-powered citation analysis.

Contains carefully crafted prompts for:
- Citation context analysis
- Dataset usage classification
- Knowledge synthesis
- Trend detection
- Research Q&A
"""

# Citation Context Analysis
CITATION_CONTEXT_ANALYSIS = """You are a biomedical research analyst. Analyze this citation to understand how a dataset/paper was used.

CITED PAPER (original dataset paper):
Title: {cited_title}
Abstract: {cited_abstract}

CITING PAPER (paper that used the dataset):
Title: {citing_title}
Abstract: {citing_abstract}

6. **Citation context** -> Sentence/paragraph mentioning the dataset:
{citation_context}

Analyze and return JSON with the following structure:
{{
    "dataset_reused": boolean,
    "usage_type": string,
    "confidence": float,
    "research_question": string,
    "application_domain": string,
    "methodology": string,
    "sample_info": string,
    "key_findings": [string],
    "clinical_relevance": string,
    "clinical_details": string,
    "novel_biomarkers": [string],
    "validation_status": string,
    "reasoning": string
}}

Field definitions:
- dataset_reused: Did they actually use/analyze the data from the cited paper?
- usage_type: "validation", "novel_application", "comparison", "meta_analysis", "methodology", "review"
- confidence: 0-1 confidence in your analysis
- research_question: What specific question did they investigate?
- application_domain: e.g., "breast cancer biomarker discovery", "drug response prediction"
- methodology: e.g., "machine learning - random forest", "statistical analysis - Cox regression"
- sample_info: Sample size and source, e.g., "500 samples from TCGA-BRCA"
- key_findings: List of 2-5 main findings from the citing paper
- clinical_relevance: "high", "medium", "low", "none"
- clinical_details: If clinically relevant, explain how (trials, validation, FDA, etc.)
- novel_biomarkers: Any new biomarkers/genes/proteins identified
- validation_status: "validated", "in_progress", "proposed", "none"
- reasoning: Brief explanation of your analysis

Be precise and evidence-based. Only include information explicitly stated or strongly implied.
If information is not available, use null or empty arrays."""

# Dataset Impact Synthesis
DATASET_IMPACT_SYNTHESIS = """You are a biomedical research expert synthesizing insights from multiple studies that used a dataset.

ORIGINAL DATASET PAPER:
Title: {dataset_title}
Abstract: {dataset_abstract}
Year: {dataset_year}

NUMBER OF CITING PAPERS ANALYZED: {num_papers}

CITING PAPERS SUMMARY:
{citing_papers_summary}

Generate a comprehensive dataset impact report with the following sections:

## 1. OVERVIEW
- Total citations and dataset reuse statistics
- Time span and adoption trajectory
- Overall scientific impact score (1-10)

## 2. PRIMARY APPLICATIONS
List the top 5-7 application domains with:
- Domain name
- Number of papers
- Representative paper titles (1-2 examples)
- Key characteristics

## 3. KEY DISCOVERIES
Aggregate novel findings:
- Novel biomarkers identified (list unique ones)
- Important biological insights
- Methodological breakthroughs
- Unexpected discoveries

## 4. METHODOLOGICAL TRENDS
- Analysis approaches used (statistical, ML, experimental)
- Evolution of methods over time
- Most successful methodologies

## 5. CLINICAL IMPACT
- Clinical trials initiated or completed
- FDA submissions or approvals
- Clinical validation studies
- Patient outcomes reported
- Translation timeline (research → clinic)

## 6. TEMPORAL EVOLUTION (by period)
- Early phase (first 1-2 years): Initial applications
- Growth phase: Expanding applications
- Maturity phase: Current state
- Emerging trends (2024-2025): Latest developments

## 7. RESEARCH GAPS & OPPORTUNITIES
- Understudied applications
- Methodological limitations addressed or remaining
- Data integration opportunities
- Future research directions

Format as a clear, well-structured research summary. Use specific numbers, paper counts, and examples.
Be concise but comprehensive. Each section should be 2-4 paragraphs."""

# Temporal Trend Analysis
TEMPORAL_TREND_ANALYSIS = """Analyze how dataset usage evolved over time.

DATASET: {dataset_title}

USAGE BY YEAR:
{usage_by_year}

Provide narrative analysis covering:

1. **Adoption Phases**
   - Identify distinct phases (early adoption, rapid growth, maturity, etc.)
   - Note inflection points and drivers

2. **Methodological Evolution**
   - How analysis methods changed over time
   - Introduction of new techniques (ML, multi-omics, etc.)

3. **Shifting Research Questions**
   - How research focus evolved
   - Emerging vs declining applications

4. **Breakthrough Moments**
   - Highly cited or impactful studies
   - Paradigm shifts in the field

5. **Current State (2024-2025)**
   - Latest applications
   - Most active research areas
   - Integration with new technologies

6. **Future Trajectory**
   - Predicted developments
   - Opportunities for innovation
   - Potential obsolescence factors

Provide specific examples with years and paper counts. Be analytical, not just descriptive."""

# Research Question Answering
RESEARCH_QUESTION_ANSWERING = """You are a research assistant with deep knowledge of biomedical literature and dataset usage.

CONTEXT:
Dataset: {dataset_title}
Dataset Usage Analysis: {usage_summary}

USER QUESTION:
{question}

Instructions:
1. Answer the question using ONLY the dataset usage data provided
2. Be specific - cite paper counts, years, and examples
3. If the data doesn't fully answer the question, explain what's available
4. Provide evidence for your claims
5. Suggest related information that might be helpful

Format your response as:

**Direct Answer:**
[Concise answer to the question]

**Supporting Evidence:**
[Specific examples, numbers, and citations from the data]

**Additional Context:**
[Related information that might be useful]

**Limitations:**
[What the data doesn't tell us about this question]"""

# Usage Classification (Batch)
BATCH_USAGE_CLASSIFICATION = """You are a research analyst classifying how datasets are used in scientific papers.

Analyze the following {num_papers} papers and classify each one's dataset usage:

PAPERS:
{papers_data}

For each paper, determine:
1. Did they use the dataset from the original paper?
2. How did they use it?
3. What domain/application?
4. What methodology?
5. What did they find?

Return a JSON array with one object per paper:
[
    {{
        "paper_id": "string",
        "paper_title": "string",
        "dataset_reused": boolean,
        "usage_type": "validation|novel_application|comparison|meta_analysis|methodology|review",
        "application_domain": "string",
        "methodology": "string",
        "key_findings": ["string"],
        "confidence": float
    }},
    ...
]

Process all {num_papers} papers. Be consistent in classification across papers."""

# Biomarker Extraction
BIOMARKER_EXTRACTION = """Extract all novel biomarkers discovered across these papers that used the dataset.

PAPERS WITH FINDINGS:
{papers_with_findings}

Identify and list:
1. **Novel Biomarkers** - Genes, proteins, metabolites newly identified
2. **Source** - Which paper(s) identified each
3. **Application** - What they predict/indicate
4. **Validation** - Level of validation (computational, experimental, clinical)
5. **Clinical relevance** - Potential clinical utility

Return JSON:
{{
    "biomarkers": [
        {{
            "name": "string",
            "type": "gene|protein|metabolite|signature",
            "sources": ["paper_title1", "paper_title2"],
            "application": "string",
            "validation_level": "computational|experimental|clinical",
            "clinical_potential": "high|medium|low",
            "details": "string"
        }}
    ],
    "summary": "string"
}}

Group duplicates (same biomarker from multiple papers). Focus on validated findings."""

# Clinical Translation Analysis
CLINICAL_TRANSLATION_ANALYSIS = """Analyze the clinical translation of research using this dataset.

DATASET: {dataset_title}
PAPERS WITH CLINICAL RELEVANCE:
{clinical_papers}

Analyze:
1. **Translation Pipeline**
   - Discovery → Validation → Clinical trials → FDA/approval
   - Where are papers in this pipeline?

2. **Clinical Trials**
   - Trials initiated based on dataset findings
   - Trial status and results

3. **Clinical Validation**
   - Independent cohort validation
   - Patient outcomes

4. **FDA/Regulatory**
   - Submissions or approvals
   - Companion diagnostics

5. **Implementation**
   - Clinical guidelines
   - Routine clinical use

6. **Translation Timeline**
   - Time from discovery to clinic
   - Success rate

7. **Barriers**
   - What's preventing translation?
   - Technical or regulatory challenges

Return a structured analysis with specific examples and statistics."""
