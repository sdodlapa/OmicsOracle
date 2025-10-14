#!/usr/bin/env python3
"""
Quick PMID Investigation

Check if PMID 40375322 exists and is accessible
"""

import json

import requests


def check_pubmed(pmid):
    """Check if PMID exists in PubMed"""
    print(f"\n{'='*80}")
    print(f"🔍 Checking PMID {pmid} in PubMed")
    print(f"{'='*80}\n")

    # Try PubMed E-utilities
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "result" in data and pmid in data["result"]:
            info = data["result"][pmid]
            print("✅ PMID EXISTS in PubMed:")
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Authors: {', '.join([a.get('name', '') for a in info.get('authors', [])[:3]])}...")
            print(f"   Journal: {info.get('fulljournalname', 'N/A')}")
            print(f"   PubDate: {info.get('pubdate', 'N/A')}")
            print(f"   DOI: {[aid for aid in info.get('articleids', []) if aid.get('idtype') == 'doi']}")

            # Check for PMC ID
            pmc_ids = [aid.get("value") for aid in info.get("articleids", []) if aid.get("idtype") == "pmc"]
            if pmc_ids:
                print(f"   ✅ PMC ID: {pmc_ids[0]} (Available in PubMed Central!)")
            else:
                print(f"   ❌ No PMC ID (Not in PubMed Central)")

            return True, info
        else:
            print(f"❌ PMID {pmid} NOT FOUND in PubMed")
            print("   This PMID may not exist, be invalid, or be too new")
            return False, None

    except Exception as e:
        print(f"❌ Error checking PubMed: {e}")
        return False, None


def check_pmc(pmid):
    """Check if paper is available in PubMed Central"""
    print(f"\n{'='*80}")
    print(f"🔍 Checking PMC Availability for PMID {pmid}")
    print(f"{'='*80}\n")

    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "records" in data and len(data["records"]) > 0:
            record = data["records"][0]

            if "pmcid" in record:
                pmcid = record["pmcid"]
                print(f"✅ Available in PMC: {pmcid}")
                print(f"   PDF URL: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/")
                return True, pmcid
            else:
                print("❌ Not available in PMC (behind paywall)")
                return False, None
        else:
            print("❌ Not found in PMC")
            return False, None

    except Exception as e:
        print(f"❌ Error checking PMC: {e}")
        return False, None


def check_unpaywall(doi):
    """Check if paper is available through Unpaywall"""
    if not doi:
        print("\n❌ No DOI available - cannot check Unpaywall")
        return False, None

    print(f"\n{'='*80}")
    print(f"🔍 Checking Unpaywall for DOI: {doi}")
    print(f"{'='*80}\n")

    # Unpaywall requires an email
    url = f"https://api.unpaywall.org/v2/{doi}?email=test@example.com"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            is_oa = data.get("is_oa", False)
            best_oa = data.get("best_oa_location")

            if is_oa and best_oa:
                print(f"✅ Open Access Available!")
                print(f"   URL: {best_oa.get('url_for_pdf') or best_oa.get('url')}")
                print(f"   Version: {best_oa.get('version')}")
                print(f"   License: {best_oa.get('license')}")
                return True, best_oa.get("url_for_pdf") or best_oa.get("url")
            else:
                print("❌ Not Open Access (behind paywall)")
                return False, None
        else:
            print(f"❌ Not found in Unpaywall (status: {response.status_code})")
            return False, None

    except Exception as e:
        print(f"❌ Error checking Unpaywall: {e}")
        return False, None


def main():
    pmid = "40375322"

    print("\n" + "=" * 80)
    print("🔬 PMID Investigation Tool")
    print("=" * 80)
    print(f"\nInvestigating: PMID {pmid}")
    print("This will check multiple sources to determine availability\n")

    # Step 1: Check PubMed
    pubmed_exists, pubmed_info = check_pubmed(pmid)

    if not pubmed_exists:
        print("\n" + "=" * 80)
        print("❌ DIAGNOSIS: PMID does not exist in PubMed")
        print("=" * 80)
        print("\nPossible reasons:")
        print("1. PMID is incorrect or typo")
        print("2. PMID is too new (not yet indexed)")
        print("3. PMID was retracted or removed")
        print("\nRecommendation: Verify the PMID is correct")
        return

    # Step 2: Check PMC
    pmc_available, pmcid = check_pmc(pmid)

    # Step 3: Get DOI and check Unpaywall
    doi = None
    if pubmed_info:
        doi_list = [
            aid.get("value") for aid in pubmed_info.get("articleids", []) if aid.get("idtype") == "doi"
        ]
        if doi_list:
            doi = doi_list[0]

    unpaywall_available, unpaywall_url = check_unpaywall(doi)

    # Final Diagnosis
    print("\n" + "=" * 80)
    print("📊 FINAL DIAGNOSIS")
    print("=" * 80 + "\n")

    if pmc_available:
        print("✅ GOOD NEWS: Paper is available in PubMed Central")
        print(f"   PMC ID: {pmcid}")
        print(f"   PDF URL: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/")
        print("\n   OmicsOracle SHOULD be able to download this!")
        print("   If it failed, there may be a temporary network issue.")

    elif unpaywall_available:
        print("✅ GOOD NEWS: Paper is Open Access via Unpaywall")
        print(f"   URL: {unpaywall_url}")
        print("\n   OmicsOracle SHOULD be able to download this!")

    else:
        print("❌ BAD NEWS: Paper is behind a paywall")
        print("\n   Checked sources:")
        print("   • PubMed Central: ❌ Not available")
        print("   • Unpaywall: ❌ Not Open Access")
        print("\n   This means:")
        print("   1. Paper requires institutional subscription")
        print("   2. Only accessible through paid journal access")
        print("   3. No free version available publicly")
        print("\n   Recommendations:")
        print("   1. Check if your institution has access")
        print("   2. Contact authors for a preprint copy")
        print("   3. Use GEO metadata for analysis instead")
        print("   4. Look for alternative papers on the same topic")

    print("\n" + "=" * 80)
    print("Investigation complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
