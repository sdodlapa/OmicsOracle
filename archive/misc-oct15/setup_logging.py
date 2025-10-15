"""
Global logging configuration utility for OmicsOracle.

Use this to enable file logging for ANY script or test.
All logs will be saved to timestamped files in the logs/ directory.

Usage:
    from setup_logging import setup_logging

    # Basic usage
    setup_logging()

    # Custom log level
    setup_logging(level=logging.DEBUG)

    # Custom log file name
    setup_logging(log_name="my_test")
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_name: Optional[str] = None,
    level: int = logging.INFO,
    log_dir: Path = Path("logs"),
    console: bool = True,
) -> Path:
    """
    Configure logging to file and optionally console.

    Args:
        log_name: Name for log file (default: "omics_oracle_TIMESTAMP")
        level: Logging level (default: INFO)
        log_dir: Directory for log files (default: logs/)
        console: Also log to console (default: True)

    Returns:
        Path to log file
    """
    # Create logs directory
    log_dir.mkdir(exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if log_name:
        log_file = log_dir / f"{log_name}_{timestamp}.log"
    else:
        log_file = log_dir / f"omics_oracle_{timestamp}.log"

    # Configure handlers
    handlers = [logging.FileHandler(log_file)]
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("OmicsOracle Logging Configured")
    logger.info(f"Log file: {log_file.absolute()}")
    logger.info(f"Log level: {logging.getLevelName(level)}")
    logger.info(f"Console output: {console}")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 80)

    return log_file


def setup_test_logging(test_name: str, level: int = logging.INFO) -> Path:
    """
    Convenience function for test scripts.

    Args:
        test_name: Name of the test (used in filename)
        level: Logging level

    Returns:
        Path to log file
    """
    return setup_logging(log_name=f"test_{test_name}", level=level)


def get_latest_log(log_dir: Path = Path("logs")) -> Optional[Path]:
    """
    Get the most recent log file.

    Args:
        log_dir: Directory containing log files

    Returns:
        Path to latest log file, or None if no logs exist
    """
    if not log_dir.exists():
        return None

    log_files = sorted(
        log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True
    )
    return log_files[0] if log_files else None


def analyze_log_for_bottlenecks(log_file: Path) -> dict:
    """
    Analyze a log file to identify performance bottlenecks.

    Args:
        log_file: Path to log file

    Returns:
        Dictionary with bottleneck analysis
    """
    if not log_file.exists():
        return {"error": "Log file not found"}

    analysis = {
        "total_lines": 0,
        "errors": 0,
        "warnings": 0,
        "rate_limits": 0,
        "api_calls": {
            "openai": 0,
            "openalex": 0,
            "semantic_scholar": 0,
            "pubmed": 0,
        },
        "phases": {},
    }

    with open(log_file) as f:
        for line in f:
            analysis["total_lines"] += 1

            # Count severity levels
            if " - ERROR - " in line:
                analysis["errors"] += 1
            elif " - WARNING - " in line:
                analysis["warnings"] += 1

            # Detect rate limiting
            if "Rate limited" in line or "429" in line:
                analysis["rate_limits"] += 1

            # Count API calls
            if "HTTP Request: POST https://api.openai.com" in line:
                analysis["api_calls"]["openai"] += 1
            elif "openalex" in line.lower():
                analysis["api_calls"]["openalex"] += 1
            elif "semantic_scholar" in line.lower():
                analysis["api_calls"]["semantic_scholar"] += 1
            elif "pubmed" in line.lower():
                analysis["api_calls"]["pubmed"] += 1

            # Detect phase transitions
            if "Enriching" in line or "Analyzing" in line or "Searching" in line:
                # Extract phase name
                parts = line.split(" - INFO - ")
                if len(parts) > 1:
                    phase = parts[1].split(":")[0].strip()
                    analysis["phases"][phase] = analysis["phases"].get(phase, 0) + 1

    return analysis


if __name__ == "__main__":
    # Demo usage
    log_file = setup_logging(log_name="demo")
    logger = logging.getLogger(__name__)

    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    print(f"\nLog file created: {log_file}")
    print("\nAnalyzing log...")
    analysis = analyze_log_for_bottlenecks(log_file)

    print(f"Total lines: {analysis['total_lines']}")
    print(f"Errors: {analysis['errors']}")
    print(f"Warnings: {analysis['warnings']}")
