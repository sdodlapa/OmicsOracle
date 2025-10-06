# 🗺️ Module Integration Roadmap

**Date**: June 25, 2025  
**Status**: Implementation Ready  
**Purpose**: Strategic roadmap for integrating advanced modules into consolidated interfaces  

---

## 🎯 **Integration Overview**

This roadmap details the integration of four advanced modules into the consolidated OmicsOracle interface architecture:

1. **Text Extraction Module** - Full-text publication processing
2. **Publication Discovery Module** - Related literature identification  
3. **Statistical Extraction Module** - Automated statistics extraction
4. **Visualization Module** - Advanced data visualization

---

## 📅 **Integration Timeline**

### **Month 1: Foundation & Text Extraction**

**Week 1-2: Interface Consolidation**
- Complete interface consolidation (per Consolidation Guide)
- Establish shared services layer
- Implement agent communication framework

**Week 3-4: Text Extraction Integration**
- Deploy PDF processing agents
- Integrate with search interface
- Add progress tracking UI components

### **Month 2: Discovery & Statistics**

**Week 1-2: Publication Discovery**
- Implement citation analysis agents
- Add recommendation components to web interface
- Integrate with CLI batch operations

**Week 3-4: Statistical Extraction**
- Deploy statistical analysis agents
- Add statistics visualization components
- Implement validation workflows

### **Month 3: Visualization & Optimization**

**Week 1-2: Advanced Visualization**
- Integrate D3.js visualization components
- Add interactive dashboard elements
- Implement real-time updates via WebSocket

**Week 3-4: Performance Optimization**
- Optimize agent communication
- Implement caching strategies
- Conduct comprehensive testing

---

## 🧩 **Module-Interface Integration Points**

### **Text Extraction Module Integration**

**API Layer Integration**:
```python
# src/omics_oracle/api/v1/endpoints/text_extraction.py
from fastapi import APIRouter, UploadFile, BackgroundTasks
from ...agents.text_extraction import TextExtractionAgent
from ...models.extraction import ExtractionJob, ExtractionResult

router = APIRouter()
extraction_agent = TextExtractionAgent("text-extractor-1")

@router.post("/extract", response_model=ExtractionJob)
async def extract_text(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    extraction_type: str = "full"
):
    """Submit document for text extraction"""
    job = await extraction_agent.submit_extraction_job(file, extraction_type)
    background_tasks.add_task(extraction_agent.process_job, job.id)
    return job

@router.get("/jobs/{job_id}", response_model=ExtractionResult)
async def get_extraction_result(job_id: str):
    """Get extraction job results"""
    return await extraction_agent.get_result(job_id)
```

**Web Interface Integration**:
```python
# src/omics_oracle/web/components/text_extraction.py
from fastapi import Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def render_extraction_interface(request: Request):
    """Render text extraction interface"""
    return templates.TemplateResponse(
        "extraction/interface.html",
        {
            "request": request,
            "supported_formats": ["pdf", "docx", "txt"],
            "extraction_types": ["full", "abstract", "methods", "results"]
        }
    )

async def handle_extraction_upload(
    request: Request,
    file: UploadFile = File(...),
    extraction_type: str = Form(...)
):
    """Handle document upload for extraction"""
    # Process file upload and start extraction
    pass
```

**CLI Integration**:
```python
# src/omics_oracle/cli/commands/extract.py
import click
from pathlib import Path
from ..agents.text_extraction import TextExtractionAgent

@click.group()
def extract():
    """Text extraction commands"""
    pass

@extract.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--type', '-t', default='full', help='Extraction type')
@click.option('--output', '-o', help='Output file path')
async def file(file_path: str, type: str, output: str):
    """Extract text from a single file"""
    agent = TextExtractionAgent("cli-extractor")
    result = await agent.extract_from_file(Path(file_path), type)
    
    if output:
        with open(output, 'w') as f:
            f.write(result.extracted_text)
    else:
        click.echo(result.extracted_text)
```

### **Publication Discovery Module Integration**

**Agent Communication Layer**:
```python
# src/omics_oracle/agents/publication_discovery.py
from .base import BaseAgent, AgentMessage
from ..services.citation_analysis import CitationAnalysisService
from ..services.similarity_search import SimilaritySearchService

class PublicationDiscoveryAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.citation_service = CitationAnalysisService()
        self.similarity_service = SimilaritySearchService()
    
    async def process_message(self, message: AgentMessage):
        if message.message_type == "discover_related":
            return await self._discover_related_publications(message.payload)
        elif message.message_type == "analyze_citations":
            return await self._analyze_citations(message.payload)
        
    async def _discover_related_publications(self, payload: dict):
        """Find related publications based on input"""
        publication_id = payload.get("publication_id")
        search_terms = payload.get("search_terms", [])
        
        # Use both citation analysis and semantic similarity
        citation_related = await self.citation_service.find_citing_papers(publication_id)
        semantic_related = await self.similarity_service.find_similar(search_terms)
        
        return AgentMessage(
            message_type="discovery_result",
            payload={
                "citation_related": citation_related,
                "semantic_related": semantic_related,
                "combined_score": self._combine_scores(citation_related, semantic_related)
            },
            sender_id=self.agent_id
        )
```

**WebSocket Integration for Real-Time Updates**:
```python
# src/omics_oracle/api/websockets/discovery.py
from fastapi import WebSocket
from ..agents.publication_discovery import PublicationDiscoveryAgent

class DiscoveryWebSocketHandler:
    def __init__(self):
        self.discovery_agent = PublicationDiscoveryAgent("ws-discovery")
        
    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_json()
                
                if data["type"] == "start_discovery":
                    # Start discovery process
                    message = AgentMessage(
                        message_type="discover_related",
                        payload=data["payload"],
                        sender_id="websocket-client"
                    )
                    
                    # Process in background and send updates
                    result = await self.discovery_agent.process_message(message)
                    await websocket.send_json({
                        "type": "discovery_progress",
                        "data": result.payload
                    })
                    
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
```

### **Statistical Extraction Integration**

**Validation Workflow Integration**:
```python
# src/omics_oracle/workflows/statistical_validation.py
from ..agents.statistical_extraction import StatisticalExtractionAgent
from ..agents.validation import ValidationAgent
from ..models.statistics import StatisticalResult

class StatisticalValidationWorkflow:
    def __init__(self):
        self.extraction_agent = StatisticalExtractionAgent("stats-extractor")
        self.validation_agent = ValidationAgent("stats-validator")
    
    async def process_document(self, document_id: str):
        """Complete statistical extraction and validation workflow"""
        
        # Step 1: Extract statistics
        extraction_message = AgentMessage(
            message_type="extract_statistics",
            payload={"document_id": document_id},
            sender_id="workflow-orchestrator"
        )
        
        extraction_result = await self.extraction_agent.process_message(extraction_message)
        
        # Step 2: Validate extracted statistics
        validation_message = AgentMessage(
            message_type="validate_statistics",
            payload={"statistics": extraction_result.payload},
            sender_id="workflow-orchestrator"
        )
        
        validation_result = await self.validation_agent.process_message(validation_message)
        
        # Step 3: Return combined result
        return StatisticalResult(
            document_id=document_id,
            extracted_stats=extraction_result.payload,
            validation_results=validation_result.payload,
            confidence_score=validation_result.payload.get("confidence", 0.0)
        )
```

### **Visualization Module Integration**

**Component-Based Architecture**:
```python
# src/omics_oracle/web/components/visualization.py
from typing import Dict, Any, List
import json

class VisualizationComponents:
    """Modular visualization component system"""
    
    @staticmethod
    def render_network_graph(data: Dict[str, Any]) -> str:
        """Render D3.js network graph for publications"""
        return f"""
        <div id="network-graph" class="visualization-container">
            <script>
                const data = {json.dumps(data)};
                renderNetworkGraph('#network-graph', data);
            </script>
        </div>
        """
    
    @staticmethod
    def render_statistical_charts(stats: List[Dict[str, Any]]) -> str:
        """Render statistical visualization charts"""
        return f"""
        <div id="stats-charts" class="charts-container">
            <script>
                const statsData = {json.dumps(stats)};
                renderStatisticalCharts('#stats-charts', statsData);
            </script>
        </div>
        """
    
    @staticmethod
    def render_timeline_visualization(timeline_data: Dict[str, Any]) -> str:
        """Render publication timeline visualization"""
        return f"""
        <div id="timeline-viz" class="timeline-container">
            <script>
                const timelineData = {json.dumps(timeline_data)};
                renderTimeline('#timeline-viz', timelineData);
            </script>
        </div>
        """
```

**Real-Time Data Binding**:
```javascript
// static/js/visualization/real-time-updates.js
class RealTimeVisualization {
    constructor(websocketUrl) {
        this.websocket = new WebSocket(websocketUrl);
        this.charts = new Map();
        this.setupWebSocketHandlers();
    }
    
    setupWebSocketHandlers() {
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'statistics_update') {
                this.updateStatisticalCharts(data.payload);
            } else if (data.type === 'network_update') {
                this.updateNetworkGraph(data.payload);
            } else if (data.type === 'timeline_update') {
                this.updateTimeline(data.payload);
            }
        };
    }
    
    updateStatisticalCharts(data) {
        // Update existing charts with new data
        if (this.charts.has('statistics')) {
            this.charts.get('statistics').update(data);
        }
    }
    
    updateNetworkGraph(data) {
        // Update network graph with new nodes/edges
        if (this.charts.has('network')) {
            this.charts.get('network').updateData(data);
        }
    }
    
    updateTimeline(data) {
        // Update timeline with new events
        if (this.charts.has('timeline')) {
            this.charts.get('timeline').addEvents(data.events);
        }
    }
}
```

---

## 🔧 **Integration Configuration**

### **Agent Orchestration Configuration**:
```yaml
# config/agent_orchestration.yml
agents:
  text_extraction:
    instances: 3
    memory_limit: "2GB"
    processing_timeout: 300
    
  publication_discovery:
    instances: 2
    memory_limit: "1GB"
    cache_size: 1000
    
  statistical_extraction:
    instances: 2
    memory_limit: "1.5GB"
    validation_enabled: true
    
  visualization:
    instances: 1
    memory_limit: "512MB"
    real_time_updates: true

communication:
  message_broker: "redis"
  message_ttl: 3600
  max_retries: 3
  
performance:
  concurrent_jobs: 10
  queue_size: 100
  monitoring_enabled: true
```

### **Database Schema Updates**:
```sql
-- Migration for module integration support
ALTER TABLE documents ADD COLUMN extraction_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN extraction_metadata JSONB;

CREATE TABLE publication_relationships (
    id SERIAL PRIMARY KEY,
    source_publication_id INTEGER REFERENCES documents(id),
    target_publication_id INTEGER REFERENCES documents(id),
    relationship_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    discovered_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE statistical_extractions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    extracted_statistics JSONB,
    validation_results JSONB,
    confidence_score DECIMAL(3,2),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pub_relationships_source ON publication_relationships(source_publication_id);
CREATE INDEX idx_pub_relationships_target ON publication_relationships(target_publication_id);
CREATE INDEX idx_stats_document ON statistical_extractions(document_id);
```

---

## 📊 **Success Metrics & Monitoring**

### **Integration Success Criteria**

**Performance Metrics**:
- Text extraction: < 30 seconds per document
- Publication discovery: < 5 seconds for similarity search
- Statistical extraction: > 90% accuracy on validation dataset
- Visualization rendering: < 2 seconds for complex charts

**Quality Metrics**:
- Agent communication: 99.9% message delivery success
- Data consistency: Zero data corruption incidents
- User experience: < 3 seconds for interface response time
- System stability: 99.5% uptime during integration period

### **Monitoring Dashboard Configuration**:
```python
# src/omics_oracle/monitoring/integration_dashboard.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics collection
extraction_jobs = Counter('text_extraction_jobs_total', 'Total text extraction jobs')
discovery_requests = Counter('publication_discovery_requests_total', 'Total discovery requests')
statistical_extractions = Counter('statistical_extractions_total', 'Total statistical extractions')

processing_time = Histogram('module_processing_time_seconds', 'Processing time by module', ['module'])
agent_queue_size = Gauge('agent_queue_size', 'Agent queue size', ['agent_type'])

def setup_monitoring():
    """Setup monitoring for module integration"""
    pass
```

---

## 🚀 **Deployment Strategy**

### **Phased Rollout Plan**

**Phase 1: Internal Testing (Week 1)**
- Deploy to development environment
- Run integration test suite
- Validate agent communication

**Phase 2: Staging Validation (Week 2)**
- Deploy to staging environment
- Conduct user acceptance testing
- Performance benchmark validation

**Phase 3: Production Deployment (Week 3)**
- Blue-green deployment strategy
- Gradual traffic routing
- Real-time monitoring

**Phase 4: Full Integration (Week 4)**
- Complete feature enablement
- Documentation updates
- Training material creation

---

## 🔍 **Next Steps**

1. **Begin Interface Consolidation** following the Consolidation Guide
2. **Implement Text Extraction Module** as the foundation
3. **Establish Agent Communication** patterns and protocols  
4. **Integrate Discovery and Statistics** modules in parallel
5. **Deploy Visualization Components** with real-time capabilities
6. **Conduct Comprehensive Testing** throughout integration process
7. **Monitor Performance Metrics** and optimize as needed

---

*This roadmap will be updated based on implementation progress and emerging requirements.*
