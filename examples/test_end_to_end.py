#!/usr/bin/env python3
"""
End-to-End OmicsOracle Demonstration
This script demonstrates the full workflow from query to response
"""

import json
import time
from datetime import datetime

import requests


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_health_check():
    """Test 1: Health Check"""
    print_section("TEST 1: Health Check")

    try:
        response = requests.get("http://localhost:8000/health/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_search_query():
    """Test 2: Search Publications"""
    print_section("TEST 2: Search Publications - CRISPR Gene Editing")

    query = "CRISPR gene editing in cancer therapy"

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/search",
            json={"query": query, "max_results": 5, "sources": ["pubmed"]},
        )

        print(f"Query: {query}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nResults Found: {}".format(len(data.get("results", []))))

            # Display first 2 results
            for i, result in enumerate(data.get("results", [])[:2], 1):
                print("\n--- Result {} ---".format(i))
                print("Title: {}".format(result.get("title", "N/A")))
                print("Authors: {}".format(", ".join(result.get("authors", [])[:3])))
                print("Journal: {}".format(result.get("journal", "N/A")))
                print("Year: {}".format(result.get("year", "N/A")))
                print("PMID: {}".format(result.get("pmid", "N/A")))
                if result.get("abstract"):
                    abstract = result["abstract"]
                    print("Abstract: {}...".format(abstract[:200]))

            return True
        else:
            print(f"Error Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_biomarker_search():
    """Test 3: Biomarker Search"""
    print_section("TEST 3: Biomarker Search")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/biomarkers/search",
            json={"query": "HER2 breast cancer", "max_results": 3},
        )

        print("Query: HER2 breast cancer")
        print("Status Code: {}".format(response.status_code))

        if response.status_code == 200:
            data = response.json()
            print("\nBiomarkers Found: {}".format(len(data.get("biomarkers", []))))

            for biomarker in data.get("biomarkers", [])[:3]:
                print("\n- {}".format(biomarker.get("name", "N/A")))
                print("  Type: {}".format(biomarker.get("type", "N/A")))
                print("  Relevance: {:.2f}".format(biomarker.get("relevance_score", 0)))

            return True
        else:
            print(f"Error Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_trend_analysis():
    """Test 4: Research Trend Analysis"""
    print_section("TEST 4: Research Trend Analysis")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/trends/analyze",
            json={"query": "immunotherapy", "time_period": "5y"},
        )

        print("Query: immunotherapy (last 5 years)")
        print("Status Code: {}".format(response.status_code))

        if response.status_code == 200:
            data = response.json()
            print("\nTrend Analysis:")
            print("- Period: {}".format(data.get("period", "N/A")))
            print("- Growth Rate: {:.1f}%".format(data.get("growth_rate", 0)))
            print("- Total Publications: {}".format(data.get("total_publications", 0)))

            if "yearly_counts" in data:
                print("\nYearly Distribution:")
                for year, count in list(data["yearly_counts"].items())[:5]:
                    print("  {}: {} publications".format(year, count))

            return True
        else:
            print(f"Error Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_citation_prediction():
    """Test 5: Citation Impact Prediction"""
    print_section("TEST 5: Citation Impact Prediction")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/citations/predict",
            json={
                "title": "CRISPR-Cas9 for cancer immunotherapy",
                "abstract": "Novel approach using CRISPR gene editing to enhance T-cell response",
                "authors": ["Smith J", "Johnson A"],
                "year": 2024,
                "journal": "Nature Medicine",
            },
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nPredicted Impact:")
            msg = "- Estimated Citations (1 year): {}"
            print(msg.format(data.get("predicted_citations_1y", 0)))
            msg = "- Estimated Citations (3 years): {}"
            print(msg.format(data.get("predicted_citations_3y", 0)))
            print("- Impact Score: {:.2f}".format(data.get("impact_score", 0)))
            print("- Confidence: {:.2f}".format(data.get("confidence", 0)))

            return True
        else:
            print(f"Error Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Run all end-to-end tests"""
    print("\n" + "=" * 70)
    print("  OMICS ORACLE - END-TO-END DEMONSTRATION")
    print("  Testing Full Workflow: Query > Processing > Response")
    print("=" * 70)
    print(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Server: http://localhost:8000")

    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    for i in range(10):
        try:
            requests.get("http://localhost:8000/health/", timeout=1)
            print("[OK] Server is ready!")
            break
        except Exception:
            time.sleep(1)
            print("  Attempt {}/10...".format(i + 1))
    else:
        print("\n[ERROR] Server did not start in time. Please start manually:")
        print("  ./scripts/start.sh --mode dev")
        return

    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("Publication Search", test_search_query),
        ("Biomarker Search", test_biomarker_search),
        ("Trend Analysis", test_trend_analysis),
        ("Citation Prediction", test_citation_prediction),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            print("\n[ERROR] {} failed: {}".format(test_name, e))
            results.append((test_name, False))

    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n[SUCCESS] All tests passed! OmicsOracle is working end-to-end.")
    else:
        print(f"\n[WARNING] {total-passed} test(s) failed. Check logs for details.")

    print("\n" + "=" * 70)
    print("  END-TO-END DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
