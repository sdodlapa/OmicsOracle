"""
Smart multi-level cache manager for full-text content.

This module provides intelligent caching that checks multiple possible
storage locations before attempting API calls. It addresses the problem
where PDFs downloaded from different sources (arXiv, PMC, institutional, etc.)
are saved in source-specific directories but not checked during retrieval.

Key Features:
- Multi-location file search (XML and PDF in various subdirectories)
- Source-specific file organization
- Automatic file type detection
- Extensible for future parsed content caching

Storage Structure:
    data/fulltext/
    ├── xml/
    │   ├── pmc/           # PMC NXML files
    │   └── biorxiv/       # bioRxiv XML (if available)
    ├── pdf/
    │   ├── arxiv/         # arXiv PDFs
    │   ├── pmc/           # PMC PDFs (fallback from XML)
    │   ├── institutional/ # Institutional access PDFs
    │   ├── publisher/     # Direct publisher PDFs
    │   ├── scihub/        # Sci-Hub PDFs
    │   ├── biorxiv/       # bioRxiv/medRxiv PDFs
    │   └── {hash}.pdf     # Legacy hash-based cache
    └── parsed/            # Future: parsed JSON cache
        └── {id}.json

Example:
    >>> from omics_oracle_v2.lib.fulltext.smart_cache import SmartCache
    >>>
    >>> cache = SmartCache()
    >>> result = cache.find_local_file(publication)
    >>>
    >>> if result.found:
    >>>     print(f"Found {result.file_type} at {result.file_path}")
    >>>     print(f"Source: {result.source}, Size: {result.size_bytes}")

Author: OmicsOracle Team
Date: October 11, 2025
"""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LocalFileResult:
    """
    Result from local file search.
    
    Attributes:
        found: Whether a local file was found
        file_path: Path to the found file
        file_type: Type of file ('pdf', 'xml', 'nxml')
        source: Source identifier ('arxiv', 'pmc', 'institutional', etc.)
        size_bytes: File size in bytes
    """
    found: bool
    file_path: Optional[Path] = None
    file_type: Optional[str] = None  # 'pdf', 'xml', 'nxml'
    source: Optional[str] = None     # 'arxiv', 'pmc', 'institutional', etc.
    size_bytes: Optional[int] = None


class SmartCache:
    """
    Multi-level cache manager for full-text content.
    
    This class implements intelligent caching that:
    1. Checks parsed JSON cache (fastest, not yet implemented)
    2. Checks local XML files (high quality, best for parsing)
    3. Checks local PDF files in multiple source-specific directories
    4. Falls back to hash-based cache (legacy system)
    
    The cache prioritizes XML over PDF because:
    - XML has better structure (sections, tables, figures)
    - XML parsing is more accurate (99-100% vs 95-99% for PDFs)
    - XML is faster to parse (no OCR, no table detection needed)
    
    Attributes:
        base_dir: Base directory for fulltext storage (default: data/fulltext)
        pdf_dir: Directory for PDF storage
        xml_dir: Directory for XML storage
        parsed_dir: Directory for parsed content cache (future)
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize SmartCache.
        
        Args:
            base_dir: Base directory for fulltext storage.
                     Defaults to 'data/fulltext' in project root.
        """
        if base_dir is None:
            # Default to data/fulltext in project root
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "fulltext"
        
        self.base_dir = Path(base_dir)
        self.pdf_dir = self.base_dir / "pdf"
        self.xml_dir = self.base_dir / "xml"
        self.parsed_dir = self.base_dir / "parsed"
        
        # Ensure directories exist
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.xml_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
    
    def find_local_file(self, publication) -> LocalFileResult:
        """
        Search for any locally stored file for this publication.
        
        Search strategy:
        1. XML files (best quality) - checks PMC NXML, bioRxiv XML
        2. PDF files (multiple locations) - checks all source-specific directories
        3. Hash-based cache (legacy) - fallback for old cached files
        
        Args:
            publication: Publication object with identifiers (doi, pmid, pmc_id, title)
        
        Returns:
            LocalFileResult with file info if found, otherwise found=False
        """
        
        # Extract identifiers from publication
        doi = getattr(publication, 'doi', None)
        pmid = getattr(publication, 'pmid', None)
        pmc_id = getattr(publication, 'pmc_id', None)
        title = getattr(publication, 'title', None)
        
        # Generate list of identifiers to check
        ids_to_check = []
        
        if pmc_id:
            # PMC IDs might be stored with or without 'PMC' prefix
            ids_to_check.append(('pmc', str(pmc_id).replace('PMC', '')))
            ids_to_check.append(('pmc', f'PMC{str(pmc_id).replace("PMC", "")}'))
        
        if pmid:
            ids_to_check.append(('pmid', str(pmid)))
        
        if doi:
            # DOI might be used as filename (sanitized)
            sanitized_doi = doi.replace('/', '_').replace('.', '_')
            ids_to_check.append(('doi', sanitized_doi))
            
            # Check if this is an arXiv paper
            if 'arxiv' in doi.lower():
                # Extract arXiv ID (e.g., "10.48550/arxiv.2301.12345" -> "2301.12345")
                arxiv_id = doi.split('arxiv.')[-1] if 'arxiv.' in doi.lower() else doi.split('/')[-1]
                ids_to_check.append(('arxiv', arxiv_id))
        
        logger.debug(f"Checking local files for identifiers: {ids_to_check}")
        
        # PRIORITY 1: Check XML files first (best quality)
        xml_result = self._check_xml_files(ids_to_check)
        if xml_result.found:
            return xml_result
        
        # PRIORITY 2: Check PDF files (multiple locations)
        pdf_result = self._check_pdf_files(ids_to_check, publication)
        if pdf_result.found:
            return pdf_result
        
        # Not found in any location
        logger.debug("No local files found")
        return LocalFileResult(found=False)
    
    def _check_xml_files(self, ids_to_check: List[tuple]) -> LocalFileResult:
        """
        Check for XML files in xml/ subdirectories.
        
        Currently checks:
        - data/fulltext/xml/pmc/ (PMC NXML files)
        
        Future: Could check bioRxiv XML, publisher XML, etc.
        
        Args:
            ids_to_check: List of (id_type, id_value) tuples
        
        Returns:
            LocalFileResult indicating if XML file was found
        """
        
        # PMC XML files
        pmc_xml_dir = self.xml_dir / "pmc"
        if pmc_xml_dir.exists():
            for id_type, id_value in ids_to_check:
                # Only check PMC/PMID identifiers for PMC XML
                if id_type in ['pmc', 'pmid']:
                    # Try various naming patterns
                    # PMC uses inconsistent naming: PMC123456.nxml, 123456.nxml, etc.
                    patterns = [
                        f"{id_value}.nxml",
                        f"{id_value}.xml",
                        f"PMC{id_value}.nxml",
                        f"PMC{id_value}.xml",
                    ]
                    
                    for pattern in patterns:
                        xml_path = pmc_xml_dir / pattern
                        if xml_path.exists() and xml_path.stat().st_size > 0:
                            logger.info(f"✓ Found local PMC XML: {xml_path.name} ({xml_path.stat().st_size // 1024} KB)")
                            return LocalFileResult(
                                found=True,
                                file_path=xml_path,
                                file_type='nxml',
                                source='pmc_xml',
                                size_bytes=xml_path.stat().st_size
                            )
        
        # Future: Check other XML sources (bioRxiv, etc.)
        
        return LocalFileResult(found=False)
    
    def _check_pdf_files(self, ids_to_check: List[tuple], publication) -> LocalFileResult:
        """
        Check for PDF files in multiple possible locations.
        
        Checks source-specific subdirectories in priority order:
        1. arxiv/ (arXiv papers)
        2. pmc/ (PMC PDFs when XML not available)
        3. institutional/ (institutional access downloads)
        4. publisher/ (direct from publisher)
        5. biorxiv/ (bioRxiv/medRxiv preprints)
        6. scihub/ (Sci-Hub downloads)
        7. Root pdf/ directory (hash-based cache - legacy)
        
        Args:
            ids_to_check: List of (id_type, id_value) tuples
            publication: Publication object (for hash-based cache)
        
        Returns:
            LocalFileResult indicating if PDF file was found
        """
        
        # Define search locations in priority order
        # Priority based on: quality > speed > likelihood
        pdf_locations = [
            ('arxiv', self.pdf_dir / 'arxiv'),
            ('pmc', self.pdf_dir / 'pmc'),
            ('institutional', self.pdf_dir / 'institutional'),
            ('publisher', self.pdf_dir / 'publisher'),
            ('biorxiv', self.pdf_dir / 'biorxiv'),
            ('scihub', self.pdf_dir / 'scihub'),
            ('libgen', self.pdf_dir / 'libgen'),
        ]
        
        # Check each location
        for source, location in pdf_locations:
            if not location.exists():
                continue
            
            # Try each identifier in this location
            for id_type, id_value in ids_to_check:
                # Skip irrelevant combinations for efficiency
                # (e.g., don't look for PMC IDs in arxiv/ directory)
                if source == 'arxiv' and id_type != 'arxiv':
                    continue
                if source == 'pmc' and id_type not in ['pmc', 'pmid']:
                    continue
                
                # Check if file exists
                pdf_path = location / f"{id_value}.pdf"
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    logger.info(f"✓ Found local PDF: {source}/{pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")
                    return LocalFileResult(
                        found=True,
                        file_path=pdf_path,
                        file_type='pdf',
                        source=source,
                        size_bytes=pdf_path.stat().st_size
                    )
        
        # FALLBACK: Check hash-based cache (legacy system)
        # This is for backwards compatibility with old cached files
        hash_path = self._get_hash_cache_path(publication)
        if hash_path and hash_path.exists() and hash_path.stat().st_size > 0:
            logger.info(f"✓ Found legacy cached PDF: {hash_path.name} ({hash_path.stat().st_size // 1024} KB)")
            return LocalFileResult(
                found=True,
                file_path=hash_path,
                file_type='pdf',
                source='cache',
                size_bytes=hash_path.stat().st_size
            )
        
        return LocalFileResult(found=False)
    
    def _get_hash_cache_path(self, publication) -> Optional[Path]:
        """
        Get hash-based cache path (legacy system).
        
        The old caching system used MD5 hash of DOI or title as filename.
        This method maintains backwards compatibility.
        
        Args:
            publication: Publication object with doi or title
        
        Returns:
            Path to potential hash-based cache file, or None if no hash can be generated
        """
        try:
            # Generate hash from DOI or title
            if hasattr(publication, 'doi') and publication.doi:
                hash_input = publication.doi
            elif hasattr(publication, 'title') and publication.title:
                hash_input = publication.title
            else:
                return None
            
            file_hash = hashlib.md5(hash_input.encode()).hexdigest()
            return self.pdf_dir / f"{file_hash}.pdf"
        except Exception as e:
            logger.debug(f"Could not generate hash cache path: {e}")
            return None
    
    def save_file(
        self,
        content: bytes,
        publication,
        source: str,
        file_type: str = 'pdf'
    ) -> Path:
        """
        Save downloaded file to appropriate source-specific location.
        
        This method organizes files by source for better management and
        to enable the smart cache system to find them later.
        
        Args:
            content: File content as bytes
            publication: Publication object with identifiers
            source: Source identifier ('arxiv', 'pmc', 'institutional', 'scihub', etc.)
            file_type: File extension ('pdf', 'xml', 'nxml')
        
        Returns:
            Path where file was saved
        
        Example:
            >>> cache = SmartCache()
            >>> pdf_bytes = download_pdf(url)
            >>> saved_path = cache.save_file(
            ...     content=pdf_bytes,
            ...     publication=pub,
            ...     source='arxiv',
            ...     file_type='pdf'
            ... )
            >>> print(f"Saved to: {saved_path}")
            Saved to: data/fulltext/pdf/arxiv/2301.12345.pdf
        """
        
        # Determine base directory by file type
        if file_type in ['xml', 'nxml']:
            base_dir = self.xml_dir / source
        else:
            base_dir = self.pdf_dir / source
        
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename based on available identifiers
        # Priority: specific ID > DOI > title hash
        filename = self._get_filename(publication, source, file_type)
        
        # Save file
        file_path = base_dir / filename
        file_path.write_bytes(content)
        
        logger.info(f"💾 Saved {file_type.upper()} to: {source}/{filename} ({len(content) // 1024} KB)")
        
        return file_path
    
    def _get_filename(self, publication, source: str, file_type: str) -> str:
        """
        Generate appropriate filename for publication based on source.
        
        Naming strategy:
        - PMC: Use PMC ID (PMC123456.pdf)
        - arXiv: Use arXiv ID (2301.12345.pdf)
        - Others: Use sanitized DOI or title hash
        
        Args:
            publication: Publication object
            source: Source identifier
            file_type: File extension
        
        Returns:
            Filename string
        """
        
        # PMC files: use PMC ID
        if source == 'pmc' and hasattr(publication, 'pmc_id') and publication.pmc_id:
            pmc_id = str(publication.pmc_id).replace('PMC', '')
            return f"PMC{pmc_id}.{file_type}"
        
        # arXiv files: extract arXiv ID from DOI
        if source == 'arxiv' and hasattr(publication, 'doi') and publication.doi:
            if 'arxiv' in publication.doi.lower():
                arxiv_id = publication.doi.split('arxiv.')[-1] if 'arxiv.' in publication.doi.lower() else publication.doi.split('/')[-1]
                return f"{arxiv_id}.{file_type}"
        
        # General case: use DOI (sanitized) or hash
        if hasattr(publication, 'doi') and publication.doi:
            sanitized = publication.doi.replace('/', '_').replace('.', '_').replace(':', '_')
            return f"{sanitized}.{file_type}"
        
        # Fallback: use hash of title
        if hasattr(publication, 'title') and publication.title:
            hash_val = hashlib.md5(publication.title.encode()).hexdigest()
            return f"{hash_val}.{file_type}"
        
        # Last resort: use hash of publication ID
        pub_id = getattr(publication, 'id', 'unknown')
        hash_val = hashlib.md5(str(pub_id).encode()).hexdigest()
        return f"{hash_val}.{file_type}"


# Convenience function for quick access
def check_local_cache(publication) -> LocalFileResult:
    """
    Quick convenience function to check if publication has local files.
    
    Args:
        publication: Publication object
    
    Returns:
        LocalFileResult with file info if found
    
    Example:
        >>> result = check_local_cache(publication)
        >>> if result.found:
        >>>     print(f"Found {result.file_type} from {result.source}")
    """
    cache = SmartCache()
    return cache.find_local_file(publication)
