#!/usr/bin/env python3
"""
Browser Automation Testing for OmicsOracle Web Interface

This module provides automated browser testing using Selenium WebDriver
for UI functionality, JavaScript execution, and accessibility testing.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BrowserAutomationTestSuite:
    """Browser automation testing suite for OmicsOracle."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        browser: str = "chrome",
        headless: bool = True,
    ):
        """Initialize browser automation test suite."""
        self.base_url = base_url
        self.browser = browser
        self.headless = headless
        self.driver = None
        self.wait = None

    def setup_driver(self) -> None:
        """Set up the WebDriver instance."""
        try:
            if self.browser.lower() == "chrome":
                options = ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                self.driver = webdriver.Chrome(options=options)
            elif self.browser.lower() == "firefox":
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                self.driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")

            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 10)

        except Exception as e:
            raise WebDriverException(f"Failed to setup WebDriver: {str(e)}")

    def teardown_driver(self) -> None:
        """Clean up the WebDriver instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def test_page_loading(self) -> Dict[str, Any]:
        """Test basic page loading and navigation."""
        results = {}

        pages_to_test = [
            {"url": self.base_url, "name": "Home Page"},
            {"url": f"{self.base_url}/search", "name": "Search Page"},
            {"url": f"{self.base_url}/about", "name": "About Page"},
            {"url": f"{self.base_url}/docs", "name": "Documentation Page"},
        ]

        for page in pages_to_test:
            page_result = {
                "url": page["url"],
                "name": page["name"],
                "loaded": False,
                "load_time": None,
                "title": None,
                "status_code": None,
                "errors": [],
            }

            try:
                start_time = time.time()
                self.driver.get(page["url"])

                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )

                load_time = time.time() - start_time

                page_result.update(
                    {
                        "loaded": True,
                        "load_time": load_time,
                        "title": self.driver.title,
                        "current_url": self.driver.current_url,
                    }
                )

                # Check for JavaScript errors
                js_errors = self.driver.execute_script("return window.jsErrors || [];")
                if js_errors:
                    page_result["errors"].extend(js_errors)

            except TimeoutException:
                page_result["errors"].append("Page load timeout")
            except WebDriverException as e:
                page_result["errors"].append(f"WebDriver error: {str(e)}")
            except Exception as e:
                page_result["errors"].append(f"Unexpected error: {str(e)}")

            results[page["name"]] = page_result

        return results

    def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality and user interactions."""
        results = {
            "search_form_present": False,
            "search_input_functional": False,
            "search_results_displayed": False,
            "search_time": None,
            "results_count": 0,
            "pagination_works": False,
            "errors": [],
        }

        try:
            # Navigate to home page (where search form is located)
            self.driver.get(self.base_url)

            # Look for search form
            search_selectors = [
                "input[id='query']",
                "input[name='query']",
                "input[type='search']",
                ".search-input",
                "#search-input",
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    results["search_form_present"] = True
                    break
                except NoSuchElementException:
                    continue

            if not search_input:
                results["errors"].append("Search input not found")
                return results

            # Test search functionality
            test_query = "cancer genomics"
            start_time = time.time()

            # Clear and type in search input
            search_input.clear()
            search_input.send_keys(test_query)

            # Submit search
            search_input.send_keys(Keys.RETURN)

            # Wait for results
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results, .results, #results"))
                )

                search_time = time.time() - start_time
                results["search_input_functional"] = True
                results["search_results_displayed"] = True
                results["search_time"] = search_time

                # Count results
                result_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, ".result-item, .search-result, .result"
                )
                results["results_count"] = len(result_elements)

                # Test pagination if present
                try:
                    next_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        ".pagination .next, .next-page, button[aria-label='Next']",
                    )
                    if next_button.is_enabled():
                        next_button.click()
                        WebDriverWait(self.driver, 10).until(
                            EC.staleness_of(result_elements[0] if result_elements else None)
                        )
                        results["pagination_works"] = True
                except (NoSuchElementException, TimeoutException):
                    results["pagination_works"] = False

            except TimeoutException:
                results["errors"].append("Search results not loaded within timeout")

        except Exception as e:
            results["errors"].append(f"Search test error: {str(e)}")

        return results

    def test_ai_summarization(self) -> Dict[str, Any]:
        """Test AI summarization functionality."""
        results = {
            "summarization_available": False,
            "summarization_works": False,
            "summary_generated": False,
            "summary_time": None,
            "summary_length": 0,
            "errors": [],
        }

        try:
            # Navigate to home page where AI summarization is available
            self.driver.get(self.base_url)

            # Look for AI summarization toggle/select
            ai_selectors = [
                "select[id='enable-ai']",
                "select[name='enable_ai']",
                ".ai-toggle",
                "#ai-summarize",
            ]

            ai_element = None
            for selector in ai_selectors:
                try:
                    ai_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    results["summarization_available"] = True
                    break
                except NoSuchElementException:
                    continue

            if not ai_element:
                results["errors"].append("Summarization interface not found")
                return results

            # Check if we can find the search form to test AI with search
            search_input = None
            try:
                search_input = self.driver.find_element(By.CSS_SELECTOR, "input[id='query']")
            except NoSuchElementException:
                results["errors"].append("Search input not found for AI test")
                return results

            # Get sample text to summarize
            sample_text = "This is a test dataset about gene expression in cancer cells."

            try:
                search_input.clear()
                search_input.send_keys(sample_text)

                # Find summarize button
                summarize_element = self.driver.find_element(By.ID, "summarize-btn")

                # Click summarize button
                start_time = time.time()
                summarize_element.click()

                # Wait for summary to appear
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".summary, .result, .ai-output"))
                    )

                    summary_time = time.time() - start_time
                    summary_element = self.driver.find_element(
                        By.CSS_SELECTOR, ".summary, .result, .ai-output"
                    )
                    summary_text = summary_element.text

                    results.update(
                        {
                            "summarization_works": True,
                            "summary_generated": len(summary_text.strip()) > 0,
                            "summary_time": summary_time,
                            "summary_length": len(summary_text),
                        }
                    )

                except TimeoutException:
                    results["errors"].append("Summary generation timeout")

            except NoSuchElementException:
                results["errors"].append("Summarize button not found")

        except Exception as e:
            results["errors"].append(f"AI summarization test error: {str(e)}")

        return results

    def test_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design across different screen sizes."""
        results = {}

        # Test different screen sizes
        screen_sizes = [
            {"name": "Mobile", "width": 375, "height": 667},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Desktop", "width": 1920, "height": 1080},
            {"name": "Large Desktop", "width": 2560, "height": 1440},
        ]

        for size in screen_sizes:
            size_result = {
                "width": size["width"],
                "height": size["height"],
                "layout_intact": True,
                "navigation_accessible": True,
                "content_readable": True,
                "interactions_functional": True,
                "errors": [],
            }

            try:
                # Set window size
                self.driver.set_window_size(size["width"], size["height"])
                self.driver.get(self.base_url)

                # Check if navigation is accessible
                try:
                    nav_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, "nav, .navbar, .navigation, .menu"
                    )
                    if not nav_elements:
                        size_result["navigation_accessible"] = False
                        size_result["errors"].append("Navigation not found")
                except Exception as e:
                    size_result["navigation_accessible"] = False
                    size_result["errors"].append(f"Navigation error: {str(e)}")

                # Check content readability
                try:
                    # Check for horizontal scrolling
                    body_width = self.driver.execute_script("return document.body.scrollWidth")
                    window_width = self.driver.execute_script("return window.innerWidth")

                    if body_width > window_width + 20:  # Allow small tolerance
                        size_result["content_readable"] = False
                        size_result["errors"].append("Horizontal scrolling detected")

                    # Check font sizes
                    font_sizes = self.driver.execute_script(
                        """
                        var elements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
                        var sizes = [];
                        for (var i = 0; i < Math.min(elements.length, 10); i++) {
                            var style = window.getComputedStyle(elements[i]);
                            sizes.push(parseInt(style.fontSize));
                        }
                        return sizes;
                    """
                    )

                    if font_sizes and min(font_sizes) < 12:
                        size_result["content_readable"] = False
                        size_result["errors"].append("Font size too small")

                except Exception as e:
                    size_result["errors"].append(f"Content readability error: {str(e)}")

                # Test interactions (if search is available)
                try:
                    search_input = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "input[type='search'], input[name='query']",
                    )

                    # Check if input is large enough to interact with
                    input_size = search_input.size
                    if input_size["width"] < 30 or input_size["height"] < 30:
                        size_result["interactions_functional"] = False
                        size_result["errors"].append("Interactive elements too small")

                except NoSuchElementException:
                    pass  # Search input not required on all pages
                except Exception as e:
                    size_result["interactions_functional"] = False
                    size_result["errors"].append(f"Interaction error: {str(e)}")

            except Exception as e:
                size_result["layout_intact"] = False
                size_result["errors"].append(f"Layout error: {str(e)}")

            results[size["name"]] = size_result

        return results

    def test_accessibility(self) -> Dict[str, Any]:
        """Test basic accessibility features."""
        results = {
            "alt_text_present": True,
            "form_labels_present": True,
            "heading_structure_proper": True,
            "keyboard_navigation": True,
            "color_contrast_adequate": True,
            "focus_indicators": True,
            "accessibility_violations": [],
            "score": 0,
        }

        try:
            self.driver.get(self.base_url)

            # Check for images without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            images_without_alt = [
                img
                for img in images
                if not img.get_attribute("alt") or img.get_attribute("alt").strip() == ""
            ]

            if images_without_alt:
                results["alt_text_present"] = False
                results["accessibility_violations"].append(
                    f"{len(images_without_alt)} images without alt text"
                )

            # Check for form inputs without labels
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            inputs_without_labels = []

            for input_elem in inputs:
                input_id = input_elem.get_attribute("id")
                aria_label = input_elem.get_attribute("aria-label")

                if input_id:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        continue
                    except NoSuchElementException:
                        pass

                if not aria_label:
                    inputs_without_labels.append(input_elem)

            if inputs_without_labels:
                results["form_labels_present"] = False
                results["accessibility_violations"].append(
                    f"{len(inputs_without_labels)} form inputs without labels"
                )

            # Check heading structure
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            heading_levels = [int(h.tag_name[1]) for h in headings]

            if heading_levels:
                # Check if h1 is present and unique
                h1_count = heading_levels.count(1)
                if h1_count != 1:
                    results["heading_structure_proper"] = False
                    results["accessibility_violations"].append(
                        f"Improper h1 usage: {h1_count} h1 elements found"
                    )

                # Check for heading level jumps
                for i in range(1, len(heading_levels)):
                    if heading_levels[i] - heading_levels[i - 1] > 1:
                        results["heading_structure_proper"] = False
                        results["accessibility_violations"].append("Heading level jumps detected")
                        break

            # Test keyboard navigation
            try:
                # Try to tab through interactive elements
                interactive_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "a, button, input, textarea, select, [tabindex]",
                )

                if interactive_elements:
                    first_element = interactive_elements[0]
                    first_element.click()

                    # Try to tab to next element
                    ActionChains(self.driver).send_keys(Keys.TAB).perform()

                    # Check if focus moved
                    active_element = self.driver.switch_to.active_element
                    if active_element == first_element:
                        results["keyboard_navigation"] = False
                        results["accessibility_violations"].append("Keyboard navigation not working")

            except Exception as e:
                results["accessibility_violations"].append(f"Keyboard navigation test failed: {str(e)}")

            # Calculate accessibility score
            violations_count = len(results["accessibility_violations"])
            max_violations = 10  # Arbitrary maximum for scoring
            results["score"] = max(0, (max_violations - violations_count) / max_violations * 100)

        except Exception as e:
            results["accessibility_violations"].append(f"Accessibility test error: {str(e)}")

        return results

    def generate_browser_report(
        self,
        page_loading: Dict[str, Any],
        search_functionality: Dict[str, Any],
        ai_summarization: Dict[str, Any],
        responsive_design: Dict[str, Any],
        accessibility: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive browser automation test report."""

        # Calculate overall scores
        pages_loaded = sum(1 for page in page_loading.values() if page.get("loaded", False))
        total_pages = len(page_loading)
        page_load_score = (pages_loaded / total_pages * 100) if total_pages > 0 else 0

        search_score = 100 if search_functionality.get("search_results_displayed", False) else 0
        ai_score = 100 if ai_summarization.get("summary_generated", False) else 0

        responsive_screens = sum(
            1
            for screen in responsive_design.values()
            if screen.get("layout_intact", False) and screen.get("interactions_functional", False)
        )
        total_screens = len(responsive_design)
        responsive_score = (responsive_screens / total_screens * 100) if total_screens > 0 else 0

        accessibility_score = accessibility.get("score", 0)

        overall_score = (
            page_load_score + search_score + ai_score + responsive_score + accessibility_score
        ) / 5

        # Generate recommendations
        recommendations = []

        if page_load_score < 100:
            recommendations.append("Fix page loading issues")
        if search_score < 100:
            recommendations.append("Improve search functionality")
        if ai_score < 100:
            recommendations.append("Fix AI summarization features")
        if responsive_score < 80:
            recommendations.append("Improve responsive design")
        if accessibility_score < 80:
            recommendations.append("Address accessibility violations")

        return {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "browser": self.browser,
            "overall_score": overall_score,
            "category_scores": {
                "page_loading": page_load_score,
                "search_functionality": search_score,
                "ai_summarization": ai_score,
                "responsive_design": responsive_score,
                "accessibility": accessibility_score,
            },
            "detailed_results": {
                "page_loading": page_loading,
                "search_functionality": search_functionality,
                "ai_summarization": ai_summarization,
                "responsive_design": responsive_design,
                "accessibility": accessibility,
            },
            "recommendations": recommendations,
            "test_status": "PASSED" if overall_score >= 70 else "FAILED",
        }


def run_browser_automation_tests(browser: str = "chrome", headless: bool = True) -> Dict[str, Any]:
    """Run all browser automation tests and generate report."""
    print(f"Starting Browser Automation Testing with {browser}...")

    # Initialize test suite
    browser_suite = BrowserAutomationTestSuite(browser=browser, headless=headless)

    try:
        # Setup WebDriver
        print("Setting up WebDriver...")
        browser_suite.setup_driver()

        # Run all test categories
        print("Testing page loading...")
        page_loading_results = browser_suite.test_page_loading()

        print("Testing search functionality...")
        search_results = browser_suite.test_search_functionality()

        print("Testing AI summarization...")
        ai_results = browser_suite.test_ai_summarization()

        print("Testing responsive design...")
        responsive_results = browser_suite.test_responsive_design()

        print("Testing accessibility...")
        accessibility_results = browser_suite.test_accessibility()

        # Generate comprehensive report
        print("Generating browser automation report...")
        report = browser_suite.generate_browser_report(
            page_loading_results,
            search_results,
            ai_results,
            responsive_results,
            accessibility_results,
        )

        # Save results
        with open("browser_automation_results.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Browser automation testing completed. Status: {report['test_status']}")
        print("Results saved to: browser_automation_results.json")

        return report

    finally:
        # Clean up WebDriver
        browser_suite.teardown_driver()


if __name__ == "__main__":
    # Run tests with Chrome (headless by default)
    run_browser_automation_tests()
