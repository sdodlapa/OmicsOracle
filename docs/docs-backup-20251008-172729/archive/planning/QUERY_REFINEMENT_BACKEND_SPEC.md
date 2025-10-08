# Query Refinement Backend Technical Specification

## Architecture Overview

The query refinement system will extend the existing OmicsOracle backend with new services and API endpoints to provide intelligent query suggestions and refinements when searches return no or limited results.

## Core Components

### 1. Query Analysis Service (`QueryAnalysisService`)

**Purpose**: Analyze queries to understand why they failed and generate refinement suggestions.

**Location**: `/src/omics_oracle/services/query_analysis.py`

**Key Methods**:
```python
class QueryAnalysisService:
    def analyze_failed_query(self, query: str, original_results: int) -> QueryAnalysis
    def generate_suggestions(self, analysis: QueryAnalysis) -> List[QuerySuggestion]
    def find_similar_successful_queries(self, query: str) -> List[SimilarQuery]
    def score_query_complexity(self, query: str) -> float
    def decompose_query(self, query: str) -> QueryDecomposition
```

**Integration Points**:
- Uses existing `EntityExtractor` for entity analysis
- Leverages `SynonymMapper` for alternative terms
- Connects to query history database for pattern analysis

### 2. Refinement Strategy Engine

**Purpose**: Implement different strategies for query refinement based on query characteristics.

**Strategies**:
- **Entity Simplification**: Remove less common entities
- **Synonym Substitution**: Replace entities with more common synonyms
- **Query Broadening**: Remove restrictive terms
- **Term Suggestion**: Add related terms that might improve results
- **Structural Modification**: Change query structure (AND to OR operations)

### 3. New API Endpoints

#### 3.1 Query Suggestions Endpoint
```python
@router.post("/api/suggestions")
async def get_query_suggestions(request: QuerySuggestionRequest) -> QuerySuggestionResponse:
    """
    Generate refinement suggestions for a query that returned few/no results.

    Request:
    - original_query: str
    - result_count: int
    - user_context: Optional[UserContext]

    Response:
    - suggestions: List[QuerySuggestion]
    - alternative_queries: List[str]
    - explanation: str
    """
```

#### 3.2 Similar Queries Endpoint
```python
@router.get("/api/similar-queries")
async def get_similar_queries(query: str, limit: int = 5) -> SimilarQueriesResponse:
    """
    Find similar queries that returned good results.

    Response:
    - similar_queries: List[SimilarQuery]
    - success_patterns: List[QueryPattern]
    """
```

#### 3.3 Query Feedback Endpoint
```python
@router.post("/api/query-feedback")
async def submit_query_feedback(feedback: QueryFeedback) -> FeedbackResponse:
    """
    Accept user feedback on suggestion effectiveness.

    Request:
    - original_query: str
    - suggested_query: str
    - was_helpful: bool
    - user_action: str (used_suggestion, modified, ignored)
    - result_improvement: Optional[int]
    """
```

#### 3.4 Enhanced Search Endpoint
```python
@router.post("/api/search/enhanced")
async def enhanced_search(request: EnhancedSearchRequest) -> EnhancedSearchResponse:
    """
    Perform search with automatic refinement suggestions.

    Response includes:
    - results: List[SearchResult]
    - refinement_suggestions: Optional[List[QuerySuggestion]]
    - search_metadata: SearchMetadata
    """
```

### 4. Data Models

#### QuerySuggestion
```python
@dataclass
class QuerySuggestion:
    suggested_query: str
    suggestion_type: SuggestionType
    confidence_score: float
    explanation: str
    expected_result_count: Optional[int]
```

#### QueryAnalysis
```python
@dataclass
class QueryAnalysis:
    original_query: str
    entities_found: List[Entity]
    complexity_score: float
    potential_issues: List[QueryIssue]
    suggested_modifications: List[QueryModification]
```

#### QueryIssue
```python
class QueryIssue(Enum):
    TOO_SPECIFIC = "query_too_specific"
    RARE_ENTITIES = "contains_rare_entities"
    CONFLICTING_TERMS = "conflicting_terms"
    MISSPELLED_TERMS = "potential_misspellings"
    UNSUPPORTED_FORMAT = "unsupported_query_format"
```

### 5. Database Schema Extensions

#### Query History Table
```sql
CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    execution_time TIMESTAMP DEFAULT NOW(),
    user_session_id VARCHAR(255),
    entities_extracted JSONB,
    success_score FLOAT
);
```

#### Query Refinement Feedback Table
```sql
CREATE TABLE query_refinement_feedback (
    id SERIAL PRIMARY KEY,
    original_query TEXT NOT NULL,
    suggested_query TEXT NOT NULL,
    user_action VARCHAR(50) NOT NULL,
    was_helpful BOOLEAN,
    result_improvement INTEGER,
    feedback_time TIMESTAMP DEFAULT NOW(),
    user_session_id VARCHAR(255)
);
```

### 6. Integration with Existing Pipeline

#### Modified Search Flow
1. **Original Search**: Execute user's query as normal
2. **Result Evaluation**: Check if results meet quality threshold
3. **Refinement Trigger**: If results are poor, trigger refinement analysis
4. **Suggestion Generation**: Generate and score potential refinements
5. **Enhanced Response**: Return results with refinement suggestions

#### Pipeline Modifications
- Extend `SearchPipeline` to capture refinement opportunities
- Modify `SearchResult` model to include refinement metadata
- Add hooks for analytics and feedback collection

### 7. Performance Considerations

#### Caching Strategy
- Cache common query patterns and their successful refinements
- Cache entity extraction results for similar queries
- Implement suggestion pre-computation for frequent query types

#### Optimization Techniques
- Lazy loading of refinement suggestions
- Batch processing of similar query analysis
- Async processing for non-critical suggestions

#### Monitoring and Metrics
- Track suggestion generation time
- Monitor suggestion acceptance rates
- Measure search success improvement

### 8. Error Handling and Fallbacks

#### Graceful Degradation
- If refinement service fails, return original results without suggestions
- Provide basic suggestions if advanced analysis fails
- Log errors without breaking main search functionality

#### Rate Limiting
- Limit suggestion requests per user session
- Implement backoff for expensive operations
- Queue non-urgent refinement processing

### 9. Testing Strategy

#### Unit Tests
- Test each refinement strategy independently
- Validate suggestion scoring algorithms
- Test error handling scenarios

#### Integration Tests
- Test API endpoints with various query types
- Validate database operations
- Test caching behavior

#### Performance Tests
- Load test suggestion generation
- Measure impact on search response times
- Test with large query datasets

### 10. Configuration

#### Environment Variables
```bash
REFINEMENT_ENABLED=true
SUGGESTION_CACHE_TTL=3600
MAX_SUGGESTIONS_PER_QUERY=5
REFINEMENT_CONFIDENCE_THRESHOLD=0.6
ENABLE_QUERY_LEARNING=true
```

#### Feature Flags
- Enable/disable refinement suggestions
- Control suggestion strategies
- Toggle analytics collection
- Enable/disable caching

This specification provides the foundation for implementing robust query refinement capabilities in the OmicsOracle backend.
