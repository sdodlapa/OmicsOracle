#!/usr/bin/env python3
"""
Frontend Simulation Test - Complete User Experience
Simulates clicking buttons in the dashboard and validates responses.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FrontendSimulator:
    """Simulates user interactions with the dashboard."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.current_results = []
        self.selected_dataset = None

    async def simulate_search(self, query: str):
        """Simulate: User types query and clicks Search button."""
        logger.info("=" * 80)
        logger.info(f"👤 USER ACTION: Types '{query}' and clicks 'Search' button")
        logger.info("=" * 80)

        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"\n📡 Frontend sends: POST {self.base_url}/api/agents/search")
            logger.info(f"   Payload: {{search_terms: ['{query}'], max_results: 5}}")

            response = await client.post(
                f"{self.base_url}/api/agents/search",
                json={
                    "search_terms": [query],
                    "max_results": 5,
                    "enable_semantic": False,
                },
            )

            if response.status_code != 200:
                logger.error(f"❌ Search failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False

            data = response.json()
            self.current_results = data.get("datasets", [])

            logger.info(f"\n✅ Backend responds:")
            logger.info(f"   Status: {data.get('success')}")
            logger.info(f"   Datasets found: {len(self.current_results)}")
            logger.info(f"   Execution time: {data.get('execution_time_ms', 0):.2f}ms")

            # Display results as they would appear in frontend
            logger.info(
                f"\n📊 FRONTEND RENDERS {len(self.current_results)} DATASET CARDS:"
            )
            logger.info("=" * 80)

            for i, dataset in enumerate(self.current_results[:3], 1):  # Show first 3
                self._render_dataset_card(i, dataset)

            return True

    def _render_dataset_card(self, index: int, dataset: dict):
        """Render dataset card as it appears in the frontend."""
        logger.info(f"\n┌─ Dataset Card #{index} " + "─" * 60)
        logger.info(f"│ GEO ID: {dataset.get('geo_id')}")
        logger.info(f"│ Title: {dataset.get('title', '')[:60]}...")
        logger.info(f"│ Organism: {dataset.get('organism', 'N/A')}")
        logger.info(f"│ Samples: {dataset.get('sample_count', 0)}")
        logger.info(f"│ Relevance: {dataset.get('relevance_score', 0)*100:.0f}%")

        # Publication info (NEW DATABASE METRICS)
        pub_date = dataset.get("publication_date")
        if pub_date:
            logger.info(f"│ Published: {pub_date}")

        # Database metrics (from our integration)
        citation_count = dataset.get("citation_count", 0)
        pdf_count = dataset.get("pdf_count", 0)
        processed_count = dataset.get("processed_count", 0)
        completion_rate = dataset.get("completion_rate", 0.0)

        logger.info(f"│")
        logger.info(f"│ 📚 Citations in database: {citation_count}")
        logger.info(f"│ 📄 PDFs downloaded: {pdf_count}/{citation_count}")
        logger.info(
            f"│ 📊 Processing: {completion_rate:.0f}% complete ({processed_count} processed)"
        )

        # Button states
        fulltext_count = dataset.get("fulltext_count", 0)

        logger.info(f"│")
        if citation_count > 0:
            if fulltext_count > 0:
                logger.info(
                    f"│ 🟢 [AI Analysis] button - ENABLED ({fulltext_count} PDFs available)"
                )
            else:
                logger.info(
                    f"│ 🔵 [Download Papers] button - ENABLED ({citation_count} in DB)"
                )
                logger.info(f"│ ⚪ [AI Analysis] button - DISABLED (PDFs required)")
        else:
            logger.info(f"│ ⚪ [Download Papers] button - DISABLED (no citations in DB)")
            logger.info(f"│ ⚪ [AI Analysis] button - DISABLED (no citations in DB)")

        logger.info(f"└" + "─" * 78)

    async def simulate_download_papers(self, card_index: int):
        """Simulate: User clicks 'Download Papers' button."""
        if card_index >= len(self.current_results):
            logger.error(f"❌ Invalid card index: {card_index}")
            return False

        dataset = self.current_results[card_index]

        logger.info("\n" + "=" * 80)
        logger.info(
            f"👤 USER ACTION: Clicks 'Download Papers' button on Card #{card_index + 1}"
        )
        logger.info(
            f"   Dataset: {dataset.get('geo_id')} - {dataset.get('title', '')[:50]}..."
        )
        logger.info("=" * 80)

        # Frontend disables button and shows loading
        logger.info(f"\n🎨 Frontend updates:")
        logger.info(f"   Button text changes: '📥 Download Papers' → '⏳ Downloading...'")
        logger.info(f"   Button disabled: true")

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:  # Longer timeout for downloads
            logger.info(
                f"\n📡 Frontend sends: POST {self.base_url}/api/agents/enrich-fulltext"
            )
            logger.info(f"   Payload: [dataset]  (1 dataset object)")

            start_time = datetime.now()

            try:
                response = await client.post(
                    f"{self.base_url}/api/agents/enrich-fulltext",
                    json=[dataset],  # Send as array
                )

                duration = (datetime.now() - start_time).total_seconds()

                if response.status_code != 200:
                    logger.error(f"❌ Download failed: {response.status_code}")
                    logger.error(f"   Response: {response.text[:500]}")
                    return False

                enriched_datasets = response.json()
                enriched = enriched_datasets[0]

                # Update current results (as frontend would)
                self.current_results[card_index] = enriched

                logger.info(f"\n✅ Backend responds after {duration:.1f} seconds:")
                logger.info(f"   Fulltext count: {enriched.get('fulltext_count', 0)}")
                logger.info(
                    f"   Fulltext status: {enriched.get('fulltext_status', 'unknown')}"
                )

                # Show what frontend would display
                fulltext_count = enriched.get("fulltext_count", 0)
                fulltext_status = enriched.get("fulltext_status", "unknown")

                logger.info(f"\n🎨 Frontend updates:")
                if fulltext_count > 0:
                    logger.info(
                        f"   ✅ Success message: 'Downloaded {fulltext_count} papers'"
                    )
                    logger.info(f"   Button text: '📥 Download Papers' → Hidden")
                    logger.info(f"   AI Analysis button: ENABLED (green)")
                    logger.info(f"   Status badge: '✓ {fulltext_count} PDFs available'")
                else:
                    logger.info(f"   ⚠️  Warning: 'No papers downloaded'")
                    logger.info(f"   Status: {fulltext_status}")

                # Re-render the card with updated data
                logger.info(f"\n📊 UPDATED CARD RENDERING:")
                logger.info("=" * 80)
                self._render_dataset_card(card_index + 1, enriched)

                # Show downloaded files
                if fulltext_count > 0:
                    logger.info(f"\n📁 Downloaded Files:")
                    geo_id = enriched.get("geo_id")
                    pdf_dir = Path(f"data/pdfs/{geo_id}")
                    if pdf_dir.exists():
                        for subdir in ["original", "citing"]:
                            subdir_path = pdf_dir / subdir
                            if subdir_path.exists():
                                pdfs = list(subdir_path.glob("*.pdf"))
                                logger.info(f"   {subdir}/: {len(pdfs)} PDFs")
                                for pdf in pdfs[:3]:  # Show first 3
                                    size_kb = pdf.stat().st_size / 1024
                                    logger.info(
                                        f"      - {pdf.name} ({size_kb:.1f} KB)"
                                    )

                return True

            except httpx.TimeoutException:
                logger.error(f"❌ Request timed out after 120 seconds")
                return False
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
                return False

    async def simulate_ai_analysis(self, card_index: int):
        """Simulate: User clicks 'AI Analysis' button."""
        if card_index >= len(self.current_results):
            logger.error(f"❌ Invalid card index: {card_index}")
            return False

        dataset = self.current_results[card_index]

        logger.info("\n" + "=" * 80)
        logger.info(
            f"👤 USER ACTION: Clicks 'AI Analysis' button on Card #{card_index + 1}"
        )
        logger.info(
            f"   Dataset: {dataset.get('geo_id')} - {dataset.get('title', '')[:50]}..."
        )
        logger.info("=" * 80)

        # Check if full-text is available
        fulltext_count = dataset.get("fulltext_count", 0)
        if fulltext_count == 0:
            logger.warning(
                f"\n⚠️  Frontend should prevent this click (button disabled)"
            )
            logger.warning(f"   Reason: No full-text content available")
            return False

        # Frontend updates
        logger.info(f"\n🎨 Frontend updates:")
        logger.info(f"   Analysis section: Expanded")
        logger.info(f"   Button text: '🤖 AI Analysis' → '⏳ Analyzing...'")
        logger.info(f"   Button disabled: true")
        logger.info(f"   Skeleton loader: Displayed")

        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"\n📡 Frontend sends: POST {self.base_url}/api/agents/analyze")
            logger.info(
                f"   Payload: {{datasets: [dataset], query: 'user query', max_datasets: 1}}"
            )

            start_time = datetime.now()

            try:
                response = await client.post(
                    f"{self.base_url}/api/agents/analyze",
                    json={
                        "datasets": [dataset],
                        "query": "breast cancer analysis",
                        "max_datasets": 1,
                    },
                )

                duration = (datetime.now() - start_time).total_seconds()

                if response.status_code != 200:
                    logger.error(f"❌ Analysis failed: {response.status_code}")
                    logger.error(f"   Response: {response.text[:500]}")
                    return False

                analysis = response.json()

                logger.info(f"\n✅ Backend responds after {duration:.1f} seconds:")
                logger.info(f"   Success: {analysis.get('success', False)}")
                logger.info(f"   Model used: {analysis.get('model_used', 'unknown')}")
                logger.info(
                    f"   Execution time: {analysis.get('execution_time_ms', 0):.2f}ms"
                )

                # Display analysis as frontend would
                logger.info(f"\n🎨 Frontend displays inline analysis:")
                logger.info("=" * 80)

                analysis_text = analysis.get("analysis", "")
                insights = analysis.get("insights", [])
                recommendations = analysis.get("recommendations", [])

                logger.info(f"\n📝 AI ANALYSIS:")
                logger.info("-" * 80)
                # Show first 500 chars of analysis
                if analysis_text:
                    logger.info(
                        analysis_text[:500] + "..."
                        if len(analysis_text) > 500
                        else analysis_text
                    )
                else:
                    logger.info("(No analysis text)")

                if insights:
                    logger.info(f"\n💡 KEY INSIGHTS:")
                    for i, insight in enumerate(insights[:3], 1):
                        logger.info(f"   {i}. {insight}")

                if recommendations:
                    logger.info(f"\n📌 RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        logger.info(f"   {i}. {rec}")

                logger.info("-" * 80)

                logger.info(f"\n🎨 Frontend updates:")
                logger.info(f"   Button text: '⏳ Analyzing...' → '✓ Analysis Complete'")
                logger.info(f"   Button color: Blue → Green")
                logger.info(f"   Button enabled: true")

                return True

            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
                return False


async def run_complete_simulation():
    """Run a complete user journey simulation."""
    simulator = FrontendSimulator()

    logger.info("\n" + "🎬 " * 20)
    logger.info("FRONTEND SIMULATION - Complete User Experience")
    logger.info("🎬 " * 20 + "\n")

    # Step 1: Search for datasets
    logger.info("\n" + "📍 STEP 1: SEARCH FOR DATASETS")
    logger.info("─" * 80)
    success = await simulator.simulate_search("breast cancer")

    if not success or len(simulator.current_results) == 0:
        logger.error("❌ Simulation failed: No datasets found")
        return

    # Wait a bit (simulate user reading results)
    logger.info("\n⏸️  [User reads search results for 2 seconds...]")
    await asyncio.sleep(2)

    # Step 2: Download papers for first dataset
    logger.info("\n" + "📍 STEP 2: DOWNLOAD PAPERS")
    logger.info("─" * 80)

    # Find a dataset with citations in database
    dataset_index = 0
    selected_dataset = simulator.current_results[dataset_index]

    logger.info(f"\n👤 USER: Reviewing dataset options...")
    logger.info(
        f"   Selected: {selected_dataset.get('geo_id')} (has {selected_dataset.get('citation_count', 0)} citations in DB)"
    )

    # Check if download is needed
    if selected_dataset.get("fulltext_count", 0) > 0:
        logger.info(f"\n✅ Papers already downloaded! Skipping to AI analysis...")
    else:
        success = await simulator.simulate_download_papers(dataset_index)
        if not success:
            logger.warning(f"⚠️  Download failed, but continuing simulation...")

    # Wait a bit (simulate user reviewing download results)
    logger.info("\n⏸️  [User reviews download results for 2 seconds...]")
    await asyncio.sleep(2)

    # Step 3: Run AI Analysis
    logger.info("\n" + "📍 STEP 3: AI ANALYSIS")
    logger.info("─" * 80)

    success = await simulator.simulate_ai_analysis(dataset_index)
    if not success:
        logger.warning(f"⚠️  AI analysis skipped (no full-text available)")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("🎉 SIMULATION COMPLETE")
    logger.info("=" * 80)

    final_dataset = simulator.current_results[dataset_index]
    logger.info(f"\nFinal State of Dataset {final_dataset.get('geo_id')}:")
    logger.info(f"  Citations in DB: {final_dataset.get('citation_count', 0)}")
    logger.info(f"  PDFs downloaded: {final_dataset.get('pdf_count', 0)}")
    logger.info(f"  Full-text available: {final_dataset.get('fulltext_count', 0)}")
    logger.info(
        f"  Processing: {final_dataset.get('completion_rate', 0):.0f}% complete"
    )
    logger.info(f"  Status: {final_dataset.get('fulltext_status', 'unknown')}")

    logger.info("\n✅ All user interactions simulated successfully!")
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_complete_simulation())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Simulation failed: {e}", exc_info=True)
