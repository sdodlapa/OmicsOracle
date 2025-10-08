#!/usr/bin/env python3
"""Test quick CI check with non-existent command."""

import subprocess
import sys
from typing import List


def run_check(cmd: List[str], description: str) -> bool:
    """Run a single check and return success status."""
    print(f"\n[CHECK] {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[PASS] {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {cmd[0]}")
        return False


def main() -> int:
    """Test with a non-existent command."""
    print("=== Testing Error Handling ===")

    # Test with a command that doesn't exist
    result = run_check(["nonexistent_command", "--version"], "Non-existent Command")

    if not result:
        print("[SUCCESS] Error handling works correctly")
        return 0
    else:
        print("[ERROR] Should have failed but didn't")
        return 1


if __name__ == "__main__":
    sys.exit(main())
