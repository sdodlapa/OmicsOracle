#!/usr/bin/env python3
"""
Security Headers and Configuration Testing for OmicsOracle Web Interface

This module tests security headers, HTTPS configuration, rate limiting,
and CORS settings.
"""

import json
import socket
import ssl
import time
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests


class SecurityHeadersTestSuite:
    """Security headers and configuration testing suite."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize security headers test suite."""
        self.base_url = base_url
        self.session = requests.Session()

    def test_security_headers(self) -> Dict[str, Any]:
        """Test for presence and configuration of security headers."""
        security_headers = {
            "X-Content-Type-Options": {
                "expected": "nosniff",
                "description": "Prevents MIME type sniffing",
            },
            "X-Frame-Options": {
                "expected": ["DENY", "SAMEORIGIN"],
                "description": "Prevents clickjacking attacks",
            },
            "X-XSS-Protection": {
                "expected": "1; mode=block",
                "description": "Enables XSS filtering in browsers",
            },
            "Strict-Transport-Security": {
                "expected": "max-age=",
                "description": "Enforces HTTPS connections",
            },
            "Content-Security-Policy": {
                "expected": "default-src",
                "description": "Controls resource loading",
            },
            "Referrer-Policy": {
                "expected": [
                    "strict-origin-when-cross-origin",
                    "strict-origin",
                ],
                "description": "Controls referrer information",
            },
            "Permissions-Policy": {
                "expected": "",
                "description": "Controls browser features",
            },
        }

        results = {}

        try:
            response = self.session.get(self.base_url, timeout=10)

            for header_name, header_config in security_headers.items():
                header_value = response.headers.get(header_name)

                if header_value:
                    # Check if header value matches expected values
                    expected = header_config["expected"]
                    if isinstance(expected, list):
                        present_correctly = any(exp in header_value for exp in expected)
                    else:
                        present_correctly = expected in header_value if expected else True
                else:
                    present_correctly = False

                results[header_name] = {
                    "present": header_value is not None,
                    "value": header_value,
                    "correct": present_correctly,
                    "description": header_config["description"],
                }

        except requests.exceptions.RequestException as e:
            results["error"] = f"Failed to test security headers: {str(e)}"

        # Calculate summary statistics
        total_headers = len(security_headers)
        present_headers = sum(1 for h in results.values() if isinstance(h, dict) and h.get("present", False))
        correct_headers = sum(1 for h in results.values() if isinstance(h, dict) and h.get("correct", False))

        results["summary"] = {
            "total_headers": total_headers,
            "present_headers": present_headers,
            "correct_headers": correct_headers,
            "security_score": (correct_headers / total_headers) * 100,
        }

        return results

    def _generate_header_recommendations(
        self, results: Dict[str, Any], info_disclosure: Dict[str, Any]
    ) -> List[str]:
        """Generate security header recommendations."""
        recommendations = []

        # Check missing or incorrect headers
        for header_name, header_data in results.items():
            if header_name == "summary" or header_name == "error":
                continue

            if not header_data.get("present"):
                recommendations.append(f"Add {header_name} header")
            elif not header_data.get("correct"):
                recommendations.append(f"Fix {header_name} header configuration")

        # Check for information disclosure
        if info_disclosure.get("server_info_exposed"):
            recommendations.append("Remove or obfuscate Server header")

        return recommendations

    def test_https_configuration(self) -> Dict[str, Any]:
        """Test HTTPS configuration and SSL settings."""
        parsed_url = urlparse(self.base_url)
        hostname = parsed_url.hostname or "localhost"
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        results: Dict[str, Any] = {
            "https_available": False,
            "https_redirect": False,
            "ssl_certificate_valid": False,
            "tls_version": None,
            "cipher_suite": None,
            "ssl_errors": [],
        }

        # Test HTTPS availability
        try:
            https_url = f"https://{hostname}:{port if port != 80 else 443}"
            response = self.session.get(https_url, timeout=10, verify=False)
            results["https_available"] = response.status_code == 200

        except requests.exceptions.SSLError as e:
            results["ssl_errors"].append(f"SSL Error: {str(e)}")
        except requests.exceptions.RequestException:
            results["ssl_errors"].append("HTTPS not available")
        except Exception as e:
            results["ssl_errors"].append(f"HTTPS test error: {str(e)}")

        # Test HTTP to HTTPS redirect
        if parsed_url.scheme == "http":
            try:
                http_response = self.session.get(self.base_url, timeout=10, allow_redirects=False)
                if http_response.status_code in [301, 302, 307, 308]:
                    location = http_response.headers.get("Location", "")
                    results["https_redirect"] = location.startswith("https://")

            except Exception as e:
                results["ssl_errors"].append(f"Redirect test error: {str(e)}")

        # Test SSL certificate and TLS configuration
        if results["https_available"]:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        results["ssl_certificate_valid"] = True
                        results["tls_version"] = ssock.version()
                        results["cipher_suite"] = ssock.cipher()

            except ssl.SSLError as e:
                results["ssl_errors"].append(f"SSL certificate error: {str(e)}")
            except Exception as e:
                results["ssl_errors"].append(f"SSL test error: {str(e)}")

        return results

    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting implementation."""
        test_endpoints = [
            f"{self.base_url}/api/search",
            f"{self.base_url}/api/summarize",
            f"{self.base_url}/api/analyze",
        ]

        results = {}

        for endpoint in test_endpoints:
            endpoint_results = {
                "rate_limited": False,
                "rate_limit_headers_present": False,
                "requests_sent": 0,
                "first_rate_limit_at": None,
                "rate_limit_headers": {},
            }

            # Send rapid requests to trigger rate limiting
            for i in range(50):  # Send 50 requests rapidly
                try:
                    response = self.session.get(endpoint, timeout=5)
                    endpoint_results["requests_sent"] = i + 1

                    # Check for rate limiting status codes
                    if response.status_code in [429, 503]:
                        endpoint_results["rate_limited"] = True
                        if not endpoint_results["first_rate_limit_at"]:
                            endpoint_results["first_rate_limit_at"] = i + 1

                    # Check for rate limiting headers
                    rate_limit_headers = [
                        "X-RateLimit-Limit",
                        "X-RateLimit-Remaining",
                        "X-RateLimit-Reset",
                        "Retry-After",
                    ]

                    for header in rate_limit_headers:
                        if header in response.headers:
                            endpoint_results["rate_limit_headers_present"] = True
                            endpoint_results["rate_limit_headers"][header] = response.headers[header]

                    # If rate limited, break the loop
                    if endpoint_results["rate_limited"]:
                        break

                    time.sleep(0.1)  # Small delay between requests

                except requests.exceptions.RequestException:
                    break

            results[endpoint] = endpoint_results

        # Calculate summary
        total_endpoints = len(test_endpoints)
        rate_limited_endpoints = sum(1 for result in results.values() if result.get("rate_limited", False))

        results["summary"] = {
            "total_endpoints_tested": total_endpoints,
            "rate_limited_endpoints": rate_limited_endpoints,
            "rate_limiting_coverage": (rate_limited_endpoints / total_endpoints) * 100,
        }

        return results

    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS (Cross-Origin Resource Sharing) configuration."""
        cors_test_origins = [
            "http://localhost:3000",
            "https://malicious-site.com",
            "https://example.com",
            "null",  # Test for null origin
        ]

        results = {}

        for origin in cors_test_origins:
            headers = {"Origin": origin} if origin != "null" else {"Origin": "null"}

            try:
                # Test preflight request
                preflight_response = self.session.options(
                    f"{self.base_url}/api/search", headers=headers, timeout=10
                )

                # Test actual request
                actual_response = self.session.get(f"{self.base_url}/api/search", headers=headers, timeout=10)

                cors_headers = {
                    "Access-Control-Allow-Origin": actual_response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": actual_response.headers.get(
                        "Access-Control-Allow-Methods"
                    ),
                    "Access-Control-Allow-Headers": actual_response.headers.get(
                        "Access-Control-Allow-Headers"
                    ),
                    "Access-Control-Allow-Credentials": actual_response.headers.get(
                        "Access-Control-Allow-Credentials"
                    ),
                }

                # Check if origin is allowed
                allowed_origin = cors_headers.get("Access-Control-Allow-Origin")
                origin_allowed = (
                    allowed_origin == "*"
                    or allowed_origin == origin
                    or (origin == "null" and allowed_origin == "null")
                )

                results[origin] = {
                    "preflight_status": preflight_response.status_code,
                    "actual_status": actual_response.status_code,
                    "cors_headers": cors_headers,
                    "origin_allowed": origin_allowed,
                    "credentials_allowed": cors_headers.get("Access-Control-Allow-Credentials") == "true",
                }

            except requests.exceptions.RequestException as e:
                results[origin] = {"error": str(e), "origin_allowed": False}

        # Check for overly permissive CORS
        wildcard_cors = any(
            result.get("cors_headers", {}).get("Access-Control-Allow-Origin") == "*"
            for result in results.values()
            if isinstance(result, dict) and "cors_headers" in result
        )

        results["summary"] = {
            "wildcard_cors_enabled": wildcard_cors,
            "total_origins_tested": len(cors_test_origins),
            "allowed_origins": sum(
                1
                for result in results.values()
                if isinstance(result, dict) and result.get("origin_allowed", False)
            ),
        }

        return results

    def generate_headers_report(
        self,
        headers_results: Dict[str, Any],
        https_results: Dict[str, Any],
        rate_limit_results: Dict[str, Any],
        cors_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive security headers report."""

        # Calculate risk scores
        headers_score = headers_results.get("summary", {}).get("security_score", 0)
        https_score = (
            100 if https_results.get("https_available") and https_results.get("ssl_certificate_valid") else 0
        )
        rate_limit_score = rate_limit_results.get("summary", {}).get("rate_limiting_coverage", 0)
        cors_score = 0 if cors_results.get("summary", {}).get("wildcard_cors_enabled") else 100

        overall_score = (headers_score + https_score + rate_limit_score + cors_score) / 4

        # Generate recommendations
        recommendations = []

        if headers_score < 80:
            recommendations.append("Implement missing security headers")
        if https_score < 100:
            recommendations.append("Enable HTTPS with proper configuration")
        if rate_limit_score < 50:
            recommendations.append("Implement rate limiting on API endpoints")
        if cors_score < 100:
            recommendations.append("Configure CORS more restrictively")

        return {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "overall_security_score": overall_score,
            "category_scores": {
                "security_headers": headers_score,
                "https_configuration": https_score,
                "rate_limiting": rate_limit_score,
                "cors_configuration": cors_score,
            },
            "detailed_results": {
                "security_headers": headers_results,
                "https_configuration": https_results,
                "rate_limiting": rate_limit_results,
                "cors_configuration": cors_results,
            },
            "recommendations": recommendations,
            "risk_level": self._calculate_risk_level(overall_score),
        }

    def _calculate_risk_level(self, score: float) -> str:
        """Calculate risk level based on overall security score."""
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"


def run_security_headers_tests() -> Dict[str, Any]:
    """Run all security headers tests and generate report."""
    print("Starting Security Headers and Configuration Testing...")

    # Initialize test suite
    headers_suite = SecurityHeadersTestSuite()

    # Run all test categories
    print("Testing security headers...")
    headers_results = headers_suite.test_security_headers()

    print("Testing HTTPS configuration...")
    https_results = headers_suite.test_https_configuration()

    print("Testing rate limiting...")
    rate_limit_results = headers_suite.test_rate_limiting()

    print("Testing CORS configuration...")
    cors_results = headers_suite.test_cors_configuration()

    # Generate comprehensive report
    print("Generating security headers report...")
    report = headers_suite.generate_headers_report(
        headers_results, https_results, rate_limit_results, cors_results
    )

    # Save results
    with open("security_headers_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Security headers testing completed. Risk level: {report['risk_level']}")
    print("Results saved to: security_headers_results.json")

    return report


if __name__ == "__main__":
    run_security_headers_tests()
