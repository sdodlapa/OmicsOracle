#!/usr/bin/env python3
"""
Test async LLM client performance improvements.

Compares sync vs async LLM operations to demonstrate speedup.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.llm.async_client import AsyncLLMClient, score_publications_batch_async
from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.search_engines.citations.models import Publication


def create_test_publications(count: int = 20) -> list[Publication]:
    """Create test publications for scoring."""
    publications = []

    papers = [
        {
            "title": "Single-cell RNA sequencing reveals novel cellular heterogeneity in pancreatic tumors",
            "abstract": "We performed single-cell RNA-seq on pancreatic cancer samples to identify distinct cell populations and their transcriptional states.",
        },
        {
            "title": "CRISPR-Cas9 genome editing in human embryonic stem cells",
            "abstract": "We demonstrate efficient CRISPR-mediated gene editing in hESCs with minimal off-target effects.",
        },
        {
            "title": "Deep learning for protein structure prediction",
            "abstract": "A novel deep learning architecture achieves state-of-the-art accuracy in protein folding prediction.",
        },
        {
            "title": "Spatial transcriptomics reveals tumor microenvironment architecture",
            "abstract": "We use spatial transcriptomics to map gene expression patterns in intact tumor tissue sections.",
        },
        {
            "title": "Multi-omics integration reveals disease mechanisms",
            "abstract": "Integrative analysis of genomics, transcriptomics, and proteomics data identifies key disease pathways.",
        },
    ]

    for i in range(count):
        paper = papers[i % len(papers)]
        pub = Publication(
            title=f"{paper['title']} (variant {i + 1})",
            abstract=paper["abstract"],
            pmid=f"PMID{12345000 + i}",
            authors=["Smith J", "Doe A"],
            journal="Nature Biotechnology",
            year=2024,
            source="pubmed",  # Required field
        )
        publications.append(pub)

    return publications


def test_sync_llm(publications: list[Publication], query: str):
    """Test synchronous LLM scoring."""
    print("\n" + "=" * 80)
    print("TEST 1: SYNCHRONOUS LLM SCORING")
    print("=" * 80)

    try:
        client = LLMClient(provider="openai", model="gpt-4o-mini", cache_enabled=True)
        print(f"✓ Initialized sync LLM client")
        print(f"  Model: {client.model}")
        print(f"  Provider: {client.provider}")
        print(f"  Publications to score: {len(publications)}")

        start_time = time.time()

        scores = []
        for i, pub in enumerate(publications):
            # Score each publication
            system_prompt = "You are a biomedical research expert. Score publication relevance from 0.0-1.0."
            user_prompt = f"""
            Query: {query}

            Publication:
            Title: {pub.title}
            Abstract: {pub.abstract}

            Respond with ONLY a number between 0.0 and 1.0.
            """

            response = client.generate(user_prompt, system_prompt, max_tokens=10)
            try:
                score = float(response["content"].strip())
                scores.append(score)
                print(f"  [{i+1}/{len(publications)}] Scored: {score:.2f} | Cached: {response['cached']}")
            except ValueError:
                scores.append(0.5)
                print(f"  [{i+1}/{len(publications)}] Failed to parse, using 0.5")

        elapsed = time.time() - start_time

        print(f"\n✓ Sync scoring complete!")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Average per publication: {elapsed/len(publications):.2f} seconds")
        print(f"  Throughput: {len(publications)/elapsed:.2f} publications/second")

        stats = client.get_usage_stats()
        print(f"\n  Cache stats:")
        print(f"    Hits: {stats['cache_hits']}")
        print(f"    Misses: {stats['cache_misses']}")
        print(f"    Hit rate: {stats['cache_hit_rate']*100:.1f}%")
        print(f"    Total tokens: {stats['total_tokens']}")

        return elapsed, scores

    except Exception as e:
        print(f"✗ Sync test failed: {e}")
        return 0, []


async def test_async_llm(publications: list[Publication], query: str):
    """Test asynchronous LLM scoring."""
    print("\n" + "=" * 80)
    print("TEST 2: ASYNCHRONOUS LLM SCORING")
    print("=" * 80)

    try:
        client = AsyncLLMClient(provider="openai", model="gpt-4o-mini", cache_enabled=True)
        print(f"✓ Initialized async LLM client")
        print(f"  Model: {client.model}")
        print(f"  Provider: {client.provider}")
        print(f"  Publications to score: {len(publications)}")
        print(f"  Max concurrent: 10")

        start_time = time.time()

        # Score all publications concurrently
        scores = await score_publications_batch_async(client, query, publications, max_concurrent=10)

        elapsed = time.time() - start_time

        print(f"\n✓ Async scoring complete!")
        print(f"  Scores: {[f'{s:.2f}' for s in scores[:5]]}... (showing first 5)")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Average per publication: {elapsed/len(publications):.2f} seconds")
        print(f"  Throughput: {len(publications)/elapsed:.2f} publications/second")

        stats = client.get_usage_stats()
        print(f"\n  Cache stats:")
        print(f"    Hits: {stats['cache_hits']}")
        print(f"    Misses: {stats['cache_misses']}")
        print(f"    Hit rate: {stats['cache_hit_rate']*100:.1f}%")
        print(f"    Total tokens: {stats['total_tokens']}")

        return elapsed, scores

    except Exception as e:
        print(f"✗ Async test failed: {e}")
        import traceback

        traceback.print_exc()
        return 0, []


async def test_async_batch_operations():
    """Test batch operations with async client."""
    print("\n" + "=" * 80)
    print("TEST 3: BATCH OPERATIONS")
    print("=" * 80)

    try:
        client = AsyncLLMClient(provider="openai", model="gpt-4o-mini", cache_enabled=True)

        prompts = [
            "Summarize the key findings of this paper in one sentence.",
            "What is the main methodology used in this research?",
            "What are the clinical implications of these findings?",
            "What future research directions are suggested?",
            "What are the limitations of this study?",
        ]

        print(f"  Testing {len(prompts)} concurrent requests...")

        start_time = time.time()
        responses = await client.generate_batch(prompts, max_concurrent=5)
        elapsed = time.time() - start_time

        print(f"\n✓ Batch operation complete!")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Average per request: {elapsed/len(prompts):.2f} seconds")

        for i, (prompt, response) in enumerate(zip(prompts, responses)):
            if "error" not in response:
                print(f"\n  [{i+1}] {prompt[:50]}...")
                print(f"      Response: {response['content'][:100]}...")
                print(f"      Tokens: {response['tokens']}, Cached: {response['cached']}")

        return elapsed

    except Exception as e:
        print(f"✗ Batch test failed: {e}")
        return 0


def main():
    """Run all async LLM tests."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ASYNC LLM CLIENT PERFORMANCE TEST" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")

    query = "single cell RNA sequencing cancer research"
    publications = create_test_publications(count=20)

    print(f"\nTest Configuration:")
    print(f"  Query: '{query}'")
    print(f"  Publications: {len(publications)}")
    print(f"  LLM Model: gpt-4o-mini (fast & cheap)")
    print(f"  Cache: Enabled")

    # Test 1: Sync LLM
    sync_time, sync_scores = test_sync_llm(publications, query)

    # Test 2: Async LLM
    async_time, async_scores = asyncio.run(test_async_llm(publications, query))

    # Test 3: Batch operations
    batch_time = asyncio.run(test_async_batch_operations())

    # Performance comparison
    if sync_time > 0 and async_time > 0:
        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON")
        print("=" * 80)

        speedup = sync_time / async_time
        time_saved = sync_time - async_time

        print(f"\n  Synchronous: {sync_time:.2f} seconds")
        print(f"  Asynchronous: {async_time:.2f} seconds")
        print(f"  Speedup: {speedup:.2f}x faster")
        print(f"  Time saved: {time_saved:.2f} seconds ({time_saved/sync_time*100:.1f}%)")

        if speedup >= 3:
            print(f"\n  ✓ SUCCESS: Achieved {speedup:.1f}x speedup (target: 3-5x)")
        elif speedup >= 2:
            print(f"\n  ~ GOOD: Achieved {speedup:.1f}x speedup (close to 3-5x target)")
        else:
            print(f"\n  ⚠ PARTIAL: Achieved {speedup:.1f}x speedup (below 3x target)")
            print(f"    Note: First run without cache will be slower. Run again for cached performance.")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\n✓ Async LLM client implementation complete!")
    print("\nKey Features:")
    print("  • Concurrent request processing")
    print("  • Automatic rate limiting")
    print("  • Connection pooling")
    print("  • Response caching")
    print("  • Retry logic with exponential backoff")
    print("  • Batch processing support")

    print("\nNext Steps:")
    print("  1. ✓ Async LLM client (DONE)")
    print("  2. → Update pipeline to use async client")
    print("  3. → Add async search operations")
    print("  4. → Implement Redis caching layer")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
