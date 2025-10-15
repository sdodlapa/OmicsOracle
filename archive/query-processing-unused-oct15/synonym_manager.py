"""
Biological synonym management for entity normalization.

Provides comprehensive mapping of biological terms to synonyms and
standard identifiers for entity normalization and search expansion.
"""

from typing import Dict, List, Set


class SynonymManager:
    """
    Manages biological entity synonyms and normalization.

    Provides bidirectional mapping between canonical terms and their
    various synonyms, abbreviations, and alternative names across
    multiple biological domains.

    Example:
        >>> sm = SynonymManager()
        >>> synonyms = sm.get_synonyms("brca1", "gene")
        >>> print("brca-1" in synonyms)
        True
        >>> canonical = sm.normalize_term("p53", "gene")
        >>> print(canonical)
        TP53
    """

    def __init__(self) -> None:
        """Initialize synonym mappings."""
        self._init_synonym_maps()

    def _init_synonym_maps(self) -> None:
        """Initialize comprehensive synonym dictionaries."""
        # Gene synonyms
        self.gene_synonyms: Dict[str, List[str]] = {
            "brca1": ["breast cancer 1", "brca-1", "brcaa1", "rcd1"],
            "brca2": ["breast cancer 2", "brca-2", "brcaa2", "fancd1"],
            "tp53": ["tumor protein p53", "p53", "tp-53", "li-fraumeni syndrome"],
            "pten": ["phosphatase and tensin homolog", "pten1", "cowden syndrome 1"],
            "apc": [
                "adenomatous polyposis coli",
                "apc1",
                "familial adenomatous polyposis",
            ],
            "myc": ["myelocytomatosis oncogene", "c-myc", "myc proto-oncogene"],
            "ras": ["rat sarcoma", "hras", "kras", "nras"],
            "egfr": ["epidermal growth factor receptor", "egf receptor", "erbb1"],
            "her2": ["human epidermal growth factor receptor 2", "erbb2", "neu"],
            "bcl2": ["b-cell lymphoma 2", "bcl-2", "apoptosis regulator bcl2"],
            "vegf": ["vascular endothelial growth factor", "vegf-a"],
            "tgfb": ["transforming growth factor beta", "tgf-beta", "tgfb1"],
            "il1": ["interleukin 1", "interleukin-1", "il-1"],
            "tnf": ["tumor necrosis factor", "tnf-alpha", "tnfa"],
            "ifn": ["interferon", "ifn-alpha", "ifn-beta", "ifn-gamma"],
        }

        # Disease synonyms
        self.disease_synonyms: Dict[str, List[str]] = {
            "breast cancer": [
                "breast carcinoma",
                "mammary cancer",
                "bc",
                "invasive ductal carcinoma",
            ],
            "lung cancer": [
                "lung carcinoma",
                "pulmonary cancer",
                "lc",
                "non-small cell lung cancer",
                "nsclc",
            ],
            "prostate cancer": [
                "prostate carcinoma",
                "pca",
                "adenocarcinoma of prostate",
            ],
            "colorectal cancer": [
                "colon cancer",
                "rectal cancer",
                "crc",
                "colorectal carcinoma",
            ],
            "alzheimer": ["alzheimer's disease", "ad", "dementia", "alzheimer disease"],
            "parkinson": [
                "parkinson's disease",
                "pd",
                "parkinson disease",
                "paralysis agitans",
            ],
            "diabetes": [
                "diabetes mellitus",
                "dm",
                "type 1 diabetes",
                "type 2 diabetes",
                "t1d",
                "t2d",
            ],
            "obesity": ["overweight", "adiposity", "corpulence"],
            "hypertension": ["high blood pressure", "htn", "arterial hypertension"],
            "atherosclerosis": ["arteriosclerosis", "coronary artery disease", "cad"],
        }

        # Organism synonyms
        self.organism_synonyms: Dict[str, List[str]] = {
            "human": ["homo sapiens", "h. sapiens", "hsa", "man"],
            "mouse": ["mus musculus", "m. musculus", "mmu", "laboratory mouse"],
            "rat": ["rattus norvegicus", "r. norvegicus", "rno", "laboratory rat"],
            "zebrafish": ["danio rerio", "d. rerio", "dre", "zebra fish"],
            "fruit fly": [
                "drosophila melanogaster",
                "d. melanogaster",
                "dme",
                "drosophila",
            ],
            "nematode": ["caenorhabditis elegans", "c. elegans", "cel", "roundworm"],
            "yeast": [
                "saccharomyces cerevisiae",
                "s. cerevisiae",
                "sce",
                "baker's yeast",
            ],
            "e. coli": ["escherichia coli", "e coli", "eco"],
            "arabidopsis": [
                "arabidopsis thaliana",
                "a. thaliana",
                "ath",
                "thale cress",
            ],
        }

        # Tissue/organ synonyms
        self.tissue_synonyms: Dict[str, List[str]] = {
            "brain": ["cerebrum", "cerebral tissue", "neural tissue", "nervous tissue"],
            "heart": ["cardiac tissue", "myocardium", "cardiac muscle"],
            "liver": ["hepatic tissue", "hepatocytes"],
            "kidney": ["renal tissue", "nephrons"],
            "lung": ["pulmonary tissue", "respiratory tissue"],
            "muscle": ["skeletal muscle", "muscular tissue", "myocytes"],
            "blood": ["hematopoietic tissue", "blood cells", "plasma"],
            "bone": ["skeletal tissue", "osseous tissue", "osteocytes"],
            "skin": ["cutaneous tissue", "dermal tissue", "epidermis", "dermis"],
        }

        # Cell type synonyms
        self.cell_type_synonyms: Dict[str, List[str]] = {
            "t cell": ["t lymphocyte", "t-cell", "helper t cell", "cytotoxic t cell"],
            "b cell": ["b lymphocyte", "b-cell", "plasma cell"],
            "macrophage": ["phagocyte", "antigen-presenting cell", "apc"],
            "neuron": ["nerve cell", "neural cell"],
            "fibroblast": ["connective tissue cell"],
            "stem cell": [
                "progenitor cell",
                "undifferentiated cell",
                "embryonic stem cell",
                "esc",
            ],
            "endothelial cell": ["vascular endothelium", "blood vessel lining"],
        }

        # Experimental technique synonyms
        self.technique_synonyms: Dict[str, List[str]] = {
            "rna-seq": [
                "rna sequencing",
                "transcriptome sequencing",
                "whole transcriptome shotgun sequencing",
            ],
            "chip-seq": ["chromatin immunoprecipitation sequencing", "chip sequencing"],
            "western blot": ["western blotting", "immunoblot", "protein blot"],
            "pcr": ["polymerase chain reaction", "amplification"],
            "qpcr": ["quantitative pcr", "real-time pcr", "rt-pcr"],
            "microarray": ["gene chip", "dna microarray", "expression array"],
            "flow cytometry": ["facs", "fluorescence-activated cell sorting"],
        }

    def get_synonyms(self, term: str, entity_type: str = "general") -> Set[str]:
        """
        Get comprehensive synonyms for a biological term.

        Args:
            term: Input term to find synonyms for
            entity_type: Entity type hint (gene, disease, organism, tissue,
                        cell_type, technique, general)

        Returns:
            Set of synonyms including the original term

        Example:
            >>> sm = SynonymManager()
            >>> synonyms = sm.get_synonyms("brca1", "gene")
            >>> "breast cancer 1" in synonyms
            True
        """
        term_lower = term.lower()
        synonyms = {term}  # Include original term

        # Map entity types to synonym dictionaries
        category_map = {
            "gene": self.gene_synonyms,
            "disease": self.disease_synonyms,
            "organism": self.organism_synonyms,
            "tissue": self.tissue_synonyms,
            "cell_type": self.cell_type_synonyms,
            "technique": self.technique_synonyms,
        }

        if entity_type in category_map:
            # Search in specific category
            synonym_dict = category_map[entity_type]
            synonyms.update(self._find_in_dict(term_lower, synonym_dict))
        else:
            # Search all categories
            for synonym_dict in category_map.values():
                synonyms.update(self._find_in_dict(term_lower, synonym_dict))
                if len(synonyms) > 1:  # Found something
                    break

        return synonyms

    def _find_in_dict(
        self, term_lower: str, synonym_dict: Dict[str, List[str]]
    ) -> Set[str]:
        """Find synonyms in a specific dictionary."""
        synonyms = set()

        # Check if term is a canonical term
        if term_lower in synonym_dict:
            synonyms.update(synonym_dict[term_lower])
            return synonyms

        # Check if term is a synonym of any canonical term
        for canonical, synonym_list in synonym_dict.items():
            if term_lower in synonym_list:
                synonyms.add(canonical)
                synonyms.update(synonym_list)
                break

        return synonyms

    def normalize_term(self, term: str, entity_type: str = "general") -> str:
        """
        Normalize a biological term to its canonical form.

        Args:
            term: Input term to normalize
            entity_type: Entity type hint

        Returns:
            Normalized canonical term (or original if not found)

        Example:
            >>> sm = SynonymManager()
            >>> sm.normalize_term("p53", "gene")
            'TP53'
            >>> sm.normalize_term("alzheimer's disease", "disease")
            'Alzheimer'
        """
        term_lower = term.lower()

        category_map = {
            "gene": self.gene_synonyms,
            "disease": self.disease_synonyms,
            "organism": self.organism_synonyms,
            "tissue": self.tissue_synonyms,
            "cell_type": self.cell_type_synonyms,
            "technique": self.technique_synonyms,
        }

        if entity_type in category_map:
            canonical = self._find_canonical(term_lower, category_map[entity_type])
            if canonical:
                return canonical.upper() if entity_type == "gene" else canonical.title()

        # Try all categories if not found
        for etype, synonym_dict in category_map.items():
            canonical = self._find_canonical(term_lower, synonym_dict)
            if canonical:
                return canonical.upper() if etype == "gene" else canonical.title()

        # Return original if no normalization found
        return term

    def _find_canonical(
        self, term_lower: str, synonym_dict: Dict[str, List[str]]
    ) -> str:
        """Find canonical term in dictionary."""
        # Check if term is already canonical
        if term_lower in synonym_dict:
            return term_lower

        # Check if term is a synonym
        for canonical, synonyms in synonym_dict.items():
            if term_lower in synonyms:
                return canonical

        return ""

    def get_entity_relationships(self, term: str) -> Dict[str, List[str]]:
        """
        Get related entities for a given term.

        This provides basic relationship mapping that could be expanded
        with knowledge graphs or external databases.

        Args:
            term: Input term

        Returns:
            Dictionary of related entities by type

        Example:
            >>> sm = SynonymManager()
            >>> rels = sm.get_entity_relationships("brca1")
            >>> "breast cancer" in rels["related_diseases"]
            True
        """
        term_lower = term.lower()
        relationships: Dict[str, List[str]] = {
            "related_genes": [],
            "related_diseases": [],
            "related_organisms": [],
            "related_techniques": [],
        }

        # Basic relationship mapping (could be expanded)
        if term_lower in ["brca1", "brca2"]:
            relationships["related_diseases"] = ["breast cancer", "ovarian cancer"]
            relationships["related_techniques"] = ["sequencing", "genetic testing"]

        elif term_lower in ["tp53", "p53"]:
            relationships["related_diseases"] = [
                "li-fraumeni syndrome",
                "various cancers",
            ]
            relationships["related_genes"] = ["mdm2", "p21"]

        elif "cancer" in term_lower:
            relationships["related_techniques"] = [
                "rna-seq",
                "chip-seq",
                "immunohistochemistry",
            ]
            relationships["related_genes"] = ["tp53", "brca1", "brca2", "pten", "apc"]

        return relationships
