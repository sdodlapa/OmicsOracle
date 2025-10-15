"""
Prompt templates for AI summarization.

Provides structured prompts for different types of genomics dataset summaries.
"""

from typing import Any, Dict, Optional


class PromptBuilder:
    """Builder for constructing LLM prompts from dataset metadata."""

    @staticmethod
    def build_overview_prompt(
        metadata: Dict[str, Any],
        query_context: Optional[str] = None,
        brief: bool = False,
    ) -> str:
        """
        Build prompt for generating dataset overview.

        Args:
            metadata: Cleaned dataset metadata
            query_context: User's original query for context
            brief: Whether to generate brief summary

        Returns:
            Formatted prompt string
        """
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
        return prompt.strip()

    @staticmethod
    def build_methodology_prompt(metadata: Dict[str, Any]) -> str:
        """
        Build prompt for methodology summary.

        Args:
            metadata: Cleaned dataset metadata

        Returns:
            Formatted prompt string
        """
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
        return prompt.strip()

    @staticmethod
    def build_significance_prompt(
        metadata: Dict[str, Any], query_context: Optional[str] = None
    ) -> str:
        """
        Build prompt for research significance summary.

        Args:
            metadata: Cleaned dataset metadata
            query_context: User's original query

        Returns:
            Formatted prompt string
        """
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
        return prompt.strip()

    @staticmethod
    def get_system_message(role: str = "overview") -> str:
        """
        Get appropriate system message for different summary types.

        Args:
            role: Type of summary (overview, methodology, significance)

        Returns:
            System message string
        """
        messages = {
            "overview": (
                "You are a genomics research expert who creates clear, "
                "accessible summaries of scientific datasets. Focus on the "
                "biological significance and research context."
            ),
            "methodology": (
                "You are a genomics methods expert. Provide clear, "
                "technical summaries of experimental methodologies."
            ),
            "significance": (
                "You are a genomics research analyst who identifies "
                "the broader scientific significance of research datasets."
            ),
            "brief": (
                "You are a genomics expert who creates concise, "
                "one-paragraph summaries of research datasets. "
                "Focus on key findings and relevance."
            ),
        }
        return messages.get(role, messages["overview"])
