"""
Synonym Expansion for Biomedical Techniques

Phase 2B implementation for expanding biomedical technique queries with synonyms
using ontologies, embeddings, and abbreviation handling.

Features:
- Gazetteer-based synonym lookup from biomedical ontologies (OBI, EDAM, EFO, MeSH)
- Abbreviation detection and expansion
- Embedding-based semantic similarity (SapBERT)
- Multi-variant generation (hyphen/space normalization)
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TechniqueSynonyms:
    """Synonyms for a biomedical technique."""
    
    canonical_name: str
    canonical_id: Optional[str] = None
    synonyms: Set[str] = field(default_factory=set)
    abbreviations: Set[str] = field(default_factory=set)
    variants: Set[str] = field(default_factory=set)
    
    def all_terms(self) -> Set[str]:
        """Get all terms (canonical + synonyms + abbreviations + variants)."""
        return {self.canonical_name} | self.synonyms | self.abbreviations | self.variants


@dataclass
class SynonymExpansionConfig:
    """Configuration for synonym expansion."""
    
    # Gazetteer settings
    use_ontologies: bool = True
    ontology_sources: List[str] = field(default_factory=lambda: ["OBI", "EDAM", "EFO", "MeSH"])
    
    # Abbreviation settings
    detect_abbreviations: bool = True
    common_abbreviations: bool = True
    
    # Variant generation
    generate_variants: bool = True
    hyphen_variants: bool = True  # RNA-seq vs RNA seq
    case_variants: bool = True  # ChIP-seq vs ChIP-Seq vs chip-seq
    
    # Embedding settings (Phase 2B.3)
    use_embeddings: bool = False  # Enable in future phase
    embedding_model: str = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
    similarity_threshold: float = 0.80
    
    # Performance
    max_synonyms_per_term: int = 10
    cache_enabled: bool = True


class SynonymExpander:
    """
    Expands biomedical technique queries with synonyms from multiple sources.
    
    Phase 2B.1: Gazetteer-based expansion using biomedical ontologies
    Future phases will add embeddings, LLM-assisted generation, etc.
    """
    
    def __init__(self, config: Optional[SynonymExpansionConfig] = None):
        """
        Initialize synonym expander.
        
        Args:
            config: Configuration for synonym expansion
        """
        self.config = config or SynonymExpansionConfig()
        self._gazetteer: Dict[str, TechniqueSynonyms] = {}
        self._normalized_lookup: Dict[str, str] = {}  # normalized -> canonical
        self._cache: Dict[str, Set[str]] = {}
        
        if self.config.use_ontologies:
            self._build_gazetteer()
        
        if self.config.common_abbreviations:
            self._add_common_abbreviations()
    
    def _normalize_term(self, term: str) -> str:
        """
        Normalize term for matching.
        
        Args:
            term: Term to normalize
            
        Returns:
            Normalized term (lowercase, spaces)
        """
        # Convert to lowercase
        term = term.lower()
        # Replace hyphens with spaces
        term = term.replace('-', ' ')
        # Remove extra whitespace
        term = ' '.join(term.split())
        return term
    
    def _build_gazetteer(self) -> None:
        """
        Build gazetteer from biomedical ontologies.
        
        Phase 2B.1 implementation - loads curated technique synonyms from:
        - OBI (Ontology for Biomedical Investigations): assay types
        - EDAM (EDAM Ontology): bioinformatics operations
        - EFO (Experimental Factor Ontology): experimental methods
        - MeSH: Medical Subject Headings synonymy
        """
        logger.info("Building gazetteer from biomedical ontologies...")
        
        # Phase 2B.1: Manually curated high-value techniques
        # Future: Load from actual ontology files using pronto
        
        techniques = {
            # Sequencing technologies
            "RNA-seq": TechniqueSynonyms(
                canonical_name="RNA sequencing",
                canonical_id="OBI:0001271",
                synonyms={
                    "RNA-seq", "RNA seq", "RNAseq",
                    "transcriptome sequencing", "whole transcriptome sequencing",
                    "shotgun RNA sequencing"
                },
                abbreviations={"RNA-seq", "RNAseq"}
            ),
            
            "single-cell RNA-seq": TechniqueSynonyms(
                canonical_name="single-cell RNA sequencing",
                canonical_id="OBI:0002631",
                synonyms={
                    "scRNA-seq", "scRNAseq", "single cell RNA-seq",
                    "single-cell transcriptomics", "scRNA sequencing"
                },
                abbreviations={"scRNA-seq", "scRNAseq"}
            ),
            
            "ATAC-seq": TechniqueSynonyms(
                canonical_name="assay for transposase-accessible chromatin using sequencing",
                canonical_id="OBI:0002039",
                synonyms={
                    "ATAC-seq", "ATAC seq", "ATACseq",
                    "assay for transposase-accessible chromatin",
                    "transposase-accessible chromatin sequencing"
                },
                abbreviations={"ATAC-seq", "ATACseq"}
            ),
            
            "ChIP-seq": TechniqueSynonyms(
                canonical_name="chromatin immunoprecipitation sequencing",
                canonical_id="OBI:0000716",
                synonyms={
                    "ChIP-seq", "ChIP seq", "ChIPseq",
                    "chromatin immunoprecipitation sequencing",
                    "ChIP sequencing"
                },
                abbreviations={"ChIP-seq", "ChIPseq"}
            ),
            
            "WGBS": TechniqueSynonyms(
                canonical_name="whole genome bisulfite sequencing",
                canonical_id="OBI:0002117",
                synonyms={
                    "WGBS", "whole-genome bisulfite sequencing",
                    "bisulfite sequencing", "BS-seq", "BS seq"
                },
                abbreviations={"WGBS", "BS-seq"}
            ),
            
            "RRBS": TechniqueSynonyms(
                canonical_name="reduced representation bisulfite sequencing",
                canonical_id="OBI:0001863",
                synonyms={
                    "RRBS", "reduced representation bisulfite sequencing",
                    "reduced-representation bisulfite sequencing"
                },
                abbreviations={"RRBS"}
            ),
            
            "Hi-C": TechniqueSynonyms(
                canonical_name="Hi-C sequencing",
                canonical_id="OBI:0002043",
                synonyms={
                    "Hi-C", "high-throughput chromosome conformation capture",
                    "genome-wide chromosome conformation capture"
                },
                abbreviations={"Hi-C"}
            ),
            
            "DNase-seq": TechniqueSynonyms(
                canonical_name="DNase I hypersensitive sites sequencing",
                canonical_id="OBI:0001853",
                synonyms={
                    "DNase-seq", "DNase seq", "DNaseq",
                    "DNase I hypersensitive site sequencing",
                    "DNase hypersensitivity sequencing"
                },
                abbreviations={"DNase-seq", "DNaseq"}
            ),
            
            # Microarray technologies
            "microarray": TechniqueSynonyms(
                canonical_name="DNA microarray",
                canonical_id="OBI:0400148",
                synonyms={
                    "microarray", "gene chip", "DNA chip",
                    "oligonucleotide array", "expression array",
                    "gene expression microarray"
                },
                abbreviations={"microarray"}
            ),
            
            "methylation array": TechniqueSynonyms(
                canonical_name="DNA methylation array",
                canonical_id="OBI:0002118",
                synonyms={
                    "methylation array", "methylation microarray",
                    "DNA methylation array", "Illumina methylation array",
                    "450K array", "EPIC array", "Infinium array"
                },
                abbreviations={"450K", "EPIC"}
            ),
            
            # Chromatin accessibility
            "FAIRE-seq": TechniqueSynonyms(
                canonical_name="formaldehyde-assisted isolation of regulatory elements sequencing",
                canonical_id="OBI:0002044",
                synonyms={
                    "FAIRE-seq", "FAIRE seq", "FAIREseq",
                    "formaldehyde-assisted isolation of regulatory elements"
                },
                abbreviations={"FAIRE-seq", "FAIREseq"}
            ),
            
            # Protein-RNA interactions
            "CLIP-seq": TechniqueSynonyms(
                canonical_name="cross-linking immunoprecipitation sequencing",
                canonical_id="OBI:0001923",
                synonyms={
                    "CLIP-seq", "CLIP seq", "CLIPseq",
                    "cross-linking immunoprecipitation sequencing",
                    "UV cross-linking immunoprecipitation"
                },
                abbreviations={"CLIP-seq", "CLIPseq", "iCLIP", "eCLIP", "PAR-CLIP"}
            ),
            
            # DNA methylation
            "DNA methylation": TechniqueSynonyms(
                canonical_name="DNA methylation profiling",
                canonical_id="OBI:0001332",
                synonyms={
                    "DNA methylation", "DNA methylation profiling",
                    "methylation profiling", "CpG methylation",
                    "5-methylcytosine profiling"
                },
                abbreviations={"5mC", "CpG"}
            ),
            
            # Gene expression
            "gene expression profiling": TechniqueSynonyms(
                canonical_name="gene expression profiling",
                canonical_id="OBI:0000424",
                synonyms={
                    "gene expression", "gene expression profiling",
                    "transcriptome profiling", "expression profiling",
                    "mRNA expression"
                },
                abbreviations=set()
            ),
        }
        
        # Build lookup tables
        for key, tech in techniques.items():
            self._gazetteer[key] = tech
            
            # Add all terms to normalized lookup
            for term in tech.all_terms():
                normalized = self._normalize_term(term)
                if normalized not in self._normalized_lookup:
                    self._normalized_lookup[normalized] = key
        
        # Generate variants if enabled
        if self.config.generate_variants:
            self._generate_variants()
        
        logger.info(f"Gazetteer built with {len(self._gazetteer)} techniques")
    
    def _generate_variants(self) -> None:
        """Generate spelling variants for all techniques."""
        for tech in self._gazetteer.values():
            variants = set()
            
            # Generate hyphen/space variants
            if self.config.hyphen_variants:
                for term in tech.all_terms():
                    # Add hyphen variant
                    if ' ' in term and '-' not in term:
                        variants.add(term.replace(' ', '-'))
                    # Add space variant
                    if '-' in term and ' ' not in term:
                        variants.add(term.replace('-', ' '))
                    # Add no-space variant
                    if ' ' in term or '-' in term:
                        variants.add(term.replace(' ', '').replace('-', ''))
            
            # Generate case variants
            if self.config.case_variants:
                for term in list(tech.all_terms()) + list(variants):
                    # Add lowercase
                    variants.add(term.lower())
                    # Add uppercase
                    variants.add(term.upper())
                    # Add title case
                    variants.add(term.title())
            
            # Add variants to technique
            tech.variants.update(variants)
            
            # Update normalized lookup
            for variant in variants:
                normalized = self._normalize_term(variant)
                if normalized not in self._normalized_lookup:
                    # Find the key for this technique
                    for key, t in self._gazetteer.items():
                        if t == tech:
                            self._normalized_lookup[normalized] = key
                            break
    
    def _add_common_abbreviations(self) -> None:
        """Add common biomedical technique abbreviations."""
        # Common abbreviations not in ontologies
        common_abbrevs = {
            "NGS": ["next-generation sequencing", "high-throughput sequencing"],
            "WGS": ["whole genome sequencing", "whole-genome sequencing"],
            "WES": ["whole exome sequencing", "whole-exome sequencing"],
            "snRNA-seq": ["single-nucleus RNA sequencing", "single nucleus RNA-seq"],
            "spatial transcriptomics": ["spatial RNA sequencing", "spatial RNA-seq"],
            "MBD-seq": ["methyl-CpG binding domain sequencing", "MBD sequencing"],
            "MeDIP-seq": ["methylated DNA immunoprecipitation sequencing"],
            "ChIA-PET": ["chromatin interaction analysis by paired-end tag sequencing"],
            "4C": ["circular chromosome conformation capture"],
            "5C": ["chromosome conformation capture carbon copy"],
            "GRO-seq": ["global run-on sequencing"],
            "NET-seq": ["native elongating transcript sequencing"],
        }
        
        for abbrev, expansions in common_abbrevs.items():
            key = abbrev
            if key not in self._gazetteer:
                self._gazetteer[key] = TechniqueSynonyms(
                    canonical_name=expansions[0],
                    abbreviations={abbrev},
                    synonyms=set(expansions)
                )
                
                # Update normalized lookup
                for term in self._gazetteer[key].all_terms():
                    normalized = self._normalize_term(term)
                    if normalized not in self._normalized_lookup:
                        self._normalized_lookup[normalized] = key
    
    def expand(self, term: str, max_synonyms: Optional[int] = None) -> Set[str]:
        """
        Expand term with synonyms.
        
        Args:
            term: Biomedical technique term to expand
            max_synonyms: Maximum number of synonyms to return (default: config value)
            
        Returns:
            Set of expanded terms including original
        """
        # Check cache
        if self.config.cache_enabled and term in self._cache:
            return self._cache[term]
        
        expanded = {term}  # Always include original
        
        # Normalize and lookup
        normalized = self._normalize_term(term)
        
        if normalized in self._normalized_lookup:
            key = self._normalized_lookup[normalized]
            tech = self._gazetteer[key]
            
            # Get all terms
            all_terms = tech.all_terms()
            
            # Limit if requested
            max_syn = max_synonyms or self.config.max_synonyms_per_term
            if len(all_terms) > max_syn:
                # Prioritize: canonical > abbreviations > synonyms > variants
                priority_terms = (
                    [tech.canonical_name] +
                    sorted(tech.abbreviations) +
                    sorted(tech.synonyms)[:max_syn - len(tech.abbreviations) - 1]
                )
                expanded.update(priority_terms[:max_syn])
            else:
                expanded.update(all_terms)
        
        # Cache result
        if self.config.cache_enabled:
            self._cache[term] = expanded
        
        return expanded
    
    def expand_query(self, query: str) -> str:
        """
        Expand all technique terms in a query.
        
        Args:
            query: Search query containing biomedical terms
            
        Returns:
            Expanded query with synonym alternatives
        """
        # Find all techniques in query with their positions
        matches = []
        
        for key, tech in self._gazetteer.items():
            for term in tech.all_terms():
                # Case-insensitive search with word boundaries for better matching
                # Use \b for word boundaries to avoid matching inside words
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                for match in pattern.finditer(query):
                    matches.append({
                        'term': term,
                        'tech': tech,
                        'start': match.start(),
                        'end': match.end(),
                        'length': len(term)
                    })
        
        if not matches:
            return query  # No techniques found
        
        # Sort by start position and prefer longer matches (greedy matching)
        matches.sort(key=lambda m: (m['start'], -m['length']))
        
        # Remove overlapping matches (keep longer/first matches)
        non_overlapping = []
        for match in matches:
            # Check if this match overlaps with any already selected
            overlaps = False
            for selected in non_overlapping:
                if not (match['end'] <= selected['start'] or match['start'] >= selected['end']):
                    overlaps = True
                    break
            if not overlaps:
                non_overlapping.append(match)
        
        # Sort by position for replacement
        non_overlapping.sort(key=lambda m: m['start'])
        
        # Build expanded query by replacing matches from end to start
        # (to maintain position indices)
        base_query = query
        for match in reversed(non_overlapping):
            tech = match['tech']
            
            # Get top synonyms
            synonyms = sorted(tech.synonyms)[:3]  # Top 3 synonyms (sorted for consistency)
            abbrevs = sorted(tech.abbreviations)[:2]  # Top 2 abbreviations
            
            # Build OR clause: (term OR syn1 OR syn2 OR abbrev1)
            alternatives = [match['term']] + synonyms + abbrevs
            if len(alternatives) > 1:
                expansion = f"({' OR '.join(alternatives)})"
            else:
                expansion = match['term']
            
            # Replace this match
            base_query = base_query[:match['start']] + expansion + base_query[match['end']:]
        
        return base_query
    
    def get_canonical(self, term: str) -> Optional[str]:
        """
        Get canonical name for a term.
        
        Args:
            term: Term to canonicalize
            
        Returns:
            Canonical name or None if not found
        """
        normalized = self._normalize_term(term)
        if normalized in self._normalized_lookup:
            key = self._normalized_lookup[normalized]
            return self._gazetteer[key].canonical_name
        return None
    
    def get_ontology_id(self, term: str) -> Optional[str]:
        """
        Get ontology ID for a term.
        
        Args:
            term: Term to look up
            
        Returns:
            Ontology ID (e.g., OBI:0001271) or None
        """
        normalized = self._normalize_term(term)
        if normalized in self._normalized_lookup:
            key = self._normalized_lookup[normalized]
            return self._gazetteer[key].canonical_id
        return None
    
    def stats(self) -> Dict[str, int]:
        """Get statistics about the gazetteer."""
        total_terms = sum(len(tech.all_terms()) for tech in self._gazetteer.values())
        total_synonyms = sum(len(tech.synonyms) for tech in self._gazetteer.values())
        total_abbrevs = sum(len(tech.abbreviations) for tech in self._gazetteer.values())
        total_variants = sum(len(tech.variants) for tech in self._gazetteer.values())
        
        return {
            "techniques": len(self._gazetteer),
            "total_terms": total_terms,
            "synonyms": total_synonyms,
            "abbreviations": total_abbrevs,
            "variants": total_variants,
            "normalized_lookup": len(self._normalized_lookup)
        }
