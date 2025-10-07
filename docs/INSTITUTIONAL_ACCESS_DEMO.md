# Institutional Access Demonstration

## Overview

OmicsOracle now provides seamless access to publications through **Georgia Tech Library** institutional subscriptions using multiple access methods:

1. **EZProxy URL Rewriting** - Primary method for off-campus access
2. **OpenURL Link Resolver** - Library's SFX service for finding all access options
3. **Unpaywall API** - Free, legal open access versions
4. **Direct Publisher URLs** - Fallback to original source

## How It Works

### Backend Architecture

```
Search Query → PubMed/Scholar → Publications
                                      ↓
                        InstitutionalAccessManager
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
            Check Access Status              Generate Access URL
                    ↓                                   ↓
        {                                  https://login.ezproxy.gatech.edu
          "unpaywall": true/false,            /login?url=https://doi.org/...
          "ezproxy": true/false,
          "openurl": true/false,
          "pmc": true/false
        }
                    ↓                                   ↓
                Publication.metadata["access_status"]
                Publication.metadata["has_access"]
                Publication.metadata["access_url"]
                    ↓
            Dashboard Display (NEW!)
```

### Access Methods

#### 1. EZProxy (Primary Method)

**What it is:** Georgia Tech's proxy server that authenticates you and routes requests through the library's subscriptions.

**How it works:**
- Wraps the target URL (DOI or publisher URL) in EZProxy authentication
- Format: `https://login.ezproxy.gatech.edu/login?url={target_url}`
- On campus: Auto-authenticates via IP recognition
- Off campus: Prompts for GT credentials (username/password)

**Example:**
```
Original URL: https://doi.org/10.1038/nature12345
Access URL:   https://login.ezproxy.gatech.edu/login?url=https%3A%2F%2Fdoi.org%2F10.1038%2Fnature12345
```

#### 2. OpenURL Link Resolver

**What it is:** Georgia Tech's SFX service that finds all available access options for a publication.

**How it works:**
- Constructs an OpenURL with publication metadata (title, authors, DOI, etc.)
- SFX searches library subscriptions, databases, and repositories
- Returns menu of all access options (PDF, HTML, databases)

**Example:**
```
https://buzzport.gatech.edu/sfx_local?
  sid=omics_oracle&
  title=Cancer+Genomics&
  doi=10.1038/nature12345&
  ...
```

#### 3. Unpaywall API

**What it is:** Non-profit service that finds free, legal open access versions.

**How it works:**
- Queries Unpaywall database by DOI
- Returns: Repository URLs (arXiv, PubMed Central, institutional repos)
- Only legal, publisher-authorized versions
- No institutional login needed!

**Example:**
```python
# API Call
GET https://api.unpaywall.org/v2/10.1038/nature12345?email=omics@gatech.edu

# Response
{
  "is_oa": true,
  "best_oa_location": {
    "url_for_pdf": "https://europepmc.org/articles/PMC1234567?pdf=render",
    "version": "publishedVersion"
  }
}
```

#### 4. Direct Publisher URLs

**Fallback:** If all else fails, provides the original publisher URL (may be paywalled).

## Configuration

### Current Setup (Georgia Tech)

```python
# omics_oracle_v2/lib/publications/clients/institutional_access.py

INSTITUTIONAL_CONFIGS = {
    InstitutionType.GEORGIA_TECH: InstitutionalConfig(
        name="Georgia Institute of Technology",
        ezproxy_url="https://login.ezproxy.gatech.edu/login?url=",
        openurl_resolver="https://buzzport.gatech.edu/sfx_local",
        shibboleth_idp="https://login.gatech.edu/idp/shibboleth",
        institution_id="gatech",
    )
}
```

### Enable/Disable

```python
# omics_oracle_v2/lib/config/config.py

class SearchConfig:
    enable_institutional_access: bool = True  # Week 4 feature
```

## Dashboard Display (NEW!)

### Before (Old)
```
📄 CRISPR-Cas9 genome editing
   Authors: Zhang, F., et al.
   Year: 2014    Citations: 5432
   [View Source](https://doi.org/10.1038/nbt.2808)
```

### After (Enhanced with Institutional Access)
```
📄 CRISPR-Cas9 genome editing
   Authors: Zhang, F., et al.
   Year: 2014    Citations: 5432

   ✅ Open Access    📥 Access via Georgia Tech Library

   [Abstract ▼]
```

When you click "Access via Georgia Tech Library":
- **On Campus:** Opens directly to the full text
- **Off Campus:** Prompts for GT login, then opens full text
- **Open Access:** Shows green badge, direct access (no login)

## Code Implementation

### 1. Backend Enrichment (pipeline.py)

```python
# Lines 265-286: Institutional access integration
if self.institutional_manager and len(all_publications) > 0:
    logger.info("Enriching with institutional access information...")
    for pub in all_publications:
        # Check what access methods are available
        access_status = self.institutional_manager.check_access_status(pub)

        # Get the best access URL
        access_url = self.institutional_manager.get_access_url(pub)

        # Add to publication metadata
        pub.metadata["access_status"] = access_status
        pub.metadata["has_access"] = any(access_status.values())
        if access_url:
            pub.metadata["access_url"] = access_url
```

### 2. Dashboard Extraction (app.py)

```python
# Lines 307-325: Extract institutional access data
pub_dict = {
    # ... existing fields ...

    # Institutional access info (Week 4)
    "access_url": pub.metadata.get("access_url") if pub.metadata else None,
    "has_access": pub.metadata.get("has_access") if pub.metadata else False,
    "access_status": pub.metadata.get("access_status") if pub.metadata else {},
}
```

### 3. Dashboard Display (components.py)

```python
# Lines 622-640: Display institutional access UI
if result.get("has_access"):
    access_status = result.get("access_status", {})
    access_url = result.get("access_url")

    # Show access status badges
    access_col1, access_col2 = st.columns([1, 3])

    with access_col1:
        if access_status.get("unpaywall"):
            st.success("✅ Open Access")
        elif access_status.get("ezproxy"):
            st.info("🏛️ Institutional")

    with access_col2:
        if access_url:
            st.markdown(
                f"**[📥 Access via Georgia Tech Library]({access_url})**",
                help="Click to access through institutional subscription (EZProxy)"
            )
```

## Testing the Feature

### Test Case 1: Paywalled Article with Institutional Access

**Query:** "CRISPR-Cas9 genome editing Nature"

**Expected Results:**
- Publications with DOIs will have EZProxy URLs
- Badge shows "🏛️ Institutional"
- Clicking link opens EZProxy login (if off-campus) or direct access (if on-campus)

**Example Publication:**
```
Title: CRISPR-Cas9 genome editing
DOI: 10.1038/nbt.2808
Access URL: https://login.ezproxy.gatech.edu/login?url=https%3A%2F%2Fdoi.org%2F10.1038%2Fnbt.2808
Status: { "ezproxy": true, "unpaywall": false }
```

### Test Case 2: Open Access Article

**Query:** "COVID-19 transmission PLOS ONE"

**Expected Results:**
- Unpaywall finds free version
- Badge shows "✅ Open Access"
- Direct link to OA repository (no login needed)

**Example Publication:**
```
Title: COVID-19 transmission dynamics
DOI: 10.1371/journal.pone.0234567
Access URL: https://journals.plos.org/plosone/article/file?id=...
Status: { "unpaywall": true, "ezproxy": true }
```

### Test Case 3: PubMed Central (PMC) Article

**Query:** "cancer biomarkers PMC"

**Expected Results:**
- PMC ID detected
- Free access via PubMed Central
- Badge shows "✅ Open Access"

**Example Publication:**
```
Title: Novel cancer biomarkers
PMCID: PMC1234567
Access URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/pdf/
Status: { "pmc": true, "unpaywall": true }
```

## Access Flow Diagram

```
User clicks "Access via Georgia Tech Library"
    ↓
Browser opens: https://login.ezproxy.gatech.edu/login?url=...
    ↓
┌───────────────────────────────────────────────┐
│  Are you on Georgia Tech campus network?     │
└───────────────────────────────────────────────┘
         │                           │
     Yes │                           │ No
         ↓                           ↓
  Auto-authenticate         Display login page
         ↓                           ↓
         │                   Enter GT credentials
         │                           │
         └───────────┬───────────────┘
                     ↓
            Redirect to publisher
                     ↓
         Full text article/PDF opens
```

## Troubleshooting

### Issue: "Access via Georgia Tech Library" link not showing

**Cause:** Publication missing DOI or URL

**Solution:**
- Check if `pub.doi` or `pub.url` exists
- Enable more data sources (Semantic Scholar, Google Scholar)
- Some older publications may not have DOIs

### Issue: EZProxy asks for login even on campus

**Cause:** Not connected to GT network (WiFi/VPN)

**Solution:**
- Connect to GT WiFi or VPN
- Or log in with GT credentials when prompted

### Issue: "Open Access" badge but link broken

**Cause:** Unpaywall data may be stale

**Solution:**
- Try the EZProxy link instead (should always work)
- Contact library if persistent issue

### Issue: No institutional access for some journals

**Cause:** GT may not have subscription to that journal

**Solution:**
- Use OpenURL link resolver to see all options
- Request via Interlibrary Loan (ILL)
- Check Unpaywall for OA version

## Benefits

### For Researchers

✅ **One-Click Access:** No need to manually navigate library website
✅ **Automatic Detection:** System knows which articles you can access
✅ **Multiple Fallbacks:** Tries several methods to get you the article
✅ **Off-Campus Support:** EZProxy works from anywhere
✅ **Open Access First:** Prioritizes free legal versions

### For Institution

✅ **Usage Tracking:** Library can track journal access patterns
✅ **ROI Demonstration:** Shows value of subscriptions
✅ **Seamless Integration:** Works with existing authentication systems
✅ **Standards Compliant:** Uses OpenURL, EZProxy industry standards

## Future Enhancements

### Planned Features

1. **Link Resolver Menu:** Show all access options from SFX
2. **One-Time Passcode (OTP):** For users without VPN
3. **Persistent Links:** Save access URLs for later
4. **Multi-Institution Support:** Add ODU, other universities
5. **Access Analytics:** Track which articles accessed, success rate

### Possible Integrations

- **ORCID:** Link to researcher profile for auto-authentication
- **Shibboleth SSO:** Single sign-on across services
- **VPN Auto-Detection:** Automatically use best access method
- **Browser Extensions:** Right-click any DOI for GT access

## Technical Details

### SSL Bypass for Institutional Networks

**Note:** The SSL bypass (`PYTHONHTTPSVERIFY=0`) does NOT affect institutional access!

**Why?**
- SSL bypass: Python HTTP client certificate validation
- Institutional access: Network-layer authentication (EZProxy, Shibboleth)
- These are separate systems!

**Security:**
- Safe on trusted networks (GT campus)
- Only affects Python's `requests` library
- Does not disable browser SSL
- Does not affect EZProxy authentication

### EZProxy URL Encoding

URLs must be properly encoded to avoid breaking EZProxy:

```python
from urllib.parse import quote

target_url = "https://doi.org/10.1038/nature12345"
ezproxy_url = f"https://login.ezproxy.gatech.edu/login?url={quote(target_url, safe='')}"

# Result: https://login.ezproxy.gatech.edu/login?url=https%3A%2F%2Fdoi.org%2F10.1038%2Fnature12345
```

### Access Status Dictionary

```python
{
    "unpaywall": bool,  # Free OA version available
    "ezproxy": bool,    # Can access via EZProxy (has DOI/URL)
    "openurl": bool,    # Can use link resolver (has title)
    "pmc": bool,        # Available in PubMed Central
}
```

## API Reference

### InstitutionalAccessManager

```python
from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType
)

# Initialize
manager = InstitutionalAccessManager(
    institution=InstitutionType.GEORGIA_TECH,
    email="your.email@gatech.edu"  # For Unpaywall API
)

# Check access
access_status = manager.check_access_status(publication)
# Returns: {"unpaywall": True, "ezproxy": True, ...}

# Get access URL
access_url = manager.get_access_url(publication, prefer_method="ezproxy")
# Returns: "https://login.ezproxy.gatech.edu/login?url=..."

# Get PDF URL
pdf_url = manager.get_pdf_url(publication)
# Returns: Direct PDF URL if available
```

## Demonstration Checklist

✅ **Setup:**
- [ ] Services running (`./start_omics_oracle_ssl_bypass.sh`)
- [ ] Dashboard accessible at http://localhost:8502
- [ ] API accessible at http://localhost:8000

✅ **Test Searches:**
- [ ] Paywalled article: "CRISPR Nature 2014"
- [ ] Open access: "COVID-19 PLOS"
- [ ] PMC article: "cancer biomarkers PMC"

✅ **Verify Display:**
- [ ] "✅ Open Access" badge for OA articles
- [ ] "🏛️ Institutional" badge for subscribed journals
- [ ] "📥 Access via Georgia Tech Library" link present
- [ ] Link format: `https://login.ezproxy.gatech.edu/login?url=...`

✅ **Test Access:**
- [ ] Click access link
- [ ] Verify EZProxy page loads
- [ ] (On campus) Auto-redirect works
- [ ] (Off campus) Login prompt appears

## Summary

**Institutional access is now fully implemented and displayed in the dashboard!**

**Key Features:**
- ✅ Backend: EZProxy, OpenURL, Unpaywall integration
- ✅ Pipeline: Automatic metadata enrichment
- ✅ Dashboard: Visual badges and access links
- ✅ Configuration: Georgia Tech default, easy to extend

**User Experience:**
1. Search for publications
2. See access status (Open Access or Institutional)
3. Click "Access via Georgia Tech Library"
4. Authenticate if needed
5. Access full text/PDF

**Next Steps:**
- Test with various article types
- Collect user feedback
- Add more institutions (ODU, etc.)
- Enhance UI with more access method details

---

**Documentation Version:** 1.0
**Date:** 2024
**Author:** OmicsOracle Development Team
**Status:** ✅ COMPLETE - Ready for demonstration
