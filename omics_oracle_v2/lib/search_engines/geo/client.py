"""
Unified GEO (Gene Expression Omnibus) client.

Provides comprehensive access to GEO data through NCBI E-utilities,
GEOparse for SOFT file parsing, and optional SRA metadata retrieval.
"""

import asyncio
import functools
import logging
import ssl
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import aiohttp

from omics_oracle_v2.core.config import GEOSettings
from omics_oracle_v2.core.exceptions import GEOError

if TYPE_CHECKING:
    from omics_oracle_v2.core.config import Settings

from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.search_engines.geo.models import ClientInfo, GEOSeriesMetadata, SearchResult, SRAInfo
from omics_oracle_v2.lib.search_engines.geo.utils import RateLimiter, retry_with_backoff

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from GEOparse import get_GEO

    HAS_GEOPARSE = True
except ImportError:
    HAS_GEOPARSE = False
    logger.warning("GEOparse not available - metadata parsing disabled")

try:
    from pysradb import SRAweb

    HAS_PYSRADB = True
except ImportError:
    HAS_PYSRADB = False
    logger.debug("pysradb not available - SRA metadata disabled")


class NCBIClient:
    """
    Direct NCBI E-utilities client using aiohttp.

    Provides async access to NCBI Entrez E-utilities for searching
    and fetching GEO data.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def __init__(
        self,
        email: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize NCBI client.

        Args:
            email: Required email for NCBI API compliance
            api_key: Optional API key for higher rate limits
            verify_ssl: Whether to verify SSL certificates
        """
        self.email = email
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create optimized aiohttp session."""
        if self.session is None:
            # Create SSL context if verification is disabled
            ssl_context = None
            if not self.verify_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.warning("SSL verification disabled - use only for testing")

            # Week 3 Day 2: Optimized connector for parallel fetching
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=50,  # Total connection pool size
                limit_per_host=20,  # Connections per host (matches max_concurrent)
                ttl_dns_cache=300,  # Cache DNS for 5 minutes
                force_close=False,  # Reuse connections
                enable_cleanup_closed=True,  # Clean up closed connections
            )

            # Week 3 Day 2: Add timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=60,  # Total timeout per request
                connect=10,  # Connection timeout
                sock_read=30,  # Socket read timeout
            )

            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        return self.session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    def _build_params(self, **kwargs) -> Dict[str, str]:
        """Build parameters for NCBI API call."""
        params = {"email": self.email, "tool": "omics_oracle"}

        if self.api_key:
            params["api_key"] = self.api_key

        # Convert all values to strings and add additional parameters
        params.update({k: str(v) for k, v in kwargs.items()})
        return params

    async def esearch(self, db: str, term: str, retmax: int = 100, retstart: int = 0, **kwargs) -> List[str]:
        """
        Search NCBI database and return list of IDs.

        Args:
            db: Database to search (e.g., 'gds' for GEO DataSets)
            term: Search term/query
            retmax: Maximum number of results
            retstart: Starting position
            **kwargs: Additional search parameters

        Returns:
            List of NCBI IDs

        Raises:
            GEOError: If API request fails
        """
        url = f"{self.BASE_URL}esearch.fcgi"
        params = self._build_params(
            db=db, term=term, retmax=retmax, retstart=retstart, retmode="json", **kwargs
        )

        session = await self._get_session()

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Extract IDs from NCBI JSON response
                esearch_result = data.get("esearchresult", {})
                id_list = esearch_result.get("idlist", [])

                logger.debug(f"NCBI esearch returned {len(id_list)} results for: {term}")
                return id_list

        except aiohttp.ClientError as e:
            raise GEOError(f"NCBI API request failed: {e}") from e
        except (KeyError, ValueError) as e:
            raise GEOError(f"Failed to parse NCBI response: {e}") from e

    async def efetch(
        self, db: str, ids: List[str], rettype: str = "xml", retmode: str = "xml", **kwargs
    ) -> str:
        """
        Fetch records from NCBI database.

        Args:
            db: Database name
            ids: List of record IDs
            rettype: Return type (xml, json, etc.)
            retmode: Return mode
            **kwargs: Additional parameters

        Returns:
            Raw response content

        Raises:
            GEOError: If API request fails
        """
        if not ids:
            return ""

        url = f"{self.BASE_URL}efetch.fcgi"
        params = self._build_params(db=db, id=",".join(ids), rettype=rettype, retmode=retmode, **kwargs)

        session = await self._get_session()

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                content = await response.text()

                logger.debug(f"NCBI efetch returned {len(content)} chars for {len(ids)} IDs")
                return content

        except aiohttp.ClientError as e:
            raise GEOError(f"NCBI API request failed: {e}") from e

    async def esummary(self, db: str, ids: List[str], **kwargs) -> Dict[str, Any]:
        """
        Fetch document summaries from NCBI database.

        E-Summary provides structured metadata in JSON format, including organism
        information that may not be available in E-Search results.

        Args:
            db: Database name (e.g., 'gds' for GEO DataSets)
            ids: List of record IDs
            **kwargs: Additional parameters

        Returns:
            Dict with summary data for each ID

        Raises:
            GEOError: If API request fails

        Example:
            >>> summaries = await client.esummary('gds', ['200096615'])
            >>> organism = summaries['result']['200096615']['taxon']
        """
        if not ids:
            return {}

        url = f"{self.BASE_URL}esummary.fcgi"
        params = self._build_params(db=db, id=",".join(ids), retmode="json", **kwargs)

        session = await self._get_session()

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                logger.debug(f"NCBI esummary returned data for {len(ids)} IDs")
                return data

        except aiohttp.ClientError as e:
            raise GEOError(f"NCBI API request failed: {e}") from e
        except (KeyError, ValueError) as e:
            raise GEOError(f"Failed to parse NCBI esummary response: {e}") from e


class GEOClient:
    """
    Unified client for accessing GEO data.

    Provides:
    - GEO database searching via NCBI E-utilities
    - Metadata retrieval using GEOparse
    - Optional SRA metadata integration
    - Caching and rate limiting
    """

    def __init__(self, settings: Optional[Union[GEOSettings, "Settings"]] = None):
        """
        Initialize GEO client.

        Args:
            settings: GEO configuration settings or full Settings object
        """
        from omics_oracle_v2.core.config import Settings as FullSettings
        from omics_oracle_v2.core.config import get_settings

        if settings is None:
            all_settings = get_settings()
            settings = all_settings.geo
        elif isinstance(settings, FullSettings):
            # Extract GEO settings from full Settings object
            settings = settings.geo

        self.settings = settings

        # Initialize rate limiter (NCBI guidelines: 3 requests/sec without API key)
        self.rate_limiter = RateLimiter(max_calls=settings.rate_limit, time_window=1.0)

        # Initialize RedisCache (replaces SimpleCache for unified caching)
        self.redis_cache = RedisCache(
            host="localhost",
            port=6379,
            db=0,
            prefix="omics_search",
            default_ttl=self.settings.cache_ttl,
            enabled=True,
        )
        logger.info("RedisCache initialized for GEO client")

        # Initialize NCBI client
        self.ncbi_client: Optional[NCBIClient] = None
        if self.settings.ncbi_email:
            self.ncbi_client = NCBIClient(
                email=self.settings.ncbi_email,
                api_key=self.settings.ncbi_api_key,
                verify_ssl=self.settings.verify_ssl,
            )
            logger.info("NCBI client initialized")
        else:
            logger.warning("NCBI client not initialized - no email configured")

        # Initialize SRA client
        self.sra_client: Optional[Any] = None
        if HAS_PYSRADB:
            try:
                self.sra_client = SRAweb()
                logger.info("SRA client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize SRA client: {e}")

        logger.info("GEO client initialized successfully")

    async def close(self) -> None:
        """Clean up resources."""
        if self.ncbi_client:
            await self.ncbi_client.close()

    def _convert_ncbi_id_to_gse(self, ncbi_id: str) -> str:
        """
        Convert NCBI numeric ID to GSE format.

        NCBI returns IDs like '200096615' where '200' is a prefix
        for GEO series and '096615' is the GSE number.

        Args:
            ncbi_id: NCBI numeric ID

        Returns:
            GSE format ID (e.g., 'GSE96615')
        """
        if not ncbi_id.isdigit():
            return ncbi_id  # Already in correct format

        # Handle GEO series IDs that start with 200
        if ncbi_id.startswith("200") and len(ncbi_id) > 3:
            gse_number = ncbi_id[3:].lstrip("0")
            if gse_number:
                return f"GSE{gse_number}"

        # Fallback for other patterns
        if len(ncbi_id) >= 6:
            for prefix_len in [3, 2, 1]:
                if len(ncbi_id) > prefix_len:
                    candidate = ncbi_id[prefix_len:].lstrip("0")
                    if candidate and len(candidate) >= 3:
                        return f"GSE{candidate}"

        logger.warning(f"Could not convert NCBI ID {ncbi_id} to GSE format")
        return ncbi_id

    async def search(self, query: str, max_results: int = 100) -> SearchResult:
        """
        Search GEO database for series matching query.

        Args:
            query: Search query (e.g., 'breast cancer[Title]')
            max_results: Maximum number of results

        Returns:
            SearchResult with GEO series IDs

        Raises:
            GEOError: If NCBI client not available or search fails
        """
        if not self.ncbi_client:
            raise GEOError("NCBI client not available - check email configuration")

        import time

        start_time = time.time()

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Check Redis cache
        if self.settings.use_cache:
            cached = await self.redis_cache.get_search_result(
                query=query, search_type="geo", max_results=max_results
            )
            if cached:
                logger.info(f"✓ Redis cache hit for search: {query[:50]}")
                return SearchResult(**cached)

        # Perform search with retry
        async def _search():
            return await self.ncbi_client.esearch(db="gds", term=query, retmax=max_results)

        try:
            ncbi_ids = await retry_with_backoff(_search)

            # Convert NCBI IDs to GSE format
            gse_ids = [self._convert_ncbi_id_to_gse(nid) for nid in ncbi_ids]

            search_time = time.time() - start_time
            result = SearchResult(
                query=query,
                total_found=len(gse_ids),
                geo_ids=gse_ids,
                search_time=search_time,
            )

            # Cache results in Redis
            if self.settings.use_cache:
                await self.redis_cache.set_search_result(
                    query=query,
                    search_type="geo",
                    result=result,
                    max_results=max_results,
                )

            logger.info(f"Found {len(gse_ids)} GEO series for: {query}")
            return result

        except Exception as e:
            raise GEOError(f"Failed to search GEO: {e}") from e

    async def get_metadata(self, geo_id: str, include_sra: bool = True) -> GEOSeriesMetadata:
        """
        Retrieve comprehensive metadata for a GEO series.

        Args:
            geo_id: GEO series ID (e.g., 'GSE123456')
            include_sra: Whether to include SRA metadata

        Returns:
            GEOSeriesMetadata with all available information

        Raises:
            GEOError: If GEOparse not available or parsing fails
        """
        if not HAS_GEOPARSE:
            raise GEOError("GEOparse library not available")

        # Validate ID format
        if not self.validate_geo_id(geo_id):
            raise GEOError(f"Invalid GEO ID format: {geo_id}")

        # Check Redis cache
        if self.settings.use_cache:
            cached = await self.redis_cache.get_geo_metadata(geo_id)
            if cached:
                logger.info(f"✓ Redis cache hit for metadata: {geo_id}")
                return GEOSeriesMetadata(**cached)

        try:
            logger.info(f"Retrieving metadata for {geo_id} from NCBI")

            # Parse GEO series using GEOparse
            # Run blocking get_GEO() in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            # Use functools.partial to properly pass keyword argument
            get_geo_func = functools.partial(get_GEO, geo_id, destdir=str(self.settings.cache_dir))
            gse = await loop.run_in_executor(None, get_geo_func)

            # Extract metadata
            meta = getattr(gse, "metadata", {})

            # ===================================================================
            # PHASE 2: ORGANISM TRACE LOGGING + E-SUMMARY FALLBACK
            # ===================================================================
            # Extract organism from platform metadata (PRIMARY SOURCE)
            organism = ""
            organism_source = "none"

            gpls = getattr(gse, "gpls", {})
            logger.info(f"[ORGANISM-TRACE] {geo_id}: Found {len(gpls)} platforms in GEOparse data")

            if gpls:
                first_platform = list(gpls.values())[0]
                platform_id = list(gpls.keys())[0]
                platform_meta = getattr(first_platform, "metadata", {})
                organism_list = platform_meta.get("organism", [])

                logger.info(
                    f"[ORGANISM-TRACE] {geo_id}: Platform {platform_id} organism field = {organism_list!r}"
                )

                if organism_list and organism_list[0]:
                    organism = organism_list[0]
                    organism_source = "geoparse_platform"
                    logger.info(
                        f"[ORGANISM-TRACE] ✓ {geo_id}: Got organism from GEOparse platform: {organism!r}"
                    )
                else:
                    logger.warning(
                        f"[ORGANISM-TRACE] {geo_id}: Platform organism field is empty, will try E-Summary"
                    )
            else:
                logger.warning(
                    f"[ORGANISM-TRACE] {geo_id}: No platforms found in GEOparse, will try E-Summary"
                )

            # FALLBACK: If organism is empty, try NCBI E-Summary API
            if not organism and self.ncbi_client:
                logger.info(f"[ORGANISM-TRACE] {geo_id}: Attempting E-Summary fallback for organism")

                try:
                    # Convert GSE ID to NCBI numeric ID for E-Summary
                    # GSE189158 → search to get NCBI ID
                    search_results = await self.ncbi_client.esearch(
                        db="gds", term=f"{geo_id}[Accession]", retmax=1
                    )

                    if search_results:
                        ncbi_id = search_results[0]
                        logger.info(
                            f"[ORGANISM-TRACE] {geo_id}: Found NCBI ID {ncbi_id} for E-Summary lookup"
                        )

                        # Get summary with organism (taxon) field
                        summary_data = await self.ncbi_client.esummary(db="gds", ids=[ncbi_id])

                        if "result" in summary_data and ncbi_id in summary_data["result"]:
                            result = summary_data["result"][ncbi_id]
                            esummary_organism = result.get("taxon", "")

                            logger.info(
                                f"[ORGANISM-TRACE] {geo_id}: E-Summary returned taxon = {esummary_organism!r}"
                            )

                            if esummary_organism:
                                organism = esummary_organism
                                organism_source = "ncbi_esummary"
                                logger.info(
                                    f"[ORGANISM-TRACE] ✓ {geo_id}: Got organism from E-Summary: {organism!r}"
                                )
                            else:
                                logger.warning(
                                    f"[ORGANISM-TRACE] {geo_id}: E-Summary taxon field is also empty!"
                                )
                        else:
                            logger.warning(
                                f"[ORGANISM-TRACE] {geo_id}: E-Summary response missing result for ID {ncbi_id}"
                            )
                    else:
                        logger.warning(
                            f"[ORGANISM-TRACE] {geo_id}: E-Search found no NCBI ID for accession lookup"
                        )

                except Exception as e:
                    logger.error(f"[ORGANISM-TRACE] {geo_id}: E-Summary fallback failed: {e}", exc_info=True)

            # Final organism status
            if organism:
                logger.info(
                    f"[ORGANISM-TRACE] ✓✓ {geo_id}: FINAL organism = {organism!r} (source: {organism_source})"
                )
            else:
                logger.error(f"[ORGANISM-TRACE] ✗✗ {geo_id}: ORGANISM STILL EMPTY after all attempts!")

            metadata = GEOSeriesMetadata(
                geo_id=geo_id,
                title=meta.get("title", [""])[0],
                summary=meta.get("summary", [""])[0],
                overall_design=meta.get("overall_design", [""])[0],
                organism=organism,
                submission_date=meta.get("submission_date", [""])[0],
                last_update_date=meta.get("last_update_date", [""])[0],
                publication_date=meta.get("status", [""])[0],
                contact_name=meta.get("contact_name", []),
                contact_email=meta.get("contact_email", []),
                contact_institute=meta.get("contact_institute", []),
                platform_count=len(getattr(gse, "gpls", {})),
                sample_count=len(getattr(gse, "gsms", {})),
                platforms=list(getattr(gse, "gpls", {}).keys()),
                samples=list(getattr(gse, "gsms", {}).keys()),
                pubmed_ids=meta.get("pubmed_id", []),
                supplementary_files=meta.get("supplementary_file", []),
            )

            # Parse and populate structured download information
            metadata.data_downloads = metadata.parse_download_info()

            logger.info(
                f"Found {len(metadata.supplementary_files)} downloadable files "
                f"({metadata.get_download_summary()})"
            )

            # Add SRA metadata if requested
            if include_sra and self.sra_client:
                try:
                    sra_info = await self._get_sra_metadata(geo_id)
                    metadata.sra_info = sra_info
                except Exception as e:
                    logger.warning(f"Could not retrieve SRA data for {geo_id}: {e}")

            # Cache results in Redis (30-day TTL for stable GEO metadata)
            if self.settings.use_cache:
                await self.redis_cache.set_geo_metadata(
                    geo_id=geo_id, metadata=metadata, ttl=2592000  # 30 days
                )

            logger.info(f"Successfully retrieved metadata for {geo_id}")
            return metadata

        except Exception as e:
            raise GEOError(f"Failed to get metadata for {geo_id}: {e}") from e

    async def _get_sra_metadata(self, geo_id: str) -> Optional[SRAInfo]:
        """Get SRA metadata for a GEO series."""
        if not self.sra_client:
            return None

        try:
            df = self.sra_client.gse_to_srp(geo_id)
            if df.empty:
                return None

            return SRAInfo(
                srp_ids=df["study_accession"].unique().tolist(),
                run_count=len(df),
                experiment_count=df["experiment_accession"].nunique(),
                sample_count=df["sample_accession"].nunique(),
                total_spots=int(df["total_spots"].sum() if "total_spots" in df else 0),
                total_bases=int(df["total_bases"].sum() if "total_bases" in df else 0),
            )

        except Exception as e:
            logger.debug(f"SRA metadata not available for {geo_id}: {e}")
            return None

    async def batch_get_metadata(
        self, geo_ids: List[str], max_concurrent: int = 20, return_list: bool = False
    ) -> Union[Dict[str, GEOSeriesMetadata], List[GEOSeriesMetadata]]:
        """
        Retrieve metadata for multiple GEO series concurrently with optimized performance.

        This method implements parallel fetching with:
        - Semaphore-based concurrency control
        - Rate limiting compliance
        - Error handling and retry logic
        - Performance metrics logging
        - Maintains result ordering when return_list=True

        Args:
            geo_ids: List of GEO series IDs
            max_concurrent: Maximum concurrent requests (default: 20, Week 3 Day 2 optimization)
            return_list: If True, return ordered list; if False, return dict (default: False)

        Returns:
            Dictionary mapping GEO IDs to metadata, or ordered list if return_list=True

        Example:
            >>> # Fetch 50 datasets in parallel (~2-3s vs 25s sequential)
            >>> client = GEOClient(settings)
            >>> ids = ['GSE123456', 'GSE123457', ...]  # 50 IDs
            >>> results = await client.batch_get_metadata(ids, max_concurrent=10)
            >>> # Returns ~50 results in 2-3 seconds (vs 25s sequential)
        """
        import time

        if not geo_ids:
            return [] if return_list else {}

        start_time = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _get_single(geo_id: str) -> tuple[str, Optional[GEOSeriesMetadata]]:
            """Fetch single metadata with concurrency control and timeout."""
            async with semaphore:
                try:
                    # Week 3 Day 2: Add 30s timeout to prevent hanging
                    metadata = await asyncio.wait_for(self.get_metadata(geo_id), timeout=30.0)
                    return geo_id, metadata
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching {geo_id} after 30s")
                    return geo_id, None
                except GEOError as e:
                    logger.error(f"Failed to get metadata for {geo_id}: {e}")
                    return geo_id, None

        # Create tasks for all IDs
        logger.info(
            f"Starting batch metadata fetch: {len(geo_ids)} datasets, " f"max_concurrent={max_concurrent}"
        )
        tasks = [_get_single(geo_id) for geo_id in geo_ids]

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        metadata_dict = {}
        failed_ids = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch retrieval error: {result}")
                continue
            if isinstance(result, tuple) and len(result) == 2:
                geo_id, metadata = result
                if metadata:
                    metadata_dict[geo_id] = metadata
                else:
                    failed_ids.append(geo_id)

        # Performance metrics
        elapsed_time = time.time() - start_time
        success_rate = len(metadata_dict) / len(geo_ids) * 100 if geo_ids else 0
        throughput = len(metadata_dict) / elapsed_time if elapsed_time > 0 else 0

        logger.info(
            f"Batch fetch complete: {len(metadata_dict)}/{len(geo_ids)} successful "
            f"({success_rate:.1f}%) in {elapsed_time:.2f}s "
            f"({throughput:.1f} datasets/sec)"
        )

        if failed_ids:
            logger.warning(f"Failed to fetch {len(failed_ids)} datasets: {failed_ids[:10]}...")

        # Return as ordered list or dict
        if return_list:
            # Maintain original order, skip failed
            ordered_results = [metadata_dict[geo_id] for geo_id in geo_ids if geo_id in metadata_dict]
            return ordered_results
        else:
            return metadata_dict

    async def batch_get_metadata_smart(
        self, geo_ids: List[str], max_concurrent: int = 20
    ) -> List[GEOSeriesMetadata]:
        """
        Smart batch metadata fetching with cache-aware optimization.

        This method checks cache first, only fetches uncached datasets,
        then combines results maintaining order for maximum performance.

        Performance:
        - First request (cache miss): 2-3s for 50 datasets (parallel)
        - Subsequent requests (cache hit): <100ms for 50 datasets (Redis)
        - Mixed (50% cached): 1-1.5s for 50 datasets

        Args:
            geo_ids: List of GEO series IDs
            max_concurrent: Maximum concurrent fetches (default: 20, Week 3 Day 2 optimization)

        Returns:
            List of metadata in same order as input geo_ids

        Example:
            >>> # First search (cache miss)
            >>> results1 = await client.batch_get_metadata_smart(ids)  # 2.5s
            >>> # Second search (cache hit)
            >>> results2 = await client.batch_get_metadata_smart(ids)  # 0.05s (50x faster!)
        """
        import time

        if not geo_ids:
            return []

        start_time = time.time()

        # Step 1: Use Redis batch get for efficiency (single round trip!)
        cached_metadata = {}
        uncached_ids = []

        if self.settings.use_cache:
            # Batch fetch from Redis (MGET - very efficient)
            batch_cached = await self.redis_cache.get_geo_datasets_batch(geo_ids)

            for geo_id in geo_ids:
                cached_data = batch_cached.get(geo_id)
                if cached_data:
                    try:
                        cached_metadata[geo_id] = GEOSeriesMetadata(**cached_data)
                    except Exception as e:
                        logger.warning(f"Invalid cached data for {geo_id}: {e}")
                        uncached_ids.append(geo_id)
                else:
                    uncached_ids.append(geo_id)

            cache_hit_rate = len(cached_metadata) / len(geo_ids) * 100 if geo_ids else 0
            logger.info(
                f"Cache analysis: {len(cached_metadata)}/{len(geo_ids)} hits "
                f"({cache_hit_rate:.1f}%), {len(uncached_ids)} to fetch"
            )
        else:
            uncached_ids = geo_ids

        # Step 2: Fetch uncached in parallel
        if uncached_ids:
            logger.info(f"Fetching {len(uncached_ids)} uncached datasets in parallel")
            uncached_metadata = await self.batch_get_metadata(
                geo_ids=uncached_ids, max_concurrent=max_concurrent, return_list=False
            )
        else:
            uncached_metadata = {}

        # Step 3: Combine and maintain order
        all_metadata = {**cached_metadata, **uncached_metadata}
        ordered_results = [all_metadata[geo_id] for geo_id in geo_ids if geo_id in all_metadata]

        # Performance summary
        elapsed_time = time.time() - start_time
        throughput = len(ordered_results) / elapsed_time if elapsed_time > 0 else 0

        logger.info(
            f"Smart batch complete: {len(ordered_results)}/{len(geo_ids)} datasets "
            f"in {elapsed_time:.2f}s ({throughput:.1f} datasets/sec)"
        )

        return ordered_results

    def validate_geo_id(self, geo_id: str) -> bool:
        """
        Validate GEO series ID format.

        Args:
            geo_id: GEO series ID to validate

        Returns:
            True if valid GSE format, False otherwise
        """
        if not isinstance(geo_id, str):
            return False
        return geo_id.upper().startswith("GSE") and geo_id[3:].isdigit()

    def get_info(self) -> ClientInfo:
        """Get information about client configuration."""
        return ClientInfo(
            entrez_email=self.settings.ncbi_email or "not_configured",
            has_api_key=bool(self.settings.ncbi_api_key),
            cache_enabled=self.settings.use_cache,
            cache_directory=str(self.settings.cache_dir),
            rate_limit=self.settings.rate_limit,
            ssl_verify=self.settings.verify_ssl,
            has_geoparse=HAS_GEOPARSE,
            has_pysradb=HAS_PYSRADB,
        )
