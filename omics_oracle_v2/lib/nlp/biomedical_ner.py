"""
Biomedical named entity recognition engine.

Provides advanced NER capabilities using spaCy and SciSpaCy models
specifically designed for biomedical text processing.
"""

import logging
import time
from typing import List, Optional

from ...core.config import NLPSettings
from ...core.exceptions import NLPError
from .models import Entity, EntityType, ModelInfo, NERResult

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import spacy
    from spacy.tokens import Doc

    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    spacy = None  # type: ignore
    Doc = None  # type: ignore

try:
    import scispacy  # noqa: F401

    HAS_SCISPACY = True
except ImportError:
    HAS_SCISPACY = False


class BiomedicalNER:
    """
    Biomedical named entity recognition engine.

    Extracts and classifies biomedical entities from text using spaCy
    with optional SciSpaCy models for enhanced biomedical accuracy.

    Example:
        >>> ner = BiomedicalNER()
        >>> result = ner.extract_entities("TP53 gene mutations in lung cancer")
        >>> genes = result.get_entities_by_type(EntityType.GENE)
        >>> print(genes[0].text)
        TP53
    """

    # Model preference order (best to fallback)
    MODEL_PREFERENCE = [
        "en_core_sci_md",  # Medium SciSpaCy model (best for biomedical)
        "en_core_sci_sm",  # Small SciSpaCy model (faster)
        "en_core_web_sm",  # Standard spaCy (fallback)
    ]

    def __init__(self, settings: Optional[NLPSettings] = None):
        """
        Initialize biomedical NER engine.

        Args:
            settings: Optional NLP configuration. Uses defaults if not provided.

        Raises:
            NLPError: If spaCy is not available or no suitable model can be loaded.
        """
        self.settings = settings or NLPSettings()
        self._nlp = None
        self._model_name = None
        self._version = "2.0.0"
        self._load_model()

    def _load_model(self) -> None:
        """Load spaCy model with biomedical support."""
        if not HAS_SPACY:
            raise NLPError("spaCy not available. Install with: pip install spacy")

        # Use specific model if configured
        if self.settings.model_name != "en_core_web_sm":
            models_to_try = [self.settings.model_name]
        else:
            # Try best available models
            models_to_try = self.MODEL_PREFERENCE

        last_error = None
        for model_name in models_to_try:
            try:
                self._nlp = spacy.load(model_name)
                self._model_name = model_name
                logger.info(f"Loaded NLP model: {model_name}")
                return
            except OSError as e:
                last_error = e
                logger.debug(f"Could not load model {model_name}: {e}")
                continue

        # No model loaded successfully
        raise NLPError(
            f"Failed to load any NLP model. Last error: {last_error}. "
            f"Install a model with: python -m spacy download en_core_web_sm"
        ) from last_error

    def extract_entities(
        self,
        text: str,
        include_entity_linking: bool = False,
    ) -> NERResult:
        """
        Extract biomedical entities from text.

        Args:
            text: Input text to analyze
            include_entity_linking: Whether to include knowledge base IDs

        Returns:
            NERResult with extracted entities organized by type

        Raises:
            NLPError: If processing fails

        Example:
            >>> ner = BiomedicalNER()
            >>> result = ner.extract_entities("BRCA1 mutations cause breast cancer")
            >>> print(result.get_entity_count())
            2
        """
        if not self._nlp:
            raise NLPError("NLP model not initialized")

        start_time = time.time()

        try:
            doc = self._nlp(text)
            entities: List[Entity] = []

            for ent in doc.ents:
                entity = self._process_entity(ent, include_entity_linking)
                entities.append(entity)

            processing_time = (time.time() - start_time) * 1000

            return NERResult(
                text=text,
                entities=entities,
                processing_time_ms=processing_time,
                model_name=self._model_name or "unknown",
                model_version=self._nlp.meta.get("version", "unknown"),
            )

        except Exception as e:
            raise NLPError(f"Failed to extract entities: {e}") from e

    def _process_entity(self, ent, include_entity_linking: bool) -> Entity:
        """Process a spaCy entity into our Entity model."""
        text_lower = ent.text.lower()
        entity_type = self._classify_entity(ent, text_lower)

        # Get confidence if available (SciSpaCy extension)
        confidence = getattr(ent._, "confidence", 1.0) if hasattr(ent, "_") else 1.0

        # Get knowledge base ID if requested and available
        kb_id = None
        if include_entity_linking and hasattr(ent, "_") and hasattr(ent._, "kb_id"):
            kb_id = ent._.kb_id

        return Entity(
            text=ent.text,
            entity_type=entity_type,
            start=ent.start_char,
            end=ent.end_char,
            confidence=confidence,
            label=ent.label_,
            kb_id=kb_id,
        )

    def _classify_entity(self, ent, text_lower: str) -> EntityType:
        """
        Classify entity into biomedical category.

        Uses a combination of spaCy labels and domain-specific heuristics.

        Priority order (Oct 9, 2025 - UPDATED):
        - Techniques checked EARLY to prevent misclassification
        - WGBS/RRBS/ATAC-seq now correctly identified as techniques, not genes/chemicals
        """
        # Priority order matters - check most specific first

        # CHECK TECHNIQUES EARLY (before gene/chemical checks)
        # Fix: WGBS/RRBS were matching gene patterns, ATAC-seq matching chemical
        if self._is_experimental_technique(ent, text_lower):
            return EntityType.TECHNIQUE

        # Then check biological entities
        if self._is_gene_entity(ent, text_lower):
            return EntityType.GENE
        elif self._is_protein_entity(ent, text_lower):
            return EntityType.PROTEIN
        elif self._is_disease_entity(ent, text_lower):
            return EntityType.DISEASE
        elif self._is_chemical_entity(ent, text_lower):
            return EntityType.CHEMICAL
        elif self._is_organism_entity(ent, text_lower):
            return EntityType.ORGANISM
        elif self._is_tissue_entity(ent, text_lower):
            return EntityType.TISSUE
        elif self._is_cell_type_entity(ent, text_lower):
            return EntityType.CELL_TYPE
        elif self._is_anatomical_entity(ent, text_lower):
            return EntityType.ANATOMICAL
        elif self._is_phenotype_entity(ent, text_lower):
            return EntityType.PHENOTYPE
        else:
            return EntityType.GENERAL

    # Entity classification methods (extracted from v1)

    def _is_gene_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a gene."""
        # Specific gene patterns (highest priority)
        gene_patterns = {
            "brca1",
            "brca2",
            "tp53",
            "p53",
            "egfr",
            "her2",
            "myc",
            "ras",
            "pten",
            "apc",
        }

        # Explicit exclusions
        if self._is_disease_pattern(text_lower) or self._is_organism_pattern(text_lower):
            return False

        # Check specific gene patterns
        if text_lower in gene_patterns:
            return True

        # SciSpaCy GENE label
        if ent.label_ == "GENE":
            return True

        # Short uppercase strings likely genes (not diseases/organisms)
        return len(text_lower) <= 8 and ent.text.isupper() and len(text_lower) >= 2

    def _is_disease_pattern(self, text_lower: str) -> bool:
        """Check if text matches disease patterns."""
        disease_keywords = {"cancer", "carcinoma", "tumor", "diabetes", "disease"}
        return any(keyword in text_lower for keyword in disease_keywords)

    def _is_organism_pattern(self, text_lower: str) -> bool:
        """Check if text matches organism patterns."""
        organism_keywords = {"human", "mouse", "rat", "sapiens", "musculus"}
        return any(keyword in text_lower for keyword in organism_keywords)

    def _is_protein_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a protein."""
        protein_labels = {"PROTEIN"}
        protein_patterns = {
            "insulin",
            "hemoglobin",
            "collagen",
            "albumin",
            "immunoglobulin",
            "antibody",
        }

        return ent.label_ in protein_labels or text_lower in protein_patterns or "protein" in text_lower

    def _is_disease_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a disease."""
        disease_labels = {"DISEASE", "DISORDER", "SYMPTOM"}
        disease_patterns = {
            "cancer",
            "carcinoma",
            "tumor",
            "diabetes",
            "alzheimer",
            "parkinson",
            "hypertension",
            "asthma",
            "arthritis",
        }

        # Explicit exclusions for genes
        if text_lower in {"brca1", "brca2", "tp53", "p53", "egfr"}:
            return False

        return (
            ent.label_ in disease_labels
            or any(pattern in text_lower for pattern in disease_patterns)
            or text_lower.endswith("oma")
            or text_lower.endswith("itis")
        )

    def _is_chemical_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a chemical compound."""
        chemical_labels = {"CHEMICAL", "DRUG", "SMALL_MOLECULE"}
        chemical_patterns = {
            "glucose",
            "insulin",
            "dopamine",
            "serotonin",
            "acetylcholine",
            "atp",
            "dna",
            "rna",
        }

        return (
            ent.label_ in chemical_labels
            or text_lower in chemical_patterns
            or text_lower.endswith("ase")  # Enzymes
            or text_lower.endswith("in")  # Many drugs/chemicals
        )

    def _is_organism_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents an organism."""
        organism_labels = {"ORGANISM", "SPECIES", "TAXON"}
        organism_patterns = {
            "human",
            "mouse",
            "rat",
            "zebrafish",
            "drosophila",
            "c. elegans",
            "e. coli",
            "s. cerevisiae",
            "homo sapiens",
            "mus musculus",
        }

        # Explicit exclusions
        if text_lower in {"cancer", "brca1", "brca2", "tp53", "diabetes"}:
            return False

        return (
            ent.label_ in organism_labels
            or text_lower in organism_patterns
            or any(pattern in text_lower for pattern in organism_patterns)
        )

    def _is_tissue_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents tissue or organ."""
        tissue_labels = {"TISSUE", "ORGAN", "ANATOMICAL_ENTITY"}
        tissue_patterns = {
            "brain",
            "heart",
            "liver",
            "kidney",
            "lung",
            "breast",
            "prostate",
            "muscle",
            "bone",
            "skin",
            "blood",
        }

        return (
            ent.label_ in tissue_labels
            or text_lower in tissue_patterns
            or any(pattern in text_lower for pattern in tissue_patterns)
        )

    def _is_cell_type_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a cell type."""
        cell_labels = {"CELL", "CELL_TYPE", "CELL_LINE"}
        cell_patterns = {
            "neuron",
            "lymphocyte",
            "fibroblast",
            "hepatocyte",
            "t cell",
            "b cell",
            "stem cell",
            "macrophage",
        }

        return (
            ent.label_ in cell_labels
            or text_lower in cell_patterns
            or "cell" in text_lower
            or text_lower.endswith("cyte")
        )

    def _is_anatomical_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents anatomical structure."""
        anatomical_labels = {"ANATOMICAL_ENTITY", "ANATOMY"}
        anatomical_patterns = {
            "chromosome",
            "mitochondria",
            "nucleus",
            "membrane",
            "cytoplasm",
            "ribosome",
        }

        return (
            ent.label_ in anatomical_labels
            or text_lower in anatomical_patterns
            or any(pattern in text_lower for pattern in anatomical_patterns)
        )

    def _is_phenotype_entity(self, ent, text_lower: str) -> bool:
        """Check if entity represents a phenotype."""
        phenotype_labels = {"PHENOTYPE", "TRAIT"}
        phenotype_patterns = {
            "expression",
            "activity",
            "function",
            "regulation",
            "pathway",
            "signaling",
        }

        return (
            ent.label_ in phenotype_labels
            or text_lower in phenotype_patterns
            or any(pattern in text_lower for pattern in phenotype_patterns)
        )

    def _is_experimental_technique(self, ent, text_lower: str) -> bool:
        """
        Check if entity represents an experimental technique.

        Enhanced Oct 9, 2025 with comprehensive genomic techniques:
        - Epigenetics: DNA methylation, WGBS, RRBS, bisulfite-seq
        - Chromatin accessibility: ATAC-seq, DNase-seq, FAIRE-seq
        - Gene expression: RNA-seq variants, microarray
        - 3D genome: Hi-C, ChIA-PET
        - RNA biology: CLIP-seq, RIP-seq
        """
        # Core NGS sequencing techniques (high priority - exact matches)
        ngs_core = {
            # RNA sequencing
            "rna-seq", "rnaseq", "rna seq",
            "scrna-seq", "scrnaseq", "single-cell rna-seq", "single cell rna-seq",
            "snrna-seq", "snrnaseq", "single-nucleus rna-seq",
            "bulk rna-seq", "total rna-seq",

            # DNA methylation / Epigenetics
            "wgbs", "rrbs",
            "bisulfite-seq", "bisulfite seq", "bs-seq",
            "whole genome bisulfite", "reduced representation bisulfite",
            "dna methylation", "methylation profiling", "methylation",

            # Chromatin accessibility
            "atac-seq", "atacseq", "atac seq", "atac",
            "dnase-seq", "dnaseseq", "dnase seq", "dnase",
            "faire-seq", "faireseq", "faire seq", "faire",
            "mnase-seq", "mnaseseq",
            "nome-seq", "nomeseq",
            "chromatin accessibility", "open chromatin",

            # ChIP-based techniques
            "chip-seq", "chipseq", "chip seq",
            "cut&run", "cut&tag", "cutrun", "cuttag",
            "chip-exo", "chipexo",
            "chromatin immunoprecipitation",

            # 3D genome structure
            "hi-c", "hic",
            "chia-pet", "chiapet",
            "plac-seq", "placseq",
            "3c", "4c", "5c",
            "chromatin conformation",

            # RNA-protein interactions
            "clip-seq", "clipseq", "par-clip", "iclip", "eclip",
            "rip-seq", "ripseq",
            "rna immunoprecipitation",

            # RNA modifications
            "m6a-seq", "m6aseq",
            "ribo-seq", "riboseq",

            # Nascent RNA / Transcription
            "gro-seq", "groseq",
            "net-seq", "netseq",
            "cage-seq", "cageseq", "cage",
            "rampage", "rampage-seq",

            # Microarray and classic techniques
            "microarray", "gene chip", "affymetrix",

            # PCR-based
            "pcr", "qpcr", "rt-pcr", "rt-qpcr",
            "quantitative pcr", "real-time pcr",

            # Proteomics
            "western blot", "immunoblot",
            "flow cytometry", "facs",
            "immunofluorescence", "if",
            "mass spectrometry", "proteomics",

            # General
            "sequencing", "genomics", "transcriptomics",
        }

        # Multi-word technique phrases (check for substring matches)
        technique_phrases = {
            "gene expression",
            "expression profiling",
            "transcription factor binding",
            "histone modification",
            "chromatin remodeling",
            "nucleosome positioning",
            "dna methylation",
            "chromatin accessibility",
            "open chromatin",
            "genome-wide association",
            "whole genome sequencing",
            "whole exome sequencing",
            "targeted sequencing",
            "amplicon sequencing",
        }

        # Check exact matches (case-insensitive)
        if text_lower in ngs_core:
            return True

        # Check multi-word phrases (substring match)
        for phrase in technique_phrases:
            if phrase in text_lower:
                return True

        # Check -seq suffix (most NGS techniques)
        if text_lower.endswith("-seq") and len(text_lower) > 4:
            return True

        # Check seq suffix (alternative spelling)
        if text_lower.endswith("seq") and len(text_lower) > 4:
            # Avoid false positives like "request"
            if not text_lower.endswith("quest"):
                return True

        # Check "sequencing" in name
        if "sequencing" in text_lower:
            return True

        # Check chromatin-related (likely technique)
        if "chromatin" in text_lower and len(text_lower) > 9:
            return True

        # Check methylation-related (epigenetics)
        if "methylation" in text_lower:
            return True

        # Check bisulfite (methylation technique)
        if "bisulfite" in text_lower:
            return True

        return False

    def get_model_info(self) -> ModelInfo:
        """
        Get information about the loaded model.

        Returns:
            ModelInfo with model details
        """
        if not self._nlp:
            return ModelInfo(status="not_loaded")

        return ModelInfo(
            status="loaded",
            model_name=self._model_name,
            model_version=self._nlp.meta.get("version", "unknown"),
            language=self._nlp.meta.get("lang", "en"),
            has_scispacy=HAS_SCISPACY,
            has_spacy=HAS_SPACY,
            pipeline_components=list(self._nlp.pipe_names),
        )

    def is_available(self) -> bool:
        """Check if NER is available and ready."""
        return self._nlp is not None
