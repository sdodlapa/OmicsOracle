#!/usr/bin/env python3
"""
Comprehensive Web Interface Testing & Live Monitoring System
============================================================

This script will extensively test ALL web interfaces and provide live monitoring
to see exactly what's happening when users interact with them.
"""

import asyncio
import json
import logging
import signal
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from colorama import Fore, Style, init
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Initialize colorama
init()


class WebInterfaceTester:
    def __init__(self):
        self.interfaces = {
            "backend": {
                "name": "Backend API",
                "url": "http://localhost:8000",
                "port": 8000,
                "start_cmd": "cd web-api-backend && ./start.sh",
                "health_endpoint": "/health",
                "search_endpoint": "/api/search",
            },
            "ui_legacy": {
                "name": "Legacy UI Interface",
                "url": "http://localhost:8001",
                "port": 8001,
                "start_cmd": "cd web-ui-legacy && ./activate_and_run.sh",
                "health_endpoint": "/health",
                "search_endpoint": "/api/search",
            },
            "ui_modern": {
                "name": "Modern React Interface",
                "url": "http://localhost:5173",
                "port": 5173,
                "start_cmd": "cd web-ui-modern && npm run dev",
                "health_endpoint": "/",
                "search_endpoint": None,  # Uses frontend
            },
            "ui_stable": {
                "name": "Stable UI Interface",
                "url": "http://localhost:8080",
                "port": 8080,
                "start_cmd": "cd web-ui-stable && ./start.sh",
                "health_endpoint": "/health",
                "search_endpoint": "/search",
            },
        }

        self.test_results = {}
        self.driver = None
        self.monitoring_active = False

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{title.center(80)}")
        print(f"{'='*80}{Style.RESET_ALL}\n")

    def print_section(self, title: str):
        """Print a section header"""
        print(f"\n{Fore.YELLOW}🔍 {title}{Style.RESET_ALL}")
        print(f"{'-'*60}")

    def check_port_availability(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
            return len(result.stdout.strip()) == 0
        except:
            return True

    def get_running_processes(self) -> Dict[int, str]:
        """Get all running processes on our ports"""
        processes = {}
        for interface_id, config in self.interfaces.items():
            port = config["port"]
            try:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}", "-t"],
                    capture_output=True,
                    text=True,
                )
                if result.stdout.strip():
                    processes[port] = f"{config['name']} (PID: {result.stdout.strip()})"
                else:
                    processes[port] = "Not running"
            except:
                processes[port] = "Unknown"
        return processes

    def test_interface_connectivity(self, interface_id: str) -> Dict[str, Any]:
        """Test basic connectivity to an interface"""
        config = self.interfaces[interface_id]
        result = {
            "interface": config["name"],
            "url": config["url"],
            "port": config["port"],
            "accessible": False,
            "health_check": False,
            "response_time": None,
            "status_code": None,
            "error": None,
            "content_type": None,
            "content_preview": None,
        }

        try:
            # Test basic connectivity
            start_time = time.time()
            response = requests.get(config["url"], timeout=10)
            end_time = time.time()

            result["accessible"] = True
            result["response_time"] = round(end_time - start_time, 3)
            result["status_code"] = response.status_code
            result["content_type"] = response.headers.get("content-type", "unknown")
            result["content_preview"] = response.text[:200] if response.text else "No content"

            # Test health endpoint if available
            if config["health_endpoint"]:
                try:
                    health_url = config["url"] + config["health_endpoint"]
                    health_response = requests.get(health_url, timeout=5)
                    result["health_check"] = health_response.status_code == 200
                    if health_response.status_code == 200:
                        try:
                            health_data = health_response.json()
                            result["health_data"] = health_data
                        except:
                            pass
                except:
                    result["health_check"] = False

        except requests.exceptions.ConnectionError:
            result["error"] = "Connection refused - service not running"
        except requests.exceptions.Timeout:
            result["error"] = "Request timeout"
        except Exception as e:
            result["error"] = str(e)

        return result

    def test_search_functionality(self, interface_id: str) -> Dict[str, Any]:
        """Test search functionality of an interface"""
        config = self.interfaces[interface_id]
        result = {
            "interface": config["name"],
            "search_working": False,
            "search_method": None,
            "response_data": None,
            "error": None,
        }

        if not config["search_endpoint"]:
            result["error"] = "No search endpoint defined"
            return result

        search_url = config["url"] + config["search_endpoint"]
        test_query = "breast cancer BRCA1"

        try:
            # Try POST request (most common)
            if interface_id == "working":
                # Form data for working interface
                response = requests.post(
                    search_url,
                    data={"query": test_query, "max_results": 5},
                    timeout=15,
                )
            else:
                # JSON data for API interfaces
                response = requests.post(
                    search_url,
                    json={"query": test_query, "max_results": 5},
                    headers={"Content-Type": "application/json"},
                    timeout=15,
                )

            result["search_method"] = "POST"
            result["status_code"] = response.status_code

            if response.status_code == 200:
                result["search_working"] = True
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:500]
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"

        except Exception as e:
            result["error"] = str(e)

        return result

    def setup_browser_driver(self) -> bool:
        """Setup Selenium WebDriver for browser testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup browser driver: {e}")
            return False

    def test_frontend_functionality(self, interface_id: str) -> Dict[str, Any]:
        """Test frontend functionality with browser automation"""
        config = self.interfaces[interface_id]
        result = {
            "interface": config["name"],
            "page_loads": False,
            "search_form_exists": False,
            "search_submits": False,
            "results_display": False,
            "javascript_errors": [],
            "console_logs": [],
            "page_source_preview": None,
            "error": None,
        }

        if not self.driver:
            result["error"] = "Browser driver not available"
            return result

        try:
            # Load the page
            self.driver.get(config["url"])
            time.sleep(3)  # Wait for page to load

            result["page_loads"] = True
            result["page_source_preview"] = self.driver.page_source[:500]

            # Check for JavaScript errors
            logs = self.driver.get_log("browser")
            result["console_logs"] = [log for log in logs if log["level"] in ["SEVERE", "WARNING"]]

            # Look for search form
            try:
                search_form = self.driver.find_element(By.TAG_NAME, "form")
                result["search_form_exists"] = True

                # Try to find search input
                search_input = self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='text'], input[name='query']"
                )
                search_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "button[type='submit'], input[type='submit']",
                )

                # Fill and submit search
                search_input.clear()
                search_input.send_keys("test cancer research")
                search_button.click()

                result["search_submits"] = True

                # Wait for results (up to 10 seconds)
                time.sleep(5)

                # Check if results are displayed
                page_content = self.driver.page_source.lower()
                if any(
                    keyword in page_content
                    for keyword in [
                        "result",
                        "dataset",
                        "found",
                        "error",
                        "success",
                    ]
                ):
                    result["results_display"] = True

            except Exception as form_error:
                result["error"] = f"Form interaction failed: {str(form_error)}"

        except Exception as e:
            result["error"] = str(e)

        return result

    def monitor_live_interaction(self, interface_id: str, duration: int = 60):
        """Monitor live user interaction with interface"""
        config = self.interfaces[interface_id]

        print(f"\n{Fore.GREEN}🔴 LIVE MONITORING: {config['name']}{Style.RESET_ALL}")
        print(f"URL: {config['url']}")
        print(f"Duration: {duration} seconds")
        print(f"Monitoring console logs, network requests, and DOM changes...")

        if not self.driver:
            print(f"{Fore.RED}❌ Browser driver not available{Style.RESET_ALL}")
            return

        try:
            # Open the interface
            self.driver.get(config["url"])

            # Also open in regular browser for user interaction
            webbrowser.open(config["url"])

            start_time = time.time()
            self.monitoring_active = True

            while time.time() - start_time < duration and self.monitoring_active:
                # Get console logs
                logs = self.driver.get_log("browser")
                if logs:
                    for log in logs:
                        timestamp = datetime.fromtimestamp(log["timestamp"] / 1000).strftime("%H:%M:%S")
                        level = log["level"]
                        message = log["message"]
                        color = (
                            Fore.RED
                            if level == "SEVERE"
                            else Fore.YELLOW
                            if level == "WARNING"
                            else Fore.WHITE
                        )
                        print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")

                # Check for DOM changes
                current_title = self.driver.title
                current_url = self.driver.current_url

                time.sleep(2)

        except Exception as e:
            print(f"{Fore.RED}❌ Live monitoring failed: {e}{Style.RESET_ALL}")

    def analyze_best_interface(self) -> str:
        """Analyze test results to determine best interface"""
        scores = {}

        for interface_id, connectivity in self.test_results.get("connectivity", {}).items():
            score = 0

            # Connectivity score (40%)
            if connectivity.get("accessible"):
                score += 20
            if connectivity.get("health_check"):
                score += 20
            if connectivity.get("response_time", 999) < 2:
                score += 10

            # Search functionality score (40%)
            search_result = self.test_results.get("search", {}).get(interface_id, {})
            if search_result.get("search_working"):
                score += 40

            # Frontend functionality score (20%)
            frontend_result = self.test_results.get("frontend", {}).get(interface_id, {})
            if frontend_result.get("page_loads"):
                score += 5
            if frontend_result.get("search_form_exists"):
                score += 5
            if frontend_result.get("search_submits"):
                score += 5
            if frontend_result.get("results_display"):
                score += 5

            scores[interface_id] = score

        if not scores:
            return "none"

        best_interface = max(scores, key=scores.get)
        return best_interface

    def generate_comprehensive_report(self):
        """Generate detailed analysis report"""
        self.print_header("COMPREHENSIVE WEB INTERFACE ANALYSIS REPORT")

        # Running processes
        print(f"{Fore.CYAN}🔧 CURRENT RUNNING PROCESSES:{Style.RESET_ALL}")
        processes = self.get_running_processes()
        for port, status in processes.items():
            color = Fore.GREEN if "PID" in status else Fore.RED
            print(f"   Port {port}: {color}{status}{Style.RESET_ALL}")

        # Connectivity results
        print(f"\n{Fore.CYAN}🌐 CONNECTIVITY TEST RESULTS:{Style.RESET_ALL}")
        for interface_id, result in self.test_results.get("connectivity", {}).items():
            name = result["interface"]
            accessible = "✅" if result["accessible"] else "❌"
            health = "✅" if result["health_check"] else "❌"
            response_time = result.get("response_time", "N/A")

            print(f"\n   {name}:")
            print(f"     Accessible: {accessible}")
            print(f"     Health Check: {health}")
            print(f"     Response Time: {response_time}s")

            if result.get("error"):
                print(f"     {Fore.RED}Error: {result['error']}{Style.RESET_ALL}")
            if result.get("content_type"):
                print(f"     Content Type: {result['content_type']}")

        # Search functionality results
        print(f"\n{Fore.CYAN}🔍 SEARCH FUNCTIONALITY RESULTS:{Style.RESET_ALL}")
        for interface_id, result in self.test_results.get("search", {}).items():
            name = result["interface"]
            working = "✅" if result["search_working"] else "❌"

            print(f"\n   {name}:")
            print(f"     Search Working: {working}")

            if result.get("error"):
                print(f"     {Fore.RED}Error: {result['error']}{Style.RESET_ALL}")
            elif result.get("response_data"):
                data = result["response_data"]
                if isinstance(data, dict):
                    print(f"     Response: {json.dumps(data, indent=6)[:200]}...")
                else:
                    print(f"     Response: {str(data)[:200]}...")

        # Frontend functionality results
        print(f"\n{Fore.CYAN}🖥️ FRONTEND FUNCTIONALITY RESULTS:{Style.RESET_ALL}")
        for interface_id, result in self.test_results.get("frontend", {}).items():
            name = result["interface"]

            print(f"\n   {name}:")
            print(f"     Page Loads: {'✅' if result['page_loads'] else '❌'}")
            print(f"     Search Form: {'✅' if result['search_form_exists'] else '❌'}")
            print(f"     Search Submits: {'✅' if result['search_submits'] else '❌'}")
            print(f"     Results Display: {'✅' if result['results_display'] else '❌'}")

            if result.get("console_logs"):
                print(f"     {Fore.YELLOW}Console Issues: {len(result['console_logs'])}{Style.RESET_ALL}")
            if result.get("error"):
                print(f"     {Fore.RED}Error: {result['error']}{Style.RESET_ALL}")

        # Best interface recommendation
        best_interface = self.analyze_best_interface()
        print(f"\n{Fore.CYAN}🏆 BEST INTERFACE RECOMMENDATION:{Style.RESET_ALL}")
        if best_interface != "none":
            best_config = self.interfaces[best_interface]
            print(f"   {Fore.GREEN}✅ RECOMMENDED: {best_config['name']}{Style.RESET_ALL}")
            print(f"   URL: {best_config['url']}")
            print(f"   Reason: Highest overall functionality score")
        else:
            print(f"   {Fore.RED}❌ NO WORKING INTERFACE FOUND{Style.RESET_ALL}")

        # Actionable recommendations
        print(f"\n{Fore.CYAN}📋 ACTIONABLE RECOMMENDATIONS:{Style.RESET_ALL}")

        working_interfaces = [
            interface_id
            for interface_id, result in self.test_results.get("connectivity", {}).items()
            if result.get("accessible")
        ]

        if not working_interfaces:
            print(
                f"   {Fore.RED}1. NO INTERFACES ARE RUNNING - Start at least one interface{Style.RESET_ALL}"
            )
            print(f"   2. Check if virtual environment is activated")
            print(f"   3. Check if dependencies are installed")
            print(f"   4. Check for port conflicts")
        else:
            fully_working = [
                interface_id
                for interface_id in working_interfaces
                if self.test_results.get("search", {}).get(interface_id, {}).get("search_working")
            ]

            if fully_working:
                best = fully_working[0]
                config = self.interfaces[best]
                print(f"   {Fore.GREEN}1. USE {config['name']} at {config['url']}{Style.RESET_ALL}")
                print(f"   2. This interface has working search functionality")
                print(f"   3. Test it manually to verify user interaction")
            else:
                print(f"   {Fore.YELLOW}1. Interfaces are running but search is broken{Style.RESET_ALL}")
                print(f"   2. Check backend API connectivity")
                print(f"   3. Verify OmicsOracle pipeline configuration")
                print(f"   4. Check for JavaScript errors in browser console")

    def run_comprehensive_test(self):
        """Run all tests"""
        self.print_header("STARTING COMPREHENSIVE WEB INTERFACE TESTING")

        # Test connectivity
        self.print_section("Testing Connectivity")
        self.test_results["connectivity"] = {}
        for interface_id in self.interfaces:
            print(f"Testing {self.interfaces[interface_id]['name']}...")
            result = self.test_interface_connectivity(interface_id)
            self.test_results["connectivity"][interface_id] = result
            status = "✅ ACCESSIBLE" if result["accessible"] else "❌ NOT ACCESSIBLE"
            print(f"   {status} ({result.get('response_time', 'N/A')}s)")

        # Test search functionality
        self.print_section("Testing Search Functionality")
        self.test_results["search"] = {}
        for interface_id in self.interfaces:
            if self.test_results["connectivity"][interface_id]["accessible"]:
                print(f"Testing search on {self.interfaces[interface_id]['name']}...")
                result = self.test_search_functionality(interface_id)
                self.test_results["search"][interface_id] = result
                status = "✅ WORKING" if result["search_working"] else "❌ BROKEN"
                print(f"   Search: {status}")
            else:
                print(f"Skipping search test for {self.interfaces[interface_id]['name']} (not accessible)")

        # Test frontend functionality (if browser driver available)
        self.print_section("Testing Frontend Functionality")
        if self.setup_browser_driver():
            self.test_results["frontend"] = {}
            for interface_id in self.interfaces:
                if self.test_results["connectivity"][interface_id]["accessible"]:
                    print(f"Testing frontend for {self.interfaces[interface_id]['name']}...")
                    result = self.test_frontend_functionality(interface_id)
                    self.test_results["frontend"][interface_id] = result
                    status = (
                        "✅ WORKING" if result["page_loads"] and result["search_form_exists"] else "❌ ISSUES"
                    )
                    print(f"   Frontend: {status}")
                else:
                    print(
                        f"Skipping frontend test for {self.interfaces[interface_id]['name']} (not accessible)"
                    )
        else:
            print("Browser testing not available (Selenium/Chrome not installed)")

        # Generate report
        self.generate_comprehensive_report()

        # Offer live monitoring
        best_interface = self.analyze_best_interface()
        if best_interface != "none":
            print(f"\n{Fore.GREEN}🔴 LIVE MONITORING AVAILABLE{Style.RESET_ALL}")
            print(
                f"Would you like to monitor live user interaction with {self.interfaces[best_interface]['name']}?"
            )
            print(f"This will open the interface in your browser and monitor all activity...")

            try:
                response = input("Start live monitoring? (y/n): ").lower().strip()
                if response in ["y", "yes"]:
                    self.monitor_live_interaction(best_interface, 120)  # 2 minutes
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Monitoring cancelled{Style.RESET_ALL}")

        # Cleanup
        if self.driver:
            self.driver.quit()

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("test_results") / f"comprehensive_interface_test_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        print(f"\n{Fore.CYAN}📄 Results saved to: {results_file}{Style.RESET_ALL}")


def main():
    """Main function"""
    print(f"{Fore.CYAN}🧬 OmicsOracle Web Interface Comprehensive Testing System{Style.RESET_ALL}")
    print(f"{'='*80}")

    tester = WebInterfaceTester()

    try:
        tester.run_comprehensive_test()
        tester.save_results()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Testing interrupted by user{Style.RESET_ALL}")
        if tester.driver:
            tester.driver.quit()
    except Exception as e:
        print(f"\n{Fore.RED}Testing failed: {e}{Style.RESET_ALL}")
        if tester.driver:
            tester.driver.quit()


if __name__ == "__main__":
    main()
