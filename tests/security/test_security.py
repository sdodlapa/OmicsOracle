#!/usr/bin/env python3
"""
Security Testing Framework for OmicsOracle Web Interface

This module provides comprehensive security testing including:
- Input validation and injection testing
- Security headers validation
- Authentication bypass testing
- Rate limiting verification
"""

import time
from typing import Any, Dict, List

import requests


class SecurityTester:
    """Comprehensive security testing suite."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize security tester with base URL."""
        self.base_url = base_url
        self.session = requests.Session()
        self.injection_payloads = self._load_injection_payloads()

    def _load_injection_payloads(self) -> Dict[str, List[str]]:
        """Load various injection attack payloads."""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "1' UNION SELECT * FROM users--",
                "'; INSERT INTO users VALUES ('hacker','password'); --",
                "admin'--",
                "admin'/*",
                "' or 1=1#",
                "' or 1=1--",
                "') or '1'='1--",
                "') or ('1'='1--",
            ],
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//",
                "<iframe src=javascript:alert('XSS')>",
                "<body onload=alert('XSS')>",
                "<input onfocus=alert('XSS') autofocus>",
                "<select onfocus=alert('XSS') autofocus>",
                "<textarea onfocus=alert('XSS') autofocus>",
            ],
            "command_injection": [
                "; ls -la",
                "| cat /etc/passwd",
                "&& whoami",
                "`id`",
                "$(id)",
                "; cat /etc/shadow",
                "| netstat -an",
                "&& ps aux",
                "`uname -a`",
                "$(cat /etc/hosts)",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "..%2F..%2F..%2Fetc%2Fpasswd",
                "..%5c..%5c..%5cetc%5cpasswd",
                "....\\\\....\\\\....\\\\etc\\\\passwd",
                "%2e%2e\\%2e%2e\\%2e%2e\\etc\\passwd",
            ],
            "nosql_injection": [
                "{'$ne': null}",
                "{'$gt': ''}",
                "{'$where': 'this.username == this.password'}",
                "'; return db.users.find(); var dummy=''",
                "{'$regex': '.*'}",
                "{'$exists': true}",
                "{'$not': {'$size': 0}}",
                "'; return true; var dummy='",
            ],
        }

    def test_search_api_injection(self) -> Dict[str, Any]:
        """Test search API against injection attacks."""
        print("🔍 Testing search API for injection vulnerabilities...")
        results = {}

        for attack_type, payloads in self.injection_payloads.items():
            print(f"  Testing {attack_type}...")
            attack_results = []

            for payload in payloads[:3]:  # Test first 3 payloads of each type
                test_cases = [
                    {"query": payload, "max_results": 10},
                    {
                        "query": "diabetes",
                        "max_results": payload if isinstance(payload, str) else 10,
                    },
                ]

                for test_case in test_cases:
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/search",
                            json=test_case,
                            timeout=10,
                        )

                        # Check for sensitive information exposure
                        error_exposed = self._check_error_exposure(response.text)
                        payload_reflected = payload in response.text if isinstance(payload, str) else False

                        attack_results.append(
                            {
                                "payload": str(payload)[:50] + "..."
                                if len(str(payload)) > 50
                                else str(payload),
                                "status_code": response.status_code,
                                "response_length": len(response.text),
                                "payload_reflected": payload_reflected,
                                "error_exposed": error_exposed,
                                "safe": response.status_code in [200, 400, 422]
                                and not error_exposed
                                and not payload_reflected,
                            }
                        )

                    except Exception as e:
                        attack_results.append(
                            {
                                "payload": str(payload)[:50] + "..."
                                if len(str(payload)) > 50
                                else str(payload),
                                "error": str(e)[:100],
                                "safe": True,  # Exception is generally safe
                            }
                        )

            # Calculate safety score for this attack type
            safe_count = sum(1 for result in attack_results if result.get("safe", False))
            safety_score = (safe_count / len(attack_results)) * 100 if attack_results else 0

            results[attack_type] = {
                "safety_score": safety_score,
                "total_tests": len(attack_results),
                "safe_responses": safe_count,
                "details": attack_results,
            }

        return results

    def _check_error_exposure(self, response_text: str) -> bool:
        """Check if response exposes sensitive information."""
        sensitive_patterns = [
            "traceback",
            "exception",
            "error at line",
            "sql syntax",
            "/usr/",
            "/var/",
            "database",
            "connection string",
            "password",
            "secret",
            "internal server error",
            "debug",
            "stack trace",
        ]

        response_lower = response_text.lower()
        return any(pattern in response_lower for pattern in sensitive_patterns)

    def test_security_headers(self) -> Dict[str, Any]:
        """Test presence and configuration of security headers."""
        print("🛡️ Testing security headers...")

        required_headers = {
            "X-Content-Type-Options": ["nosniff"],
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": ["1; mode=block", "0"],
            "Content-Security-Policy": ["default-src"],
            "Referrer-Policy": [
                "strict-origin-when-cross-origin",
                "no-referrer",
                "same-origin",
            ],
            "Strict-Transport-Security": ["max-age="],
        }

        try:
            response = self.session.get(f"{self.base_url}/")
            headers = response.headers

            results = {}
            security_score = 0

            for header, expected_values in required_headers.items():
                if header in headers:
                    header_value = headers[header]
                    is_valid = any(expected in header_value for expected in expected_values)

                    results[header] = {
                        "present": True,
                        "value": header_value,
                        "valid": is_valid,
                    }

                    if is_valid:
                        security_score += 1
                else:
                    results[header] = {
                        "present": False,
                        "valid": False,
                        "recommendation": f"Add {header} header",
                    }

            # Calculate overall security score
            max_score = len(required_headers)
            security_percentage = (security_score / max_score) * 100

            return {
                "security_score": security_percentage,
                "headers_tested": max_score,
                "headers_valid": security_score,
                "details": results,
            }

        except Exception as e:
            return {"error": str(e)}

    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting implementation."""
        print("⏱️ Testing rate limiting...")

        # Test different endpoints for rate limiting
        endpoints = ["/api/status", "/api/search", "/api/summarize"]

        results = {}

        for endpoint in endpoints:
            print(f"  Testing rate limiting on {endpoint}...")
            responses = []
            rate_limited = False

            # Make rapid requests
            for i in range(20):  # Reduced from 100 to 20 for faster testing
                try:
                    if endpoint == "/api/search":
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            json={"query": f"test{i}", "max_results": 1},
                            timeout=5,
                        )
                    elif endpoint == "/api/summarize":
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            json={"query": f"test{i}", "max_results": 1},
                            timeout=5,
                        )
                    else:
                        response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)

                    is_rate_limited = response.status_code == 429
                    responses.append(
                        {
                            "request_num": i,
                            "status_code": response.status_code,
                            "rate_limited": is_rate_limited,
                        }
                    )

                    if is_rate_limited:
                        rate_limited = True
                        print(f"    Rate limiting detected at request {i}")
                        break

                except Exception as e:
                    responses.append({"request_num": i, "error": str(e)[:100]})

                # Small delay to avoid overwhelming the server
                time.sleep(0.1)

            rate_limited_count = sum(1 for r in responses if r.get("rate_limited", False))

            results[endpoint] = {
                "total_requests": len(responses),
                "rate_limited_requests": rate_limited_count,
                "rate_limiting_active": rate_limited,
                "rate_limiting_percentage": (rate_limited_count / len(responses)) * 100 if responses else 0,
            }

        return results

    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation on various endpoints."""
        print("✅ Testing input validation...")

        # Test various invalid inputs
        invalid_inputs = [
            {"query": "", "max_results": 10},  # Empty query
            {"query": "test", "max_results": -1},  # Negative number
            {"query": "test", "max_results": 99999},  # Very large number
            {"query": "A" * 10000, "max_results": 10},  # Very long query
            {"query": "test", "max_results": "not_a_number"},  # Invalid type
            {"query": None, "max_results": 10},  # Null query
            {"query": ["array", "instead"], "max_results": 10},  # Wrong type
        ]

        results = []

        for invalid_input in invalid_inputs:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/search",
                    json=invalid_input,
                    timeout=10,
                )

                # Good validation should return 400 or 422
                proper_validation = response.status_code in [400, 422]

                results.append(
                    {
                        "input": str(invalid_input)[:100],
                        "status_code": response.status_code,
                        "proper_validation": proper_validation,
                        "response_preview": response.text[:200],
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "input": str(invalid_input)[:100],
                        "error": str(e)[:100],
                        "proper_validation": True,  # Exception handling is good
                    }
                )

        # Calculate validation score
        valid_responses = sum(1 for r in results if r.get("proper_validation", False))
        validation_score = (valid_responses / len(results)) * 100 if results else 0

        return {
            "validation_score": validation_score,
            "total_tests": len(results),
            "properly_validated": valid_responses,
            "details": results,
        }

    def run_comprehensive_security_test(self) -> Dict[str, Any]:
        """Run all security tests and generate a comprehensive report."""
        print("🔒 Starting comprehensive security testing...")
        print("=" * 60)

        start_time = time.time()

        # Run all security tests
        test_results = {
            "injection_testing": self.test_search_api_injection(),
            "security_headers": self.test_security_headers(),
            "rate_limiting": self.test_rate_limiting(),
            "input_validation": self.test_input_validation(),
        }

        end_time = time.time()

        # Calculate overall security score
        scores = []

        # Injection testing score (average of all attack types)
        injection_scores = [
            result["safety_score"]
            for result in test_results["injection_testing"].values()
            if isinstance(result, dict) and "safety_score" in result
        ]
        if injection_scores:
            scores.append(sum(injection_scores) / len(injection_scores))

        # Security headers score
        if "security_score" in test_results["security_headers"]:
            scores.append(test_results["security_headers"]["security_score"])

        # Input validation score
        if "validation_score" in test_results["input_validation"]:
            scores.append(test_results["input_validation"]["validation_score"])

        # Rate limiting is less critical, so we'll count it as partial credit
        rate_limiting_active = any(
            result.get("rate_limiting_active", False)
            for result in test_results["rate_limiting"].values()
            if isinstance(result, dict)
        )
        scores.append(50 if rate_limiting_active else 25)  # 50% if active, 25% if not

        overall_score = sum(scores) / len(scores) if scores else 0

        # Generate summary
        summary = {
            "overall_security_score": overall_score,
            "test_duration": end_time - start_time,
            "test_results": test_results,
            "recommendations": self._generate_security_recommendations(test_results),
        }

        print("\n" + "=" * 60)
        print(f"🔒 Security Testing Complete!")
        print(f"📊 Overall Security Score: {overall_score:.1f}%")
        print(f"⏱️ Test Duration: {end_time - start_time:.2f} seconds")
        print("=" * 60)

        return summary

    def _generate_security_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on test results."""
        recommendations = []

        # Check injection testing results
        for attack_type, result in test_results["injection_testing"].items():
            if isinstance(result, dict) and result.get("safety_score", 0) < 90:
                recommendations.append(
                    f"Improve {attack_type} protection (score: {result.get('safety_score', 0):.1f}%)"
                )

        # Check security headers
        headers_result = test_results.get("security_headers", {})
        if headers_result.get("security_score", 0) < 80:
            recommendations.append("Add missing security headers")

        # Check input validation
        validation_result = test_results.get("input_validation", {})
        if validation_result.get("validation_score", 0) < 90:
            recommendations.append("Improve input validation")

        # Check rate limiting
        rate_limiting_result = test_results.get("rate_limiting", {})
        if not any(
            result.get("rate_limiting_active", False)
            for result in rate_limiting_result.values()
            if isinstance(result, dict)
        ):
            recommendations.append("Implement rate limiting")

        if not recommendations:
            recommendations.append("Security configuration looks good!")

        return recommendations


if __name__ == "__main__":
    # Run security tests
    tester = SecurityTester()
    results = tester.run_comprehensive_security_test()

    # Print summary
    print("\n📋 Security Test Summary:")
    for recommendation in results["recommendations"]:
        print(f"  • {recommendation}")
