"""
File Integrity Utilities

SHA256 hashing and verification for PDFs and other binary files.
"""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal SHA256 hash string

    Example:
        hash_value = calculate_sha256(Path("paper.pdf"))
        # "a3b5c7d9..."
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in 8KB chunks for memory efficiency
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify file integrity by comparing SHA256 hash.

    Args:
        file_path: Path to file
        expected_hash: Expected SHA256 hash

    Returns:
        True if hash matches, False otherwise

    Example:
        is_valid = verify_file_integrity(
            Path("paper.pdf"),
            "a3b5c7d9..."
        )
    """
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    actual_hash = calculate_sha256(file_path)

    if actual_hash != expected_hash:
        logger.error(
            f"Hash mismatch for {file_path}\n" f"  Expected: {expected_hash}\n" f"  Actual:   {actual_hash}"
        )
        return False

    return True


def get_file_info(file_path: Path) -> dict:
    """
    Get file metadata including size and hash.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file metadata

    Example:
        info = get_file_info(Path("paper.pdf"))
        # {
        #     "path": "paper.pdf",
        #     "size_bytes": 1234567,
        #     "sha256": "a3b5c7d9...",
        #     "exists": True
        # }
    """
    if not file_path.exists():
        return {
            "path": str(file_path),
            "size_bytes": 0,
            "sha256": None,
            "exists": False,
        }

    return {
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "sha256": calculate_sha256(file_path),
        "exists": True,
    }


class IntegrityVerifier:
    """
    Batch integrity verification for multiple files.

    Example:
        verifier = IntegrityVerifier()
        verifier.add_file(Path("paper1.pdf"), "hash1")
        verifier.add_file(Path("paper2.pdf"), "hash2")

        results = verifier.verify_all()
        # {
        #     "total": 2,
        #     "valid": 1,
        #     "invalid": 1,
        #     "failures": ["paper2.pdf"]
        # }
    """

    def __init__(self):
        """Initialize verifier."""
        self.files = []  # List of (path, expected_hash) tuples

    def add_file(self, file_path: Path, expected_hash: str):
        """Add file to verification queue."""
        self.files.append((file_path, expected_hash))

    def verify_all(self) -> dict:
        """
        Verify all queued files.

        Returns:
            Dictionary with verification results
        """
        total = len(self.files)
        valid = 0
        invalid = 0
        failures = []

        for file_path, expected_hash in self.files:
            if verify_file_integrity(file_path, expected_hash):
                valid += 1
            else:
                invalid += 1
                failures.append(str(file_path))

        return {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "failures": failures,
            "success_rate": (valid / total * 100) if total > 0 else 0.0,
        }

    def clear(self):
        """Clear verification queue."""
        self.files = []
