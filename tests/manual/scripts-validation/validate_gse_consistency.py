#!/usr/bin/env python3
"""
GSE ID Consistency Validator

This script validates that GSE IDs match their content by cross-referencing with the NCBI GEO database.
It checks:
1. GSE ID existence in NCBI GEO
2. Title consistency between our data and NCBI GEO
3. Summary/description consistency
4. Organism consistency

Usage:
    python validate_gse_consistency.py --query "cancer" [--max-results 10]
    python validate_gse_consistency.py --gse-id "GSE278726"
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("gse_validation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("gse_validator")


class GSEValidator:
    def __init__(self, base_url="http://localhost:8000", ncbi_api_key=None):
        self.base_url = base_url
        self.ncbi_api_key = ncbi_api_key  # Optional NCBI API key for higher rate limits
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = "validation_reports"
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize session
        self.session = None

        logger.info(f"GSE Validator initialized with base URL: {self.base_url}")

    async def init_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def validate_by_query(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Validate GSE IDs returned from a search query
        """
        await self.init_session()

        logger.info(f"Starting validation for query: '{query}'")

        # Step 1: Get search results from our API
        search_results = await self.get_search_results(query, max_results)

        if not search_results or "results" not in search_results:
            logger.error("No results returned from API")
            return {"error": "No results returned from API"}

        # Step 2: Validate each GSE ID in the results
        validation_results = []

        for i, result in enumerate(search_results["results"]):
            gse_id = result.get("geo_id")
            if not gse_id:
                logger.warning(f"Result {i} missing GSE ID")
                continue

            logger.info(f"Validating GSE ID: {gse_id}")
            validation = await self.validate_gse_id(gse_id, result)
            validation_results.append(validation)

            # Be nice to NCBI API - don't hammer it
            await asyncio.sleep(1)

        # Step 3: Generate report
        report = {
            "query": query,
            "timestamp": self.timestamp,
            "results_count": len(search_results["results"]),
            "validation_results": validation_results,
            "summary": self.generate_validation_summary(validation_results),
        }

        # Save report
        self.save_report(report)

        return report

    async def validate_gse_id(self, gse_id: str, our_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a specific GSE ID against NCBI GEO database
        """
        await self.init_session()

        validation = {
            "gse_id": gse_id,
            "exists_in_geo": False,
            "title_match": False,
            "summary_match": None,  # None = not compared, True/False = match result
            "organism_match": None,
            "issues": [],
            "ncbi_data": None,
            "our_data": our_data,
        }

        # Get data from NCBI GEO
        ncbi_data = await self.fetch_geo_data(gse_id)

        if not ncbi_data or "error" in ncbi_data:
            validation["exists_in_geo"] = False
            validation["issues"].append(f"GSE ID {gse_id} not found in NCBI GEO")
            return validation

        validation["exists_in_geo"] = True
        validation["ncbi_data"] = ncbi_data

        # If we have our data, compare it
        if our_data:
            # Check title
            our_title = our_data.get("title", "").strip().lower()
            ncbi_title = ncbi_data.get("title", "").strip().lower()

            if our_title and ncbi_title:
                # Exact match
                if our_title == ncbi_title:
                    validation["title_match"] = True
                # Contains match (our title is part of NCBI title or vice versa)
                elif our_title in ncbi_title or ncbi_title in our_title:
                    validation["title_match"] = "partial"
                # No match
                else:
                    validation["title_match"] = False
                    validation["issues"].append("Title mismatch")

            # Check summary
            our_summary = our_data.get("summary", "").strip().lower()
            ncbi_summary = ncbi_data.get("summary", "").strip().lower()

            if our_summary and ncbi_summary:
                # Check if summaries are similar enough (at least some overlap)
                words_in_common = set(our_summary.split()) & set(ncbi_summary.split())
                if len(words_in_common) > 10:  # Arbitrary threshold for some overlap
                    validation["summary_match"] = "partial"
                else:
                    validation["summary_match"] = False
                    validation["issues"].append("Summary has little overlap with NCBI data")

            # Check organism
            our_organism = our_data.get("organism", "").strip().lower()
            ncbi_organism = ncbi_data.get("organism", "").strip().lower()

            if our_organism and ncbi_organism:
                if our_organism == ncbi_organism:
                    validation["organism_match"] = True
                elif our_organism in ncbi_organism or ncbi_organism in our_organism:
                    validation["organism_match"] = "partial"
                else:
                    validation["organism_match"] = False
                    validation["issues"].append("Organism mismatch")

        # Overall validation verdict
        if validation["exists_in_geo"]:
            if validation["title_match"] is False or validation["organism_match"] is False:
                validation["verdict"] = "MISMATCH"
            elif validation["issues"]:
                validation["verdict"] = "PARTIAL_MATCH"
            else:
                validation["verdict"] = "MATCH"
        else:
            validation["verdict"] = "NOT_FOUND"

        return validation

    async def get_search_results(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get search results from our API
        """
        try:
            payload = {
                "query": query,
                "max_results": max_results,
                "search_type": "comprehensive",
                "disable_cache": True,
                "timestamp": int(time.time() * 1000),
            }

            logger.info(f"Making API request to {self.base_url}/api/search with payload: {payload}")

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

                return await response.json()

        except Exception as e:
            logger.error(f"Error getting search results: {str(e)}")
            return {"error": str(e)}

    async def fetch_geo_data(self, gse_id: str) -> Dict[str, Any]:
        """
        Fetch data for a GSE ID from NCBI GEO
        """
        try:
            # Option 1: Fetch from NCBI Entrez eUtils API
            entrez_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

            params = {
                "db": "gds",  # GEO DataSets
                "id": gse_id.replace("GSE", ""),  # NCBI wants the ID without the GSE prefix
                "retmode": "json",
                "version": "2.0",
            }

            if self.ncbi_api_key:
                params["api_key"] = self.ncbi_api_key

            logger.info(f"Fetching GSE data from NCBI Entrez for {gse_id}")

            async with self.session.get(entrez_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NCBI Entrez API returned status {response.status}")

                    # Option 2: Try direct GEO API as fallback
                    return await self.fetch_geo_direct(gse_id)

                data = await response.json()

                # Process Entrez response
                if "result" in data:
                    result = data["result"]
                    if gse_id.replace("GSE", "") in result:
                        entry = result[gse_id.replace("GSE", "")]
                        return {
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "organism": "; ".join(entry.get("organism", [])),
                            "entrytype": entry.get("entrytype", ""),
                            "accession": f"GSE{entry.get('accession', '')}",
                        }

                # If parsing fails, try direct GEO API
                return await self.fetch_geo_direct(gse_id)

        except Exception as e:
            logger.error(f"Error fetching GSE data from NCBI Entrez: {str(e)}")

            # Try direct GEO API as fallback
            return await self.fetch_geo_direct(gse_id)

    async def fetch_geo_direct(self, gse_id: str) -> Dict[str, Any]:
        """
        Fetch data directly from GEO (text format)
        """
        try:
            geo_url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

            params = {
                "acc": gse_id,
                "targ": "self",
                "form": "text",
                "view": "brief",
            }

            logger.info(f"Fetching GSE data directly from GEO for {gse_id}")

            async with self.session.get(geo_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"GEO API returned status {response.status}")
                    return {"error": f"GEO API returned status {response.status}"}

                text = await response.text()

                # Parse the text format response
                data = {}

                if "!Series_title" in text:
                    title_line = [line for line in text.split("\n") if line.startswith("!Series_title")][0]
                    data["title"] = title_line.split("=", 1)[1].strip()

                if "!Series_summary" in text:
                    summary_lines = [line for line in text.split("\n") if line.startswith("!Series_summary")]
                    data["summary"] = " ".join([line.split("=", 1)[1].strip() for line in summary_lines])

                if "!Series_organism" in text:
                    organism_line = [
                        line for line in text.split("\n") if line.startswith("!Series_organism")
                    ][0]
                    data["organism"] = organism_line.split("=", 1)[1].strip()

                if "!Series_platform_organism" in text:
                    platform_organism_line = [
                        line for line in text.split("\n") if line.startswith("!Series_platform_organism")
                    ][0]
                    if "organism" not in data:
                        data["organism"] = platform_organism_line.split("=", 1)[1].strip()

                return data

        except Exception as e:
            logger.error(f"Error fetching GSE data directly from GEO: {str(e)}")
            return {"error": str(e)}

    def generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of validation results
        """
        total = len(validation_results)
        existing_in_geo = sum(1 for v in validation_results if v.get("exists_in_geo", False))
        title_matches = sum(1 for v in validation_results if v.get("title_match") is True)
        title_partial = sum(1 for v in validation_results if v.get("title_match") == "partial")
        organism_matches = sum(1 for v in validation_results if v.get("organism_match") is True)
        organism_partial = sum(1 for v in validation_results if v.get("organism_match") == "partial")

        # Count verdicts
        matches = sum(1 for v in validation_results if v.get("verdict") == "MATCH")
        partial_matches = sum(1 for v in validation_results if v.get("verdict") == "PARTIAL_MATCH")
        mismatches = sum(1 for v in validation_results if v.get("verdict") == "MISMATCH")
        not_found = sum(1 for v in validation_results if v.get("verdict") == "NOT_FOUND")

        return {
            "total_validated": total,
            "existing_in_geo": existing_in_geo,
            "not_found_in_geo": total - existing_in_geo,
            "title_exact_matches": title_matches,
            "title_partial_matches": title_partial,
            "organism_exact_matches": organism_matches,
            "organism_partial_matches": organism_partial,
            "complete_matches": matches,
            "partial_matches": partial_matches,
            "mismatches": mismatches,
            "not_found": not_found,
            "accuracy": {
                "overall": matches / total if total > 0 else 0,
                "title": (title_matches + 0.5 * title_partial) / existing_in_geo
                if existing_in_geo > 0
                else 0,
                "organism": (organism_matches + 0.5 * organism_partial) / existing_in_geo
                if existing_in_geo > 0
                else 0,
            },
        }

    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Save validation report to file
        """
        filename = f"{self.output_dir}/validation_{self.timestamp}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Validation report saved to {filename}")

        # Also save a summary file
        summary_filename = f"{self.output_dir}/validation_summary_{self.timestamp}.json"
        summary = {
            "query": report["query"],
            "timestamp": report["timestamp"],
            "results_count": report["results_count"],
            "summary": report["summary"],
            "mismatches": [
                {
                    "gse_id": result["gse_id"],
                    "verdict": result["verdict"],
                    "issues": result["issues"],
                    "our_title": result.get("our_data", {}).get("title", ""),
                    "ncbi_title": result.get("ncbi_data", {}).get("title", ""),
                }
                for result in report["validation_results"]
                if result["verdict"] in ["MISMATCH", "NOT_FOUND"]
            ],
        }

        with open(summary_filename, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Validation summary saved to {summary_filename}")

    def print_summary(self, report: Dict[str, Any]) -> None:
        """
        Print a human-readable summary of validation results
        """
        print("\n" + "=" * 80)
        print(f"GSE ID VALIDATION SUMMARY FOR QUERY: '{report['query']}'")
        print("=" * 80)

        summary = report["summary"]

        print(f"\nTotal datasets validated: {summary['total_validated']}")
        print(
            f"Found in NCBI GEO: {summary['existing_in_geo']} ({summary['existing_in_geo']/summary['total_validated']*100:.1f}%)"
        )
        print(
            f"Not found in NCBI GEO: {summary['not_found_in_geo']} ({summary['not_found_in_geo']/summary['total_validated']*100:.1f}%)"
        )

        if summary["existing_in_geo"] > 0:
            print(f"\nOf datasets found in NCBI GEO:")
            print(
                f"  Title exact matches: {summary['title_exact_matches']} ({summary['title_exact_matches']/summary['existing_in_geo']*100:.1f}%)"
            )
            print(
                f"  Title partial matches: {summary['title_partial_matches']} ({summary['title_partial_matches']/summary['existing_in_geo']*100:.1f}%)"
            )
            print(
                f"  Organism exact matches: {summary['organism_exact_matches']} ({summary['organism_exact_matches']/summary['existing_in_geo']*100:.1f}%)"
            )
            print(
                f"  Organism partial matches: {summary['organism_partial_matches']} ({summary['organism_partial_matches']/summary['existing_in_geo']*100:.1f}%)"
            )

        print(f"\nOverall accuracy: {summary['accuracy']['overall']*100:.1f}%")

        if summary["mismatches"] > 0:
            print(f"\nMISMATCHES DETECTED: {summary['mismatches']}")

            # Show details of mismatches
            print("\nMismatch Details:")
            for i, result in enumerate(
                [r for r in report["validation_results"] if r["verdict"] == "MISMATCH"]
            ):
                print(f"\n{i+1}. GSE ID: {result['gse_id']} - MISMATCH")
                print(f"   Our Title: {result.get('our_data', {}).get('title', 'N/A')}")
                print(f"   NCBI Title: {result.get('ncbi_data', {}).get('title', 'N/A')}")
                print(f"   Issues: {', '.join(result['issues'])}")

        if summary["not_found"] > 0:
            print(f"\nNOT FOUND IN NCBI GEO: {summary['not_found']}")

            # Show GSE IDs not found
            print("\nNot Found GSE IDs:")
            not_found_ids = [r["gse_id"] for r in report["validation_results"] if r["verdict"] == "NOT_FOUND"]
            for i, gse_id in enumerate(not_found_ids):
                print(f"{i+1}. {gse_id}")

        print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="Validate GSE ID consistency")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", help="Search query to validate results for")
    group.add_argument("--gse-id", help="Specific GSE ID to validate")

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results to validate",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL for the API",
    )
    parser.add_argument("--ncbi-api-key", help="NCBI API key for higher rate limits")

    args = parser.parse_args()

    validator = GSEValidator(base_url=args.api_url, ncbi_api_key=args.ncbi_api_key)

    try:
        if args.query:
            logger.info(f"Validating search results for query: {args.query}")
            report = await validator.validate_by_query(args.query, args.max_results)
            validator.print_summary(report)
        elif args.gse_id:
            logger.info(f"Validating specific GSE ID: {args.gse_id}")
            validation = await validator.validate_gse_id(args.gse_id)

            print("\n" + "=" * 80)
            print(f"VALIDATION RESULT FOR GSE ID: {args.gse_id}")
            print("=" * 80)
            print(f"\nExists in NCBI GEO: {validation['exists_in_geo']}")

            if validation["exists_in_geo"]:
                print(f"NCBI Title: {validation.get('ncbi_data', {}).get('title', 'N/A')}")
                print(f"NCBI Organism: {validation.get('ncbi_data', {}).get('organism', 'N/A')}")

            print(f"\nVerdict: {validation['verdict']}")

            if validation["issues"]:
                print(f"Issues: {', '.join(validation['issues'])}")

            print("\n" + "=" * 80)

            # Save single validation result
            filename = f"{validator.output_dir}/validation_single_{args.gse_id}_{validator.timestamp}.json"
            with open(filename, "w") as f:
                json.dump(validation, f, indent=2)

            logger.info(f"Single validation result saved to {filename}")
    finally:
        await validator.close_session()


if __name__ == "__main__":
    asyncio.run(main())
