"""
Data models for GEO (Gene Expression Omnibus) data.

Provides Pydantic models for GEO series, platforms, samples, and metadata
with full type safety and validation.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GEOSample(BaseModel):
    """GEO sample (GSM) metadata."""

    gsm_id: str = Field(..., description="GEO sample ID (e.g., GSM123456)")
    title: str = Field(default="", description="Sample title")
    source_name: str = Field(default="", description="Sample source")
    organism: str = Field(default="", description="Source organism")
    characteristics: Dict[str, str] = Field(default_factory=dict, description="Sample characteristics")
    treatment: str = Field(default="", description="Treatment protocol")
    extract_protocol: str = Field(default="", description="Extraction protocol")
    description: str = Field(default="", description="Sample description")
    platform_id: str = Field(default="", description="Platform ID (GPL)")
    series_id: List[str] = Field(default_factory=list, description="Parent series IDs")


class GEOPlatform(BaseModel):
    """GEO platform (GPL) metadata."""

    gpl_id: str = Field(..., description="GEO platform ID (e.g., GPL96)")
    title: str = Field(default="", description="Platform title")
    organism: str = Field(default="", description="Target organism")
    manufacturer: str = Field(default="", description="Platform manufacturer")
    technology: str = Field(default="", description="Technology type")
    distribution: str = Field(default="", description="Distribution method")
    description: str = Field(default="", description="Platform description")


class DataDownloadInfo(BaseModel):
    """
    Information about downloadable dataset files.

    Contains FTP links and metadata for actual experimental data
    that can be downloaded separately with user approval.
    """

    file_url: str = Field(..., description="FTP/HTTP URL to download file")
    file_type: str = Field(default="", description="File type (RAW, processed, matrix, etc.)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes (if known)")
    file_format: str = Field(default="", description="File format (tar, txt, CEL, etc.)")
    description: str = Field(default="", description="File description")

    def get_file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes."""
        if self.file_size_bytes:
            return self.file_size_bytes / (1024 * 1024)
        return None

    def get_file_size_gb(self) -> Optional[float]:
        """Get file size in gigabytes."""
        if self.file_size_bytes:
            return self.file_size_bytes / (1024 * 1024 * 1024)
        return None


class SRAInfo(BaseModel):
    """SRA (Sequence Read Archive) metadata."""

    srp_ids: List[str] = Field(default_factory=list, description="SRA project IDs")
    run_count: int = Field(default=0, description="Number of sequencing runs")
    experiment_count: int = Field(default=0, description="Number of experiments")
    sample_count: int = Field(default=0, description="Number of samples")
    total_spots: int = Field(default=0, description="Total number of spots/reads")
    total_bases: int = Field(default=0, description="Total number of bases")


class GEOSeriesMetadata(BaseModel):
    """
    Comprehensive GEO series (GSE) metadata.

    Contains all available information about a GEO series including
    basic metadata, samples, platforms, and optional SRA data.
    """

    model_config = {"protected_namespaces": ()}  # Allow model_* field names

    geo_id: str = Field(..., description="GEO series ID (e.g., GSE123456)")
    title: str = Field(default="", description="Study title")
    summary: str = Field(default="", description="Study summary/abstract")
    overall_design: str = Field(default="", description="Experimental design")
    organism: str = Field(default="", description="Organism(s) studied")

    submission_date: str = Field(default="", description="Submission date")
    last_update_date: str = Field(default="", description="Last update date")
    publication_date: str = Field(default="", description="Public release date")

    contact_name: List[str] = Field(default_factory=list, description="Contact names")
    contact_email: List[str] = Field(default_factory=list, description="Contact emails")
    contact_institute: List[str] = Field(default_factory=list, description="Contact institutions")

    platform_count: int = Field(default=0, description="Number of platforms")
    sample_count: int = Field(default=0, description="Number of samples")

    platforms: List[str] = Field(default_factory=list, description="Platform IDs (GPL)")
    samples: List[str] = Field(default_factory=list, description="Sample IDs (GSM)")

    pubmed_ids: List[str] = Field(default_factory=list, description="PubMed IDs")
    supplementary_files: List[str] = Field(
        default_factory=list,
        description="FTP URLs to actual dataset files (RAW data, processed matrices, etc.)",
    )

    # NEW: Structured download information
    data_downloads: List[DataDownloadInfo] = Field(
        default_factory=list, description="Structured information about downloadable dataset files"
    )

    sra_info: Optional[SRAInfo] = Field(None, description="SRA metadata if available")

    def get_age_days(self) -> Optional[int]:
        """Get age of study in days since submission."""
        if not self.submission_date:
            return None
        try:
            submission = datetime.strptime(self.submission_date, "%Y-%m-%d")
            return (datetime.now() - submission).days
        except (ValueError, TypeError):
            return None

    def is_recent(self, days: int = 365) -> bool:
        """Check if study was published within specified days."""
        age = self.get_age_days()
        return age is not None and age <= days

    def has_sra_data(self) -> bool:
        """Check if SRA sequencing data is available."""
        return self.sra_info is not None and len(self.sra_info.srp_ids) > 0

    def get_data_download_links(self) -> List[str]:
        """
        Get all FTP/HTTP links to downloadable dataset files.

        Returns:
            List of URLs to actual experimental data files
        """
        return self.supplementary_files

    def parse_download_info(self) -> List[DataDownloadInfo]:
        """
        Parse supplementary_files into structured DataDownloadInfo objects.

        Extracts file type, format, and categorizes download links.
        """
        downloads = []

        for url in self.supplementary_files:
            # Parse file information from URL
            file_name = url.split("/")[-1] if "/" in url else url

            # Determine file type based on naming convention
            if "_RAW.tar" in file_name:
                file_type = "RAW"
                file_format = "tar"
                description = "Raw data archive (CEL files, IDAT files, etc.)"
            elif "_processed" in file_name or "_matrix" in file_name:
                file_type = "processed"
                file_format = "txt" if ".txt" in file_name else "unknown"
                description = "Processed expression matrix or normalized data"
            elif ".fastq" in file_name or ".fq" in file_name:
                file_type = "sequencing"
                file_format = "fastq"
                description = "Raw sequencing reads (FASTQ format)"
            elif ".bam" in file_name or ".sam" in file_name:
                file_type = "alignment"
                file_format = "bam" if ".bam" in file_name else "sam"
                description = "Aligned sequencing reads"
            elif ".CEL" in file_name:
                file_type = "microarray"
                file_format = "CEL"
                description = "Microarray raw data (Affymetrix)"
            else:
                file_type = "supplementary"
                file_format = file_name.split(".")[-1] if "." in file_name else "unknown"
                description = "Supplementary data file"

            downloads.append(
                DataDownloadInfo(
                    file_url=url, file_type=file_type, file_format=file_format, description=description
                )
            )

        return downloads

    def get_download_summary(self) -> Dict[str, int]:
        """
        Get summary of available download files by type.

        Returns:
            Dictionary mapping file type to count
        """
        downloads = self.parse_download_info()
        summary = {}
        for download in downloads:
            summary[download.file_type] = summary.get(download.file_type, 0) + 1
        return summary

    def has_raw_data(self) -> bool:
        """Check if raw experimental data files are available for download."""
        return any("_RAW.tar" in url or ".CEL" in url or ".fastq" in url for url in self.supplementary_files)

    def estimate_download_size_mb(self) -> str:
        """
        Estimate total download size based on file types.

        Returns:
            Human-readable size estimate (e.g., "500 MB - 5 GB")
        """
        downloads = self.parse_download_info()

        # Common size estimates for different file types
        if any(d.file_type == "RAW" for d in downloads):
            return "500 MB - 50 GB (depending on sample count)"
        elif any(d.file_type == "sequencing" for d in downloads):
            return "1 GB - 500 GB (depending on sequencing depth)"
        elif any(d.file_type == "microarray" for d in downloads):
            return "100 MB - 2 GB (depending on platform)"
        elif any(d.file_type == "processed" for d in downloads):
            return "10 MB - 500 MB"
        else:
            return "Unknown (check individual files)"


class SearchResult(BaseModel):
    """Result from GEO database search."""

    query: str = Field(..., description="Original search query")
    total_found: int = Field(..., description="Total results found")
    geo_ids: List[str] = Field(..., description="List of GEO series IDs")
    search_time: float = Field(default=0.0, description="Search time in seconds")


class ClientInfo(BaseModel):
    """Information about GEO client configuration."""

    entrez_email: str = Field(..., description="Configured email for NCBI")
    has_api_key: bool = Field(default=False, description="Whether API key is configured")
    cache_enabled: bool = Field(default=True, description="Whether caching is enabled")
    cache_directory: str = Field(default="", description="Cache directory path")
    rate_limit: int = Field(default=3, description="Requests per second limit")
    ssl_verify: bool = Field(default=True, description="SSL verification enabled")
    has_geoparse: bool = Field(default=False, description="GEOparse library available")
    has_pysradb: bool = Field(default=False, description="pysradb library available")
