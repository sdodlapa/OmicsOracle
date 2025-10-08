#!/usr/bin/env python3
"""
GSE278726 Mismatch Test

This script directly tests the GSE278726 ID that has been reported to show incorrect COVID-19 content.
It:
1. Gets the actual data from NCBI GEO (with SSL verification disabled)
2. Gets the data as displayed in our OmicsOracle interface
3. Compares the two to identify mismatches

Usage:
    python test_gse_mismatch.py
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
logger = logging.getLogger("gse_mismatch_test")


class GSEMismatchTester:
    def __init__(self, gse_id="GSE278726", base_url="http://localhost:8001"):
        self.gse_id = gse_id
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = None

    async def init_session(self):
        """Initialize aiohttp session with SSL verification disabled"""
        if self.session is None:
            # Create connector that doesn't verify SSL certificates for NCBI
            connector = aiohttp.TCPConnector(ssl=False)

            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "OmicsOracle-MismatchTester/1.0"},
            )
            logger.warning("Using insecure SSL connection (verification disabled)")

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_from_ncbi(self):
        """Fetch data directly from NCBI GEO"""
        try:
            # First try esearch to get the correct ID
            esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

            esearch_params = {
                "db": "gds",  # GEO DataSets
                "term": self.gse_id,
                "retmode": "json",
            }

            logger.info(f"Searching for GSE ID in NCBI Entrez: {self.gse_id}")

            async with self.session.get(esearch_url, params=esearch_params) as response:
                if response.status != 200:
                    logger.error(f"NCBI Entrez esearch API returned status {response.status}")
                    return {"error": f"NCBI Entrez esearch API returned status {response.status}"}

                search_data = await response.json()

                if "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
                    logger.error(f"No results found for {self.gse_id} in Entrez esearch")
                    return {"error": f"No results found for {self.gse_id} in Entrez"}

                id_list = search_data["esearchresult"]["idlist"]
                if not id_list:
                    logger.error(f"Empty ID list for {self.gse_id} in Entrez esearch")
                    return {"error": f"Empty ID list for {self.gse_id} in Entrez"}

                entrez_id = id_list[0]

            # Now fetch the summary with the correct ID
            entrez_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

            params = {
                "db": "gds",  # GEO DataSets
                "id": entrez_id,
                "retmode": "json",
                "version": "2.0",
            }

            logger.info(f"Fetching GSE data from NCBI Entrez for {self.gse_id} using ID {entrez_id}")

            async with self.session.get(entrez_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NCBI Entrez API returned status {response.status}")
                    return {"error": f"NCBI Entrez API returned status {response.status}"}

                data = await response.json()

                # Process Entrez response
                if "result" in data:
                    result = data["result"]
                    if str(entrez_id) in result:
                        entry = result[str(entrez_id)]
                        return {
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "organism": "; ".join(entry.get("organism", [])),
                            "entrytype": entry.get("entrytype", ""),
                            "accession": entry.get("accession", ""),
                        }

                return {"error": "Could not parse Entrez response"}

        except Exception as e:
            logger.error(f"Error fetching from Entrez: {str(e)}")
            return {"error": str(e)}

    async def search_in_omicsoracle(self):
        """Search for the GSE ID in OmicsOracle"""
        try:
            # First, try to search directly for the GSE ID
            payload = {
                "query": self.gse_id,
                "max_results": 10,
                "search_type": "comprehensive",
                "disable_cache": True,
                "timestamp": int(datetime.now().timestamp() * 1000),
            }

            logger.info(f"Searching for {self.gse_id} in OmicsOracle...")

            async with self.session.post(
                f"{self.base_url}/api/search",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                json=payload,
            ) as response:
                if response.status != 200:
                    logger.error(f"API returned status {response.status}")
                    return {"error": f"API returned status {response.status}"}

                search_results = await response.json()

            # Check if the GSE ID is in the results
            result = None
            for item in search_results.get("results", []):
                if item.get("geo_id") == self.gse_id:
                    result = item
                    break

            if not result:
                logger.warning(f"GSE ID {self.gse_id} not found in search results")

                # Try to search for a keyword that might retrieve this GSE ID
                # Testing if it shows up with COVID-19 content as reported
                logger.info("Trying search with 'COVID-19' to see if this GSE appears...")

                covid_payload = {
                    "query": "COVID-19",
                    "max_results": 20,
                    "search_type": "comprehensive",
                    "disable_cache": True,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                }

                async with self.session.post(
                    f"{self.base_url}/api/search",
                    headers={
                        "Content-Type": "application/json",
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    },
                    json=covid_payload,
                ) as response:
                    if response.status != 200:
                        logger.error(f"API returned status {response.status}")
                        return {"error": f"API returned status {response.status}"}

                    covid_results = await response.json()

                # Check if the GSE ID is in the COVID-19 results
                for item in covid_results.get("results", []):
                    if item.get("geo_id") == self.gse_id:
                        result = item
                        logger.info(f"Found {self.gse_id} in COVID-19 search results!")
                        break

                if not result:
                    logger.warning(f"GSE ID {self.gse_id} not found in COVID-19 search results either")
                    # Try one more general search
                    logger.info("Trying generic search to locate this GSE ID...")

                    generic_payload = {
                        "query": "gene expression",
                        "max_results": 50,
                        "search_type": "comprehensive",
                        "disable_cache": True,
                        "timestamp": int(datetime.now().timestamp() * 1000),
                    }

                    async with self.session.post(
                        f"{self.base_url}/api/search",
                        headers={
                            "Content-Type": "application/json",
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0",
                        },
                        json=generic_payload,
                    ) as response:
                        if response.status != 200:
                            logger.error(f"API returned status {response.status}")
                            return {"error": f"API returned status {response.status}"}

                        generic_results = await response.json()

                    # Check if the GSE ID is in the generic results
                    for item in generic_results.get("results", []):
                        if item.get("geo_id") == self.gse_id:
                            result = item
                            logger.info(f"Found {self.gse_id} in generic search results!")
                            break

            return result or {"error": f"Could not find {self.gse_id} in OmicsOracle search results"}

        except Exception as e:
            logger.error(f"Error searching in OmicsOracle: {str(e)}")
            return {"error": str(e)}

    async def run_test(self):
        """Run the mismatch test"""
        await self.init_session()

        try:
            logger.info(f"Starting GSE mismatch test for {self.gse_id}")

            # Step 1: Get data from NCBI
            ncbi_data = await self.fetch_from_ncbi()

            # Step 2: Get data from OmicsOracle
            our_data = await self.search_in_omicsoracle()

            # Step 3: Compare the data
            results = {
                "gse_id": self.gse_id,
                "timestamp": self.timestamp,
                "ncbi_data": ncbi_data,
                "our_data": our_data,
            }

            # Check for mismatches
            if "error" in ncbi_data:
                results["verdict"] = "NCBI_ERROR"
                results["issues"] = [ncbi_data["error"]]
            elif "error" in our_data:
                results["verdict"] = "OMICSORACLE_ERROR"
                results["issues"] = [our_data["error"]]
            else:
                # Compare titles
                ncbi_title = ncbi_data.get("title", "").lower()
                our_title = our_data.get("title", "").lower()

                # Check for COVID-19 mismatch
                covid_keywords = [
                    "covid",
                    "covid-19",
                    "sars-cov-2",
                    "coronavirus",
                ]
                ncbi_has_covid = any(kw in ncbi_title for kw in covid_keywords)
                our_has_covid = any(kw in our_title for kw in covid_keywords)

                results["ncbi_has_covid_reference"] = ncbi_has_covid
                results["our_has_covid_reference"] = our_has_covid

                issues = []

                if our_has_covid and not ncbi_has_covid:
                    issues.append(
                        "CRITICAL: COVID-19 content mismatch - our data mentions COVID-19 but NCBI data does not"
                    )

                if ncbi_title and our_title and ncbi_title != our_title:
                    issues.append(f"Title mismatch between NCBI and OmicsOracle")

                if issues:
                    results["verdict"] = "MISMATCH"
                    results["issues"] = issues
                else:
                    results["verdict"] = "MATCH"

            # Save results
            with open(f"gse_mismatch_test_{self.gse_id}_{self.timestamp}.json", "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Test results saved to gse_mismatch_test_{self.gse_id}_{self.timestamp}.json")

            # Print summary
            print("\n" + "=" * 80)
            print(f"GSE MISMATCH TEST RESULTS FOR {self.gse_id}")
            print("=" * 80)

            if "error" in ncbi_data:
                print(f"\nNCBI Error: {ncbi_data['error']}")
            else:
                print(f"\nNCBI Title: {ncbi_data.get('title', 'N/A')}")

            if "error" in our_data:
                print(f"\nOmicsOracle Error: {our_data['error']}")
            else:
                print(f"\nOmicsOracle Title: {our_data.get('title', 'N/A')}")

            print(f"\nVerdict: {results.get('verdict', 'UNKNOWN')}")

            if results.get("issues"):
                print(f"Issues: {', '.join(results['issues'])}")

            print("\n" + "=" * 80)

            return results

        finally:
            await self.close_session()


async def main():
    gse_id = "GSE278726"
    if len(sys.argv) > 1:
        gse_id = sys.argv[1]

    tester = GSEMismatchTester(gse_id=gse_id)
    await tester.run_test()


if __name__ == "__main__":
    asyncio.run(main())
