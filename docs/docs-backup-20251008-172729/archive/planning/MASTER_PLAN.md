# 🚀 OmicsOracle v2: Multi-Agent Implementation Master Plan

**Project**: OmicsOracle Multi-Agent Smart Data Summary System
**Start Date**: October 2, 2025
**Approach**: Selective Ground-Up Redesign (Hybrid)
**Timeline**: 12 weeks (3 months)
**Status**: Planning Phase

---

## 📋 Executive Summary

This master plan outlines the transformation of OmicsOracle from a monolithic pipeline to a modern multi-agent architecture while preserving proven domain logic. The implementation is divided into 4 major phases with clear deliverables and success criteria.

**Key Principle**: Extract proven algorithms → Build new architecture → Integrate and extend

---

## 🎯 Project Goals

### Primary Goals
1. ✅ Build multi-agent smart data summary system
2. ✅ Preserve proven NER, GEO, and AI algorithms ($50-75K value)
3. ✅ Achieve clean, maintainable architecture (8.5+/10)
4. ✅ Implement proper dependency injection
5. ✅ Increase test coverage to 80%+

### Success Metrics
- Multi-agent system operational by Week 12
- All core algorithms preserved and improved
- Zero sys.path manipulations
- Clean git history with no backup bloat
- Production-ready code quality

---

## 📅 Phase Overview

### Phase 0: Comprehensive Cleanup (Week 1-2)
**Goal**: Clean workspace, fix critical issues
**Duration**: 2 weeks
**Effort**: ~40 hours

### Phase 1: Algorithm Extraction (Week 3-4)
**Goal**: Extract proven logic into clean library
**Duration**: 2 weeks
**Effort**: ~60 hours

### Phase 2: Multi-Agent Architecture (Week 5-8)
**Goal**: Build new agent framework from scratch
**Duration**: 4 weeks
**Effort**: ~120 hours

### Phase 3: Integration & Enhancement (Week 9-12)
**Goal**: Integrate agents, add features, test
**Duration**: 4 weeks
**Effort**: ~120 hours

**Total Timeline**: 12 weeks
**Total Effort**: ~340 hours

---

## 📊 Detailed Phase Breakdown

### Phase 0: Comprehensive Cleanup ✨
**Status**: PENDING
**Document**: `PHASE_0_CLEANUP_PLAN.md`

**Objectives**:
1. Remove 365MB backup directory
2. Fix all sys.path manipulations
3. Consolidate route files
4. Add missing __init__.py files
5. Clean git history

**Deliverables**:
- Clean repository (<50MB)
- Zero sys.path hacks
- Consolidated route structure
- Proper package structure

**Success Criteria**:
- [ ] Repository size reduced by 70%+
- [ ] All imports work without sys.path
- [ ] pip install -e . works correctly
- [ ] Pre-commit hooks pass

---

### Phase 1: Algorithm Extraction 🔬
**Status**: PENDING
**Document**: `PHASE_1_EXTRACTION_PLAN.md`

**Objectives**:
1. Create omics_oracle_v2/ structure
2. Extract BiomedicalNER to lib/nlp/
3. Extract UnifiedGEOClient to lib/geo/
4. Extract SummarizationService to lib/ai/
5. Extract Config system to core/
6. Add comprehensive tests

**Deliverables**:
- Clean algorithm library in lib/
- Unit tests for each algorithm (80%+ coverage)
- Documentation for library APIs
- Standalone, reusable components

**Success Criteria**:
- [ ] All algorithms work standalone
- [ ] 80%+ test coverage on extracted code
- [ ] Zero dependencies on old architecture
- [ ] API documentation complete

---

### Phase 2: Multi-Agent Architecture 🤖
**Status**: PENDING
**Document**: `PHASE_2_MULTI_AGENT_PLAN.md`

**Objectives**:
1. Design agent base classes
2. Implement SearchAgent
3. Implement AnalysisAgent
4. Implement SummaryAgent
5. Build agent coordinator
6. Implement dependency injection

**Deliverables**:
- Agent framework with base classes
- 3 specialized agents (search, analysis, summary)
- Agent coordinator with orchestration
- Dependency injection container
- Agent communication protocol

**Success Criteria**:
- [ ] Agents communicate via standard protocol
- [ ] Each agent is independently testable
- [ ] Coordinator handles complex workflows
- [ ] DI container manages all dependencies
- [ ] Agent state is properly managed

---

### Phase 3: Integration & Enhancement 🔗
**Status**: PENDING
**Document**: `PHASE_3_INTEGRATION_PLAN.md`

**Objectives**:
1. Integrate multi-agent with web interface
2. Add real-time agent monitoring
3. Implement caching and optimization
4. Enhance error handling
5. Production hardening
6. Comprehensive testing

**Deliverables**:
- Full multi-agent web interface
- Real-time agent status dashboard
- Performance optimization
- Production configuration
- End-to-end test suite
- Deployment documentation

**Success Criteria**:
- [ ] Web interface shows agent activity
- [ ] System handles 100+ concurrent requests
- [ ] Error recovery is automatic
- [ ] 80%+ overall test coverage
- [ ] Production deployment successful

---

## 🗂️ Directory Structure Evolution

### Current State (v1)
```
OmicsOracle/
├── src/omics_oracle/          # Mixed quality code
├── backups/                   # 365MB of duplication (DELETE)
├── tests/                     # Scattered tests
└── docs/                      # Good documentation
```

### After Phase 0: Cleanup
```
OmicsOracle/
├── src/omics_oracle/          # Cleaned up v1 (reference only)
├── tests/                     # Organized tests
└── docs/                      # Enhanced documentation
```

### After Phase 1: Extraction
```
OmicsOracle/
├── src/omics_oracle/          # v1 (deprecated but kept for reference)
├── omics_oracle_v2/           # New structure
│   ├── lib/                   # Extracted algorithms
│   │   ├── nlp/              # BiomedicalNER + synonyms
│   │   ├── geo/              # UnifiedGEOClient
│   │   └── ai/               # SummarizationService
│   ├── core/                  # Config + exceptions
│   └── tests/                 # Comprehensive test suite
└── docs/
    └── v2/                    # v2 documentation
```

### After Phase 2: Multi-Agent
```
OmicsOracle/
├── omics_oracle_v2/           # Main development
│   ├── agents/                # NEW: Multi-agent framework
│   │   ├── base.py
│   │   ├── search_agent.py
│   │   ├── analysis_agent.py
│   │   ├── summary_agent.py
│   │   └── coordinator.py
│   ├── core/
│   │   ├── config.py
│   │   └── di_container.py   # NEW: Dependency injection
│   ├── lib/                   # Proven algorithms
│   ├── services/              # NEW: Service layer
│   └── tests/                 # Growing test suite
└── src/omics_oracle/          # v1 (kept for reference)
```

### After Phase 3: Final
```
OmicsOracle/
├── omics_oracle_v2/           # Production code
│   ├── agents/                # Multi-agent system
│   ├── presentation/          # NEW: Web + CLI + API
│   │   ├── web/
│   │   ├── api/
│   │   └── cli/
│   ├── core/                  # Core infrastructure
│   ├── lib/                   # Algorithm library
│   ├── services/              # Service layer
│   └── tests/                 # Comprehensive tests (80%+)
├── docs/                      # Complete documentation
└── deployment/                # NEW: Production configs
```

---

## 🔧 Key Technical Decisions

### 1. Multi-Agent Communication
**Decision**: Event-driven async message passing
**Rationale**: Loose coupling, scalability, testability

### 2. Dependency Injection
**Decision**: Custom lightweight DI container
**Rationale**: No heavy framework overhead, full control

### 3. State Management
**Decision**: Immutable state with event sourcing
**Rationale**: Debuggability, reproducibility, testing

### 4. Testing Strategy
**Decision**: Test pyramid (70% unit, 20% integration, 10% e2e)
**Rationale**: Fast feedback, high confidence

### 5. Deployment
**Decision**: Docker containers with docker-compose
**Rationale**: Consistency, easy deployment, scalability

---

## 📚 Documentation Structure

```
docs/
├── planning/
│   ├── MASTER_PLAN.md                    # This file
│   ├── PHASE_0_CLEANUP_PLAN.md
│   ├── PHASE_1_EXTRACTION_PLAN.md
│   ├── PHASE_2_MULTI_AGENT_PLAN.md
│   └── PHASE_3_INTEGRATION_PLAN.md
├── architecture/
│   ├── MULTI_AGENT_DESIGN.md
│   ├── DEPENDENCY_INJECTION.md
│   └── COMMUNICATION_PROTOCOL.md
├── development/
│   ├── DEVELOPMENT_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── CONTRIBUTION_GUIDE.md
└── deployment/
    ├── DEPLOYMENT_GUIDE.md
    ├── MONITORING_GUIDE.md
    └── TROUBLESHOOTING.md
```

---

## 🎯 Risk Management

### High-Risk Areas

1. **Algorithm Extraction Complexity**
   - **Risk**: Breaking existing functionality during extraction
   - **Mitigation**: Comprehensive tests before and after extraction
   - **Contingency**: Keep v1 functional as fallback

2. **Multi-Agent Coordination**
   - **Risk**: Deadlocks, race conditions, state inconsistency
   - **Mitigation**: Event sourcing, immutable state, thorough testing
   - **Contingency**: Simple coordinator fallback

3. **Performance Regression**
   - **Risk**: New architecture slower than v1
   - **Mitigation**: Performance benchmarks at each phase
   - **Contingency**: Optimization sprint if needed

4. **Integration Issues**
   - **Risk**: Agents don't integrate smoothly
   - **Mitigation**: Integration tests from Phase 2
   - **Contingency**: Staged integration approach

---

## 📈 Progress Tracking

### Weekly Checkpoints

**Every Friday**:
- Review progress against plan
- Update success criteria checklist
- Adjust timeline if needed
- Document lessons learned

### Phase Gates

**Before starting each phase**:
- [ ] Previous phase deliverables complete
- [ ] Success criteria met
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Code reviewed

---

## 🚀 Quick Start (After Planning)

### Step 1: Complete Phase 0 Cleanup
```bash
cd OmicsOracle
git checkout -b cleanup-phase-0
# Follow PHASE_0_CLEANUP_PLAN.md
```

### Step 2: Execute Phase 1 Extraction
```bash
git checkout -b extraction-phase-1
mkdir -p omics_oracle_v2/lib/{nlp,geo,ai}
# Follow PHASE_1_EXTRACTION_PLAN.md
```

### Step 3: Build Phase 2 Multi-Agent
```bash
git checkout -b multi-agent-phase-2
mkdir -p omics_oracle_v2/agents
# Follow PHASE_2_MULTI_AGENT_PLAN.md
```

### Step 4: Complete Phase 3 Integration
```bash
git checkout -b integration-phase-3
# Follow PHASE_3_INTEGRATION_PLAN.md
```

---

## 📝 Notes & Reminders

### Remember
- Keep v1 code intact until v2 is fully working
- Write tests BEFORE extracting code
- Document decisions and rationale
- Commit frequently with clear messages
- Review code at end of each phase

### Don't
- Delete v1 code prematurely
- Skip tests "to save time"
- Mix v1 and v2 dependencies
- Rush through phases
- Ignore failing tests

---

## 📞 Support & Resources

### Key Documents
- Architecture evaluation: `docs/architecture/COMPREHENSIVE_CODEBASE_EVALUATION.md`
- Decision rationale: `docs/architecture/DECISION_SCRATCH_VS_REFACTOR.md`
- Current plans: `docs/architecture/[VARIOUS]_PLAN.md`

### Review Schedule
- Weekly progress review: Every Friday
- Phase completion review: End of each phase
- Architecture review: After Phase 2
- Final review: End of Phase 3

---

## ✅ Implementation Checklist

### Planning Phase (Current)
- [x] Comprehensive codebase evaluation
- [x] Start from scratch vs refactor decision
- [x] Master plan creation
- [ ] Phase 0 detailed plan
- [ ] Phase 1 detailed plan
- [ ] Phase 2 detailed plan
- [ ] Phase 3 detailed plan

### Phase 0: Cleanup
- [ ] Remove backup directory
- [ ] Fix import structure
- [ ] Consolidate routes
- [ ] Clean git history

### Phase 1: Extraction
- [ ] Extract NER algorithms
- [ ] Extract GEO client
- [ ] Extract AI summarizer
- [ ] Add comprehensive tests

### Phase 2: Multi-Agent
- [ ] Design agent framework
- [ ] Implement agents
- [ ] Build coordinator
- [ ] Add DI container

### Phase 3: Integration
- [ ] Integrate with web
- [ ] Add monitoring
- [ ] Optimize performance
- [ ] Production deployment

---

**Last Updated**: October 2, 2025
**Next Review**: After Phase 0 completion
**Status**: Ready to begin Phase 0 detailed planning
