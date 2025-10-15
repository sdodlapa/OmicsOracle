"""
Text Enrichment Modules

Modular enrichers that progressively enhance extracted text:
1. SectionDetector - Detect paper sections (Intro, Methods, Results, Discussion)
2. TableExtractor - Extract and parse tables
3. ReferenceParser - Parse bibliography and citations
4. ChatGPTFormatter - Format for optimal ChatGPT consumption

All enrichers follow the Enricher protocol:
- Input: ExtractedContent (raw text + metadata)
- Output: EnrichedContent (structured + annotated)
- Composable: Output of one enricher feeds into next
"""

from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers.chatgpt_formatter import ChatGPTFormatter
from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers.reference_parser import ReferenceParser
from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers.section_detector import SectionDetector
from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers.table_extractor import TableExtractor

__all__ = [
    "SectionDetector",
    "TableExtractor",
    "ReferenceParser",
    "ChatGPTFormatter",
]
