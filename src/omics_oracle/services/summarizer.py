"""
LLM-powered summarization service for OmicsOracle.

This service provides:
- Natural language dataset summaries
- Intelligent experiment descriptions
- Contextual analysis of GEO metadata
- Research insights and recommendations
"""

import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..core.config import Config
from .cache import SummaryCache

logger = logging.getLogger(__name__)

try:
    from .cost_manager import cost_manager  # noqa: F401

    COST_TRACKING_AVAILABLE = True
except ImportError:
    COST_TRACKING_AVAILABLE = False
    logger.warning("Cost manager not available - cost tracking disabled")


class SummarizationService:
    """Service for generating AI-powered summaries of genomics datasets."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize summarization service with OpenAI client."""
        self.config = config or Config()

        # Initialize caching
        self.cache = SummaryCache()

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. AI summarization will be unavailable.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

        # Model configuration
        self.model = "gpt-4o-mini"  # Cost-effective model for summarization
        self.max_tokens = 500
        self.temperature = 0.3  # Low temperature for consistent, factual output

        logger.info("Summarization service initialized")

    def summarize_dataset(
        self,
        metadata: Dict[str, Any],
        query_context: Optional[str] = None,
        summary_type: str = "comprehensive",
        dataset_id: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Generate AI-powered summary of a GEO dataset.

        Args:
            metadata: Dataset metadata from GEO
            query_context: Original user query for context
            summary_type: Type of summary ('brief', 'comprehensive', 'technical')
            dataset_id: Explicit dataset ID (e.g., geo_id) for cache key generation

        Returns:
            Dictionary with summary components OR None if AI service unavailable
        """
        if not self.client:
            logger.warning("OpenAI client not available - cannot generate real AI summary")
            return None

        # Create cache key based on dataset and query context
        # Use provided dataset_id or fall back to metadata extraction
        actual_dataset_id = (
            dataset_id
            or metadata.get("accession")
            or metadata.get("id")
            or metadata.get("geo_id")
            or "unknown"
        )
        cache_key = f"{actual_dataset_id}_{query_context or 'no_context'}_{summary_type}"

        # CACHE REMOVED: Always generate fresh AI summaries for accurate results
        logger.info(f"Generating fresh AI summary for dataset: {actual_dataset_id} (cache disabled)")

        try:
            # Prepare metadata for summarization
            cleaned_metadata = self._prepare_metadata(metadata)

            # Generate different summary components
            summaries = {}

            if summary_type in ["brief", "comprehensive"]:
                overview = self._generate_overview(cleaned_metadata, query_context)
                if overview:  # Only add if real content was generated
                    summaries["overview"] = overview

            if summary_type in ["comprehensive", "technical"]:
                methodology = self._generate_methodology_summary(cleaned_metadata)
                if methodology:  # Only add if real content was generated
                    summaries["methodology"] = methodology

                significance = self._generate_significance_summary(cleaned_metadata, query_context)
                if significance:  # Only add if real content was generated
                    summaries["significance"] = significance

            if summary_type == "brief":
                brief = self._generate_brief_summary(cleaned_metadata, query_context)
                if brief:  # Only add if real content was generated
                    summaries["brief"] = brief

            # Add technical details for comprehensive summaries
            if summary_type == "comprehensive":
                technical = self._generate_technical_summary(cleaned_metadata)
                if technical:  # Only add if real content was generated
                    summaries["technical_details"] = technical

            # Only return if we have real content (cache removed for fresh results)
            if summaries:
                # Log for query flow analysis (no caching of user-facing results)
                estimated_tokens = sum(len(str(v).split()) * 1.3 for v in summaries.values())
                logger.info(
                    f"Generated fresh AI summary for {cache_key} "
                    f"(estimated {int(estimated_tokens)} tokens)"
                )
                return summaries
            else:
                logger.warning(f"No real AI content generated for {dataset_id}")
                return None

        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return None

    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and prepare metadata for LLM processing."""
        # Handle case where metadata might be a string or have unexpected structure
        if isinstance(metadata, str):
            return {
                "accession": "Unknown",
                "title": metadata[:200] if len(metadata) > 200 else str(metadata),
                "summary": str(metadata),
                "type": "Unknown",
                "organism": "Unknown",
                "platform": "Unknown",
                "sample_count": 0,
                "submission_date": "",
                "last_update_date": "",
            }

        # Extract key fields and clean them
        cleaned = {
            "accession": metadata.get("accession", metadata.get("geo_id", "Unknown")),
            "title": metadata.get("title", metadata.get("name", "")),
            "summary": metadata.get("summary", metadata.get("description", "")),
            "type": metadata.get("type", metadata.get("study_type", "")),
            "organism": metadata.get("organism", metadata.get("species", "")),
            "platform": metadata.get("platform", metadata.get("technology", "")),
            "sample_count": len(metadata.get("samples", [])),
            "submission_date": metadata.get("submission_date", metadata.get("date", "")),
            "last_update_date": metadata.get("last_update_date", ""),
        }

        # Add sample information if available
        samples = metadata.get("samples", [])
        if samples and isinstance(samples, list):
            sample_titles = []
            for s in samples[:5]:
                if isinstance(s, dict):
                    sample_titles.append(s.get("title", s.get("name", "")))
                elif isinstance(s, str):
                    sample_titles.append(s)
            cleaned["sample_examples"] = sample_titles

        return cleaned

    def _generate_overview(self, metadata: Dict[str, Any], query_context: Optional[str]) -> Optional[str]:
        """Generate high-level overview summary using real AI only."""
        prompt = self._build_overview_prompt(metadata, query_context)

        try:
            if not self.client:
                return None  # No fake summaries

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a genomics research expert who creates clear, "
                            "accessible summaries of scientific datasets. Focus on the "
                            "biological significance and research context."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            return content.strip() if content and content.strip() else None

        except Exception as e:
            logger.error(f"Error generating overview: {e}")
            return None

    def _generate_methodology_summary(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate methodology and experimental design summary using real AI only."""
        prompt = f"""
        Analyze this genomics dataset and provide a concise summary of the experimental methodology:

        Dataset: {metadata.get('accession', 'Unknown')}
        Title: {metadata.get('title', 'No title')}
        Type: {metadata.get('type', 'Unknown')}
        Platform: {metadata.get('platform', 'Unknown')}
        Organism: {metadata.get('organism', 'Unknown')}
        Samples: {metadata.get('sample_count', 0)}

        Description: {metadata.get('summary', 'No description available')[:1000]}

        Focus on:
        1. Experimental technique/assay type
        2. Sample characteristics and experimental design
        3. Technical platform and methodology
        4. Key experimental parameters

        Provide a technical but accessible summary in 2-3 sentences.
        """

        try:
            if not self.client:
                return None  # No fake summaries

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a genomics methods expert. Provide clear, "
                            "technical summaries of experimental methodologies."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            return content.strip() if content and content.strip() else None

        except Exception as e:
            logger.error(f"Error generating methodology summary: {e}")
            return None

    def _generate_significance_summary(
        self, metadata: Dict[str, Any], query_context: Optional[str]
    ) -> Optional[str]:
        """Generate research significance and implications summary using real AI only."""
        prompt = f"""
        Analyze the research significance of this genomics dataset:

        Dataset: {metadata.get('accession', 'Unknown')} - {metadata.get('title', 'No title')}
        Context: {query_context or 'General genomics research'}
        Organism: {metadata.get('organism', 'Unknown')}
        Study Type: {metadata.get('type', 'Unknown')}

        Description: {metadata.get('summary', 'No description available')[:1000]}

        Explain:
        1. Scientific significance and research impact
        2. Relevance to the field of genomics/epigenomics
        3. Potential applications or follow-up research
        4. Connection to the user's query context

        Provide insights in 2-3 sentences focusing on biological significance.
        """

        try:
            if not self.client:
                return None  # No fake summaries

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a genomics research analyst who identifies "
                            "the broader scientific significance of research datasets."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            return content.strip() if content and content.strip() else None

        except Exception as e:
            logger.error(f"Error generating significance summary: {e}")
            return None

    def _generate_brief_summary(
        self, metadata: Dict[str, Any], query_context: Optional[str]
    ) -> Optional[str]:
        """Generate brief, one-paragraph summary using real AI only."""
        prompt = self._build_overview_prompt(metadata, query_context, brief=True)

        try:
            if not self.client:
                return None  # No fake summaries

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a genomics expert who creates concise, "
                            "one-paragraph summaries of research datasets. "
                            "Focus on key findings and relevance."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            return content.strip() if content and content.strip() else None

        except Exception as e:
            logger.error(f"Error generating brief summary: {e}")
            return None

    def _generate_technical_summary(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate technical details summary - only real data, no placeholders."""
        technical_info = []

        if metadata.get("platform") and metadata["platform"] != "Unknown":
            technical_info.append(f"Platform: {metadata['platform']}")

        if metadata.get("sample_count") and metadata["sample_count"] > 0:
            technical_info.append(f"Samples: {metadata['sample_count']}")

        if metadata.get("organism") and metadata["organism"] != "Unknown":
            technical_info.append(f"Organism: {metadata['organism']}")

        if metadata.get("submission_date"):
            technical_info.append(f"Submitted: {metadata['submission_date']}")

        # Only return if we have real technical information
        return " | ".join(technical_info) if technical_info else None

    def _build_overview_prompt(
        self,
        metadata: Dict[str, Any],
        query_context: Optional[str],
        brief: bool = False,
    ) -> str:
        """Build the prompt for overview generation."""
        context_text = f" in the context of '{query_context}'" if query_context else ""
        length_instruction = "1-2 sentences" if brief else "2-3 sentences"

        prompt = f"""
        Summarize this genomics dataset{context_text}:

        Dataset ID: {metadata.get('accession', 'Unknown')}
        Title: {metadata.get('title', 'No title available')}
        Type: {metadata.get('type', 'Unknown')}
        Organism: {metadata.get('organism', 'Unknown')}
        Platform: {metadata.get('platform', 'Unknown')}
        Sample Count: {metadata.get('sample_count', 0)}

        Description: {metadata.get('summary', 'No description available')[:800]}

        Provide a clear, scientific summary in {length_instruction} that explains:
        1. What biological question this study addresses
        2. The experimental approach used
        3. Why this data is valuable for research{context_text}

        Write for researchers who want to quickly understand the dataset's relevance.
        """

        return prompt

    def summarize_batch_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Generate summary of multiple dataset results."""
        if not results:
            return {"summary": "No datasets found for the given query."}

        # CACHE REMOVED: Always generate fresh batch summaries for accurate results
        logger.info(f"Generating fresh batch summary for query: {query[:50]}... (cache disabled)")

        # Extract key statistics
        total_datasets = len(results)
        organisms = set()
        platforms = set()
        types = set()
        total_samples = 0

        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("organism"):
                organisms.add(metadata["organism"])
            if metadata.get("platform"):
                platforms.add(metadata["platform"])
            if metadata.get("type"):
                types.add(metadata["type"])
            total_samples += len(metadata.get("samples", []))

        # Generate batch summary
        summary = {
            "query": query,
            "total_datasets": total_datasets,
            "total_samples": total_samples,
            "organisms": list(organisms),
            "platforms": list(platforms),
            "study_types": list(types),
            "overview": (
                f"Found {total_datasets} datasets with {total_samples} total samples "
                f"across {len(organisms)} organisms using {len(platforms)} different platforms."
            ),
        }

        # Log for query flow analysis (no caching of user-facing results)
        cache_key = f"{query}_batch_{len(results)}"
        logger.info(f"Generated fresh batch summary for {cache_key}")

        return summary


# Global summarization service instance
summarization_service = SummarizationService()
