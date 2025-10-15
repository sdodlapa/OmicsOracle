"""
GEO-Centric Storage Manager

Organizes PDFs and other files by GEO dataset ID.
Provides manifest management and integrity verification.

Directory Structure:
    data/
    +-- pdfs/by_geo/
    |   +-- GSE12345/
    |   |   +-- pmid_12345678.pdf
    |   |   +-- pmid_87654321.pdf
    |   |   +-- .manifest.json
    |   +-- GSE67890/
    |       +-- ...
    +-- enriched/by_geo/
        +-- GSE12345/
            +-- pmid_12345678.json
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .integrity import calculate_sha256, get_file_info, verify_file_integrity

logger = logging.getLogger(__name__)


class GEOStorage:
    """
    GEO-centric filesystem storage manager.

    Features:
    - Organize files by GEO dataset ID
    - Automatic directory creation
    - SHA256 hash calculation
    - Manifest file management
    - Integrity verification

    Example:
        storage = GEOStorage("data")

        # Save PDF
        pdf_info = storage.save_pdf(
            geo_id="GSE12345",
            pmid="12345678",
            source_path=Path("downloaded.pdf")
        )

        # Get PDF path
        pdf_path = storage.get_pdf_path("GSE12345", "12345678")

        # Verify integrity
        is_valid = storage.verify_pdf("GSE12345", "12345678")

        # Get GEO statistics
        stats = storage.get_geo_stats("GSE12345")
    """

    def __init__(self, base_dir: str | Path):
        """
        Initialize GEO storage.

        Args:
            base_dir: Base directory for all data (e.g., "data")
        """
        self.base_dir = Path(base_dir)
        self.pdfs_dir = self.base_dir / "pdfs" / "by_geo"
        self.enriched_dir = self.base_dir / "enriched" / "by_geo"

        # Create base directories
        self.pdfs_dir.mkdir(parents=True, exist_ok=True)
        self.enriched_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized GEOStorage at {self.base_dir}")

    def _get_geo_dir(self, geo_id: str, content_type: str = "pdfs") -> Path:
        """
        Get directory for a GEO dataset.

        Args:
            geo_id: GEO dataset ID (e.g., "GSE12345")
            content_type: Type of content ("pdfs" or "enriched")

        Returns:
            Path to GEO directory
        """
        if content_type == "pdfs":
            geo_dir = self.pdfs_dir / geo_id
        elif content_type == "enriched":
            geo_dir = self.enriched_dir / geo_id
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        geo_dir.mkdir(parents=True, exist_ok=True)
        return geo_dir

    def _get_manifest_path(self, geo_id: str) -> Path:
        """Get path to manifest file for a GEO dataset."""
        return self._get_geo_dir(geo_id, "pdfs") / ".manifest.json"

    def _load_manifest(self, geo_id: str) -> dict:
        """Load manifest file for a GEO dataset."""
        manifest_path = self._get_manifest_path(geo_id)

        if not manifest_path.exists():
            return {"geo_id": geo_id, "files": {}, "created_at": datetime.utcnow().isoformat()}

        with open(manifest_path) as f:
            return json.load(f)

    def _save_manifest(self, geo_id: str, manifest: dict):
        """Save manifest file for a GEO dataset."""
        manifest_path = self._get_manifest_path(geo_id)
        manifest["updated_at"] = datetime.utcnow().isoformat()

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    # =========================================================================
    # PDF OPERATIONS
    # =========================================================================

    def save_pdf(
        self,
        geo_id: str,
        pmid: str,
        source_path: Path,
        verify_after_save: bool = True,
    ) -> Dict[str, any]:
        """
        Save PDF to GEO-organized directory.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            source_path: Path to source PDF file
            verify_after_save: Verify integrity after saving

        Returns:
            Dictionary with file info:
            {
                "pdf_path": "by_geo/GSE12345/pmid_12345678.pdf",
                "full_path": Path object,
                "sha256": "hash...",
                "size_bytes": 1234567,
                "verified": True
            }

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If verification fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source PDF not found: {source_path}")

        # Get destination path
        geo_dir = self._get_geo_dir(geo_id, "pdfs")
        dest_filename = f"pmid_{pmid}.pdf"
        dest_path = geo_dir / dest_filename

        # Calculate hash before copying
        source_hash = calculate_sha256(source_path)
        source_size = source_path.stat().st_size

        # Copy file
        shutil.copy2(source_path, dest_path)
        logger.info(f"Saved PDF: {dest_path}")

        # Verify after save
        verified = False
        if verify_after_save:
            verified = verify_file_integrity(dest_path, source_hash)
            if not verified:
                raise ValueError(f"Integrity verification failed for {dest_path}")

        # Update manifest
        manifest = self._load_manifest(geo_id)
        manifest["files"][pmid] = {
            "filename": dest_filename,
            "sha256": source_hash,
            "size_bytes": source_size,
            "saved_at": datetime.utcnow().isoformat(),
            "verified": verified,
        }
        self._save_manifest(geo_id, manifest)

        # Return relative path for database storage
        relative_path = dest_path.relative_to(self.base_dir)

        return {
            "pdf_path": str(relative_path),  # For database
            "full_path": dest_path,  # For direct access
            "sha256": source_hash,
            "size_bytes": source_size,
            "verified": verified,
        }

    def get_pdf_path(self, geo_id: str, pmid: str, absolute: bool = True) -> Optional[Path]:
        """
        Get path to PDF file.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            absolute: Return absolute path (True) or relative (False)

        Returns:
            Path to PDF file or None if not found
        """
        geo_dir = self._get_geo_dir(geo_id, "pdfs")
        pdf_path = geo_dir / f"pmid_{pmid}.pdf"

        if not pdf_path.exists():
            return None

        if absolute:
            return pdf_path
        else:
            return pdf_path.relative_to(self.base_dir)

    def verify_pdf(self, geo_id: str, pmid: str) -> bool:
        """
        Verify PDF integrity using manifest hash.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID

        Returns:
            True if PDF exists and hash matches manifest
        """
        pdf_path = self.get_pdf_path(geo_id, pmid)
        if not pdf_path:
            logger.warning(f"PDF not found for verification: {geo_id}/{pmid}")
            return False

        manifest = self._load_manifest(geo_id)
        if pmid not in manifest["files"]:
            logger.warning(f"No manifest entry for: {geo_id}/{pmid}")
            return False

        expected_hash = manifest["files"][pmid]["sha256"]
        return verify_file_integrity(pdf_path, expected_hash)

    def delete_pdf(self, geo_id: str, pmid: str) -> bool:
        """
        Delete PDF file and remove from manifest.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID

        Returns:
            True if deleted, False if not found
        """
        pdf_path = self.get_pdf_path(geo_id, pmid)
        if not pdf_path:
            return False

        # Remove file
        pdf_path.unlink()
        logger.info(f"Deleted PDF: {pdf_path}")

        # Update manifest
        manifest = self._load_manifest(geo_id)
        if pmid in manifest["files"]:
            del manifest["files"][pmid]
            self._save_manifest(geo_id, manifest)

        return True

    # =========================================================================
    # ENRICHED CONTENT OPERATIONS
    # =========================================================================

    def save_enriched(
        self,
        geo_id: str,
        pmid: str,
        content: dict,
    ) -> Path:
        """
        Save enriched content as JSON.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            content: Dictionary to save as JSON

        Returns:
            Path to saved file
        """
        geo_dir = self._get_geo_dir(geo_id, "enriched")
        json_path = geo_dir / f"pmid_{pmid}.json"

        with open(json_path, "w") as f:
            json.dump(content, f, indent=2)

        logger.info(f"Saved enriched content: {json_path}")
        return json_path

    def get_enriched(self, geo_id: str, pmid: str) -> Optional[dict]:
        """
        Load enriched content from JSON.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID

        Returns:
            Dictionary or None if not found
        """
        geo_dir = self._get_geo_dir(geo_id, "enriched")
        json_path = geo_dir / f"pmid_{pmid}.json"

        if not json_path.exists():
            return None

        with open(json_path) as f:
            return json.load(f)

    # =========================================================================
    # STATISTICS & MANAGEMENT
    # =========================================================================

    def get_geo_stats(self, geo_id: str) -> Dict[str, any]:
        """
        Get statistics for a GEO dataset.

        Returns:
            Dictionary with statistics:
            {
                "geo_id": "GSE12345",
                "total_pdfs": 10,
                "total_size_bytes": 12345678,
                "total_size_mb": 11.77,
                "files": ["12345678", "87654321", ...],
                "has_manifest": True
            }
        """
        geo_dir = self._get_geo_dir(geo_id, "pdfs")
        pdf_files = list(geo_dir.glob("pmid_*.pdf"))

        total_size = sum(f.stat().st_size for f in pdf_files)
        pmids = [f.stem.replace("pmid_", "") for f in pdf_files]

        manifest_path = self._get_manifest_path(geo_id)

        return {
            "geo_id": geo_id,
            "total_pdfs": len(pdf_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": sorted(pmids),
            "has_manifest": manifest_path.exists(),
        }

    def list_all_geo_ids(self) -> List[str]:
        """
        Get list of all GEO dataset IDs with stored files.

        Returns:
            List of GEO IDs
        """
        geo_dirs = [d for d in self.pdfs_dir.iterdir() if d.is_dir()]
        return sorted([d.name for d in geo_dirs])

    def verify_all_pdfs(self, geo_id: str) -> Dict[str, any]:
        """
        Verify integrity of all PDFs for a GEO dataset.

        Args:
            geo_id: GEO dataset ID

        Returns:
            Dictionary with verification results
        """
        manifest = self._load_manifest(geo_id)
        total = len(manifest["files"])
        valid = 0
        invalid = 0
        failures = []

        for pmid in manifest["files"]:
            if self.verify_pdf(geo_id, pmid):
                valid += 1
            else:
                invalid += 1
                failures.append(pmid)

        return {
            "geo_id": geo_id,
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "failures": failures,
            "success_rate": (valid / total * 100) if total > 0 else 0.0,
        }

    def rebuild_manifest(self, geo_id: str) -> dict:
        """
        Rebuild manifest from existing PDF files.

        Useful for recovery if manifest is lost or corrupted.

        Args:
            geo_id: GEO dataset ID

        Returns:
            Rebuilt manifest dictionary
        """
        geo_dir = self._get_geo_dir(geo_id, "pdfs")
        pdf_files = list(geo_dir.glob("pmid_*.pdf"))

        manifest = {"geo_id": geo_id, "files": {}, "created_at": datetime.utcnow().isoformat()}

        for pdf_path in pdf_files:
            pmid = pdf_path.stem.replace("pmid_", "")
            file_info = get_file_info(pdf_path)

            manifest["files"][pmid] = {
                "filename": pdf_path.name,
                "sha256": file_info["sha256"],
                "size_bytes": file_info["size_bytes"],
                "saved_at": datetime.utcnow().isoformat(),
                "verified": True,
            }

        self._save_manifest(geo_id, manifest)
        logger.info(f"Rebuilt manifest for {geo_id}: {len(manifest['files'])} files")

        return manifest

    def export_geo_dataset(self, geo_id: str, output_dir: Path) -> Dict[str, any]:
        """
        Export all files for a GEO dataset to a directory.

        Args:
            geo_id: GEO dataset ID
            output_dir: Output directory

        Returns:
            Dictionary with export statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy PDFs
        geo_dir = self._get_geo_dir(geo_id, "pdfs")
        pdf_files = list(geo_dir.glob("pmid_*.pdf"))

        for pdf_file in pdf_files:
            dest_path = output_dir / pdf_file.name
            shutil.copy2(pdf_file, dest_path)

        # Copy manifest
        manifest_path = self._get_manifest_path(geo_id)
        if manifest_path.exists():
            shutil.copy2(manifest_path, output_dir / ".manifest.json")

        # Copy enriched content if available
        enriched_dir = self._get_geo_dir(geo_id, "enriched")
        if enriched_dir.exists():
            enriched_files = list(enriched_dir.glob("pmid_*.json"))
            for json_file in enriched_files:
                dest_path = output_dir / json_file.name
                shutil.copy2(json_file, dest_path)

        logger.info(f"Exported {len(pdf_files)} files for {geo_id} to {output_dir}")

        return {
            "geo_id": geo_id,
            "pdfs_exported": len(pdf_files),
            "output_dir": str(output_dir),
        }
