# 🏛️ Institutional Access Integration Guide

**Purpose:** Leverage Old Dominion University and Georgia Tech institutional access to bypass journal paywalls  
**Status:** Ready for Week 4 integration (PDF processing module)  
**Methods:** EZProxy, Unpaywall, OpenURL, VPN routing  

---

## 📋 Overview

You have access to **thousands of journals** through your university subscriptions! This guide shows how to integrate that access into the OmicsOracle pipeline.

### **Your Institutions:**
1. 🎓 **Old Dominion University (ODU)**
   - EZProxy: `https://proxy.lib.odu.edu/login?url=`
   - OpenURL: `https://odu.illiad.oclc.org/illiad/illiad.dll/OpenURL`
   - Shibboleth: `https://shib.odu.edu/idp/shibboleth`

2. 🐝 **Georgia Institute of Technology (Georgia Tech)**
   - EZProxy: `https://login.ezproxy.gatech.edu/login?url=`
   - OpenURL: `https://buzzport.gatech.edu/sfx_local`
   - Shibboleth: `https://login.gatech.edu/idp/shibboleth`

---

## 🎯 Access Methods (In Priority Order)

### **1. Unpaywall API** (Free, Legal, No Auth) ⭐
**What:** Database of 30M+ open access articles  
**When:** Always try first  
**Advantage:** No authentication, completely legal, high coverage  

**How it works:**
```python
# Check if article is open access
unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=your@email.com"
response = requests.get(unpaywall_url)
if response.json()['is_oa']:
    pdf_url = response.json()['best_oa_location']['url_for_pdf']
```

**Coverage:** ~30% of all publications (growing)

---

### **2. EZProxy Authentication** (Most Common) ⭐⭐⭐
**What:** URL rewriting to route through university proxy  
**When:** Article is paywalled, institution has subscription  
**Advantage:** Works with 99% of publishers, automatic authentication  

**How it works:**
```python
# Original paywalled URL
original_url = "https://www.sciencedirect.com/science/article/pii/S0092867420316822"

# EZProxy-wrapped URL (Georgia Tech)
ezproxy_url = "https://login.ezproxy.gatech.edu/login?url=https://www.sciencedirect.com/science/article/pii/S0092867420316822"

# User clicks → Georgia Tech login → Redirected to article with access
```

**Setup Required:**
1. Store university credentials securely (optional - browser session works)
2. Configure EZProxy URLs in settings
3. URL rewriting is automatic

**Publishers Supported:** Elsevier, Springer, Nature, Wiley, PLOS, Oxford, Cambridge, IEEE, ACM, etc.

---

### **3. OpenURL Link Resolvers** (Library Discovery) ⭐⭐
**What:** Library systems that find where article is available  
**When:** Not sure if institution has access  
**Advantage:** Checks all subscriptions, interlibrary loan  

**How it works:**
```python
# Build OpenURL with article metadata
params = {
    'title': publication.title,
    'journal': publication.journal,
    'doi': publication.doi,
    'pmid': publication.pmid,
}

# Library resolver finds access
resolver_url = "https://buzzport.gatech.edu/sfx_local?{params}"
```

**Result:** Shows all ways to access (subscription, OA, interlibrary loan)

---

### **4. PubMed Central (PMC)** (Free Full Text) ⭐⭐⭐
**What:** Free repository of NIH-funded research  
**When:** Publication has PMCID  
**Advantage:** Completely free, no authentication  

**How it works:**
```python
if publication.pmcid:
    free_pdf = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication.pmcid}/pdf/"
```

**Coverage:** 5M+ articles (all NIH-funded research after 2008)

---

### **5. VPN/Proxy Routing** (Network-Level Access) ⭐
**What:** Route all traffic through university network  
**When:** On-campus IP authentication  
**Advantage:** Works for IP-authenticated resources  

**How it works:**
- Connect to Georgia Tech VPN
- Your IP becomes GT campus IP
- Publishers see campus IP → grant access

**Setup:** Requires VPN client installation

---

## 🚀 Integration into Pipeline

### **Week 4: PDF Processing Module**

Add institutional access to `PublicationSearchPipeline`:

```python
# config.py - Add institutional settings
@dataclass
class PublicationSearchConfig:
    # Existing
    enable_pdf_download: bool = False
    
    # NEW: Institutional access
    enable_institutional_access: bool = True
    institution: str = "gatech"  # or "odu"
    institution_credentials: Optional[Dict] = None

# pipeline.py - Integration
class PublicationSearchPipeline:
    def __init__(self, config):
        # Existing
        if config.enable_pdf_download:
            self.pdf_downloader = PDFDownloader(config.pdf_config)
        
        # NEW: Institutional access
        if config.enable_institutional_access:
            self.institutional_manager = InstitutionalAccessManager(
                institution=InstitutionType.GEORGIA_TECH
            )
    
    def _download_pdfs(self, results):
        for result in results:
            pub = result.publication
            
            # Try institutional access for PDF URL
            if self.institutional_manager:
                pdf_url = self.institutional_manager.get_pdf_url(pub)
                if pdf_url:
                    # Download PDF
                    self.pdf_downloader.download(pdf_url)
```

---

## 📝 Implementation Checklist

### **Phase 1: Basic Integration** (Week 4)
- [x] ✅ `InstitutionalAccessManager` class created
- [x] ✅ EZProxy URL rewriting implemented
- [x] ✅ Unpaywall API integration ready
- [x] ✅ PMC PDF detection added
- [ ] ⏳ Add to `PublicationSearchPipeline`
- [ ] ⏳ Configuration in `PublicationSearchConfig`
- [ ] ⏳ Test with real articles

### **Phase 2: Enhanced Access** (Week 5+)
- [ ] ⏳ OpenURL resolver integration
- [ ] ⏳ Publisher-specific PDF patterns
- [ ] ⏳ Shibboleth/SAML authentication (if needed)
- [ ] ⏳ VPN proxy routing (optional)
- [ ] ⏳ Cookie/session management

### **Phase 3: Production** (Week 6+)
- [ ] ⏳ Credential encryption
- [ ] ⏳ Access status caching
- [ ] ⏳ Rate limiting per institution
- [ ] ⏳ Fallback strategies
- [ ] ⏳ Usage analytics

---

## 🔐 Security & Authentication

### **Option 1: Browser-Based (Recommended for Manual Use)**
**Setup:** None  
**How:** User clicks EZProxy link → logs in via browser → accesses article  
**Pros:** No credential storage, uses existing university login  
**Cons:** Requires manual interaction  

**Use Case:** Manual research, ad-hoc article access

---

### **Option 2: Automated with Credentials (Programmatic Access)**
**Setup:** Store encrypted credentials  
**How:** Selenium/Playwright automates login → downloads PDF  
**Pros:** Fully automated  
**Cons:** Requires secure credential storage  

**Implementation:**
```python
from playwright.sync_api import sync_playwright

def download_via_ezproxy(url, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Go to EZProxy URL
        page.goto(ezproxy_url)
        
        # Login (if needed)
        if "login" in page.url:
            page.fill("#username", username)
            page.fill("#password", password)
            page.click("button[type=submit]")
        
        # Download PDF
        page.goto(article_url)
        # ... download logic
```

**Security:**
```python
# Use environment variables or key vault
import os
from cryptography.fernet import Fernet

# Encrypted storage
ODU_USERNAME = os.getenv("ODU_USERNAME")
ODU_PASSWORD = Fernet(key).decrypt(encrypted_password)
```

---

### **Option 3: Session-Based (Best for Development)**
**Setup:** Manual login once, save cookies  
**How:** Reuse authenticated session for API calls  
**Pros:** No repeated authentication  
**Cons:** Sessions expire  

**Implementation:**
```python
import requests

# Login once, save session
session = requests.Session()
session.post(login_url, data={'username': user, 'password': pwd})

# Reuse session
response = session.get(ezproxy_article_url)
```

---

## 📊 Access Coverage Estimates

| Method | Coverage | Speed | Auth Required |
|--------|----------|-------|---------------|
| **PMC** | ~15% | Fast | ❌ No |
| **Unpaywall** | ~30% | Fast | ❌ No |
| **EZProxy (GT)** | ~60% | Medium | ✅ Yes |
| **EZProxy (ODU)** | ~50% | Medium | ✅ Yes |
| **Combined** | **~80-90%** | - | Varies |

**Translation:** You can access 80-90% of biomedical literature for free!

---

## 💡 Usage Examples

### **Example 1: Automatic PDF Download**
```python
from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType
)

# Initialize manager
manager = InstitutionalAccessManager(
    institution=InstitutionType.GEORGIA_TECH
)

# Get PDF URL for publication
pdf_url = manager.get_pdf_url(publication)

if pdf_url:
    # Download PDF
    download_pdf(pdf_url)
else:
    # Fallback: get access instructions
    instructions = manager.get_access_instructions(publication)
    print(instructions)
```

---

### **Example 2: Check Access Before Search**
```python
# In pipeline
def search(self, query, max_results=50):
    # ... search and rank ...
    
    # Enrich with access info
    for result in ranked_results:
        pub = result.publication
        
        # Check access methods
        access_status = self.institutional_manager.check_access_status(pub)
        
        # Add to metadata
        result.publication.metadata['access'] = {
            'open_access': access_status['unpaywall'],
            'institutional': access_status['ezproxy'],
            'pmc': access_status['pmc'],
        }
    
    return ranked_results
```

---

### **Example 3: Prioritize Accessible Articles**
```python
# Custom ranking with access boost
def _score_publication(self, publication, query):
    # Base score
    score = calculate_base_score(publication, query)
    
    # Boost if easily accessible
    if self.institutional_manager:
        access_status = self.institutional_manager.check_access_status(publication)
        
        if access_status['unpaywall']:
            score *= 1.2  # 20% boost for OA
        elif access_status['pmc']:
            score *= 1.15  # 15% boost for PMC
        elif access_status['ezproxy']:
            score *= 1.1  # 10% boost for institutional
    
    return score
```

---

## 🎓 Which Institution to Use?

### **Georgia Tech** (Recommended Primary)
**Strengths:**
- Large research university → more journal subscriptions
- Better engineering/CS coverage
- Faster EZProxy (better infrastructure)
- Active Shibboleth federation

**Best for:** Most queries, CS/engineering, general science

---

### **Old Dominion University**
**Strengths:**
- Strong biomedical/health sciences
- Unique regional subscriptions
- Good oceanography/marine biology

**Best for:** Marine biology, oceanography, specialized biomedical

---

### **Strategy: Try Both!**
```python
# Fallback between institutions
def get_pdf_url(self, publication):
    # Try Georgia Tech first
    gt_manager = InstitutionalAccessManager(InstitutionType.GEORGIA_TECH)
    url = gt_manager.get_pdf_url(publication)
    if url:
        return url
    
    # Fallback to ODU
    odu_manager = InstitutionalAccessManager(InstitutionType.OLD_DOMINION)
    url = odu_manager.get_pdf_url(publication)
    return url
```

---

## 🚨 Legal & Ethical Considerations

### ✅ **Legal:**
- ✅ Using institutional subscriptions you're entitled to
- ✅ Unpaywall provides legally free OA versions
- ✅ PMC is government-funded, completely free
- ✅ Personal research use is covered by university license

### ⚠️ **Best Practices:**
- ⚠️ Don't share downloaded PDFs publicly (copyright)
- ⚠️ Respect publisher rate limits
- ⚠️ Don't mass-download entire journals
- ⚠️ Use for research/education only

### ❌ **Avoid:**
- ❌ Sharing login credentials with non-affiliates
- ❌ Commercial use without proper licensing
- ❌ Automated bulk downloading (triggers alerts)

---

## 📚 Resources

### **University Library Resources:**
- **Georgia Tech Library:** https://library.gatech.edu
  - Journal access: https://library.gatech.edu/search
  - EZProxy help: https://library.gatech.edu/ezproxy
  
- **ODU Libraries:** https://www.odu.edu/library
  - Journal finder: https://odu.illiad.oclc.org
  - Off-campus access: https://www.odu.edu/library/help/off-campus

### **Tools & APIs:**
- **Unpaywall:** https://unpaywall.org/products/api
- **Shareyourpaper:** https://shareyourpaper.org
- **OpenURL:** https://www.oclc.org/research/areas/standards/openurl.html

---

## 🎯 Next Steps

### **Immediate (Week 4):**
1. ✅ Review `institutional_access.py` implementation
2. ⏳ Test EZProxy URLs with sample articles
3. ⏳ Integrate into `PublicationSearchPipeline`
4. ⏳ Add configuration options

### **Week 5:**
1. ⏳ Add automated authentication (if needed)
2. ⏳ Implement OpenURL resolver
3. ⏳ Add access status to search results
4. ⏳ Test with 100+ articles

### **Week 6:**
1. ⏳ Production deployment
2. ⏳ Monitor access rates
3. ⏳ Add analytics dashboard
4. ⏳ User documentation

---

## 💪 Impact

**Without institutional access:**
- ❌ ~70% of articles behind paywall
- ❌ $30-50 per article to purchase
- ❌ Limited research capability

**With institutional access:**
- ✅ ~80-90% of articles accessible
- ✅ $0 cost (covered by university)
- ✅ Full research capability
- ✅ Competitive with major research institutions

**Bottom line:** This unlocks the full potential of OmicsOracle! 🚀

---

**Status:** Implementation ready, Week 4 integration planned  
**Estimated Development:** 2-3 days  
**Value:** Transforms OmicsOracle from limited to comprehensive article access
