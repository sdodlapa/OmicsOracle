# 📦 Archived Original Planning Documents

**Archive Date:** October 6, 2025  
**Reason:** Superseded by refactored integration strategy  
**Status:** Reference only - do not use for implementation

---

## ⚠️ Important Notice

These documents contain the **original enhancement plans** created before architecture validation. They have been **superseded** by the refactored integration strategy.

**DO NOT use these for implementation.** Instead, use:
- [../REFACTORED_INTEGRATION_STRATEGY.md](../REFACTORED_INTEGRATION_STRATEGY.md) - Master implementation plan
- [../WEEK_1_2_PUBLICATIONS_IMPLEMENTATION.md](../WEEK_1_2_PUBLICATIONS_IMPLEMENTATION.md) - Week 1-2 guide
- Future week-by-week guides

---

## 📚 Archived Documents

### **What Changed**

| Original Document | Issue | Refactored Approach |
|-------------------|-------|---------------------|
| QUERY_FLOW_ENHANCEMENT_PLAN.md | 7 new modules, flat orchestration | 3 consolidated modules, pipeline composition |
| IMPLEMENTATION_ROADMAP_QUERY_ENHANCEMENT.md | Week-by-week without architecture alignment | Week-by-week following golden pattern |
| PUBLICATION_MINING_SPEC.md | Component design ✅ (valid), integration ❌ | Same components, refactored integration |
| PDF_PROCESSING_SPEC.md | Component design ✅ (valid), integration ❌ | Same components, refactored integration |
| ENHANCED_DATA_SOURCES_SPEC.md | Component design ✅ (valid), integration ❌ | Same components, consolidated into publications/ |
| WEB_SCRAPING_INTEGRATION_SUMMARY.md | Integration strategy unclear | Clear feature toggle strategy |
| WEB_ENHANCEMENT_VISUAL_MAP.md | Visualization only | Integrated into refactored docs |
| LLM_INTEGRATION_STRATEGY.md | Component design ✅ (valid), flat orchestration ❌ | Same LLMs, pipeline pattern |
| LLM_QUICK_REFERENCE.md | Reference outdated | Integrated into refactored docs |
| COMPLETE_ENHANCEMENT_SUMMARY.md | Summary of old plans | New summary in refactored docs |

### **What's Still Valid**

✅ **Component Designs** - All individual component designs (PubMedClient, GoogleScholarClient, BiomedicalQueryReformulator, etc.) are still excellent and will be used as-is.

✅ **Functionality** - All features, performance targets, and capabilities remain the same.

✅ **Timeline** - 10-week implementation timeline is preserved.

✅ **Cost Estimates** - Budget estimates ($50-200/month) are still valid.

### **What Changed**

❌ **Module Organization** - 7 modules → 3 consolidated modules  
❌ **Integration Strategy** - Flat orchestration → Pipeline composition  
❌ **Feature Enablement** - All-or-nothing → Feature toggles  
❌ **Pattern Compliance** - New patterns → Existing AdvancedSearchPipeline pattern  

---

## 📋 Archive Contents

### **1. QUERY_FLOW_ENHANCEMENT_PLAN.md**
**Original:** 8-week master roadmap with 5 modules  
**Superseded by:** REFACTORED_INTEGRATION_STRATEGY.md  
**Still valid:** Overall feature list and goals  

### **2. IMPLEMENTATION_ROADMAP_QUERY_ENHANCEMENT.md**
**Original:** Week-by-week tasks without architecture alignment  
**Superseded by:** Week-by-week implementation guides (WEEK_1_2_PUBLICATIONS_IMPLEMENTATION.md, etc.)  
**Still valid:** Task breakdowns (need reorganization)  

### **3. PUBLICATION_MINING_SPEC.md**
**Original:** PubMed, PMC, Europe PMC clients (400+ lines of code)  
**Superseded by:** Consolidated into lib/publications/ module  
**Still valid:** ✅ All component designs, API interactions, data models  

### **4. PDF_PROCESSING_SPEC.md**
**Original:** PDFDownloader, GROBIDClient (300+ lines of code)  
**Superseded by:** Consolidated into lib/publications/pdf/  
**Still valid:** ✅ All PDF processing logic, GROBID integration  

### **5. ENHANCED_DATA_SOURCES_SPEC.md**
**Original:** GoogleScholarClient, WebPDFScraper, TrendingTopicsDetector (400+ lines of code)  
**Superseded by:** Consolidated into lib/publications/  
**Still valid:** ✅ All web scraping implementations  

### **6. WEB_SCRAPING_INTEGRATION_SUMMARY.md**
**Original:** Executive summary of web enhancements  
**Superseded by:** Integrated into REFACTORED_INTEGRATION_STRATEGY.md  
**Still valid:** Impact analysis, cost estimates  

### **7. WEB_ENHANCEMENT_VISUAL_MAP.md**
**Original:** ASCII diagrams and visual references  
**Superseded by:** Integrated into refactored documentation  
**Still valid:** Feature-to-method mappings  

### **8. LLM_INTEGRATION_STRATEGY.md**
**Original:** 5 LLM components with full implementations (BioMistral, E5-Mistral, Llama, Meditron, Falcon)  
**Superseded by:** Consolidated into lib/llm/ module with pipeline pattern  
**Still valid:** ✅ All LLM component designs, GPU allocations, model selections  

### **9. LLM_QUICK_REFERENCE.md**
**Original:** Quick LLM implementation guide  
**Superseded by:** Integrated into refactored strategy  
**Still valid:** Model-to-task mappings, hardware allocations  

### **10. COMPLETE_ENHANCEMENT_SUMMARY.md**
**Original:** Master summary of all original plans  
**Superseded by:** ARCHITECTURE_VALIDATION_SUMMARY.md and ORIGINAL_VS_REFACTORED_COMPARISON.md  
**Still valid:** Performance targets, impact analysis  

---

## 🔍 How to Use These Archives

### **For Component Implementation**
✅ **USE** the component designs from these documents:
- PubMedClient implementation from PUBLICATION_MINING_SPEC.md
- PDFDownloader implementation from PDF_PROCESSING_SPEC.md
- GoogleScholarClient from ENHANCED_DATA_SOURCES_SPEC.md
- LLM components from LLM_INTEGRATION_STRATEGY.md

### **For Integration**
❌ **DON'T USE** the integration strategies from these documents  
✅ **USE** the refactored integration strategy instead:
- REFACTORED_INTEGRATION_STRATEGY.md for overall approach
- Week-by-week guides for step-by-step implementation

### **For Reference**
✅ **USE** for understanding:
- Original thinking process
- Feature specifications
- Performance targets
- Cost estimates

---

## 📊 Migration Guide

If you need to reference these documents:

1. **For component code:** ✅ Copy component implementations directly
2. **For integration code:** ❌ Don't use - follow refactored pipeline pattern instead
3. **For architecture:** ❌ Don't use - follow REFACTORED_INTEGRATION_STRATEGY.md
4. **For features:** ✅ Feature lists are still valid
5. **For timeline:** ✅ 10-week timeline preserved

---

## 🚀 Next Steps

**Don't start here!** Instead:

1. Read: [../README.md](../README.md) - Implementation index
2. Follow: [../REFACTORED_INTEGRATION_STRATEGY.md](../REFACTORED_INTEGRATION_STRATEGY.md) - Master plan
3. Implement: [../WEEK_1_2_PUBLICATIONS_IMPLEMENTATION.md](../WEEK_1_2_PUBLICATIONS_IMPLEMENTATION.md) - Week 1-2 guide

---

**Archive Status:** Reference only  
**Use for:** Component designs and specifications  
**Don't use for:** Integration and orchestration strategies  
**Current plan:** See [../REFACTORED_INTEGRATION_STRATEGY.md](../REFACTORED_INTEGRATION_STRATEGY.md)
