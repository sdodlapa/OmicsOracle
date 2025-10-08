#!/usr/bin/env python3
"""
Mobile and Responsive Testing for OmicsOracle Web Interface

This module provides mobile-specific testing including touch interactions,
device emulation, and mobile performance testing.
"""

import json
import time
from typing import Any, Dict

import requests


class MobileTestSuite:
    """Mobile and responsive testing suite for OmicsOracle."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize mobile test suite."""
        self.base_url = base_url
        self.session = requests.Session()

        # Common mobile user agents
        self.mobile_user_agents = {
            "iPhone": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Android": "Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "iPad": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        }

        # Mobile viewport sizes
        self.mobile_viewports = {
            "iPhone_SE": {"width": 375, "height": 667},
            "iPhone_12": {"width": 390, "height": 844},
            "iPhone_12_Pro_Max": {"width": 428, "height": 926},
            "Android_Small": {"width": 360, "height": 640},
            "Android_Medium": {"width": 412, "height": 732},
            "Android_Large": {"width": 414, "height": 896},
            "iPad": {"width": 768, "height": 1024},
            "iPad_Pro": {"width": 1024, "height": 1366},
        }

    def test_mobile_responsiveness(self) -> Dict[str, Any]:
        """Test mobile responsiveness using HTTP requests with mobile user agents."""
        results = {}

        for device, user_agent in self.mobile_user_agents.items():
            device_result = {
                "user_agent": user_agent,
                "pages_tested": {},
                "mobile_optimized": True,
                "viewport_meta_present": False,
                "errors": [],
            }

            # Set mobile user agent
            self.session.headers.update({"User-Agent": user_agent})

            # Test main pages
            pages_to_test = [
                {"url": self.base_url, "name": "home"},
                {"url": f"{self.base_url}/search", "name": "search"},
                {"url": f"{self.base_url}/about", "name": "about"},
            ]

            for page in pages_to_test:
                page_result = {
                    "status_code": None,
                    "load_time": None,
                    "content_size": None,
                    "mobile_features": {
                        "viewport_meta": False,
                        "touch_friendly": False,
                        "mobile_css": False,
                        "responsive_images": False,
                    },
                    "errors": [],
                }

                try:
                    start_time = time.time()
                    response = self.session.get(page["url"], timeout=15)
                    load_time = time.time() - start_time

                    page_result.update(
                        {
                            "status_code": response.status_code,
                            "load_time": load_time,
                            "content_size": len(response.content),
                        }
                    )

                    if response.status_code == 200:
                        content = response.text.lower()

                        # Check for viewport meta tag
                        if 'name="viewport"' in content:
                            page_result["mobile_features"]["viewport_meta"] = True
                            device_result["viewport_meta_present"] = True

                        # Check for touch-friendly elements
                        touch_indicators = [
                            "touch-action",
                            "ontouchstart",
                            "ontouchmove",
                            "mobile-menu",
                            "hamburger",
                            "swipe",
                        ]
                        if any(indicator in content for indicator in touch_indicators):
                            page_result["mobile_features"]["touch_friendly"] = True

                        # Check for mobile CSS
                        mobile_css_indicators = [
                            "@media",
                            "mobile",
                            "responsive",
                            "min-width",
                            "max-width",
                            "screen",
                        ]
                        if any(indicator in content for indicator in mobile_css_indicators):
                            page_result["mobile_features"]["mobile_css"] = True

                        # Check for responsive images
                        responsive_img_indicators = [
                            "srcset",
                            "sizes",
                            "picture",
                            "img-responsive",
                            "responsive-img",
                        ]
                        if any(indicator in content for indicator in responsive_img_indicators):
                            page_result["mobile_features"]["responsive_images"] = True

                except requests.exceptions.RequestException as e:
                    page_result["errors"].append(f"Request failed: {str(e)}")
                except Exception as e:
                    page_result["errors"].append(f"Unexpected error: {str(e)}")

                device_result["pages_tested"][page["name"]] = page_result

            # Determine if mobile optimized
            mobile_features_count = sum(
                sum(page["mobile_features"].values())
                for page in device_result["pages_tested"].values()
                if isinstance(page, dict) and "mobile_features" in page
            )

            total_possible_features = len(pages_to_test) * 4  # 4 features per page
            device_result["mobile_optimized"] = mobile_features_count >= (total_possible_features * 0.5)

            results[device] = device_result

        return results

    def test_mobile_performance(self) -> Dict[str, Any]:
        """Test mobile-specific performance metrics."""
        results = {
            "page_load_times": {},
            "resource_sizes": {},
            "mobile_performance_score": 0,
            "recommendations": [],
        }

        # Test with mobile user agent
        mobile_ua = self.mobile_user_agents["iPhone"]
        self.session.headers.update({"User-Agent": mobile_ua})

        pages_to_test = [
            self.base_url,
            f"{self.base_url}/search",
            f"{self.base_url}/about",
        ]

        total_load_time = 0
        total_size = 0
        page_count = 0

        for page_url in pages_to_test:
            try:
                start_time = time.time()
                response = self.session.get(page_url, timeout=20)
                load_time = time.time() - start_time

                page_name = page_url.split("/")[-1] or "home"
                results["page_load_times"][page_name] = load_time
                results["resource_sizes"][page_name] = len(response.content)

                total_load_time += load_time
                total_size += len(response.content)
                page_count += 1

            except requests.exceptions.RequestException as e:
                page_name = page_url.split("/")[-1] or "home"
                results["page_load_times"][page_name] = None
                results["resource_sizes"][page_name] = None
                results["recommendations"].append(f"Failed to load {page_name}: {str(e)}")

        # Calculate performance score
        if page_count > 0:
            avg_load_time = total_load_time / page_count
            avg_size = total_size / page_count

            # Score based on mobile performance criteria
            # Good mobile load time: < 3 seconds
            # Good mobile page size: < 1MB
            time_score = max(0, (3 - avg_load_time) / 3 * 100) if avg_load_time <= 3 else 0
            size_score = max(0, (1000000 - avg_size) / 1000000 * 100) if avg_size <= 1000000 else 0

            results["mobile_performance_score"] = (time_score + size_score) / 2

            # Generate recommendations
            if avg_load_time > 3:
                results["recommendations"].append("Optimize page load times for mobile (target < 3 seconds)")
            if avg_size > 1000000:  # 1MB
                results["recommendations"].append("Reduce page size for mobile (target < 1MB)")
            if avg_load_time > 5:
                results["recommendations"].append("Critical: Page load times too slow for mobile users")

        return results

    def test_touch_interactions(self) -> Dict[str, Any]:
        """Test touch interaction compatibility."""
        results = {
            "touch_targets_adequate": True,
            "hover_alternatives": True,
            "scroll_behavior": True,
            "gesture_support": False,
            "touch_feedback": False,
            "issues": [],
        }

        # Use mobile user agent
        mobile_ua = self.mobile_user_agents["Android"]
        self.session.headers.update({"User-Agent": mobile_ua})

        try:
            response = self.session.get(self.base_url, timeout=10)
            content = response.text.lower()

            # Check for touch target size considerations
            touch_size_indicators = [
                "min-height: 44px",
                "min-height: 48px",
                "touch-target",
                "tap-target",
                "button-size",
            ]

            if not any(indicator in content for indicator in touch_size_indicators):
                results["touch_targets_adequate"] = False
                results["issues"].append("No evidence of adequate touch target sizing")

            # Check for hover alternative implementations
            hover_alternatives = [
                "click",
                "tap",
                "touch",
                "active",
                "focus",
                "ontouchstart",
                "touch-action",
            ]

            if not any(alt in content for alt in hover_alternatives):
                results["hover_alternatives"] = False
                results["issues"].append("No touch alternatives for hover interactions detected")

            # Check for scroll behavior optimization
            scroll_indicators = [
                "overflow-x: hidden",
                "scroll-behavior",
                "touch-action: pan",
                "momentum-scrolling",
            ]

            if not any(indicator in content for indicator in scroll_indicators):
                results["scroll_behavior"] = False
                results["issues"].append("No mobile scroll optimization detected")

            # Check for gesture support
            gesture_indicators = [
                "swipe",
                "pinch",
                "zoom",
                "gesture",
                "ontouchstart",
                "ontouchmove",
                "ontouchend",
            ]

            if any(indicator in content for indicator in gesture_indicators):
                results["gesture_support"] = True

            # Check for touch feedback
            feedback_indicators = [
                "active",
                "pressed",
                "touch-feedback",
                "ripple",
                "highlight",
                "vibrate",
            ]

            if any(indicator in content for indicator in feedback_indicators):
                results["touch_feedback"] = True

        except requests.exceptions.RequestException as e:
            results["issues"].append(f"Failed to test touch interactions: {str(e)}")

        return results

    def test_mobile_accessibility(self) -> Dict[str, Any]:
        """Test mobile-specific accessibility features."""
        results = {
            "screen_reader_friendly": True,
            "keyboard_navigation": True,
            "color_contrast_mobile": True,
            "text_scaling": True,
            "accessibility_score": 0,
            "violations": [],
        }

        # Use mobile user agent
        mobile_ua = self.mobile_user_agents["iPhone"]
        self.session.headers.update({"User-Agent": mobile_ua})

        try:
            response = self.session.get(self.base_url, timeout=10)
            content = response.text.lower()

            # Check for screen reader support
            screen_reader_indicators = [
                "aria-",
                "role=",
                "alt=",
                "title=",
                "sr-only",
                "screen-reader",
                "voiceover",
            ]

            screen_reader_count = sum(content.count(indicator) for indicator in screen_reader_indicators)
            if screen_reader_count < 5:  # Arbitrary minimum
                results["screen_reader_friendly"] = False
                results["violations"].append("Insufficient screen reader support")

            # Check for keyboard navigation support
            keyboard_indicators = [
                "tabindex",
                "focus",
                "accesskey",
                "keyboard-navigation",
                "tab-order",
            ]

            if not any(indicator in content for indicator in keyboard_indicators):
                results["keyboard_navigation"] = False
                results["violations"].append("No keyboard navigation support detected")

            # Check for mobile text scaling
            text_scale_indicators = [
                "rem",
                "em",
                "font-size: calc",
                "text-size-adjust",
                "zoom",
            ]

            if not any(indicator in content for indicator in text_scale_indicators):
                results["text_scaling"] = False
                results["violations"].append("No text scaling support detected")

            # Calculate accessibility score
            features = [
                results["screen_reader_friendly"],
                results["keyboard_navigation"],
                results["color_contrast_mobile"],
                results["text_scaling"],
            ]

            results["accessibility_score"] = sum(features) / len(features) * 100

        except requests.exceptions.RequestException as e:
            results["violations"].append(f"Failed to test mobile accessibility: {str(e)}")

        return results

    def generate_mobile_report(
        self,
        responsiveness: Dict[str, Any],
        performance: Dict[str, Any],
        touch_interactions: Dict[str, Any],
        accessibility: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive mobile testing report."""

        # Calculate overall scores
        responsive_devices = sum(
            1 for device in responsiveness.values() if device.get("mobile_optimized", False)
        )
        total_devices = len(responsiveness)
        responsiveness_score = (responsive_devices / total_devices * 100) if total_devices > 0 else 0

        performance_score = performance.get("mobile_performance_score", 0)

        touch_features = [
            touch_interactions.get("touch_targets_adequate", False),
            touch_interactions.get("hover_alternatives", False),
            touch_interactions.get("scroll_behavior", False),
        ]
        touch_score = sum(touch_features) / len(touch_features) * 100

        accessibility_score = accessibility.get("accessibility_score", 0)

        overall_score = (responsiveness_score + performance_score + touch_score + accessibility_score) / 4

        # Generate recommendations
        recommendations = []

        if responsiveness_score < 80:
            recommendations.append("Improve mobile responsiveness across devices")
        if performance_score < 70:
            recommendations.append("Optimize mobile performance (load times and page sizes)")
        if touch_score < 80:
            recommendations.append("Enhance touch interaction support")
        if accessibility_score < 80:
            recommendations.append("Address mobile accessibility issues")

        # Combine all specific recommendations
        recommendations.extend(performance.get("recommendations", []))
        recommendations.extend([f"Touch: {issue}" for issue in touch_interactions.get("issues", [])])
        recommendations.extend(
            [f"Accessibility: {violation}" for violation in accessibility.get("violations", [])]
        )

        return {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "overall_mobile_score": overall_score,
            "category_scores": {
                "responsiveness": responsiveness_score,
                "performance": performance_score,
                "touch_interactions": touch_score,
                "accessibility": accessibility_score,
            },
            "detailed_results": {
                "responsiveness": responsiveness,
                "performance": performance,
                "touch_interactions": touch_interactions,
                "accessibility": accessibility,
            },
            "recommendations": recommendations,
            "mobile_ready": overall_score >= 70,
        }


def run_mobile_tests() -> Dict[str, Any]:
    """Run all mobile tests and generate report."""
    print("Starting Mobile and Responsive Testing...")

    # Initialize test suite
    mobile_suite = MobileTestSuite()

    # Run all test categories
    print("Testing mobile responsiveness...")
    responsiveness_results = mobile_suite.test_mobile_responsiveness()

    print("Testing mobile performance...")
    performance_results = mobile_suite.test_mobile_performance()

    print("Testing touch interactions...")
    touch_results = mobile_suite.test_touch_interactions()

    print("Testing mobile accessibility...")
    accessibility_results = mobile_suite.test_mobile_accessibility()

    # Generate comprehensive report
    print("Generating mobile testing report...")
    report = mobile_suite.generate_mobile_report(
        responsiveness_results,
        performance_results,
        touch_results,
        accessibility_results,
    )

    # Save results
    with open("mobile_test_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Mobile testing completed. Mobile ready: {report['mobile_ready']}")
    print("Results saved to: mobile_test_results.json")

    return report


if __name__ == "__main__":
    run_mobile_tests()
