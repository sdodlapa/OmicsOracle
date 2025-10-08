"""
Test MLClient against live backend
"""
import asyncio

from omics_oracle_v2.integration import MLClient, SearchClient


async def test_ml_client():
    """Test all MLClient methods"""
    print("\n" + "=" * 80)
    print("TESTING ML CLIENT")
    print("=" * 80)

    # Get some search results for seed papers
    print("\n[SETUP] Getting search results for seed papers...")
    async with SearchClient() as search:
        search_results = await search.search(query="machine learning genomics", max_results=5)
        print(f"  [OK] Got {len(search_results.results)} results")
        seed_papers = [result.id for result in search_results.results[:2] if result.id]
        print(f"  [OK] Seed papers: {seed_papers}")

    async with MLClient() as client:
        # Test 1: Get Recommendations
        print("\n[TEST 1] Paper Recommendations - get_recommendations()")
        try:
            if seed_papers:
                recs = await client.get_recommendations(seed_papers=seed_papers, count=5)
                print("  [OK] Recommendations retrieved!")
                print(f"  Response type: {type(recs)}")
                print(f"  Response preview: {str(recs)[:200]}...")
            else:
                print("  [SKIP] No seed papers available")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 2: Predict Citations
        print("\n[TEST 2] Citation Prediction - predict_citations()")
        try:
            if search_results.results:
                pub_id = search_results.results[0].id
                prediction = await client.predict_citations(pub_id=pub_id, years_ahead=5)
                print("  [OK] Citation prediction completed!")
                print(f"  Response type: {type(prediction)}")
                print(f"  Response: {prediction}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 3: Get Trending Topics
        print("\n[TEST 3] Trending Topics - get_trending_topics()")
        try:
            trends = await client.get_trending_topics()
            print("  [OK] Trending topics retrieved!")
            print(f"  Response type: {type(trends)}")
            print(f"  Response preview: {str(trends)[:200]}...")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 4: Rank by Relevance
        print("\n[TEST 4] Relevance Ranking - rank_by_relevance()")
        try:
            ranked = await client.rank_by_relevance(
                query="CRISPR applications", publications=search_results.results[:5]
            )
            print("  [OK] Ranking completed!")
            print(f"  Response type: {type(ranked)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 5: Predict Impact
        print("\n[TEST 5] Impact Prediction - predict_impact()")
        try:
            if search_results.results:
                impact = await client.predict_impact(publication=search_results.results[0])
                print("  [OK] Impact prediction completed!")
                print(f"  Response type: {type(impact)}")
                print(f"  Response: {impact}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 6: Get Emerging Authors
        print("\n[TEST 6] Emerging Authors - get_emerging_authors()")
        try:
            authors = await client.get_emerging_authors()
            print("  [OK] Emerging authors retrieved!")
            print(f"  Response type: {type(authors)}")
            print(f"  Response preview: {str(authors)[:200]}...")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ML CLIENT TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ml_client())
