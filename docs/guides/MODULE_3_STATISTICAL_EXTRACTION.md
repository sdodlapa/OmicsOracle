# 📊 Module 3: Statistical Information Extraction System

**Date**: December 28, 2024
**Module**: Statistical Data Extraction & Analysis
**Priority**: High - Data Quality Assessment
**Estimated Timeline**: 6-8 weeks

---

## 🎯 **Module Overview**

The Statistical Information Extraction System automatically extracts, validates, and computes comprehensive statistical information from multiple sources: publication text, tables, figures, and direct dataset analysis. This module provides quantitative insights essential for dataset quality assessment and research reproducibility.

### **Core Objectives**

1. **Multi-Source Statistics**: Extract from text, tables, figures, and raw data
2. **Quality Assessment**: Validate and score statistical reliability
3. **Metadata Enrichment**: Enhance dataset descriptions with computed statistics
4. **Trend Analysis**: Identify patterns across datasets and time
5. **Reproducibility Support**: Provide statistics for research validation

---

## 🏗️ **System Architecture**

### **Component Structure**

```
src/omics_oracle/stats_extraction/
├── __init__.py
├── orchestrator.py              # Main extraction orchestrator
├── text_extraction/             # Text-based statistics
│   ├── __init__.py
│   ├── pattern_matcher.py       # Statistical pattern recognition
│   ├── nlp_extractor.py         # NLP-based extraction
│   ├── context_analyzer.py      # Statistical context analysis
│   └── confidence_scorer.py     # Confidence assessment
├── table_processing/            # Table analysis
│   ├── __init__.py
│   ├── table_detector.py        # Table identification
│   ├── structure_parser.py      # Table structure parsing
│   ├── data_extractor.py        # Numerical data extraction
│   ├── statistical_analyzer.py  # Statistical computation
│   └── relationship_finder.py   # Inter-column relationships
├── figure_analysis/             # Figure processing
│   ├── __init__.py
│   ├── ocr_processor.py         # OCR for figure text
│   ├── chart_analyzer.py        # Chart data extraction
│   ├── image_classifier.py      # Figure type classification
│   └── data_digitizer.py        # Plot data digitization
├── direct_analysis/             # Raw dataset analysis
│   ├── __init__.py
│   ├── geo_downloader.py        # GEO data retrieval
│   ├── quality_metrics.py       # Data quality assessment
│   ├── summary_statistics.py    # Descriptive statistics
│   ├── distribution_analyzer.py # Statistical distributions
│   └── experimental_design.py   # Design analysis
├── validation/                  # Validation and scoring
│   ├── __init__.py
│   ├── cross_validator.py       # Cross-source validation
│   ├── outlier_detector.py      # Outlier identification
│   ├── consistency_checker.py   # Consistency validation
│   └── reliability_scorer.py    # Reliability assessment
└── models/                      # Data models
    ├── __init__.py
    ├── statistics.py            # Statistical data models
    ├── extraction.py            # Extraction result models
    └── validation.py            # Validation models
```

---

## 🔧 **Core Components Implementation**

### **1. Text-Based Statistics Extraction**

**Statistical Pattern Matcher**:
```python
# src/omics_oracle/stats_extraction/text_extraction/pattern_matcher.py

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class StatisticType(Enum):
    SAMPLE_SIZE = "sample_size"
    P_VALUE = "p_value"
    EFFECT_SIZE = "effect_size"
    CORRELATION = "correlation"
    CONFIDENCE_INTERVAL = "confidence_interval"
    MEAN = "mean"
    MEDIAN = "median"
    STANDARD_DEVIATION = "std_dev"
    FOLD_CHANGE = "fold_change"
    PERCENTAGE = "percentage"

@dataclass
class ExtractedStatistic:
    """Represents an extracted statistical value"""
    type: StatisticType
    value: float
    context: str
    confidence: float
    source_location: str
    unit: Optional[str] = None
    associated_variable: Optional[str] = None
    comparison_group: Optional[str] = None

class StatisticalPatternMatcher:
    """Extract statistical values using regex patterns"""

    def __init__(self):
        self.patterns = {
            StatisticType.SAMPLE_SIZE: [
                r'n\s*=\s*(\d+)',
                r'N\s*=\s*(\d+)',
                r'(\d+)\s+patients?',
                r'(\d+)\s+subjects?',
                r'(\d+)\s+samples?',
                r'(\d+)\s+participants?',
                r'(\d+)\s+individuals?',
                r'total\s+of\s+(\d+)',
                r'cohort\s+of\s+(\d+)',
                r'dataset\s+with\s+(\d+)\s+samples?'
            ],

            StatisticType.P_VALUE: [
                r'p\s*[<>=]\s*(0?\.\d+)',
                r'P\s*[<>=]\s*(0?\.\d+)',
                r'p-value\s*[<>=]\s*(0?\.\d+)',
                r'P-value\s*[<>=]\s*(0?\.\d+)',
                r'significance\s*[<>=]\s*(0?\.\d+)',
                r'p\s*=\s*(0?\.\d+)',
                r'P\s*=\s*(0?\.\d+)',
                r'p\s*<\s*(0?\.0+1)',  # For very small p-values
                r'statistically\s+significant.*?p\s*[<>=]\s*(0?\.\d+)'
            ],

            StatisticType.FOLD_CHANGE: [
                r'fold[- ]?change\s*[<>=]?\s*([\d.]+)',
                r'FC\s*[<>=]?\s*([\d.]+)',
                r'log2\s*FC\s*[<>=]?\s*([\d.-]+)',
                r'log2\s*fold[- ]?change\s*[<>=]?\s*([\d.-]+)',
                r'(\d+\.?\d*)[- ]?fold\s+(?:increase|decrease|change)',
                r'up[- ]?regulated\s+by\s+([\d.]+)[- ]?fold',
                r'down[- ]?regulated\s+by\s+([\d.]+)[- ]?fold'
            ],

            StatisticType.CORRELATION: [
                r'correlation\s*[<>=]?\s*(0?\.\d+)',
                r'r\s*=\s*(0?\.\d+)',
                r'R\s*=\s*(0?\.\d+)',
                r'pearson.*?r\s*=\s*(0?\.\d+)',
                r'spearman.*?r\s*=\s*(0?\.\d+)',
                r'correlation\s+coefficient\s*[<>=]?\s*(0?\.\d+)'
            ],

            StatisticType.CONFIDENCE_INTERVAL: [
                r'95%\s*CI[:\s]*([\d.-]+)\s*[-–]\s*([\d.-]+)',
                r'confidence\s+interval[:\s]*([\d.-]+)\s*[-–]\s*([\d.-]+)',
                r'CI\s*=\s*([\d.-]+)\s*[-–]\s*([\d.-]+)',
                r'\[([\d.-]+),\s*([\d.-]+)\]'
            ],

            StatisticType.MEAN: [
                r'mean\s*[<>=]?\s*([\d.]+)',
                r'average\s*[<>=]?\s*([\d.]+)',
                r'μ\s*=\s*([\d.]+)',
                r'mean\s*±\s*[\d.]+\s*=\s*([\d.]+)'
            ],

            StatisticType.STANDARD_DEVIATION: [
                r'standard\s+deviation\s*[<>=]?\s*([\d.]+)',
                r'std\s*[<>=]?\s*([\d.]+)',
                r'SD\s*[<>=]?\s*([\d.]+)',
                r'σ\s*=\s*([\d.]+)',
                r'±\s*([\d.]+)'
            ]
        }

        # Context keywords to improve extraction accuracy
        self.context_keywords = {
            'experimental': ['treatment', 'control', 'experiment', 'trial'],
            'statistical': ['significant', 'analysis', 'test', 'hypothesis'],
            'biological': ['gene', 'protein', 'expression', 'pathway'],
            'clinical': ['patient', 'disease', 'diagnosis', 'therapy']
        }

    async def extract_statistics_from_text(self, text: str) -> List[ExtractedStatistic]:
        """Extract statistical values from text"""
        extracted_statistics = []

        # Process text in chunks to maintain context
        chunks = self._split_into_chunks(text, chunk_size=500, overlap=50)

        for chunk_idx, chunk in enumerate(chunks):
            chunk_statistics = await self._extract_from_chunk(chunk, chunk_idx)
            extracted_statistics.extend(chunk_statistics)

        # Post-process and deduplicate
        return self._post_process_statistics(extracted_statistics)

    async def _extract_from_chunk(self, chunk: str, chunk_idx: int) -> List[ExtractedStatistic]:
        """Extract statistics from a text chunk"""
        chunk_statistics = []

        for stat_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, chunk, re.IGNORECASE))

                for match in matches:
                    try:
                        # Extract value(s)
                        if stat_type == StatisticType.CONFIDENCE_INTERVAL:
                            # Special handling for confidence intervals (two values)
                            values = [float(match.group(1)), float(match.group(2))]
                            value = (values[0] + values[1]) / 2  # Use midpoint
                        else:
                            value = float(match.group(1))

                        # Extract context around match
                        context = self._extract_context(chunk, match.start(), match.end())

                        # Calculate confidence score
                        confidence = self._calculate_confidence(
                            stat_type, value, context, pattern
                        )

                        # Create extracted statistic
                        statistic = ExtractedStatistic(
                            type=stat_type,
                            value=value,
                            context=context,
                            confidence=confidence,
                            source_location=f"chunk_{chunk_idx}_{match.start()}",
                            associated_variable=self._extract_variable_name(context),
                            unit=self._extract_unit(context)
                        )

                        chunk_statistics.append(statistic)

                    except (ValueError, IndexError):
                        continue

        return chunk_statistics

    def _calculate_confidence(self,
                            stat_type: StatisticType,
                            value: float,
                            context: str,
                            pattern: str) -> float:
        """Calculate confidence score for extracted statistic"""
        confidence = 0.5  # Base confidence

        # Pattern-specific confidence boosts
        pattern_confidence = {
            r'n\s*=\s*(\d+)': 0.9,
            r'p\s*=\s*(0?\.\d+)': 0.9,
            r'fold[- ]?change\s*=\s*([\d.]+)': 0.8
        }

        for high_conf_pattern, boost in pattern_confidence.items():
            if re.search(high_conf_pattern, pattern):
                confidence = max(confidence, boost)
                break

        # Context-based confidence adjustments
        context_lower = context.lower()

        # Boost for statistical context
        if any(keyword in context_lower for keyword in ['significant', 'analysis', 'test']):
            confidence += 0.1

        # Boost for specific domains
        if any(keyword in context_lower for keyword in ['gene', 'expression', 'protein']):
            confidence += 0.05

        # Penalize if value seems unrealistic
        if stat_type == StatisticType.P_VALUE and (value < 0 or value > 1):
            confidence *= 0.3
        elif stat_type == StatisticType.CORRELATION and (value < -1 or value > 1):
            confidence *= 0.3
        elif stat_type == StatisticType.SAMPLE_SIZE and value < 1:
            confidence *= 0.1

        return min(1.0, confidence)

    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _extract_variable_name(self, context: str) -> Optional[str]:
        """Extract the variable name associated with a statistic"""
        # Look for common variable patterns
        variable_patterns = [
            r'(\w+)\s+(?:gene|protein|marker)',
            r'(\w+)\s+expression',
            r'(?:for|of)\s+(\w+)',
            r'(\w+)\s+levels?'
        ]

        for pattern in variable_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_unit(self, context: str) -> Optional[str]:
        """Extract unit from context"""
        unit_patterns = [
            r'(\w+/\w+)',  # units like mg/ml
            r'(mg|kg|ml|μg|ng|%)',
            r'(fold|log2|log10)'
        ]

        for pattern in unit_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
```

### **2. Table Processing System**

**Table Structure Parser**:
```python
# src/omics_oracle/stats_extraction/table_processing/structure_parser.py

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ColumnType(Enum):
    IDENTIFIER = "identifier"
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    STATISTICAL = "statistical"
    P_VALUE = "p_value"
    FOLD_CHANGE = "fold_change"
    PERCENTAGE = "percentage"

@dataclass
class TableColumn:
    """Represents a table column with metadata"""
    name: str
    type: ColumnType
    data: List[Any]
    statistics: Dict[str, float]
    missing_count: int
    unique_count: int
    sample_values: List[Any]

@dataclass
class ProcessedTable:
    """Represents a processed table with analysis"""
    title: str
    caption: str
    columns: List[TableColumn]
    row_count: int
    statistical_content_score: float
    relationships: List[Dict[str, Any]]
    summary_statistics: Dict[str, Any]

class TableStructureParser:
    """Parse and analyze table structure and content"""

    def __init__(self):
        self.statistical_keywords = {
            'p_value': ['p-value', 'p value', 'significance', 'p', 'pval'],
            'fold_change': ['fold change', 'fc', 'log2fc', 'fold-change'],
            'correlation': ['correlation', 'r', 'pearson', 'spearman'],
            'confidence': ['ci', 'confidence interval', '95% ci'],
            'effect_size': ['effect size', 'cohen', 'eta squared']
        }

        self.numerical_indicators = [
            'mean', 'median', 'average', 'std', 'deviation',
            'min', 'max', 'range', 'count', 'total', 'sum'
        ]

    async def parse_table(self,
                        table_data: List[List[str]],
                        title: str = "",
                        caption: str = "") -> ProcessedTable:
        """Parse table structure and analyze content"""

        if not table_data or len(table_data) < 2:
            return self._create_empty_table(title, caption)

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(table_data[1:], columns=table_data[0])

        # Clean and standardize data
        df = self._clean_table_data(df)

        # Analyze columns
        columns = []
        for col_name in df.columns:
            column_analysis = await self._analyze_column(df[col_name], col_name)
            columns.append(column_analysis)

        # Find statistical relationships
        relationships = self._find_statistical_relationships(df, columns)

        # Calculate summary statistics
        summary_stats = self._calculate_table_summary_statistics(df, columns)

        # Score statistical content
        statistical_score = self._calculate_statistical_content_score(columns, relationships)

        return ProcessedTable(
            title=title,
            caption=caption,
            columns=columns,
            row_count=len(df),
            statistical_content_score=statistical_score,
            relationships=relationships,
            summary_statistics=summary_stats
        )

    async def _analyze_column(self, series: pd.Series, column_name: str) -> TableColumn:
        """Analyze individual column"""

        # Detect column type
        column_type = self._detect_column_type(series, column_name)

        # Calculate basic statistics
        statistics = {}
        if column_type in [ColumnType.NUMERICAL, ColumnType.STATISTICAL,
                          ColumnType.P_VALUE, ColumnType.FOLD_CHANGE]:
            numeric_data = pd.to_numeric(series, errors='coerce')
            if not numeric_data.isna().all():
                statistics = {
                    'mean': float(numeric_data.mean()),
                    'median': float(numeric_data.median()),
                    'std': float(numeric_data.std()),
                    'min': float(numeric_data.min()),
                    'max': float(numeric_data.max()),
                    'q25': float(numeric_data.quantile(0.25)),
                    'q75': float(numeric_data.quantile(0.75))
                }

        # Get sample values
        sample_values = series.dropna().head(5).tolist()

        return TableColumn(
            name=column_name,
            type=column_type,
            data=series.tolist(),
            statistics=statistics,
            missing_count=int(series.isna().sum()),
            unique_count=int(series.nunique()),
            sample_values=sample_values
        )

    def _detect_column_type(self, series: pd.Series, column_name: str) -> ColumnType:
        """Detect the type of data in a column"""

        column_name_lower = column_name.lower()

        # Check for specific statistical column types
        for stat_type, keywords in self.statistical_keywords.items():
            if any(keyword in column_name_lower for keyword in keywords):
                if stat_type == 'p_value':
                    return ColumnType.P_VALUE
                elif stat_type == 'fold_change':
                    return ColumnType.FOLD_CHANGE
                else:
                    return ColumnType.STATISTICAL

        # Try to convert to numeric
        numeric_series = pd.to_numeric(series, errors='coerce')
        numeric_ratio = (1 - numeric_series.isna().sum() / len(series))

        if numeric_ratio > 0.8:  # 80% of values are numeric
            # Check if values look like percentages
            if column_name_lower.endswith('%') or 'percent' in column_name_lower:
                return ColumnType.PERCENTAGE

            # Check for statistical indicators in column name
            if any(indicator in column_name_lower for indicator in self.numerical_indicators):
                return ColumnType.STATISTICAL

            return ColumnType.NUMERICAL

        # Check if categorical
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.5:  # Less than 50% unique values
            return ColumnType.CATEGORICAL

        # Default to identifier
        return ColumnType.IDENTIFIER

    def _find_statistical_relationships(self,
                                      df: pd.DataFrame,
                                      columns: List[TableColumn]) -> List[Dict[str, Any]]:
        """Find statistical relationships between columns"""
        relationships = []

        # Look for common statistical table patterns
        p_value_cols = [col for col in columns if col.type == ColumnType.P_VALUE]
        fold_change_cols = [col for col in columns if col.type == ColumnType.FOLD_CHANGE]
        numerical_cols = [col for col in columns if col.type in [ColumnType.NUMERICAL, ColumnType.STATISTICAL]]

        # P-value and fold change relationships
        for p_col in p_value_cols:
            for fc_col in fold_change_cols:
                # Check if they might be related (similar row patterns)
                correlation = self._calculate_column_similarity(
                    df[p_col.name], df[fc_col.name]
                )

                if correlation > 0.3:  # Threshold for relationship
                    relationships.append({
                        'type': 'p_value_fold_change',
                        'columns': [p_col.name, fc_col.name],
                        'strength': correlation,
                        'description': f"P-values and fold changes appear related"
                    })

        # Statistical summaries (mean/std relationships)
        mean_cols = [col for col in numerical_cols if 'mean' in col.name.lower()]
        std_cols = [col for col in numerical_cols if any(keyword in col.name.lower()
                                                        for keyword in ['std', 'deviation', 'error'])]

        for mean_col in mean_cols:
            for std_col in std_cols:
                # Check if they have similar naming patterns
                if self._similar_column_names(mean_col.name, std_col.name):
                    relationships.append({
                        'type': 'mean_std_pair',
                        'columns': [mean_col.name, std_col.name],
                        'strength': 1.0,
                        'description': f"Mean and standard deviation pair"
                    })

        return relationships

    def _calculate_statistical_content_score(self,
                                           columns: List[TableColumn],
                                           relationships: List[Dict[str, Any]]) -> float:
        """Calculate how much statistical content the table contains"""

        score = 0.0

        # Base score from column types
        statistical_cols = sum(1 for col in columns if col.type in [
            ColumnType.STATISTICAL, ColumnType.P_VALUE,
            ColumnType.FOLD_CHANGE, ColumnType.PERCENTAGE
        ])

        if len(columns) > 0:
            score += (statistical_cols / len(columns)) * 0.6

        # Boost from relationships
        score += min(0.3, len(relationships) * 0.1)

        # Boost from specific statistical indicators
        has_p_values = any(col.type == ColumnType.P_VALUE for col in columns)
        has_effect_sizes = any(col.type == ColumnType.FOLD_CHANGE for col in columns)

        if has_p_values:
            score += 0.1
        if has_effect_sizes:
            score += 0.1
        if has_p_values and has_effect_sizes:
            score += 0.1  # Bonus for having both

        return min(1.0, score)
```

### **3. Direct Dataset Analysis**

**GEO Dataset Analyzer**:
```python
# src/omics_oracle/stats_extraction/direct_analysis/summary_statistics.py

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..models.statistics import DatasetStatistics, SampleDistribution

@dataclass
class QualityMetrics:
    """Dataset quality assessment metrics"""
    completeness_score: float
    consistency_score: float
    outlier_percentage: float
    missing_data_percentage: float
    duplicate_percentage: float
    overall_quality_score: float

class DatasetStatisticalAnalyzer:
    """Compute comprehensive statistics from raw GEO datasets"""

    def __init__(self):
        self.quality_thresholds = {
            'high_quality': 0.8,
            'medium_quality': 0.6,
            'low_quality': 0.4
        }

    async def analyze_geo_dataset(self, geo_id: str) -> DatasetStatistics:
        """Perform comprehensive statistical analysis of GEO dataset"""

        # Download dataset metadata and sample information
        dataset_info = await self._download_geo_metadata(geo_id)
        sample_data = await self._download_sample_data(geo_id)

        # Compute basic statistics
        basic_stats = self._compute_basic_statistics(dataset_info, sample_data)

        # Analyze sample distribution
        sample_distribution = self._analyze_sample_distribution(sample_data)

        # Platform analysis
        platform_analysis = self._analyze_platform_characteristics(dataset_info)

        # Experimental design analysis
        experimental_design = self._analyze_experimental_design(sample_data)

        # Quality assessment
        quality_metrics = self._assess_data_quality(sample_data)

        # Statistical summaries
        statistical_summaries = await self._compute_statistical_summaries(sample_data)

        return DatasetStatistics(
            geo_id=geo_id,
            basic_statistics=basic_stats,
            sample_distribution=sample_distribution,
            platform_analysis=platform_analysis,
            experimental_design=experimental_design,
            quality_metrics=quality_metrics,
            statistical_summaries=statistical_summaries,
            analysis_timestamp=datetime.utcnow()
        )

    def _compute_basic_statistics(self,
                                dataset_info: Dict[str, Any],
                                sample_data: pd.DataFrame) -> Dict[str, Any]:
        """Compute basic dataset statistics"""

        return {
            'total_samples': len(sample_data),
            'total_features': dataset_info.get('feature_count', 0),
            'organism': dataset_info.get('organism', 'Unknown'),
            'platform': dataset_info.get('platform', 'Unknown'),
            'submission_date': dataset_info.get('submission_date'),
            'last_update_date': dataset_info.get('last_update_date'),
            'data_processing': dataset_info.get('data_processing', 'Unknown'),
            'normalization_method': dataset_info.get('normalization', 'Unknown')
        }

    def _analyze_sample_distribution(self, sample_data: pd.DataFrame) -> SampleDistribution:
        """Analyze distribution of samples across different characteristics"""

        # Extract sample characteristics
        characteristics = {}

        # Tissue types
        if 'tissue' in sample_data.columns:
            tissue_dist = sample_data['tissue'].value_counts().to_dict()
            characteristics['tissue_types'] = tissue_dist

        # Cell types
        if 'cell_type' in sample_data.columns:
            cell_dist = sample_data['cell_type'].value_counts().to_dict()
            characteristics['cell_types'] = cell_dist

        # Treatment conditions
        treatment_cols = [col for col in sample_data.columns
                         if any(keyword in col.lower()
                               for keyword in ['treatment', 'condition', 'drug'])]

        if treatment_cols:
            treatment_dist = {}
            for col in treatment_cols:
                treatment_dist[col] = sample_data[col].value_counts().to_dict()
            characteristics['treatment_conditions'] = treatment_dist

        # Time points
        time_cols = [col for col in sample_data.columns
                    if any(keyword in col.lower()
                          for keyword in ['time', 'day', 'hour', 'week'])]

        if time_cols:
            time_dist = {}
            for col in time_cols:
                time_dist[col] = sample_data[col].value_counts().to_dict()
            characteristics['time_points'] = time_dist

        # Calculate distribution balance
        balance_score = self._calculate_distribution_balance(characteristics)

        return SampleDistribution(
            characteristics=characteristics,
            balance_score=balance_score,
            sample_size_adequacy=self._assess_sample_size_adequacy(len(sample_data)),
            power_analysis=self._estimate_statistical_power(sample_data)
        )

    def _assess_data_quality(self, sample_data: pd.DataFrame) -> QualityMetrics:
        """Assess overall data quality"""

        # Completeness: proportion of non-missing data
        total_cells = sample_data.size
        missing_cells = sample_data.isna().sum().sum()
        completeness_score = 1 - (missing_cells / total_cells)

        # Consistency: check for consistent data types and formats
        consistency_score = self._assess_data_consistency(sample_data)

        # Outlier detection
        outlier_percentage = self._detect_outliers(sample_data)

        # Missing data percentage
        missing_data_percentage = missing_cells / total_cells

        # Duplicate detection
        duplicate_percentage = (len(sample_data) - len(sample_data.drop_duplicates())) / len(sample_data)

        # Overall quality score
        overall_quality_score = (
            completeness_score * 0.4 +
            consistency_score * 0.3 +
            (1 - outlier_percentage) * 0.2 +
            (1 - duplicate_percentage) * 0.1
        )

        return QualityMetrics(
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            outlier_percentage=outlier_percentage,
            missing_data_percentage=missing_data_percentage,
            duplicate_percentage=duplicate_percentage,
            overall_quality_score=overall_quality_score
        )

    async def _compute_statistical_summaries(self, sample_data: pd.DataFrame) -> Dict[str, Any]:
        """Compute comprehensive statistical summaries"""

        summaries = {}

        # Numerical columns analysis
        numerical_cols = sample_data.select_dtypes(include=[np.number]).columns

        if len(numerical_cols) > 0:
            numerical_summary = {}
            for col in numerical_cols:
                col_data = sample_data[col].dropna()
                if len(col_data) > 0:
                    numerical_summary[col] = {
                        'count': len(col_data),
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'q25': float(col_data.quantile(0.25)),
                        'q75': float(col_data.quantile(0.75)),
                        'skewness': float(col_data.skew()),
                        'kurtosis': float(col_data.kurtosis())
                    }

            summaries['numerical_summary'] = numerical_summary

        # Categorical columns analysis
        categorical_cols = sample_data.select_dtypes(include=['object']).columns

        if len(categorical_cols) > 0:
            categorical_summary = {}
            for col in categorical_cols:
                col_data = sample_data[col].dropna()
                if len(col_data) > 0:
                    value_counts = col_data.value_counts()
                    categorical_summary[col] = {
                        'unique_count': len(value_counts),
                        'most_frequent': value_counts.index[0] if len(value_counts) > 0 else None,
                        'most_frequent_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                        'distribution': value_counts.head(10).to_dict()  # Top 10 values
                    }

            summaries['categorical_summary'] = categorical_summary

        # Correlation analysis for numerical variables
        if len(numerical_cols) > 1:
            correlation_matrix = sample_data[numerical_cols].corr()
            summaries['correlation_analysis'] = {
                'correlation_matrix': correlation_matrix.to_dict(),
                'high_correlations': self._find_high_correlations(correlation_matrix)
            }

        return summaries

    def _find_high_correlations(self, corr_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find pairs of variables with high correlation"""

        high_correlations = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                correlation = corr_matrix.iloc[i, j]
                if abs(correlation) > threshold:
                    high_correlations.append({
                        'variable1': corr_matrix.columns[i],
                        'variable2': corr_matrix.columns[j],
                        'correlation': float(correlation),
                        'strength': 'strong' if abs(correlation) > 0.9 else 'moderate'
                    })

        return sorted(high_correlations, key=lambda x: abs(x['correlation']), reverse=True)
```

---

## 📊 **Data Models**

### **Statistical Data Models**

```python
# src/omics_oracle/stats_extraction/models/statistics.py

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

@dataclass
class DatasetStatistics:
    """Comprehensive dataset statistics"""
    geo_id: str
    basic_statistics: Dict[str, Any]
    sample_distribution: 'SampleDistribution'
    platform_analysis: Dict[str, Any]
    experimental_design: Dict[str, Any]
    quality_metrics: 'QualityMetrics'
    statistical_summaries: Dict[str, Any]
    analysis_timestamp: datetime

    # Computed scores
    overall_quality_score: float = 0.0
    statistical_power: float = 0.0
    reproducibility_score: float = 0.0

@dataclass
class SampleDistribution:
    """Sample distribution analysis"""
    characteristics: Dict[str, Dict[str, int]]
    balance_score: float
    sample_size_adequacy: str  # 'adequate', 'marginal', 'inadequate'
    power_analysis: Dict[str, float]

    # Distribution metrics
    entropy: float = 0.0
    gini_coefficient: float = 0.0
    simpson_diversity: float = 0.0

@dataclass
class ExtractionConfidence:
    """Confidence assessment for extracted statistics"""
    overall_confidence: float
    source_reliability: Dict[str, float]  # text, table, figure, direct
    validation_score: float
    consistency_score: float

    # Individual statistic confidences
    statistic_confidences: Dict[str, float] = None

    def __post_init__(self):
        if self.statistic_confidences is None:
            self.statistic_confidences = {}
```

---

## 🎯 **Implementation Timeline**

### **Phase 1: Foundation (Weeks 1-2)**

**Week 1: Text Statistics**
- [ ] Statistical pattern matching system
- [ ] NLP-based extraction framework
- [ ] Context analysis and confidence scoring
- [ ] Basic validation mechanisms

**Week 2: Table Processing**
- [ ] Table structure detection and parsing
- [ ] Column type classification
- [ ] Statistical relationship identification
- [ ] Summary statistics computation

### **Phase 2: Enhancement (Weeks 3-4)**

**Week 3: Figure Analysis**
- [ ] OCR integration for figure text
- [ ] Chart type classification
- [ ] Data extraction from plots
- [ ] Figure quality assessment

**Week 4: Direct Data Analysis**
- [ ] GEO dataset download and processing
- [ ] Comprehensive statistical computation
- [ ] Quality metrics calculation
- [ ] Distribution analysis

### **Phase 3: Integration (Weeks 5-6)**

**Week 5: Validation & Integration**
- [ ] Cross-source validation system
- [ ] Consistency checking algorithms
- [ ] Confidence scoring refinement
- [ ] API endpoint development

**Week 6: Optimization & Testing**
- [ ] Performance optimization
- [ ] Comprehensive testing suite
- [ ] Error handling and edge cases
- [ ] Documentation and deployment

---

## 📋 **Success Metrics**

### **Extraction Accuracy Metrics**
- **Text Statistics**: 85%+ accuracy for p-values and effect sizes
- **Table Processing**: 90%+ accuracy for numerical data extraction
- **Figure Analysis**: 70%+ accuracy for chart data extraction
- **Direct Analysis**: 95%+ accuracy for computed statistics

### **Quality Assessment Metrics**
- **Confidence Correlation**: 90%+ correlation between confidence scores and actual accuracy
- **Validation Success**: 95%+ of statistics pass cross-source validation
- **Completeness**: 80%+ of available statistics successfully extracted
- **Processing Speed**: <30 seconds per publication for statistical extraction

### **System Performance Metrics**
- **Throughput**: 50+ publications processed per hour
- **Memory Efficiency**: <4GB RAM per extraction worker
- **Error Tolerance**: <5% system errors under normal load
- **Cache Efficiency**: 85%+ cache hit rate for repeat analyses

---

This detailed specification provides the foundation for implementing a comprehensive statistical information extraction system that can process multiple data sources and provide reliable, validated statistical insights for biomedical research analysis.
