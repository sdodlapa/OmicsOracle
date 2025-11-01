#!/usr/bin/env python3
"""
Direct GSE ID Content Check

This script checks if a specific GSE ID (GSE278726) appears in OmicsOracle search results,
and if so, whether it displays content related to COVID-19 despite actually being a
cardiovascular disease study according to NCBI GEO.

This script directly calls the OmicsOracle API and compares the results.
"""

import asyncio
import json
import logging
import ssl
import sys
from datetime import datetime

import aiohttp
import certifi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gse_direct_check")


async def check_gse_content():
    # Create SSL context with proper certificate validation
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Create connector with SSL context
    connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for local testing

    # Create session with timeout and SSL-enabled connector
    timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for potentially slow responses

    base_url = "http://localhost:8001"  # Use port 8001 as confirmed working
    gse_id = "GSE278726"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Queries to try (direct GSE ID and related terms)
    queries = [
        gse_id,  # Direct GSE ID
        f"{gse_id} cardiovascular",  # Actual topic
        "SMAD2 mutations iPSCs cardiovascular",  # Related to actual content
        "COVID-19 cardiac",  # Testing if mismatched content shows up
        "COVID-19",  # General COVID query
    ]

    results = {
        "timestamp": timestamp,
        "gse_id": gse_id,
        "queries": {},
        "conclusion": "No data found",
    }

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            logger.info(f"Testing direct GSE search for {gse_id}")

            for query in queries:
                logger.info(f"Trying query: '{query}'")

                # Make API request
                payload = {
                    "query": query,
                    "max_results": 20,
                    "search_type": "comprehensive",
                    "disable_cache": True,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                }

                try:
                    async with session.post(
                        f"{base_url}/api/search",
                        headers={
                            "Content-Type": "application/json",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0",
                        },
                        json=payload,
                        timeout=45,  # Specific timeout for this request
                    ) as response:
                        if response.status != 200:
                            logger.error(f"API returned status {response.status}")
                            results["queries"][query] = {"error": f"API returned status {response.status}"}
                            continue

                        data = await response.json()

                        # Look for our target GSE ID in results
                        found = False
                        for result in data.get("results", []):
                            if result.get("geo_id") == gse_id:
                                found = True

                                # Record this result
                                results["queries"][query] = {
                                    "found": True,
                                    "title": result.get("title", "No title"),
                                    "summary": result.get("summary", "No summary"),
                                    "organism": result.get("organism", "No organism"),
                                    "has_covid_terms": any(
                                        term in (result.get("title", "") + result.get("summary", "")).lower()
                                        for term in [
                                            "covid",
                                            "covid-19",
                                            "sars-cov-2",
                                            "coronavirus",
                                        ]
                                    ),
                                }

                                # Log what we found
                                logger.info(f"Found {gse_id} in results for query '{query}'")
                                logger.info(f"Title: {result.get('title', 'No title')}")

                                # Check for COVID-19 terms
                                if results["queries"][query]["has_covid_terms"]:
                                    logger.warning(f"COVID-19 terms found in result for {gse_id}!")
                                break

                        if not found:
                            results["queries"][query] = {
                                "found": False,
                                "total_results": len(data.get("results", [])),
                                "first_result_title": data.get("results", [{}])[0].get("title", "No results")
                                if data.get("results")
                                else "No results",
                            }
                            logger.info(f"Did not find {gse_id} in results for query '{query}'")

                except asyncio.TimeoutError:
                    logger.error(f"Request timeout for query '{query}'")
                    results["queries"][query] = {"error": "Request timeout"}
                except Exception as e:
                    logger.error(f"Error for query '{query}': {str(e)}")
                    results["queries"][query] = {"error": str(e)}

            # Analyze results
            mismatch_detected = False
            found_in_any_query = False
            covid_terms_detected = False

            for query, query_result in results["queries"].items():
                if query_result.get("found", False):
                    found_in_any_query = True
                    if query_result.get("has_covid_terms", False):
                        covid_terms_detected = True

            if found_in_any_query and covid_terms_detected:
                results[
                    "conclusion"
                ] = "CRITICAL ISSUE: GSE278726 shows COVID-19 content despite being a cardiovascular study"
                mismatch_detected = True
            elif found_in_any_query:
                results["conclusion"] = "No issue detected: GSE278726 content appears correct"
            else:
                results["conclusion"] = "GSE278726 not found in any search results"

            # Save detailed results
            filename = f"gse_direct_check_{gse_id}_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Results saved to {filename}")

            # Display conclusion
            print("\n" + "=" * 80)
            print(f"GSE CONTENT CHECK RESULTS FOR {gse_id}")
            print("=" * 80)

            print(f"\nConclusion: {results['conclusion']}")

            if found_in_any_query:
                # Show the title from the most direct query
                if gse_id in results["queries"] and results["queries"][gse_id].get("found", False):
                    print(f"\nTitle in OmicsOracle: {results['queries'][gse_id]['title']}")
                    print(f"Has COVID-19 terms: {results['queries'][gse_id]['has_covid_terms']}")

                if mismatch_detected:
                    print("\nWARNING: Content mismatch detected!")
                    print("Expected: Cardiovascular disease study (SMAD2 mutations)")
                    print("Found: Content with COVID-19 terms")

            print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        results["error"] = str(e)
        results["conclusion"] = f"Error during testing: {str(e)}"

        # Save error results
        filename = f"gse_direct_check_{gse_id}_{timestamp}_error.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 80)
        print(f"ERROR CHECKING GSE CONTENT FOR {gse_id}")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(check_gse_content())
