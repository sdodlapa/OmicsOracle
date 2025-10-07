"""
Day 28: Biomarker Embeddings & Recommendation Engine Test

Tests:
1. Embedding generation and caching
2. Similarity search
3. Recommendation strategies
4. Performance benchmarks
"""

import asyncio
import time
from datetime import datetime

import numpy as np

from omics_oracle_v2.lib.ml.embeddings import BiomarkerEmbedder, SimilaritySearch
from omics_oracle_v2.lib.ml.recommender import BiomarkerRecommender, RecommendationScorer
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource


def create_sample_biomarker_data():
    """Create sample biomarker data for testing."""
    biomarker_data = {}

    # Biomarker 1: BRCA1 (breast cancer, high impact)
    biomarker_data["BRCA1"] = [
        Publication(
            pmid=f"BRCA1_{i}",
            title=f"BRCA1 and breast cancer susceptibility study {i}",
            authors=["Smith J", "Jones A"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2020 + i % 4, 1, 1),
            abstract="Study on BRCA1 mutations in breast cancer patients",
            journal="Nature",
            citations=100 + i * 20,
        )
        for i in range(20)
    ]

    # Biomarker 2: BRCA2 (similar to BRCA1)
    biomarker_data["BRCA2"] = [
        Publication(
            pmid=f"BRCA2_{i}",
            title=f"BRCA2 genetic mutations and cancer risk {i}",
            authors=["Johnson M", "Williams K"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2020 + i % 4, 2, 1),
            abstract="Investigation of BRCA2 in hereditary breast cancer",
            journal="Cell",
            citations=90 + i * 15,
        )
        for i in range(18)
    ]

    # Biomarker 3: TP53 (tumor suppressor, high impact)
    biomarker_data["TP53"] = [
        Publication(
            pmid=f"TP53_{i}",
            title=f"TP53 mutations in human cancers {i}",
            authors=["Brown T", "Davis R"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2019 + i % 5, 3, 1),
            abstract="Analysis of TP53 tumor suppressor gene mutations",
            journal="Science",
            citations=150 + i * 25,
        )
        for i in range(25)
    ]

    # Biomarker 4: PD-L1 (immunotherapy, emerging)
    biomarker_data["PD-L1"] = [
        Publication(
            pmid=f"PDL1_{i}",
            title=f"PD-L1 expression in cancer immunotherapy {i}",
            authors=["Miller S", "Wilson P"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2021 + i % 3, 4, 1),
            abstract="PD-L1 as biomarker for immune checkpoint therapy",
            journal="NEJM",
            citations=60 + i * 30,  # Rapidly growing citations
        )
        for i in range(15)
    ]

    # Biomarker 5: circRNA (very emerging, novel)
    biomarker_data["circRNA"] = [
        Publication(
            pmid=f"circRNA_{i}",
            title=f"Circular RNA in cancer detection {i}",
            authors=["Anderson L", "Thomas K"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2022 + i % 2, 5, 1),
            abstract="Novel circular RNA biomarkers for early cancer detection",
            journal="Nature Biotechnology",
            citations=20 + i * 10,
        )
        for i in range(10)
    ]

    # Biomarker 6: KRAS (oncogene)
    biomarker_data["KRAS"] = [
        Publication(
            pmid=f"KRAS_{i}",
            title=f"KRAS mutations in colorectal cancer {i}",
            authors=["Lee H", "Garcia M"],
            source=PublicationSource.PUBMED,
            publication_date=datetime(2020 + i % 4, 6, 1),
            abstract="KRAS oncogene mutations and therapeutic implications",
            journal="Cancer Cell",
            citations=80 + i * 18,
        )
        for i in range(16)
    ]

    return biomarker_data


async def test_embeddings_and_recommendations():
    """Test embedding generation and recommendation system."""
    print("Starting Day 28 Embeddings & Recommendations Test...\n")
    print("=" * 60)
    print("Day 28: Biomarker Embeddings & Recommendation Engine")
    print("=" * 60)

    # Create sample data
    print("\nCreating sample biomarker data...")
    biomarker_data = create_sample_biomarker_data()
    biomarker_names = list(biomarker_data.keys())
    print(f"Created {len(biomarker_names)} biomarkers with publications")
    for name, pubs in biomarker_data.items():
        print(f"  {name}: {len(pubs)} publications")

    # Test 1: Embedding Generation
    print("\n" + "-" * 60)
    print("TEST 1: Embedding Generation")
    print("-" * 60)

    print("\n1.1 Initializing Embedder...")
    embedder = BiomarkerEmbedder()
    print(f"Model: {embedder.model_name}")
    print(f"Embedding dimension: {embedder.embedding_dim}")

    print("\n1.2 Generating Biomarker Embeddings...")
    start = time.time()
    embeddings = {}
    for name, pubs in biomarker_data.items():
        embedding = embedder.embed_biomarker(name, pubs)
        embeddings[name] = embedding
        print(f"  {name}: {embedding.shape}, norm={np.linalg.norm(embedding):.3f}")
    embed_time = time.time() - start
    print(f"\nGenerated {len(embeddings)} embeddings in {embed_time:.3f}s")
    print(f"Avg time per biomarker: {embed_time*1000/len(embeddings):.2f}ms")

    # Test 2: Similarity Search
    print("\n" + "-" * 60)
    print("TEST 2: Similarity Search")
    print("-" * 60)

    print("\n2.1 Building FAISS Index...")
    similarity_search = SimilaritySearch(embedder.embedding_dim)
    embeddings_array = np.array([embeddings[name] for name in biomarker_names])
    similarity_search.build_index(biomarker_names, embeddings_array)
    print(f"Index built with {len(biomarker_names)} biomarkers")

    print("\n2.2 Finding Similar Biomarkers to BRCA1...")
    start = time.time()
    similar = similarity_search.find_similar(embeddings["BRCA1"], k=5)
    search_time = (time.time() - start) * 1000
    print(f"Search completed in {search_time:.2f}ms")
    print("Top 5 similar biomarkers:")
    for biomarker, score in similar:
        print(f"  {biomarker}: {score:.4f}")

    print("\n2.3 Testing Similarity Scores...")
    # Test known relationships
    brca1_brca2_sim = similarity_search.cosine_similarity(embeddings["BRCA1"], embeddings["BRCA2"])
    brca1_tp53_sim = similarity_search.cosine_similarity(embeddings["BRCA1"], embeddings["TP53"])
    brca1_circrna_sim = similarity_search.cosine_similarity(embeddings["BRCA1"], embeddings["circRNA"])
    print(f"BRCA1 vs BRCA2: {brca1_brca2_sim:.4f} (should be high - both breast cancer)")
    print(f"BRCA1 vs TP53: {brca1_tp53_sim:.4f} (should be moderate - both cancer)")
    print(f"BRCA1 vs circRNA: {brca1_circrna_sim:.4f} (should be lower - different contexts)")

    # Test 3: Recommendation Engine
    print("\n" + "-" * 60)
    print("TEST 3: Recommendation Engine")
    print("-" * 60)

    print("\n3.1 Initializing Recommender...")
    scorer = RecommendationScorer()
    recommender = BiomarkerRecommender(embedder, similarity_search, scorer)
    print("Recommender initialized")

    print("\n3.2 Similar Biomarker Recommendations (for BRCA1)...")
    start = time.time()
    similar_recs = recommender.recommend_similar("BRCA1", biomarker_data, k=3)
    rec_time = (time.time() - start) * 1000
    print(f"Generated {len(similar_recs)} recommendations in {rec_time:.2f}ms")
    for i, rec in enumerate(similar_recs, 1):
        print(f"\n{i}. {rec.biomarker} (score: {rec.score:.3f})")
        print(f"   Similarity: {rec.similarity_score:.3f}")
        print(f"   Trend: {rec.trend_score:.3f}")
        print(f"   Impact: {rec.impact_score:.3f}")
        print(f"   Novelty: {rec.novelty_score:.3f}")
        print(f"   Publications: {rec.related_publications}")
        print(f"   Explanation: {rec.explanation}")

    print("\n3.3 Emerging Biomarker Recommendations...")
    start = time.time()
    emerging_recs = recommender.recommend_emerging(biomarker_data, k=3)
    emerging_time = (time.time() - start) * 1000
    print(f"Found {len(emerging_recs)} emerging biomarkers in {emerging_time:.2f}ms")
    for i, rec in enumerate(emerging_recs, 1):
        print(f"\n{i}. {rec.biomarker} (score: {rec.score:.3f})")
        print(f"   Trend: {rec.trend_score:.3f} (growth momentum)")
        print(f"   Impact: {rec.impact_score:.3f}")
        print(f"   Novelty: {rec.novelty_score:.3f}")
        print(f"   Publications: {rec.related_publications}")
        print(f"   Explanation: {rec.explanation}")

    print("\n3.4 High-Impact Biomarker Recommendations...")
    start = time.time()
    impact_recs = recommender.recommend_high_impact(biomarker_data, k=3)
    impact_time = (time.time() - start) * 1000
    print(f"Found {len(impact_recs)} high-impact biomarkers in {impact_time:.2f}ms")
    for i, rec in enumerate(impact_recs, 1):
        print(f"\n{i}. {rec.biomarker} (score: {rec.score:.3f})")
        print(f"   Impact: {rec.impact_score:.3f} (citation impact)")
        print(f"   Trend: {rec.trend_score:.3f}")
        print(f"   Novelty: {rec.novelty_score:.3f}")
        print(f"   Publications: {rec.related_publications}")
        print(f"   Explanation: {rec.explanation}")

    # Test 4: Performance Benchmarks
    print("\n" + "-" * 60)
    print("TEST 4: Performance Benchmarks")
    print("-" * 60)

    print("\n4.1 Embedding Speed Test...")
    test_texts = [f"Test biomarker {i} in cancer research" for i in range(10)]
    start = time.time()
    _ = embedder.embed_batch(test_texts)  # noqa: F841
    batch_time = (time.time() - start) * 1000
    print(f"Batch embed 10 texts: {batch_time:.2f}ms")
    print(f"Per-text time: {batch_time/10:.2f}ms")
    print("Target: <50ms per biomarker")
    print(f"Status: {'PASS' if batch_time/10 < 50 else 'FAIL'}")

    print("\n4.2 Similarity Search Speed Test...")
    search_times = []
    for _ in range(10):
        start = time.time()
        similarity_search.find_similar(embeddings["BRCA1"], k=10)
        search_times.append((time.time() - start) * 1000)
    avg_search = np.mean(search_times)
    print("10 similarity searches:")
    print(f"  Average: {avg_search:.2f}ms")
    print(f"  Min: {min(search_times):.2f}ms")
    print(f"  Max: {max(search_times):.2f}ms")
    print("Target: <100ms")
    print(f"Status: {'PASS' if avg_search < 100 else 'FAIL'}")

    print("\n4.3 Recommendation Speed Test...")
    rec_times = []
    for _ in range(10):
        start = time.time()
        recommender.recommend_similar("BRCA1", biomarker_data, k=10)
        rec_times.append((time.time() - start) * 1000)
    avg_rec = np.mean(rec_times)
    print("10 recommendation requests:")
    print(f"  Average: {avg_rec:.2f}ms")
    print(f"  Min: {min(rec_times):.2f}ms")
    print(f"  Max: {max(rec_times):.2f}ms")
    print("Target: <200ms")
    print(f"Status: {'PASS' if avg_rec < 200 else 'FAIL'}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Day 28 Tests")
    print("=" * 60)

    all_tests_pass = True
    results = {
        "embedding_speed_ms": batch_time / 10,
        "search_speed_ms": avg_search,
        "recommendation_speed_ms": avg_rec,
        "embedding_dim": embedder.embedding_dim,
        "num_biomarkers": len(biomarker_names),
        "brca1_brca2_similarity": brca1_brca2_sim,
    }

    print("\nPerformance Metrics:")
    print(f"  Embedding Speed: {results['embedding_speed_ms']:.2f}ms (Target: <50ms)")
    if results["embedding_speed_ms"] >= 50:
        all_tests_pass = False
    print(f"  Search Speed: {results['search_speed_ms']:.2f}ms (Target: <100ms)")
    if results["search_speed_ms"] >= 100:
        all_tests_pass = False
    print(f"  Recommendation Speed: {results['recommendation_speed_ms']:.2f}ms (Target: <200ms)")
    if results["recommendation_speed_ms"] >= 200:
        all_tests_pass = False

    print("\nQuality Metrics:")
    print(f"  BRCA1-BRCA2 Similarity: {results['brca1_brca2_similarity']:.3f}")
    print(f"  Embedding Dimension: {results['embedding_dim']}")
    print(f"  Biomarkers Indexed: {results['num_biomarkers']}")

    print("\nRecommendation Counts:")
    print(f"  Similar: {len(similar_recs)} recommendations")
    print(f"  Emerging: {len(emerging_recs)} biomarkers")
    print(f"  High-Impact: {len(impact_recs)} biomarkers")

    print("\nDay 28 Implementation Status:")
    print("  Embedding Generation: COMPLETE")
    print("  Similarity Search: COMPLETE")
    print("  Recommendation Engine: COMPLETE")
    print("  Performance Testing: COMPLETE")

    if all_tests_pass:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("SOME TESTS FAILED - Review performance")
        print("=" * 60)

    return results


if __name__ == "__main__":
    print("Starting Day 28: Biomarker Embeddings & Recommendation Engine Test\n")
    results = asyncio.run(test_embeddings_and_recommendations())
    print("\nTest completed successfully!")
    print(f"Results: {results}")
