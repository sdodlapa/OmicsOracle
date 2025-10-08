#!/usr/bin/env python3
"""
Test script to verify all OmicsOracle web interfaces can run simultaneously.
"""

import time

import requests
from colorama import Fore, Style, init

# Initialize colorama
init()


def test_all_interfaces():
    """Test all web interfaces running simultaneously."""

    print(f"{Fore.BLUE}🧬 OmicsOracle Multi-Interface Test{Style.RESET_ALL}\n")

    interfaces = [
        {
            "name": "Backend API",
            "url": "http://localhost:8000/health",
            "port": 8000,
            "description": "Main API backend",
        },
        {
            "name": "Original Interface",
            "url": "http://localhost:8001/health",
            "port": 8001,
            "description": "First HTML interface",
        },
        {
            "name": "Modern React Interface",
            "url": "http://localhost:5173",
            "port": 5173,
            "description": "Current React frontend",
        },
        {
            "name": "WORKING Interface",
            "url": "http://localhost:8080/health",
            "port": 8080,
            "description": "New honest, working interface",
        },
    ]

    results = {}

    for interface in interfaces:
        print(f"{Fore.YELLOW}Testing {interface['name']} (Port {interface['port']}){Style.RESET_ALL}")

        try:
            response = requests.get(interface["url"], timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {interface['name']} is running")
                print(f"   📝 {interface['description']}")

                # Try to get additional info for API endpoints
                if "/health" in interface["url"]:
                    try:
                        data = response.json()
                        print(f"   📊 Status: {data.get('status', 'unknown')}")
                        if "interface" in data:
                            print(f"   🏷️  Interface Type: {data['interface']}")
                    except:
                        pass

                results[interface["name"]] = True
            else:
                print(f"   ❌ {interface['name']} returned status {response.status_code}")
                results[interface["name"]] = False

        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  {interface['name']} is not running")
            results[interface["name"]] = False
        except Exception as e:
            print(f"   ❌ Error testing {interface['name']}: {e}")
            results[interface["name"]] = False

        print()

    # Summary
    print(f"{Fore.CYAN}{'='*60}")
    print(f"MULTI-INTERFACE TEST SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}")

    running_count = sum(results.values())
    total_count = len(results)

    for name, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")

    print(
        f"\n{Fore.GREEN if running_count == total_count else Fore.YELLOW}Running: {running_count}/{total_count} interfaces{Style.RESET_ALL}"
    )

    if running_count == total_count:
        print(f"\n{Fore.GREEN}🎉 All interfaces are running successfully!{Style.RESET_ALL}")
        print(f"\n{Fore.BLUE}Available URLs:{Style.RESET_ALL}")
        print(f"• Backend API: http://localhost:8000")
        print(f"• Original Interface: http://localhost:8001")
        print(f"• Modern Interface: http://localhost:5173")

        # Test search on multiple interfaces
        print(f"\n{Fore.YELLOW}Testing Search Functionality:{Style.RESET_ALL}")
        test_search_endpoints()

    elif running_count > 0:
        print(
            f"\n{Fore.YELLOW}⚠️  Some interfaces are not running. You can still use the available ones.{Style.RESET_ALL}"
        )
    else:
        print(f"\n{Fore.RED}❌ No interfaces are running. Please start the servers first.{Style.RESET_ALL}")

    return running_count == total_count


def test_search_endpoints():
    """Test search functionality on available endpoints."""

    search_tests = [
        {
            "name": "Backend API Search",
            "url": "http://localhost:8000/api/search",
            "method": "POST",
            "data": {"query": "test", "max_results": 1},
        },
        {
            "name": "Original Interface Search",
            "url": "http://localhost:8001/search?query=test&max_results=1",
            "method": "GET",
            "data": None,
        },
    ]

    for test in search_tests:
        try:
            if test["method"] == "POST":
                response = requests.post(
                    test["url"],
                    json=test["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
            else:
                response = requests.get(test["url"], timeout=10)

            if response.status_code == 200:
                print(f"   ✅ {test['name']} working")
            else:
                print(f"   ⚠️  {test['name']} returned {response.status_code}")

        except Exception as e:
            print(f"   ❌ {test['name']} failed: {str(e)[:50]}...")


if __name__ == "__main__":
    test_all_interfaces()
