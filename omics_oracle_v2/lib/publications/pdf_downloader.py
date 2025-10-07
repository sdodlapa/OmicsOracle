"""PDF Downloader for OmicsOracle.

Downloads PDFs from institutional access URLs, OA repositories, and PMC.
Supports concurrent downloads with deduplication.
"""

import requests
from pathlib import Path
import hashlib
import logging
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class PDFDownloader:
    """Download PDFs from institutional access or OA repositories."""
    
    def __init__(self, download_dir: Path, institutional_manager=None):
        """Initialize PDF downloader.
        
        Args:
            download_dir: Directory to save PDFs
            institutional_manager: Optional InstitutionalAccessManager for getting PDF URLs
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.institutional_manager = institutional_manager
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OmicsOracle/2.0 (https://github.com/sdodlapati3/OmicsOracle)"
        })
        
    def download(
        self, 
        pdf_url: str, 
        identifier: str, 
        source: str = "unknown"
    ) -> Optional[Path]:
        """Download a single PDF.
        
        Args:
            pdf_url: URL to PDF
            identifier: PMID, DOI, or unique ID
            source: Source type (pubmed, pmc, unpaywall, etc.)
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            # Create source subdirectory
            source_dir = self.download_dir / source
            source_dir.mkdir(exist_ok=True)
            
            # Sanitize identifier for filename
            safe_id = identifier.replace("/", "_").replace(":", "_").replace(" ", "_")
            pdf_path = source_dir / f"{safe_id}.pdf"
            
            # Check if already downloaded
            if pdf_path.exists():
                file_size = pdf_path.stat().st_size
                if file_size > 1000:  # At least 1KB
                    logger.info(f"PDF already exists: {pdf_path} ({file_size} bytes)")
                    return pdf_path
                else:
                    # Remove corrupted file
                    pdf_path.unlink()
                    logger.warning(f"Removed corrupted PDF: {pdf_path}")
            
            # Download with timeout and retries
            logger.info(f"Downloading PDF from {pdf_url[:100]}...")
            
            # Special handling for PMC
            headers = {"User-Agent": "OmicsOracle/2.0 (https://github.com/sdodlapati3/OmicsOracle)"}
            if "ncbi.nlm.nih.gov/pmc" in pdf_url:
                # PMC requires specific headers
                headers["Accept"] = "application/pdf,*/*"
            
            for attempt in range(3):  # 3 retries
                try:
                    response = self.session.get(
                        pdf_url,
                        timeout=30,
                        stream=True,
                        allow_redirects=True,
                        headers=headers
                    )
                    response.raise_for_status()
                    
                    # Verify it's actually a PDF
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "pdf" not in content_type and not pdf_url.lower().endswith(".pdf"):
                        # Check first few bytes for PDF magic number
                        first_bytes = response.content[:4] if hasattr(response, 'content') else b''
                        if first_bytes != b'%PDF':
                            logger.warning(f"Not a PDF (Content-Type: {content_type})")
                            return None
                    
                    # Save to file
                    with open(pdf_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = pdf_path.stat().st_size
                    logger.info(f"Downloaded PDF: {pdf_path.name} ({file_size} bytes)")
                    return pdf_path
                    
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Download attempt {attempt + 1} failed: {e}, retrying...")
                        continue
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url[:100]}: {e}")
            # Clean up partial download
            if pdf_path.exists():
                pdf_path.unlink()
            return None
    
    def download_batch(
        self, 
        publications: List, 
        max_workers: int = 5
    ) -> Dict[str, Path]:
        """Download multiple PDFs in parallel.
        
        Args:
            publications: List of Publication objects
            max_workers: Number of parallel downloads
            
        Returns:
            Dict of {identifier: pdf_path}
        """
        results = {}
        total = len(publications)
        
        logger.info(f"Starting batch download of {total} PDFs with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pub = {}
            
            for pub in publications:
                # Get PDF URL via institutional access or existing URL
                pdf_url = None
                if self.institutional_manager:
                    pdf_url = self.institutional_manager.get_pdf_url(pub)
                elif hasattr(pub, 'pdf_url') and pub.pdf_url:
                    pdf_url = pub.pdf_url
                
                if pdf_url:
                    # Determine identifier and source
                    identifier = pub.pmid or pub.doi or pub.title[:50]
                    
                    # Determine source
                    source = "unknown"
                    if hasattr(pub, "source"):
                        source = pub.source.value if hasattr(pub.source, "value") else str(pub.source)
                    elif pub.pmid:
                        source = "pubmed"
                    elif pub.pmcid:
                        source = "pmc"
                    elif "unpaywall" in pdf_url.lower():
                        source = "unpaywall"
                    
                    future = executor.submit(
                        self.download, 
                        pdf_url, 
                        identifier,
                        source
                    )
                    future_to_pub[future] = (pub, identifier)
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_pub):
                pub, identifier = future_to_pub[future]
                completed += 1
                try:
                    pdf_path = future.result()
                    if pdf_path:
                        results[identifier] = pdf_path
                        pub.pdf_path = pdf_path
                        if not hasattr(pub, 'metadata'):
                            pub.metadata = {}
                        pub.metadata["pdf_downloaded"] = True
                        pub.metadata["pdf_path"] = str(pdf_path)
                        logger.info(f"[{completed}/{total}] Successfully downloaded: {pub.title[:50]}...")
                    else:
                        logger.warning(f"[{completed}/{total}] No PDF available: {pub.title[:50]}...")
                except Exception as e:
                    logger.error(f"[{completed}/{total}] Download failed for {identifier}: {e}")
        
        success_count = len(results)
        logger.info(f"Batch download complete: {success_count}/{total} PDFs downloaded successfully")
        return results
    
    def get_download_stats(self) -> Dict[str, int]:
        """Get statistics about downloaded PDFs.
        
        Returns:
            Dict with counts by source and total size
        """
        stats = {
            "total_pdfs": 0,
            "total_size_mb": 0,
            "by_source": {}
        }
        
        if not self.download_dir.exists():
            return stats
        
        for source_dir in self.download_dir.iterdir():
            if source_dir.is_dir():
                pdf_count = len(list(source_dir.glob("*.pdf")))
                total_size = sum(p.stat().st_size for p in source_dir.glob("*.pdf"))
                
                stats["by_source"][source_dir.name] = {
                    "count": pdf_count,
                    "size_mb": round(total_size / (1024 * 1024), 2)
                }
                stats["total_pdfs"] += pdf_count
                stats["total_size_mb"] += total_size / (1024 * 1024)
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
