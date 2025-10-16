"""
Metadata Enrichment Service

Handles cases where primary citation sources (OpenAlex, Semantic Scholar, PubMed)
return incomplete metadata. Fetches missing fields from alternative sources.

Common Issue:
- OpenAlex sometimes returns `title: null` for valid papers with DOIs
- Example: W2911964244 ("Random Forests" by Leo Breiman) - 98K citations!

Strategy:
1. If title missing but DOI exists → Fetch from Crossref
2. If title missing but PMID exists → Fetch from PubMed
3. Generate content_hash from enriched metadata
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication, PublicationSource)

logger = logging.getLogger(__name__)


class MetadataEnrichmentService:
    """
    Enriches incomplete publication metadata from alternative sources.

    Fallback hierarchy:
    1. Crossref (for DOI-based enrichment)
    2. PubMed (for PMID-based enrichment)
    3. Europe PMC (alternative for biomedical papers)
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize enrichment service.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "OmicsOracle/1.0 (Academic Research; mailto:research@example.com)"
            }
        )

    def enrich_from_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata from Crossref using DOI.

        Crossref is the DOI registration agency - authoritative source for DOI metadata.

        Args:
            doi: Digital Object Identifier

        Returns:
            Dictionary with enriched metadata (title, authors, journal, year, etc.)

        Example:
            >>> service = MetadataEnrichmentService()
            >>> metadata = service.enrich_from_doi("10.1023/a:1010933404324")
            >>> metadata['title']
            'Random Forests'
        """
        if not doi:
            return None

        # Clean DOI
        doi_clean = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

        try:
            # Crossref API: https://api.crossref.org/works/{doi}
            url = f"https://api.crossref.org/works/{doi_clean}"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                logger.debug(
                    f"Crossref returned {response.status_code} for DOI: {doi_clean}"
                )
                return None

            data = response.json()
            message = data.get("message", {})

            # Extract title
            title = None
            if message.get("title"):
                title = (
                    message["title"][0]
                    if isinstance(message["title"], list)
                    else message["title"]
                )

            # Extract authors
            authors = []
            for author in message.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    full_name = f"{given} {family}".strip() if given else family
                    authors.append(full_name)

            # Extract journal
            journal = None
            container_title = message.get("container-title")
            if container_title:
                journal = (
                    container_title[0]
                    if isinstance(container_title, list)
                    else container_title
                )

            # Extract publication date
            pub_date = None
            if message.get("published-print"):
                date_parts = message["published-print"].get("date-parts", [[]])[0]
                if len(date_parts) >= 1:
                    year = date_parts[0]
                    month = date_parts[1] if len(date_parts) > 1 else 1
                    day = date_parts[2] if len(date_parts) > 2 else 1
                    try:
                        pub_date = datetime(year, month, day)
                    except ValueError:
                        pub_date = datetime(year, 1, 1)

            enriched = {
                "title": title,
                "authors": authors,
                "journal": journal,
                "publication_date": pub_date,
                "publication_year": message.get("published-print", {}).get(
                    "date-parts", [[None]]
                )[0][0],
                "doi": doi_clean,
                "citations": message.get("is-referenced-by-count", 0),
                "source": "crossref",
                "metadata": {
                    "type": message.get("type"),
                    "publisher": message.get("publisher"),
                    "issn": message.get("ISSN", []),
                    "volume": message.get("volume"),
                    "issue": message.get("issue"),
                    "page": message.get("page"),
                },
            }

            logger.info(
                f"✅ Enriched from Crossref: {title[:50] if title else 'No title'}... (DOI: {doi_clean})"
            )
            return enriched

        except requests.exceptions.Timeout:
            logger.warning(f"Crossref timeout for DOI: {doi_clean}")
            return None
        except Exception as e:
            logger.error(f"Error enriching from Crossref (DOI: {doi_clean}): {e}")
            return None

    def enrich_from_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata from PubMed using PMID.

        Uses E-utilities API (same as PubMed client).

        Args:
            pmid: PubMed ID

        Returns:
            Dictionary with enriched metadata
        """
        if not pmid:
            return None

        try:
            # PubMed E-utilities: efetch
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": pmid,
                "retmode": "xml",
                "rettype": "abstract",
            }

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code != 200:
                logger.debug(f"PubMed returned {response.status_code} for PMID: {pmid}")
                return None

            # Parse XML (simplified - would need proper XML parsing)
            # For now, return None and rely on Crossref enrichment via DOI
            # TODO: Implement XML parsing for PubMed metadata

            logger.debug(f"PubMed enrichment for PMID {pmid} not yet implemented")
            return None

        except Exception as e:
            logger.error(f"Error enriching from PubMed (PMID: {pmid}): {e}")
            return None

    def enrich_publication(self, publication: Publication) -> Publication:
        """
        Enrich a Publication object with missing metadata.

        Strategy:
        1. If title is missing or is placeholder → fetch from Crossref/PubMed
        2. Update publication with enriched metadata
        3. Return enriched publication (or original if enrichment not needed/failed)

        Args:
            publication: Publication object with potentially missing fields

        Returns:
            Enriched Publication object

        Example:
            >>> service = MetadataEnrichmentService()
            >>> pub = Publication(doi="10.1023/a:1010933404324", title="Unknown Title", ...)
            >>> enriched = service.enrich_publication(pub)
            >>> enriched.title
            'Random Forests'
        """
        # Skip if title already exists and is not a placeholder
        if (
            publication.title
            and publication.title.strip()
            and publication.title not in ["Unknown Title", "Untitled", "No Title"]
        ):
            return publication

        logger.info(
            f"🔍 Enriching publication with missing/placeholder title (DOI: {publication.doi}, PMID: {publication.pmid})"
        )

        # Try Crossref first (most reliable for DOI-based papers)
        if publication.doi:
            enriched = self.enrich_from_doi(publication.doi)
            if enriched and enriched.get("title"):
                # Create new Publication object with enriched data
                # (Pydantic models are immutable, so we need to create a new one)
                enriched_pub = Publication(
                    # Use enriched title
                    title=enriched["title"],
                    # Prefer original metadata, fallback to enriched
                    authors=publication.authors
                    if publication.authors
                    else enriched.get("authors", []),
                    journal=publication.journal
                    if publication.journal
                    else enriched.get("journal"),
                    publication_date=publication.publication_date
                    if publication.publication_date
                    else enriched.get("publication_date"),
                    abstract=publication.abstract,  # Crossref doesn't provide abstracts
                    # Keep original identifiers
                    doi=publication.doi,
                    pmid=publication.pmid,
                    pmcid=publication.pmcid,
                    citations=max(
                        publication.citations or 0, enriched.get("citations", 0)
                    ),
                    source=publication.source,
                    # Merge metadata
                    metadata={
                        **(publication.metadata or {}),
                        **enriched.get("metadata", {}),
                        "enriched_from": "crossref",
                        "enrichment_date": datetime.now().isoformat(),
                    },
                    # Pass through other fields
                    mesh_terms=publication.mesh_terms,
                    keywords=publication.keywords,
                    url=publication.url,
                    pdf_url=publication.pdf_url,
                    paper_type=publication.paper_type,
                )

                logger.info(
                    f"✅ Successfully enriched: {enriched_pub.title[:50]}... (from {publication.source.value})"
                )
                return enriched_pub

        # Try PubMed if DOI enrichment failed
        if publication.pmid:
            enriched = self.enrich_from_pmid(publication.pmid)
            if enriched and enriched.get("title"):
                # Similar to above - create new Publication with enriched data
                # TODO: Implement when PubMed enrichment is ready
                logger.info(
                    f"✅ Successfully enriched from PubMed: {enriched['title'][:50]}..."
                )
                pass

        # If all enrichment attempts failed, log warning
        logger.warning(
            f"⚠️ Could not enrich publication (DOI: {publication.doi}, PMID: {publication.pmid}). "
            "Returning original publication."
        )
        return publication


# Global instance
_enrichment_service: Optional[MetadataEnrichmentService] = None


def get_enrichment_service() -> MetadataEnrichmentService:
    """Get or create global metadata enrichment service instance."""
    global _enrichment_service
    if _enrichment_service is None:
        _enrichment_service = MetadataEnrichmentService()
    return _enrichment_service
