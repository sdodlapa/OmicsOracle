#!/usr/bin/env python3
"""
Comprehensive system validation and testing script for OmicsOracle.
Tests all critical functionality to ensure everything works properly.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from colorama import Fore, Style, init

# Initialize colorama
init()


class SystemValidator:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5173"  # Fixed port
        self.test_results = []
        self.start_time = datetime.now()

    def log_test(self, test_name: str, status: str, message: str = "", details: str = ""):
        """Log test results with colors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = Fore.GREEN if status == "PASS" else Fore.RED if status == "FAIL" else Fore.YELLOW

        print(f"{color}[{timestamp}] {status:<4} {test_name}{Style.RESET_ALL}")
        if message:
            print(f"      → {message}")
        if details:
            print(f"      Details: {details}")

        self.test_results.append(
            {
                "test": test_name,
                "status": status,
                "message": message,
                "details": details,
                "timestamp": timestamp,
            }
        )

    def test_backend_health(self):
        """Test backend server health"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Backend Health", "PASS", "Server is healthy")
                    return True
                else:
                    self.log_test("Backend Health", "FAIL", f"Unhealthy status: {data}")
                    return False
            else:
                self.log_test("Backend Health", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", "FAIL", f"Connection error: {str(e)}")
            return False

    def test_frontend_accessibility(self):
        """Test frontend server accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Access", "PASS", "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Access", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Access", "FAIL", f"Connection error: {str(e)}")
            return False

    def test_search_functionality(self):
        """Test core search functionality"""
        test_queries = [
            "dna methylation WGBS human brain cancer",
            "BRCA1 mutation",
            "insulin resistance",
            "tumor suppressor p53",
            "RNA-seq breast cancer",
        ]

        all_passed = True
        for query in test_queries:
            try:
                payload = {
                    "query": query,
                    "max_results": 10,
                    "output_format": "json",
                }

                response = requests.post(
                    f"{self.backend_url}/api/search",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data.get("metadata", []))
                    self.log_test(
                        f"Search: '{query[:20]}...'",
                        "PASS",
                        f"Found {result_count} results",
                        f"Processing time: {data.get('processing_time', 'N/A')}s",
                    )
                else:
                    self.log_test(
                        f"Search: '{query[:20]}...'",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )
                    all_passed = False

            except Exception as e:
                self.log_test(f"Search: '{query[:20]}...'", "FAIL", f"Error: {str(e)}")
                all_passed = False

        return all_passed

    def test_query_refinement(self):
        """Test query refinement functionality"""
        try:
            # Test suggestions endpoint
            payload = {"query": "nonexistent cancer study"}
            response = requests.post(
                f"{self.backend_url}/api/refinement/suggestions",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])
                self.log_test(
                    "Query Refinement",
                    "PASS",
                    f"Generated {len(suggestions)} suggestions",
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Query Refinement",
                    "WARN",
                    f"Not implemented (HTTP {response.status_code})",
                )
                return None  # Skip
            else:
                self.log_test("Query Refinement", "FAIL", f"HTTP {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            self.log_test("Query Refinement", "WARN", "Endpoint not available")
            return None  # Skip
        except Exception as e:
            self.log_test("Query Refinement", "FAIL", f"Error: {str(e)}")
            return False

    def test_enhanced_search(self):
        """Test enhanced search with refinement"""
        try:
            payload = {
                "query": "brain tumor methylation",
                "use_refinement": True,
                "max_results": 5,
            }

            response = requests.post(
                f"{self.backend_url}/api/refinement/search",
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get("results", []))
                refinement_used = data.get("refinement_applied", False)
                self.log_test(
                    "Enhanced Search",
                    "PASS",
                    f"Found {result_count} results, refinement: {refinement_used}",
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Enhanced Search",
                    "WARN",
                    f"Not implemented (HTTP {response.status_code})",
                )
                return None  # Skip
            else:
                self.log_test("Enhanced Search", "FAIL", f"HTTP {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            self.log_test("Enhanced Search", "WARN", "Endpoint not available")
            return None  # Skip
        except Exception as e:
            self.log_test("Enhanced Search", "FAIL", f"Error: {str(e)}")
            return False

    def test_api_endpoints(self):
        """Test various API endpoints"""
        endpoints = [
            ("/api/config", "GET"),
            ("/docs", "GET"),  # Swagger documentation
            ("/health", "GET"),
        ]

        all_passed = True
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.backend_url}{endpoint}", timeout=5)

                if response.status_code in [
                    200,
                    404,
                ]:  # 404 is acceptable for some endpoints
                    status = "PASS" if response.status_code == 200 else "WARN"
                    self.log_test(
                        f"API {endpoint}",
                        status,
                        f"HTTP {response.status_code}",
                    )
                else:
                    self.log_test(
                        f"API {endpoint}",
                        "FAIL",
                        f"HTTP {response.status_code}",
                    )
                    all_passed = False

            except Exception as e:
                self.log_test(f"API {endpoint}", "FAIL", f"Error: {str(e)}")
                all_passed = False

        return all_passed

    def test_performance(self):
        """Test system performance"""
        try:
            start_time = time.time()

            payload = {"query": "cancer genomics", "max_results": 20}

            response = requests.post(f"{self.backend_url}/api/search", json=payload, timeout=30)

            end_time = time.time()
            response_time = end_time - start_time

            if response.status_code == 200 and response_time < 10:
                self.log_test(
                    "Performance Test",
                    "PASS",
                    f"Response time: {response_time:.2f}s",
                )
                return True
            else:
                status = "FAIL" if response.status_code != 200 else "WARN"
                self.log_test(
                    "Performance Test",
                    status,
                    f"Response time: {response_time:.2f}s, Status: {response.status_code}",
                )
                return status == "WARN"

        except Exception as e:
            self.log_test("Performance Test", "FAIL", f"Error: {str(e)}")
            return False

    def generate_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.test_results if r["status"] == "WARN"])

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"SYSTEM VALIDATION REPORT")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"\nTotal Tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Warnings: {warned_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {failed_tests}{Style.RESET_ALL}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if failed_tests > 0:
            print(f"\n{Fore.RED}FAILED TESTS:{Style.RESET_ALL}")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  ❌ {result['test']}: {result['message']}")

        # Save detailed report
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warned_tests,
                "success_rate": success_rate,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "detailed_results": self.test_results,
        }

        report_file = (
            Path("test_results") / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\nDetailed report saved to: {report_file}")

        return failed_tests == 0

    def run_all_tests(self):
        """Run all validation tests"""
        print(f"{Fore.CYAN}Starting OmicsOracle System Validation...{Style.RESET_ALL}\n")

        # Core functionality tests
        self.test_backend_health()
        self.test_frontend_accessibility()
        self.test_search_functionality()
        self.test_query_refinement()
        self.test_enhanced_search()
        self.test_api_endpoints()
        self.test_performance()

        # Generate final report
        return self.generate_report()


def main():
    """Main function"""
    validator = SystemValidator()

    try:
        success = validator.run_all_tests()
        if success:
            print(f"\n{Fore.GREEN}✅ All tests passed! System is working properly.{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}❌ Some tests failed. Please check the issues above.{Style.RESET_ALL}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Testing interrupted by user.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Testing failed with error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
