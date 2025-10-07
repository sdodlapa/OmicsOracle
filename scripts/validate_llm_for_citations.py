"""
LLM Validation Test - Day 16

Compares traditional keyword-based citation analysis vs LLM-powered analysis.

Tests:
1. Baseline (keyword matching)
2. LLM (BioMistral 7B or configured provider)
3. Comparison and decision

Usage:
    python scripts/validate_llm_for_citations.py
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations import LLMCitationAnalyzer
from omics_oracle_v2.lib.publications.citations.models import (
    CitationContext,
    UsageAnalysis,
)
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaselineAnalyzer:
    """Traditional keyword-based citation analysis."""

    def __init__(self):
        self.reuse_keywords = [
            "used data",
            "analyzed data",
            "downloaded",
            "obtained from",
            "using tcga",
            "tcga dataset",
            "tcga samples",
        ]

        self.method_keywords = {
            "machine learning": ["machine learning", "ml", "random forest", "svm"],
            "statistical": ["statistical analysis", "t-test", "anova"],
            "deep learning": ["deep learning", "neural network", "cnn"],
        }

    def analyze(self, paper: Publication, context_text: str) -> Dict:
        """Analyze using keyword matching."""
        text = (paper.abstract or "").lower() + " " + context_text.lower()

        # Detect reuse
        reused = any(kw in text for kw in self.reuse_keywords)

        # Extract method
        method = "unknown"
        for method_name, keywords in self.method_keywords.items():
            if any(kw in text for kw in keywords):
                method = method_name
                break

        # Simple findings extraction (look for "found", "identified", etc.)
        findings = []
        finding_markers = ["found", "identified", "discovered", "showed"]
        sentences = text.split(".")
        for sentence in sentences:
            if any(marker in sentence for marker in finding_markers):
                findings.append(sentence.strip()[:100])  # First 100 chars

        return {
            "dataset_reused": reused,
            "confidence": 0.6 if reused else 0.4,  # Low confidence
            "usage_type": "novel_application" if reused else "citation_only",
            "methodology": method,
            "key_findings": findings[:3],  # Max 3
            "reasoning": f"Keyword matching based on {len(findings)} markers",
        }


def create_sample_papers() -> List[tuple]:
    """
    Create sample papers for testing.

    Returns list of (cited_paper, citing_paper, context, ground_truth)
    """
    cited_paper = Publication(
        title="The Cancer Genome Atlas (TCGA): A Comprehensive Database",
        authors=["TCGA Consortium"],
        doi="10.1234/tcga.2015",
        publication_date=datetime(2015, 1, 1),
        abstract="TCGA is a comprehensive cancer genomics database.",
        source=PublicationSource.PUBMED,
    )

    samples = [
        # Sample 1: Clear reuse with explicit keywords - EASY
        {
            "citing_paper": Publication(
                title="Machine Learning Identifies Breast Cancer Biomarkers",
                authors=["Smith J"],
                doi="10.5678/ml.2020",
                publication_date=datetime(2020, 1, 1),
                abstract="We analyzed TCGA breast cancer RNA-seq data using random forest to identify prognostic biomarkers. Found 15 genes associated with survival.",
                source=PublicationSource.PUBMED,
            ),
            "context": "We downloaded TCGA breast cancer data and performed differential expression analysis.",
            "ground_truth": {
                "reused": True,
                "usage_type": "novel_application",
                "methodology": "machine learning",
                "findings": [
                    "15 genes associated with survival",
                    "Random forest classification",
                ],
            },
        },
        # Sample 2: Citation only - EASY
        {
            "citing_paper": Publication(
                title="Review of Cancer Genomics Databases",
                authors=["Jones A"],
                doi="10.9999/review.2021",
                publication_date=datetime(2021, 1, 1),
                abstract="We review major cancer databases including TCGA, discussing their structure and utility for research.",
                source=PublicationSource.PUBMED,
            ),
            "context": "TCGA is one of the largest cancer genomics databases.",
            "ground_truth": {
                "reused": False,
                "usage_type": "citation_only",
                "methodology": "narrative review",
                "findings": [],
            },
        },
        # Sample 3: Ambiguous - mentions but doesn't use - MEDIUM
        {
            "citing_paper": Publication(
                title="Novel Cancer Biomarker Discovery Pipeline",
                authors=["Lee K"],
                doi="10.1111/pipeline.2022",
                publication_date=datetime(2022, 1, 1),
                abstract="We developed a pipeline for biomarker discovery. Datasets like TCGA can be used with our method.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Our method is compatible with TCGA data.",
            "ground_truth": {
                "reused": False,  # Just mentioning, not using
                "usage_type": "citation_only",
                "methodology": "method development",
                "findings": [],
            },
        },
        # Sample 4: Tricky - uses TCGA but NO obvious keywords - HARD
        {
            "citing_paper": Publication(
                title="Genomic Predictors of Response to Immunotherapy",
                authors=["Chen M"],
                doi="10.2222/immuno.2023",
                publication_date=datetime(2023, 1, 1),
                abstract="Tumor mutational burden correlates with immunotherapy response. Our cohort of 500 melanoma patients revealed significant associations with PD-L1 expression.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Patient samples were obtained through institutional collaboration, with genomic profiles referenced from publicly available sources.",
            "ground_truth": {
                "reused": True,  # Actually used TCGA data but hidden in vague language
                "usage_type": "reanalysis",
                "methodology": "statistical analysis",
                "findings": [
                    "TMB correlates with immunotherapy response",
                    "PD-L1 expression associations",
                ],
            },
        },
        # Sample 5: Tricky - looks like use but it's comparison only - HARD
        {
            "citing_paper": Publication(
                title="Single-cell RNA-seq Reveals Tumor Heterogeneity",
                authors=["Wang L"],
                doi="10.3333/scrna.2023",
                publication_date=datetime(2023, 1, 1),
                abstract="We performed single-cell RNA-seq on 50 tumors. Bulk RNA-seq approaches from TCGA showed less granularity in capturing tumor heterogeneity.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Comparing our single-cell data to TCGA bulk sequencing demonstrates the advantages of our approach.",
            "ground_truth": {
                "reused": False,  # Just comparing/contrasting, not actually using the data
                "usage_type": "citation_only",
                "methodology": "single-cell sequencing",
                "findings": [],
            },
        },
        # Sample 6: Tricky - method development with validation on TCGA - HARD
        {
            "citing_paper": Publication(
                title="DeepSurv: Deep Learning for Cancer Prognosis",
                authors=["Brown R"],
                doi="10.4444/deep.2023",
                publication_date=datetime(2023, 1, 1),
                abstract="We developed DeepSurv, a neural network for survival prediction. The model achieves 0.85 C-index.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Model performance was validated across multiple cohorts showing consistent results.",
            "ground_truth": {
                "reused": True,  # Validated on TCGA (mentioned in context subtly)
                "usage_type": "validation",
                "methodology": "deep learning",
                "findings": [
                    "0.85 C-index achieved",
                    "Consistent across cohorts",
                ],
            },
        },
        # Sample 7: Extreme tricky - semantic understanding needed - VERY HARD
        {
            "citing_paper": Publication(
                title="Pan-Cancer Analysis of TP53 Mutations",
                authors=["Garcia S"],
                doi="10.5555/pancancer.2024",
                publication_date=datetime(2024, 1, 1),
                abstract="TP53 is the most frequently mutated gene across cancers. We analyzed mutation patterns in 10,000 samples revealing hotspot residues.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Leveraging large-scale genomic efforts, our analysis spans multiple cancer types.",
            "ground_truth": {
                "reused": True,  # "large-scale genomic efforts" = TCGA, needs semantic understanding
                "usage_type": "novel_application",
                "methodology": "computational analysis",
                "findings": [
                    "Hotspot residues identified",
                    "Pan-cancer mutation patterns",
                ],
            },
        },
        # Sample 8: Methodological citation - MEDIUM
        {
            "citing_paper": Publication(
                title="Best Practices for Cancer Genomics Studies",
                authors=["Taylor K"],
                doi="10.6666/best.2024",
                publication_date=datetime(2024, 1, 1),
                abstract="Standardized protocols are essential. TCGA's quality control metrics provide a benchmark for sample preparation and sequencing.",
                source=PublicationSource.PUBMED,
            ),
            "context": "Following TCGA protocols ensures data quality and reproducibility.",
            "ground_truth": {
                "reused": False,  # Using protocols/methods, not data
                "usage_type": "methodological_reference",
                "methodology": "protocol development",
                "findings": [],
            },
        },
    ]

    # Convert to test format
    test_cases = []
    for sample in samples:
        context = CitationContext(
            citing_paper_id=sample["citing_paper"].doi,
            cited_paper_id=cited_paper.doi,
            context_text=sample["context"],
            section="Methods",
        )
        test_cases.append(
            (cited_paper, sample["citing_paper"], context, sample["ground_truth"])
        )

    return test_cases


def evaluate_accuracy(predictions: List[Dict], ground_truths: List[Dict]) -> Dict:
    """Calculate accuracy metrics."""
    total = len(predictions)
    correct_reuse = sum(
        1
        for pred, truth in zip(predictions, ground_truths)
        if pred["dataset_reused"] == truth["reused"]
    )

    # Calculate precision, recall for reuse detection
    true_positives = sum(
        1
        for pred, truth in zip(predictions, ground_truths)
        if pred["dataset_reused"] and truth["reused"]
    )
    false_positives = sum(
        1
        for pred, truth in zip(predictions, ground_truths)
        if pred["dataset_reused"] and not truth["reused"]
    )
    false_negatives = sum(
        1
        for pred, truth in zip(predictions, ground_truths)
        if not pred["dataset_reused"] and truth["reused"]
    )

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0
    )
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "accuracy": correct_reuse / total,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def run_validation_test(use_llm: bool = False, llm_provider: str = "ollama"):
    """
    Run validation test comparing baseline vs LLM.

    Args:
        use_llm: Whether to test LLM (False = baseline only)
        llm_provider: LLM provider to test
    """
    logger.info("=" * 80)
    logger.info("LLM VALIDATION TEST - Week 3 Day 16")
    logger.info("=" * 80)

    # Create test cases
    logger.info("Creating test dataset...")
    test_cases = create_sample_papers()
    logger.info(f"Created {len(test_cases)} test cases")

    results = {"baseline": {}, "llm": {}}

    # Test 1: Baseline (keyword matching)
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: BASELINE (Keyword Matching)")
    logger.info("=" * 80)

    baseline_analyzer = BaselineAnalyzer()
    baseline_predictions = []
    baseline_start = time.time()

    for cited, citing, context, ground_truth in test_cases:
        prediction = baseline_analyzer.analyze(citing, context.context_text)
        baseline_predictions.append(prediction)

        logger.info(f"\nPaper: {citing.title[:50]}...")
        logger.info(f"  Predicted reuse: {prediction['dataset_reused']}")
        logger.info(f"  Actual reuse: {ground_truth['reused']}")
        logger.info(
            f"  Match: {'✓' if prediction['dataset_reused'] == ground_truth['reused'] else '✗'}"
        )

    baseline_time = time.time() - baseline_start

    # Evaluate baseline
    ground_truths = [gt for _, _, _, gt in test_cases]
    baseline_metrics = evaluate_accuracy(baseline_predictions, ground_truths)

    results["baseline"] = {
        "metrics": baseline_metrics,
        "time": baseline_time,
        "time_per_paper": baseline_time / len(test_cases),
        "predictions": baseline_predictions,
    }

    logger.info("\n" + "-" * 80)
    logger.info("BASELINE RESULTS:")
    logger.info(f"  Accuracy: {baseline_metrics['accuracy']:.2%}")
    logger.info(f"  Precision: {baseline_metrics['precision']:.2%}")
    logger.info(f"  Recall: {baseline_metrics['recall']:.2%}")
    logger.info(f"  F1 Score: {baseline_metrics['f1_score']:.2%}")
    logger.info(f"  Time: {baseline_time:.2f}s ({baseline_time/len(test_cases):.2f}s per paper)")

    # Test 2: LLM (if enabled)
    if use_llm:
        logger.info("\n" + "=" * 80)
        logger.info(f"TEST 2: LLM ({llm_provider.upper()})")
        logger.info("=" * 80)

        try:
            llm = LLMClient(provider=llm_provider, cache_enabled=True)
            llm_analyzer = LLMCitationAnalyzer(llm)

            llm_predictions = []
            llm_start = time.time()

            for cited, citing, context, ground_truth in test_cases:
                try:
                    analysis = llm_analyzer.analyze_citation_context(
                        context, cited, citing
                    )

                    prediction = {
                        "dataset_reused": analysis.dataset_reused,
                        "confidence": analysis.confidence,
                        "usage_type": analysis.usage_type,
                        "methodology": analysis.methodology,
                        "key_findings": analysis.key_findings,
                        "reasoning": analysis.reasoning,
                    }

                    llm_predictions.append(prediction)

                    logger.info(f"\nPaper: {citing.title[:50]}...")
                    logger.info(f"  Predicted reuse: {prediction['dataset_reused']}")
                    logger.info(f"  Confidence: {prediction['confidence']:.2f}")
                    logger.info(f"  Actual reuse: {ground_truth['reused']}")
                    logger.info(
                        f"  Match: {'✓' if prediction['dataset_reused'] == ground_truth['reused'] else '✗'}"
                    )

                except Exception as e:
                    logger.error(f"LLM analysis failed: {e}")
                    llm_predictions.append(
                        {
                            "dataset_reused": False,
                            "confidence": 0.0,
                            "usage_type": "unknown",
                            "methodology": "error",
                            "key_findings": [],
                            "reasoning": f"Error: {str(e)}",
                        }
                    )

            llm_time = time.time() - llm_start

            # Evaluate LLM
            llm_metrics = evaluate_accuracy(llm_predictions, ground_truths)

            results["llm"] = {
                "metrics": llm_metrics,
                "time": llm_time,
                "time_per_paper": llm_time / len(test_cases),
                "predictions": llm_predictions,
            }

            logger.info("\n" + "-" * 80)
            logger.info("LLM RESULTS:")
            logger.info(f"  Accuracy: {llm_metrics['accuracy']:.2%}")
            logger.info(f"  Precision: {llm_metrics['precision']:.2%}")
            logger.info(f"  Recall: {llm_metrics['recall']:.2%}")
            logger.info(f"  F1 Score: {llm_metrics['f1_score']:.2%}")
            logger.info(f"  Time: {llm_time:.2f}s ({llm_time/len(test_cases):.2f}s per paper)")

        except Exception as e:
            logger.error(f"LLM test failed: {e}")
            results["llm"] = {"error": str(e)}

    # Comparison
    logger.info("\n" + "=" * 80)
    logger.info("COMPARISON & DECISION")
    logger.info("=" * 80)

    if use_llm and "error" not in results["llm"]:
        # Compare metrics
        improvement = {
            "accuracy": results["llm"]["metrics"]["accuracy"]
            - results["baseline"]["metrics"]["accuracy"],
            "precision": results["llm"]["metrics"]["precision"]
            - results["baseline"]["metrics"]["precision"],
            "recall": results["llm"]["metrics"]["recall"]
            - results["baseline"]["metrics"]["recall"],
            "f1_score": results["llm"]["metrics"]["f1_score"]
            - results["baseline"]["metrics"]["f1_score"],
        }

        logger.info("\nIMPROVEMENT (LLM vs Baseline):")
        logger.info(f"  Accuracy: {improvement['accuracy']:+.1%}")
        logger.info(f"  Precision: {improvement['precision']:+.1%}")
        logger.info(f"  Recall: {improvement['recall']:+.1%}")
        logger.info(f"  F1 Score: {improvement['f1_score']:+.1%}")

        # Decision logic
        llm_accuracy = results["llm"]["metrics"]["accuracy"]
        llm_f1 = results["llm"]["metrics"]["f1_score"]

        logger.info("\nDECISION CRITERIA:")
        logger.info(f"  LLM Accuracy: {llm_accuracy:.1%} (threshold: >85%)")
        logger.info(f"  LLM F1 Score: {llm_f1:.1%}")
        logger.info(f"  Time per paper: {results['llm']['time_per_paper']:.1f}s (threshold: <5min)")

        if llm_accuracy >= 0.85 and llm_f1 >= 0.80:
            decision = "✅ GO: Use LLM - Excellent performance!"
        elif llm_accuracy >= 0.75:
            decision = "⚠️  HYBRID: Use LLM + keywords - Good but not excellent"
        else:
            decision = "❌ NO-GO: Stick with keywords - LLM doesn't add enough value"

        logger.info(f"\nRECOMMENDATION: {decision}")

    # Save results
    output_dir = Path("./data/validation_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"llm_validation_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate LLM for citation analysis")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Test LLM (default: baseline only)",
    )
    parser.add_argument(
        "--provider",
        default="ollama",
        choices=["openai", "anthropic", "ollama"],
        help="LLM provider to test",
    )

    args = parser.parse_args()

    logger.info(f"Running validation test (LLM: {args.llm}, Provider: {args.provider})")
    results = run_validation_test(use_llm=args.llm, llm_provider=args.provider)

    logger.info("\n✅ Validation test complete!")
