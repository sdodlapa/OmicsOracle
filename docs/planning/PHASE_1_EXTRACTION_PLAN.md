# 🔬 Phase 1: Algorithm Extraction - Detailed Plan

**Phase**: 1 of 4
**Duration**: 2 weeks (Weeks 3-4)
**Effort**: ~60 hours
**Start Date**: October 16, 2025
**Target Completion**: October 30, 2025
**Status**: READY TO START

---

## 📋 Executive Summary

Phase 1 extracts proven domain algorithms from the monolithic v1 codebase into clean, reusable libraries. This creates the foundation for the v2 multi-agent architecture while preserving $50-75K worth of validated biomedical logic.

**Key Principle**: Extract → Test → Document → Validate Independence

---

## 🎯 Phase Goals

### Primary Objectives
1. ✅ Create clean `omics_oracle_v2/` structure
2. ✅ Extract BiomedicalNER with zero dependencies on v1
3. ✅ Extract UnifiedGEOClient as standalone library
4. ✅ Extract SummarizationService with clean interfaces
5. ✅ Extract Config system to core module
6. ✅ Achieve 80%+ test coverage on all extracted code

### Success Metrics
- All extracted algorithms work independently
- Zero imports from `src/omics_oracle/` (v1)
- 80%+ test coverage on new code
- All tests pass (pytest, mypy, flake8)
- Complete API documentation
- Performance benchmarks show no regression

---

## 📊 Detailed Task Breakdown

### Task 1: Project Structure Setup (4 hours)

**Objective**: Create the v2 directory structure and scaffolding

**Subtasks**:
1. Create `omics_oracle_v2/` root directory
2. Create library structure (`lib/nlp/`, `lib/geo/`, `lib/ai/`)
3. Create core structure (`core/`)
4. Create test structure (`tests/unit/`, `tests/integration/`)
5. Add all `__init__.py` files with proper docstrings
6. Create `py.typed` marker for type checking
7. Setup initial `pyproject.toml` for v2
8. Create `README.md` for v2

**Deliverables**:
```
omics_oracle_v2/
├── __init__.py                 # Root package
├── py.typed                    # Type checking marker
├── README.md                   # v2 overview
├── lib/                        # Algorithm library
│   ├── __init__.py
│   ├── nlp/                    # NLP algorithms
│   │   └── __init__.py
│   ├── geo/                    # GEO data access
│   │   └── __init__.py
│   └── ai/                     # AI/ML services
│       └── __init__.py
├── core/                       # Core infrastructure
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom exceptions
│   └── types.py               # Type definitions
└── tests/                      # Test suite
    ├── __init__.py
    ├── conftest.py            # Shared fixtures
    ├── unit/                  # Unit tests
    │   ├── __init__.py
    │   ├── test_nlp.py
    │   ├── test_geo.py
    │   └── test_ai.py
    └── integration/           # Integration tests
        └── __init__.py
```

**Success Criteria**:
- [ ] All directories created
- [ ] All `__init__.py` files have docstrings
- [ ] `py.typed` marker present
- [ ] Import test: `import omics_oracle_v2` works
- [ ] pytest discovers test structure

**Commands**:
```bash
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
mkdir -p omics_oracle_v2/{lib/{nlp,geo,ai},core,tests/{unit,integration}}
touch omics_oracle_v2/py.typed
# Create all __init__.py files with proper headers
```

---

### Task 2: Core Infrastructure Extraction (8 hours)

**Objective**: Extract configuration system and core utilities

**Source Files** (from v1):
- `src/omics_oracle/core/config.py` → Review and extract
- `src/omics_oracle/config/` → Review patterns
- Environment variable handling
- Logging configuration

**Target Files** (in v2):
- `omics_oracle_v2/core/config.py`
- `omics_oracle_v2/core/exceptions.py`
- `omics_oracle_v2/core/types.py`
- `omics_oracle_v2/core/logging.py`

**Extraction Strategy**:
1. **Analyze v1 config patterns**:
   - Review all config usage in v1
   - Identify essential vs. bloat
   - Document configuration requirements

2. **Design v2 config system**:
   - Pydantic-based settings (type-safe)
   - Environment variable support
   - Validation and defaults
   - No global state (injectable)

3. **Create custom exceptions**:
   - Base `OmicsOracleError`
   - Domain-specific exceptions (NER, GEO, AI)
   - Proper error messages and context

4. **Define core types**:
   - Type aliases for common patterns
   - Protocol classes for interfaces
   - Generic types for reusability

**Code Structure**:
```python
# omics_oracle_v2/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class NLPSettings(BaseSettings):
    """NLP pipeline configuration."""
    model_name: str = "en_core_web_sm"
    batch_size: int = 32
    max_entities: int = 100

    class Config:
        env_prefix = "OMICS_NLP_"

class GEOSettings(BaseSettings):
    """GEO data access configuration."""
    api_key: Optional[str] = None
    cache_ttl: int = 3600
    max_retries: int = 3

    class Config:
        env_prefix = "OMICS_GEO_"

class AISettings(BaseSettings):
    """AI summarization configuration."""
    openai_api_key: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7

    class Config:
        env_prefix = "OMICS_AI_"

class Settings(BaseSettings):
    """Main application settings."""
    nlp: NLPSettings = NLPSettings()
    geo: GEOSettings = GEOSettings()
    ai: AISettings = AISettings()
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

```python
# omics_oracle_v2/core/exceptions.py
class OmicsOracleError(Exception):
    """Base exception for OmicsOracle v2."""
    pass

class ConfigurationError(OmicsOracleError):
    """Configuration-related errors."""
    pass

class NLPError(OmicsOracleError):
    """NLP processing errors."""
    pass

class GEOError(OmicsOracleError):
    """GEO data access errors."""
    pass

class AIError(OmicsOracleError):
    """AI service errors."""
    pass
```

**Testing**:
- Test config loading from environment
- Test config validation (invalid values)
- Test config defaults
- Test exception hierarchy

**Success Criteria**:
- [ ] Settings class loads from environment
- [ ] Validation catches invalid configs
- [ ] Zero dependencies on v1 config
- [ ] 90%+ test coverage on config module
- [ ] All exceptions properly typed

---

### Task 3: BiomedicalNER Extraction (16 hours)

**Objective**: Extract NER algorithms into standalone library

**Source Files** (from v1):
- `src/omics_oracle/nlp/biomedical_ner.py` (primary)
- `src/omics_oracle/nlp/entity_resolver.py`
- `src/omics_oracle/nlp/synonym_manager.py`
- Related utility functions

**Target Files** (in v2):
```
omics_oracle_v2/lib/nlp/
├── __init__.py
├── biomedical_ner.py          # Main NER engine
├── entity_resolver.py         # Entity resolution
├── synonym_manager.py         # Synonym mapping
├── models.py                  # Data models (Pydantic)
├── preprocessing.py           # Text preprocessing
└── utils.py                   # Utility functions
```

**Extraction Strategy**:

**Step 1: Analyze Current Implementation**
```bash
# Review current NER implementation
grep -r "class BiomedicalNER" src/omics_oracle/
grep -r "import.*BiomedicalNER" src/
# Document dependencies, inputs, outputs
```

**Step 2: Create Data Models**
```python
# omics_oracle_v2/lib/nlp/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class EntityType(str, Enum):
    """Supported biomedical entity types."""
    GENE = "gene"
    PROTEIN = "protein"
    DISEASE = "disease"
    DRUG = "drug"
    CELL_TYPE = "cell_type"
    TISSUE = "tissue"
    ORGANISM = "organism"

class Entity(BaseModel):
    """Biomedical named entity."""
    text: str = Field(..., description="Entity text as it appears")
    entity_type: EntityType = Field(..., description="Entity category")
    start: int = Field(..., description="Start character position")
    end: int = Field(..., description="End character position")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    normalized_id: Optional[str] = Field(None, description="Database ID (e.g., NCBI Gene ID)")
    synonyms: List[str] = Field(default_factory=list)

    class Config:
        frozen = True  # Immutable

class NERResult(BaseModel):
    """Result of NER processing."""
    text: str = Field(..., description="Original input text")
    entities: List[Entity] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Processing duration")
    model_version: str = Field(..., description="NER model version")
```

**Step 3: Extract Core NER Logic**
```python
# omics_oracle_v2/lib/nlp/biomedical_ner.py
from typing import List, Optional
import spacy
from .models import Entity, EntityType, NERResult
from ..core.config import NLPSettings
from ..core.exceptions import NLPError

class BiomedicalNER:
    """
    Biomedical Named Entity Recognition engine.

    Extracts and classifies biomedical entities from text using
    spaCy with custom domain-specific models and rules.

    Example:
        >>> ner = BiomedicalNER()
        >>> result = ner.extract_entities("TP53 gene mutations in lung cancer")
        >>> print(result.entities)
        [Entity(text='TP53', entity_type='gene', ...),
         Entity(text='lung cancer', entity_type='disease', ...)]
    """

    def __init__(self, settings: Optional[NLPSettings] = None):
        """
        Initialize NER engine.

        Args:
            settings: Optional NLP configuration. Uses defaults if not provided.
        """
        self.settings = settings or NLPSettings()
        self._model = None
        self._version = "2.0.0"

    def _load_model(self) -> None:
        """Load spaCy model with custom components."""
        if self._model is not None:
            return

        try:
            self._model = spacy.load(self.settings.model_name)
            # Add custom biomedical pipeline components
            # (extract from v1, clean up, add tests)
        except OSError as e:
            raise NLPError(
                f"Failed to load NER model '{self.settings.model_name}'. "
                f"Run: python -m spacy download {self.settings.model_name}"
            ) from e

    def extract_entities(self, text: str) -> NERResult:
        """
        Extract biomedical entities from text.

        Args:
            text: Input text to process

        Returns:
            NERResult with extracted entities and metadata

        Raises:
            NLPError: If processing fails
        """
        import time
        start_time = time.time()

        self._load_model()

        # Process text (extract clean logic from v1)
        doc = self._model(text)

        entities = self._extract_entities_from_doc(doc)

        processing_time = (time.time() - start_time) * 1000

        return NERResult(
            text=text,
            entities=entities,
            processing_time_ms=processing_time,
            model_version=self._version
        )

    def _extract_entities_from_doc(self, doc) -> List[Entity]:
        """Extract Entity objects from spaCy Doc."""
        # Extract clean logic from v1
        # Add proper type mapping
        # Add confidence scoring
        pass
```

**Step 4: Extract Synonym Manager**
```python
# omics_oracle_v2/lib/nlp/synonym_manager.py
from typing import Dict, List, Set
from pathlib import Path
import json

class SynonymManager:
    """
    Manages biomedical entity synonyms and aliases.

    Provides bidirectional mapping between entity names and their
    various synonyms, abbreviations, and alternative names.
    """

    def __init__(self, synonym_data_path: Optional[Path] = None):
        """Initialize with synonym data."""
        self._synonyms: Dict[str, Set[str]] = {}
        self._reverse_map: Dict[str, str] = {}

        if synonym_data_path:
            self.load_synonyms(synonym_data_path)

    def load_synonyms(self, path: Path) -> None:
        """Load synonym mappings from JSON file."""
        # Extract from v1, add proper error handling
        pass

    def get_synonyms(self, entity: str) -> Set[str]:
        """Get all synonyms for an entity."""
        # Extract from v1
        pass

    def get_canonical_form(self, synonym: str) -> Optional[str]:
        """Get canonical entity name for a synonym."""
        # Extract from v1
        pass
```

**Testing Strategy**:
```python
# tests/unit/test_nlp.py
import pytest
from omics_oracle_v2.lib.nlp import BiomedicalNER
from omics_oracle_v2.lib.nlp.models import EntityType

class TestBiomedicalNER:
    """Test BiomedicalNER extraction."""

    @pytest.fixture
    def ner(self):
        """Create NER instance."""
        return BiomedicalNER()

    def test_gene_extraction(self, ner):
        """Test gene entity extraction."""
        text = "TP53 gene is mutated in many cancers"
        result = ner.extract_entities(text)

        genes = [e for e in result.entities if e.entity_type == EntityType.GENE]
        assert len(genes) > 0
        assert any(e.text.upper() == "TP53" for e in genes)

    def test_disease_extraction(self, ner):
        """Test disease entity extraction."""
        text = "Patients with lung cancer show TP53 mutations"
        result = ner.extract_entities(text)

        diseases = [e for e in result.entities if e.entity_type == EntityType.DISEASE]
        assert len(diseases) > 0
        assert any("cancer" in e.text.lower() for e in diseases)

    def test_empty_input(self, ner):
        """Test handling of empty input."""
        result = ner.extract_entities("")
        assert len(result.entities) == 0

    def test_no_entities(self, ner):
        """Test text with no biomedical entities."""
        result = ner.extract_entities("The quick brown fox jumps")
        # Should return empty or minimal results
        assert isinstance(result.entities, list)
```

**Success Criteria**:
- [ ] BiomedicalNER works independently
- [ ] No imports from `src/omics_oracle/`
- [ ] All entity types supported
- [ ] Synonym resolution works
- [ ] 80%+ test coverage
- [ ] Performance benchmarks pass (< 100ms per document)

---

### Task 4: UnifiedGEOClient Extraction (14 hours)

**Objective**: Extract GEO data access as standalone library

**Source Files** (from v1):
- `src/omics_oracle/integrations/geo_integration.py`
- `src/omics_oracle/data/geo_*.py`
- Related parsers and utilities

**Target Files** (in v2):
```
omics_oracle_v2/lib/geo/
├── __init__.py
├── client.py                  # Main GEO client
├── models.py                  # Data models
├── parsers.py                 # SOFT/MINiML parsers
├── cache.py                   # Response caching
└── utils.py                   # Utility functions
```

**Extraction Strategy**:

**Step 1: Create Data Models**
```python
# omics_oracle_v2/lib/geo/models.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime

class GEOSample(BaseModel):
    """GEO sample metadata."""
    accession: str = Field(..., pattern=r"^GSM\d+$")
    title: str
    organism: str
    description: Optional[str] = None
    characteristics: Dict[str, str] = Field(default_factory=dict)
    supplementary_files: List[HttpUrl] = Field(default_factory=list)

class GEOSeries(BaseModel):
    """GEO series (dataset) metadata."""
    accession: str = Field(..., pattern=r"^GSE\d+$")
    title: str
    summary: str
    design: Optional[str] = None
    organism: List[str]
    publication_date: Optional[datetime] = None
    sample_count: int = 0
    samples: List[GEOSample] = Field(default_factory=list)

class GEOPlatform(BaseModel):
    """GEO platform metadata."""
    accession: str = Field(..., pattern=r"^GPL\d+$")
    title: str
    organism: str
    technology: str
    description: Optional[str] = None
```

**Step 2: Extract Client Logic**
```python
# omics_oracle_v2/lib/geo/client.py
from typing import Optional
import requests
from .models import GEOSeries, GEOSample, GEOPlatform
from ..core.config import GEOSettings
from ..core.exceptions import GEOError
from .cache import GEOCache

class UnifiedGEOClient:
    """
    Unified client for NCBI GEO database access.

    Provides programmatic access to GEO series, samples, and platforms
    with automatic caching and error handling.

    Example:
        >>> client = UnifiedGEOClient()
        >>> series = client.get_series("GSE123456")
        >>> print(f"Dataset: {series.title}")
        >>> print(f"Samples: {len(series.samples)}")
    """

    BASE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

    def __init__(self, settings: Optional[GEOSettings] = None):
        """
        Initialize GEO client.

        Args:
            settings: Optional GEO configuration
        """
        self.settings = settings or GEOSettings()
        self._cache = GEOCache(ttl=self.settings.cache_ttl)
        self._session = requests.Session()

    def get_series(self, accession: str) -> GEOSeries:
        """
        Fetch GEO series metadata.

        Args:
            accession: GEO series accession (e.g., 'GSE123456')

        Returns:
            GEOSeries object with metadata and samples

        Raises:
            GEOError: If fetch fails or accession is invalid
        """
        # Check cache first
        cached = self._cache.get(accession)
        if cached:
            return cached

        # Fetch from GEO (extract clean logic from v1)
        try:
            response = self._fetch_geo_data(accession, "SERIES")
            series = self._parse_series(response)
            self._cache.set(accession, series)
            return series
        except Exception as e:
            raise GEOError(f"Failed to fetch {accession}: {e}") from e

    def get_sample(self, accession: str) -> GEOSample:
        """Fetch GEO sample metadata."""
        # Similar pattern to get_series
        pass

    def get_platform(self, accession: str) -> GEOPlatform:
        """Fetch GEO platform metadata."""
        # Similar pattern to get_series
        pass

    def _fetch_geo_data(self, accession: str, record_type: str) -> str:
        """Fetch raw data from GEO API."""
        # Extract HTTP logic from v1
        pass

    def _parse_series(self, raw_data: str) -> GEOSeries:
        """Parse SOFT format to GEOSeries."""
        # Extract parser logic from v1
        pass
```

**Step 3: Implement Caching**
```python
# omics_oracle_v2/lib/geo/cache.py
from typing import Optional, Any
from datetime import datetime, timedelta
import pickle
from pathlib import Path

class GEOCache:
    """Simple file-based cache for GEO responses."""

    def __init__(self, cache_dir: Path = Path(".cache/geo"), ttl: int = 3600):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files
            ttl: Time-to-live in seconds
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(seconds=ttl)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        cache_file = self.cache_dir / f"{key}.pkl"

        if not cache_file.exists():
            return None

        # Check expiration
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            cache_file.unlink()
            return None

        with cache_file.open("rb") as f:
            return pickle.load(f)

    def set(self, key: str, value: Any) -> None:
        """Cache value to disk."""
        cache_file = self.cache_dir / f"{key}.pkl"
        with cache_file.open("wb") as f:
            pickle.dump(value, f)
```

**Testing**:
```python
# tests/unit/test_geo.py
import pytest
from omics_oracle_v2.lib.geo import UnifiedGEOClient

class TestUnifiedGEOClient:
    """Test GEO client functionality."""

    @pytest.fixture
    def client(self):
        """Create GEO client."""
        return UnifiedGEOClient()

    def test_get_series(self, client):
        """Test series retrieval."""
        # Use a known stable GEO accession
        series = client.get_series("GSE10000")
        assert series.accession == "GSE10000"
        assert len(series.title) > 0
        assert series.sample_count > 0

    def test_caching(self, client):
        """Test response caching."""
        # First call - should fetch
        series1 = client.get_series("GSE10000")

        # Second call - should use cache
        import time
        start = time.time()
        series2 = client.get_series("GSE10000")
        elapsed = time.time() - start

        assert elapsed < 0.1  # Cache should be instant
        assert series1.accession == series2.accession

    def test_invalid_accession(self, client):
        """Test error handling for invalid accession."""
        with pytest.raises(GEOError):
            client.get_series("INVALID123")
```

**Success Criteria**:
- [ ] GEO client works independently
- [ ] Caching reduces API calls
- [ ] Handles network errors gracefully
- [ ] Parses SOFT format correctly
- [ ] 80%+ test coverage
- [ ] Integration tests with real GEO data pass

---

### Task 5: SummarizationService Extraction (12 hours)

**Objective**: Extract AI summarization as standalone service

**Source Files** (from v1):
- `src/omics_oracle/ai/summarization.py`
- `src/omics_oracle/ai/prompts.py`
- OpenAI integration code

**Target Files** (in v2):
```
omics_oracle_v2/lib/ai/
├── __init__.py
├── summarizer.py              # Main summarization service
├── models.py                  # Data models
├── prompts.py                 # Prompt templates
└── utils.py                   # Utility functions
```

**Extraction Strategy**:

**Step 1: Create Data Models**
```python
# omics_oracle_v2/lib/ai/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class SummaryType(str, Enum):
    """Types of summaries to generate."""
    CONCISE = "concise"          # 1-2 sentences
    DETAILED = "detailed"        # 1 paragraph
    COMPREHENSIVE = "comprehensive"  # Multi-paragraph

class SummaryRequest(BaseModel):
    """Request for text summarization."""
    text: str = Field(..., min_length=1)
    summary_type: SummaryType = SummaryType.CONCISE
    max_tokens: Optional[int] = None
    focus_areas: List[str] = Field(default_factory=list)
    context: Optional[str] = None

class SummaryResponse(BaseModel):
    """Response from summarization."""
    summary: str
    summary_type: SummaryType
    token_usage: Dict[str, int]
    model: str
    processing_time_ms: float
```

**Step 2: Extract Summarizer**
```python
# omics_oracle_v2/lib/ai/summarizer.py
from typing import Optional
import openai
from .models import SummaryRequest, SummaryResponse, SummaryType
from .prompts import PromptManager
from ..core.config import AISettings
from ..core.exceptions import AIError

class SummarizationService:
    """
    AI-powered text summarization service.

    Provides intelligent summarization of biomedical text using
    large language models (OpenAI GPT).

    Example:
        >>> summarizer = SummarizationService()
        >>> request = SummaryRequest(
        ...     text="Long biomedical text...",
        ...     summary_type=SummaryType.CONCISE
        ... )
        >>> response = summarizer.summarize(request)
        >>> print(response.summary)
    """

    def __init__(self, settings: Optional[AISettings] = None):
        """
        Initialize summarization service.

        Args:
            settings: Optional AI configuration
        """
        self.settings = settings or AISettings()
        self.prompts = PromptManager()

        if self.settings.openai_api_key:
            openai.api_key = self.settings.openai_api_key

    def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """
        Generate summary from text.

        Args:
            request: Summarization request with text and parameters

        Returns:
            SummaryResponse with generated summary

        Raises:
            AIError: If summarization fails
        """
        import time
        start_time = time.time()

        # Build prompt
        prompt = self.prompts.build_summary_prompt(
            text=request.text,
            summary_type=request.summary_type,
            focus_areas=request.focus_areas,
            context=request.context
        )

        # Call OpenAI API (extract clean logic from v1)
        try:
            response = openai.ChatCompletion.create(
                model=self.settings.model,
                messages=[
                    {"role": "system", "content": "You are a biomedical research assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens or self.settings.max_tokens,
                temperature=self.settings.temperature
            )

            summary = response.choices[0].message.content
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            processing_time = (time.time() - start_time) * 1000

            return SummaryResponse(
                summary=summary,
                summary_type=request.summary_type,
                token_usage=token_usage,
                model=response.model,
                processing_time_ms=processing_time
            )

        except Exception as e:
            raise AIError(f"Summarization failed: {e}") from e
```

**Step 3: Prompt Management**
```python
# omics_oracle_v2/lib/ai/prompts.py
from typing import List, Optional
from .models import SummaryType

class PromptManager:
    """Manages AI prompt templates."""

    SUMMARY_TEMPLATES = {
        SummaryType.CONCISE: """
Summarize the following biomedical text in 1-2 clear sentences:

{text}

Focus on: {focus_areas}
Context: {context}
""",
        SummaryType.DETAILED: """
Provide a detailed paragraph summary of the following biomedical text:

{text}

Key points to emphasize: {focus_areas}
Additional context: {context}
""",
        SummaryType.COMPREHENSIVE: """
Generate a comprehensive multi-paragraph summary of the following biomedical text:

{text}

Areas of focus: {focus_areas}
Background context: {context}

Include:
1. Main findings
2. Methodology highlights
3. Clinical implications
4. Future directions
"""
    }

    def build_summary_prompt(
        self,
        text: str,
        summary_type: SummaryType,
        focus_areas: List[str],
        context: Optional[str]
    ) -> str:
        """Build prompt from template."""
        template = self.SUMMARY_TEMPLATES[summary_type]

        return template.format(
            text=text,
            focus_areas=", ".join(focus_areas) if focus_areas else "general overview",
            context=context or "N/A"
        )
```

**Testing**:
```python
# tests/unit/test_ai.py
import pytest
from omics_oracle_v2.lib.ai import SummarizationService
from omics_oracle_v2.lib.ai.models import SummaryRequest, SummaryType

class TestSummarizationService:
    """Test AI summarization."""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer (with mock API for tests)."""
        # Use mock OpenAI for unit tests
        return SummarizationService()

    def test_concise_summary(self, summarizer, monkeypatch):
        """Test concise summary generation."""
        # Mock OpenAI response
        # ... (add proper mocking)

        request = SummaryRequest(
            text="Long biomedical text about TP53 mutations...",
            summary_type=SummaryType.CONCISE
        )

        response = summarizer.summarize(request)
        assert len(response.summary) > 0
        assert response.summary_type == SummaryType.CONCISE

    def test_prompt_building(self):
        """Test prompt template generation."""
        from omics_oracle_v2.lib.ai.prompts import PromptManager

        pm = PromptManager()
        prompt = pm.build_summary_prompt(
            text="Test text",
            summary_type=SummaryType.CONCISE,
            focus_areas=["genes", "diseases"],
            context="Cancer research"
        )

        assert "Test text" in prompt
        assert "genes" in prompt or "diseases" in prompt
```

**Success Criteria**:
- [ ] Summarizer works independently
- [ ] Supports multiple summary types
- [ ] Proper prompt engineering
- [ ] Error handling for API failures
- [ ] Mock testing works (no API calls in unit tests)
- [ ] 80%+ test coverage

---

### Task 6: Integration Testing (4 hours)

**Objective**: Ensure all extracted libraries work together

**Test Scenarios**:

1. **End-to-End NER → GEO → Summary Pipeline**
```python
# tests/integration/test_pipeline.py
def test_full_pipeline():
    """Test complete analysis pipeline."""
    from omics_oracle_v2.lib.nlp import BiomedicalNER
    from omics_oracle_v2.lib.geo import UnifiedGEOClient
    from omics_oracle_v2.lib.ai import SummarizationService

    # 1. Extract entities from query
    ner = BiomedicalNER()
    query = "Find datasets about TP53 mutations in lung cancer"
    ner_result = ner.extract_entities(query)

    genes = [e for e in ner_result.entities if e.entity_type == "gene"]
    assert len(genes) > 0

    # 2. Search GEO for relevant datasets
    geo = UnifiedGEOClient()
    # (This would require GEO search API, not just get_series)

    # 3. Summarize findings
    summarizer = SummarizationService()
    # ... generate summary
```

2. **Configuration Integration**
```python
def test_config_propagation():
    """Test config works across all libraries."""
    from omics_oracle_v2.core.config import Settings

    settings = Settings(debug=True)

    # All services should respect config
    # ...
```

3. **Error Handling Integration**
```python
def test_error_propagation():
    """Test errors propagate correctly."""
    from omics_oracle_v2.core.exceptions import GEOError
    from omics_oracle_v2.lib.geo import UnifiedGEOClient

    client = UnifiedGEOClient()

    with pytest.raises(GEOError):
        client.get_series("INVALID")
```

**Success Criteria**:
- [ ] All libraries integrate smoothly
- [ ] Configuration works end-to-end
- [ ] Error handling is consistent
- [ ] Performance is acceptable
- [ ] No v1 dependencies leak through

---

### Task 7: Documentation & Performance (6 hours)

**Objective**: Complete API documentation and performance validation

**Documentation Tasks**:

1. **API Reference Documentation**
```bash
# Generate API docs with Sphinx
cd omics_oracle_v2
sphinx-quickstart docs
# Configure autodoc
sphinx-apidoc -o docs/api .
sphinx-build docs docs/_build
```

2. **Usage Examples**
```python
# Create examples/ directory
omics_oracle_v2/examples/
├── 01_basic_ner.py
├── 02_geo_access.py
├── 03_summarization.py
└── 04_full_pipeline.py
```

3. **Migration Guide**
```markdown
# docs/MIGRATION_V1_TO_V2.md

## Migrating from v1 to v2

### NER Migration
**v1:**
```python
from src.omics_oracle.nlp.biomedical_ner import BiomedicalNER
ner = BiomedicalNER()
entities = ner.extract(text)
```

**v2:**
```python
from omics_oracle_v2.lib.nlp import BiomedicalNER
ner = BiomedicalNER()
result = ner.extract_entities(text)
entities = result.entities  # Typed Pydantic models
```
```

**Performance Validation**:

1. **Benchmark Suite**
```python
# tests/benchmarks/test_performance.py
import pytest
from omics_oracle_v2.lib.nlp import BiomedicalNER

def test_ner_performance():
    """NER should process documents in < 100ms."""
    ner = BiomedicalNER()

    import time
    text = "TP53 gene mutations in lung cancer" * 10

    start = time.time()
    result = ner.extract_entities(text)
    elapsed = time.time() - start

    assert elapsed < 0.1  # 100ms threshold
    assert result.processing_time_ms < 100
```

2. **Memory Profiling**
```bash
# Run memory profiler
python -m memory_profiler tests/benchmarks/test_memory.py
```

**Success Criteria**:
- [ ] API documentation complete (Sphinx)
- [ ] Usage examples for all libraries
- [ ] Migration guide written
- [ ] Performance benchmarks pass
- [ ] Memory usage acceptable

---

## 📈 Progress Tracking

### Daily Checklist Template

**Day 1-2: Setup (Task 1 + Task 2)**
- [ ] Create directory structure
- [ ] Create all __init__.py files
- [ ] Extract core config system
- [ ] Create exception hierarchy
- [ ] Test: `import omics_oracle_v2` works

**Day 3-5: NER Extraction (Task 3)**
- [ ] Create NER data models
- [ ] Extract BiomedicalNER class
- [ ] Extract SynonymManager
- [ ] Add comprehensive tests
- [ ] Test: 80%+ coverage on NLP module

**Day 6-8: GEO Extraction (Task 4)**
- [ ] Create GEO data models
- [ ] Extract UnifiedGEOClient
- [ ] Implement caching layer
- [ ] Add integration tests (real API)
- [ ] Test: Caching reduces API calls

**Day 9-10: AI Extraction (Task 5)**
- [ ] Create AI data models
- [ ] Extract SummarizationService
- [ ] Create prompt templates
- [ ] Add mocked unit tests
- [ ] Test: No real API calls in unit tests

**Day 11: Integration (Task 6)**
- [ ] Create integration test suite
- [ ] Test end-to-end pipeline
- [ ] Validate configuration propagation
- [ ] Test error handling

**Day 12-14: Documentation (Task 7)**
- [ ] Generate API documentation
- [ ] Write usage examples
- [ ] Create migration guide
- [ ] Run performance benchmarks
- [ ] Final review and cleanup

---

## 🎯 Success Criteria Summary

### Code Quality
- ✅ Zero imports from `src/omics_oracle/` (v1)
- ✅ All type hints present (passes mypy strict)
- ✅ Follows PEP 8 (passes flake8)
- ✅ Docstrings on all public APIs
- ✅ 80%+ test coverage

### Functionality
- ✅ BiomedicalNER extracts entities correctly
- ✅ UnifiedGEOClient fetches GEO data
- ✅ SummarizationService generates summaries
- ✅ All services configurable via Settings
- ✅ Error handling is robust

### Testing
- ✅ 80%+ unit test coverage
- ✅ Integration tests pass
- ✅ Performance benchmarks pass
- ✅ No flaky tests
- ✅ Tests run in < 30 seconds

### Documentation
- ✅ API documentation complete
- ✅ Usage examples provided
- ✅ Migration guide written
- ✅ README updated

---

## 🚀 Getting Started

### Prerequisites
```bash
# Ensure Phase 0 is complete and merged
git checkout main
git pull
git log --oneline -5  # Should show Phase 0 merge

# Create Phase 1 branch
git checkout -b phase-1-extraction
```

### Initial Setup
```bash
# Create v2 structure
mkdir -p omics_oracle_v2/{lib/{nlp,geo,ai},core,tests/{unit,integration}}

# Create __init__.py files
touch omics_oracle_v2/__init__.py
touch omics_oracle_v2/lib/__init__.py
touch omics_oracle_v2/lib/nlp/__init__.py
touch omics_oracle_v2/lib/geo/__init__.py
touch omics_oracle_v2/lib/ai/__init__.py
touch omics_oracle_v2/core/__init__.py
touch omics_oracle_v2/tests/__init__.py
touch omics_oracle_v2/tests/unit/__init__.py
touch omics_oracle_v2/tests/integration/__init__.py

# Create type marker
touch omics_oracle_v2/py.typed

# Verify structure
tree omics_oracle_v2
```

---

## 📝 Notes & Reminders

### Critical Principles
1. **Independence First**: Each extracted library must work standalone
2. **Test Before Extract**: Write failing tests, then extract code to make them pass
3. **Document As You Go**: Don't leave documentation for the end
4. **Preserve Behavior**: Extracted code should match v1 behavior exactly
5. **No Shortcuts**: Don't skip tests "to save time"

### Common Pitfalls to Avoid
- ❌ Importing from v1 (`src/omics_oracle/`)
- ❌ Skipping type hints
- ❌ Copying code without understanding it
- ❌ Leaving TODOs without tracking them
- ❌ Breaking v1 while extracting

### Review Checkpoints
- **After Task 1**: Structure should be complete and importable
- **After Task 3**: NER should work independently with tests
- **After Task 4**: GEO should work independently with tests
- **After Task 5**: AI should work independently with tests
- **Before Task 7**: All integration tests should pass

---

## 📞 Support & Resources

### Key Documents
- Master Plan: `docs/planning/MASTER_PLAN.md`
- Phase 0 Summary: `docs/PHASE_0_CLEANUP_SUMMARY.md`
- Code Quality Guide: `docs/CODE_QUALITY_GUIDE.md`

### Testing Resources
- Test templates: `docs/TEST_TEMPLATES.md`
- Testing hierarchy: `docs/TESTING_HIERARCHY.md`

---

## ✅ Final Checklist

Before considering Phase 1 complete:

### Code Completion
- [ ] All 7 tasks completed
- [ ] All subtasks verified
- [ ] Zero TODO comments remain
- [ ] All tests passing

### Quality Gates
- [ ] pytest: All tests pass
- [ ] mypy: Zero type errors
- [ ] flake8: Zero style warnings
- [ ] coverage: 80%+ overall

### Documentation
- [ ] API docs generated
- [ ] Examples tested
- [ ] Migration guide reviewed
- [ ] README updated

### Git Hygiene
- [ ] All changes committed
- [ ] Meaningful commit messages
- [ ] Branch ready for review
- [ ] No merge conflicts with main

### Handoff Preparation
- [ ] Phase 1 summary document created
- [ ] Lessons learned documented
- [ ] Known issues listed
- [ ] Phase 2 dependencies identified

---

**Last Updated**: October 2, 2025
**Status**: Ready to start
**Next Action**: Begin Task 1 (Project Structure Setup)
