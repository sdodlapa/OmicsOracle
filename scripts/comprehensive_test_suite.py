"""
Comprehensive test and validation suite for OmicsOracle integrations.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, List

import pytest

from omics_oracle.integrations.citation_managers import CitationManagerIntegration
from omics_oracle.integrations.pubmed import PubMedIntegration
from omics_oracle.integrations.service import IntegrationService


class IntegrationTestSuite:
    """Comprehensive test suite for all integrations."""

    def __init__(self):
        self.results: Dict[str, Any] = {
            "unit_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "validation_tests": {},
            "summary": {},
        }
        self.start_time = time.time()

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        print("🧪 COMPREHENSIVE INTEGRATION TESTING")
        print("=" * 50)

        # Run test categories
        await self.run_unit_tests()
        await self.run_integration_tests()
        await self.run_performance_tests()
        await self.run_validation_tests()

        # Generate summary
        self.generate_summary()

        return self.results

    async def run_unit_tests(self) -> None:
        """Run unit tests for all integration components."""
        print("\n📋 1. UNIT TESTS")
        print("-" * 20)

        # Citation Manager Tests
        print("  Testing Citation Manager...")
        citation_results = await self._test_citation_manager()
        self.results["unit_tests"]["citation_manager"] = citation_results

        # PubMed Integration Tests
        print("  Testing PubMed Integration...")
        pubmed_results = await self._test_pubmed_integration()
        self.results["unit_tests"]["pubmed_integration"] = pubmed_results

        # Integration Service Tests
        print("  Testing Integration Service...")
        service_results = await self._test_integration_service()
        self.results["unit_tests"]["integration_service"] = service_results

    async def run_integration_tests(self) -> None:
        """Run integration tests with real APIs."""
        print("\n🌐 2. INTEGRATION TESTS")
        print("-" * 25)

        # Live PubMed API test
        print("  Testing Live PubMed API...")
        live_api_results = await self._test_live_pubmed_api()
        self.results["integration_tests"]["live_pubmed_api"] = live_api_results

        # End-to-end workflow test
        print("  Testing End-to-End Workflow...")
        e2e_results = await self._test_end_to_end_workflow()
        self.results["integration_tests"]["end_to_end"] = e2e_results

        # File export test
        print("  Testing File Export...")
        export_results = await self._test_file_export()
        self.results["integration_tests"]["file_export"] = export_results

    async def run_performance_tests(self) -> None:
        """Run performance benchmarks."""
        print("\n⚡ 3. PERFORMANCE TESTS")
        print("-" * 24)

        # Citation generation speed
        print("  Testing Citation Generation Speed...")
        citation_perf = await self._test_citation_performance()
        self.results["performance_tests"]["citation_generation"] = citation_perf

        # Batch processing performance
        print("  Testing Batch Processing...")
        batch_perf = await self._test_batch_performance()
        self.results["performance_tests"]["batch_processing"] = batch_perf

        # Memory usage test
        print("  Testing Memory Usage...")
        memory_perf = await self._test_memory_usage()
        self.results["performance_tests"]["memory_usage"] = memory_perf

    async def run_validation_tests(self) -> None:
        """Run data validation tests."""
        print("\n✅ 4. VALIDATION TESTS")
        print("-" * 21)

        # Citation format validation
        print("  Validating Citation Formats...")
        format_results = await self._test_citation_formats()
        self.results["validation_tests"]["citation_formats"] = format_results

        # Data integrity validation
        print("  Validating Data Integrity...")
        integrity_results = await self._test_data_integrity()
        self.results["validation_tests"]["data_integrity"] = integrity_results

        # Error handling validation
        print("  Validating Error Handling...")
        error_results = await self._test_error_handling()
        self.results["validation_tests"]["error_handling"] = error_results

    # Unit Test Methods
    async def _test_citation_manager(self) -> Dict[str, Any]:
        """Test citation manager functionality."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            citation_manager = CitationManagerIntegration()

            # Test reference formatting
            mock_data = {
                "accession": "GSE12345",
                "title": "Test Dataset",
                "summary": "Test summary",
                "submission_date": "2023-01-01",
            }

            reference = citation_manager.format_geo_reference(mock_data)
            assert reference["title"] == "Test Dataset"
            results["passed"] += 1
            results["details"].append("✅ Reference formatting")

            # Test BibTeX generation
            bibtex = citation_manager.to_bibtex(reference)
            assert "@misc{GSE12345," in bibtex
            results["passed"] += 1
            results["details"].append("✅ BibTeX generation")

            # Test RIS generation
            ris = citation_manager.to_ris(reference)
            assert "TY  - DATA" in ris
            results["passed"] += 1
            results["details"].append("✅ RIS generation")

            # Test CSL-JSON generation
            csl_json = citation_manager.to_csl_json(reference)
            data = json.loads(csl_json)
            assert len(data) == 1
            results["passed"] += 1
            results["details"].append("✅ CSL-JSON generation")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Error: {e}")

        return results

    async def _test_pubmed_integration(self) -> Dict[str, Any]:
        """Test PubMed integration functionality."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            # Test initialization
            pubmed = PubMedIntegration(email="test@example.com")
            assert pubmed.email == "test@example.com"
            results["passed"] += 1
            results["details"].append("✅ Initialization")

            # Test parameter building
            params = pubmed._build_params(db="pubmed", term="test")
            assert params["tool"] == "OmicsOracle"
            assert params["email"] == "test@example.com"
            results["passed"] += 1
            results["details"].append("✅ Parameter building")

            # Test XML parsing (mock data)
            mock_xml = """<PubmedArticle>
                <MedlineCitation>
                    <PMID>12345</PMID>
                    <Article>
                        <ArticleTitle>Test Title</ArticleTitle>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>"""

            import xml.etree.ElementTree as ET

            element = ET.fromstring(mock_xml)
            paper_info = pubmed._extract_paper_info(element)
            assert paper_info["pmid"] == "12345"
            results["passed"] += 1
            results["details"].append("✅ XML parsing")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Error: {e}")

        return results

    async def _test_integration_service(self) -> Dict[str, Any]:
        """Test integration service functionality."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            service = IntegrationService()

            # Test citation export without network calls
            mock_datasets = [
                {
                    "accession": "GSE12345",
                    "title": "Test Dataset",
                    "summary": "Test summary",
                    "submission_date": "2023-01-01",
                }
            ]

            citations = service.export_citations(mock_datasets, "bibtex", include_papers=False)
            assert "@misc{GSE12345," in citations
            results["passed"] += 1
            results["details"].append("✅ Citation export")

            # Test different formats
            ris_citations = service.export_citations(mock_datasets, "ris", include_papers=False)
            assert "TY  - DATA" in ris_citations
            results["passed"] += 1
            results["details"].append("✅ Multi-format export")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Error: {e}")

        return results

    # Integration Test Methods
    async def _test_live_pubmed_api(self) -> Dict[str, Any]:
        """Test live PubMed API calls."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            async with PubMedIntegration() as pubmed:
                # Test search with timeout
                papers = await asyncio.wait_for(
                    pubmed.search_papers("GSE30611", max_results=2),
                    timeout=15.0,
                )

                if papers:
                    results["passed"] += 1
                    results["details"].append(f"✅ Search successful: {len(papers)} papers")

                    # Test paper details
                    details = await asyncio.wait_for(pubmed.fetch_paper_details(papers[:1]), timeout=15.0)

                    if details and details[0].get("title"):
                        results["passed"] += 1
                        results["details"].append("✅ Paper details fetched")
                    else:
                        results["failed"] += 1
                        results["details"].append("❌ No paper details")
                else:
                    results["failed"] += 1
                    results["details"].append("❌ No papers found")

        except asyncio.TimeoutError:
            results["failed"] += 1
            results["details"].append("❌ API call timed out")
        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ API error: {e}")

        return results

    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            service = IntegrationService()

            # Mock dataset
            mock_dataset = {
                "accession": "GSE30611",
                "title": "RNA-seq analysis",
                "summary": "Test RNA sequencing data",
                "submission_date": "2023-01-01",
            }

            # Test enrichment (without live API for speed)
            enriched = await service.enrich_geo_dataset(
                mock_dataset,
                include_papers=False,  # Skip live API for testing
                max_papers=1,
            )

            assert "citation_info" in enriched
            results["passed"] += 1
            results["details"].append("✅ Dataset enrichment")

            # Test batch processing
            enriched_batch = await service.batch_enrich_datasets(
                [mock_dataset], include_papers=False, max_papers=1
            )

            assert len(enriched_batch) == 1
            results["passed"] += 1
            results["details"].append("✅ Batch processing")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Workflow error: {e}")

        return results

    async def _test_file_export(self) -> Dict[str, Any]:
        """Test file export functionality."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            service = IntegrationService()
            mock_datasets = [
                {
                    "accession": "GSE12345",
                    "title": "Test Dataset",
                    "summary": "Test summary",
                    "submission_date": "2023-01-01",
                }
            ]

            # Test various export formats
            formats = ["bibtex", "ris", "csl-json", "endnote"]

            for fmt in formats:
                citations = service.export_citations(mock_datasets, fmt, include_papers=False)
                assert len(citations) > 0

                # Test file writing
                with tempfile.NamedTemporaryFile(mode="w", suffix=f".{fmt}", delete=False) as f:
                    f.write(citations)
                    temp_path = f.name

                # Verify file was written
                with open(temp_path, "r") as f:
                    content = f.read()
                    assert len(content) > 0

                os.unlink(temp_path)  # Clean up
                results["passed"] += 1
                results["details"].append(f"✅ {fmt.upper()} export")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Export error: {e}")

        return results

    # Performance Test Methods
    async def _test_citation_performance(self) -> Dict[str, Any]:
        """Test citation generation performance."""
        results = {"passed": 0, "failed": 0, "details": [], "metrics": {}}

        try:
            citation_manager = CitationManagerIntegration()
            mock_data = {
                "accession": "GSE12345",
                "title": "Test Dataset",
                "summary": "Test summary",
                "submission_date": "2023-01-01",
            }

            # Test single citation speed
            start_time = time.time()
            reference = citation_manager.format_geo_reference(mock_data)
            bibtex = citation_manager.to_bibtex(reference)
            single_time = time.time() - start_time

            results["metrics"]["single_citation_time"] = single_time

            if single_time < 0.1:  # Should be under 100ms
                results["passed"] += 1
                results["details"].append(f"✅ Single citation: {single_time:.3f}s")
            else:
                results["failed"] += 1
                results["details"].append(f"❌ Single citation too slow: {single_time:.3f}s")

            # Test bulk citation speed
            datasets = [mock_data] * 50
            start_time = time.time()

            for dataset in datasets:
                ref = citation_manager.format_geo_reference(dataset)
                citation_manager.to_bibtex(ref)

            bulk_time = time.time() - start_time
            avg_time = bulk_time / 50

            results["metrics"]["bulk_citation_time"] = bulk_time
            results["metrics"]["average_citation_time"] = avg_time

            if avg_time < 0.05:  # Should be under 50ms average
                results["passed"] += 1
                results["details"].append(f"✅ Bulk citations: {avg_time:.3f}s avg")
            else:
                results["failed"] += 1
                results["details"].append(f"❌ Bulk citations too slow: {avg_time:.3f}s avg")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Performance error: {e}")

        return results

    async def _test_batch_performance(self) -> Dict[str, Any]:
        """Test batch processing performance."""
        results = {"passed": 0, "failed": 0, "details": [], "metrics": {}}

        try:
            service = IntegrationService()

            # Create batch of mock datasets
            mock_datasets = []
            for i in range(20):
                mock_datasets.append(
                    {
                        "accession": f"GSE{12345 + i}",
                        "title": f"Test Dataset {i}",
                        "summary": f"Test summary {i}",
                        "submission_date": "2023-01-01",
                    }
                )

            # Test batch enrichment (without live API)
            start_time = time.time()
            enriched = await service.batch_enrich_datasets(mock_datasets, include_papers=False, max_papers=0)
            batch_time = time.time() - start_time

            results["metrics"]["batch_processing_time"] = batch_time
            results["metrics"]["datasets_processed"] = len(enriched)

            if batch_time < 5.0 and len(enriched) == 20:  # Should complete in under 5 seconds
                results["passed"] += 1
                results["details"].append(
                    f"✅ Batch processing: {batch_time:.2f}s for {len(enriched)} datasets"
                )
            else:
                results["failed"] += 1
                results["details"].append(f"❌ Batch processing too slow: {batch_time:.2f}s")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Batch error: {e}")

        return results

    async def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage patterns."""
        results = {"passed": 0, "failed": 0, "details": [], "metrics": {}}

        try:
            import gc

            import psutil

            # Get initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create large batch
            service = IntegrationService()
            large_datasets = []
            for i in range(100):
                large_datasets.append(
                    {
                        "accession": f"GSE{10000 + i}",
                        "title": f"Large Dataset {i}" * 10,  # Make title longer
                        "summary": f"Large summary {i}" * 50,  # Make summary much longer
                        "submission_date": "2023-01-01",
                    }
                )

            # Process large batch
            enriched = await service.batch_enrich_datasets(large_datasets, include_papers=False, max_papers=0)

            # Get peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = peak_memory - initial_memory

            # Clean up
            del enriched, large_datasets
            gc.collect()

            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_freed = peak_memory - final_memory

            results["metrics"]["initial_memory_mb"] = initial_memory
            results["metrics"]["peak_memory_mb"] = peak_memory
            results["metrics"]["memory_used_mb"] = memory_used
            results["metrics"]["memory_freed_mb"] = memory_freed

            if memory_used < 100:  # Should use less than 100MB for 100 datasets
                results["passed"] += 1
                results["details"].append(f"✅ Memory usage: {memory_used:.1f}MB")
            else:
                results["failed"] += 1
                results["details"].append(f"❌ Memory usage too high: {memory_used:.1f}MB")

        except ImportError:
            results["failed"] += 1
            results["details"].append("❌ psutil not available for memory testing")
        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Memory test error: {e}")

        return results

    # Validation Test Methods
    async def _test_citation_formats(self) -> Dict[str, Any]:
        """Test citation format validity."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            citation_manager = CitationManagerIntegration()
            mock_data = {
                "accession": "GSE12345",
                "title": "Test Dataset with Special Characters: <>&\"'",
                "summary": "Summary with unicode: αβγ and special chars: <>&\"'",
                "submission_date": "2023-01-01",
            }

            reference = citation_manager.format_geo_reference(mock_data)

            # Test BibTeX format
            bibtex = citation_manager.to_bibtex(reference)
            # Basic BibTeX validation
            assert bibtex.startswith("@misc{")
            assert bibtex.endswith("}")
            assert "title = {" in bibtex
            results["passed"] += 1
            results["details"].append("✅ BibTeX format valid")

            # Test RIS format
            ris = citation_manager.to_ris(reference)
            assert ris.startswith("TY  - DATA")
            assert ris.endswith("ER  - ")
            assert "TI  -" in ris
            results["passed"] += 1
            results["details"].append("✅ RIS format valid")

            # Test CSL-JSON format
            csl_json = citation_manager.to_csl_json(reference)
            data = json.loads(csl_json)  # Should not raise exception
            assert isinstance(data, list)
            assert len(data) == 1
            results["passed"] += 1
            results["details"].append("✅ CSL-JSON format valid")

            # Test EndNote XML format
            endnote_xml = citation_manager.to_endnote_xml(reference)
            assert endnote_xml.startswith("<?xml")
            assert "<xml>" in endnote_xml
            assert "</xml>" in endnote_xml
            results["passed"] += 1
            results["details"].append("✅ EndNote XML format valid")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Format validation error: {e}")

        return results

    async def _test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and accuracy."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            citation_manager = CitationManagerIntegration()

            # Test data preservation
            original_data = {
                "accession": "GSE12345",
                "title": "Original Title",
                "summary": "Original Summary",
                "submission_date": "2023-01-01",
            }

            reference = citation_manager.format_geo_reference(original_data)

            # Verify key data is preserved
            assert reference["title"] == original_data["title"]
            assert reference["note"] == f"GEO accession: {original_data['accession']}"
            assert reference["abstract"] == original_data["summary"]
            results["passed"] += 1
            results["details"].append("✅ Data preservation")

            # Test date handling
            bibtex = citation_manager.to_bibtex(reference)
            assert "year = {2023}" in bibtex
            results["passed"] += 1
            results["details"].append("✅ Date handling")

            # Test URL generation
            assert (
                reference["URL"]
                == f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={original_data['accession']}"
            )
            results["passed"] += 1
            results["details"].append("✅ URL generation")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Data integrity error: {e}")

        return results

    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling scenarios."""
        results = {"passed": 0, "failed": 0, "details": []}

        try:
            citation_manager = CitationManagerIntegration()

            # Test with minimal data
            minimal_data = {"accession": "GSE12345"}
            reference = citation_manager.format_geo_reference(minimal_data)
            assert reference["title"] == "Untitled Dataset"
            results["passed"] += 1
            results["details"].append("✅ Minimal data handling")

            # Test with invalid date
            invalid_date_data = {
                "accession": "GSE12345",
                "title": "Test",
                "submission_date": "invalid-date",
            }
            reference = citation_manager.format_geo_reference(invalid_date_data)
            # Should not crash
            results["passed"] += 1
            results["details"].append("✅ Invalid date handling")

            # Test empty dataset list
            empty_citations = citation_manager.export_references([], "bibtex")
            assert empty_citations == ""
            results["passed"] += 1
            results["details"].append("✅ Empty dataset handling")

            # Test unsupported format
            citation_manager.export_references([minimal_data], "unsupported_format")
            # Should not crash (logs warning)
            results["passed"] += 1
            results["details"].append("✅ Unsupported format handling")

        except Exception as e:
            results["failed"] += 1
            results["details"].append(f"❌ Error handling test failed: {e}")

        return results

    def generate_summary(self) -> None:
        """Generate test summary."""
        total_time = time.time() - self.start_time

        # Count totals
        total_passed = 0
        total_failed = 0

        for category in [
            "unit_tests",
            "integration_tests",
            "performance_tests",
            "validation_tests",
        ]:
            for test_name, test_results in self.results[category].items():
                if isinstance(test_results, dict) and "passed" in test_results:
                    total_passed += test_results["passed"]
                    total_failed += test_results["failed"]

        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": success_rate,
            "total_time_seconds": total_time,
            "status": "PASSED" if total_failed == 0 else "FAILED",
        }

        print(f"\n🎯 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Status: {'✅ PASSED' if total_failed == 0 else '❌ FAILED'}")


async def main():
    """Run the comprehensive test suite."""
    suite = IntegrationTestSuite()
    results = await suite.run_all_tests()

    # Save results to file
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Detailed results saved to: integration_test_results.json")

    # Return exit code based on results
    return 0 if results["summary"]["status"] == "PASSED" else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
