# 📊 Dashboard Display Guide - Institutional Access

## Before vs After Comparison

### BEFORE (Without Institutional Access)
```
┌─────────────────────────────────────────────────────────────────┐
│ 📄 Search Results                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. CRISPR-Cas9 genome editing                                   │
│    Authors: Zhang, F., Wen, Y., Guo, X.                        │
│    Year: 2014          Citations: 5432                         │
│                                                                 │
│    [Abstract ▼]                                                │
│    View Source                                                 │
│                                                                 │
│ ─────────────────────────────────────────────────────────────  │
│                                                                 │
│ 2. COVID-19 transmission dynamics                               │
│    Authors: Smith, J., Doe, A.                                 │
│    Year: 2020          Citations: 234                          │
│                                                                 │
│    [Abstract ▼]                                                │
│    View Source                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Issues:**
- ❌ No indication if article is accessible
- ❌ No institutional access links
- ❌ Users must manually navigate to library website
- ❌ No open access detection

---

### AFTER (With Institutional Access) ✨

```
┌─────────────────────────────────────────────────────────────────┐
│ 📄 Search Results                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. CRISPR-Cas9 genome editing                                   │
│    Authors: Zhang, F., Wen, Y., Guo, X.                        │
│    Year: 2014          Citations: 5432                         │
│                                                                 │
│    ┌───────────────┬─────────────────────────────────────────┐ │
│    │🏛️ Institutional│ 📥 Access via Georgia Tech Library     │ │
│    └───────────────┴─────────────────────────────────────────┘ │
│                                                                 │
│    [Abstract ▼]                                                │
│                                                                 │
│ ─────────────────────────────────────────────────────────────  │
│                                                                 │
│ 2. COVID-19 transmission dynamics                               │
│    Authors: Smith, J., Doe, A.                                 │
│    Year: 2020          Citations: 234                          │
│                                                                 │
│    ┌───────────────┬─────────────────────────────────────────┐ │
│    │✅ Open Access │ 📥 Access via Georgia Tech Library     │ │
│    └───────────────┴─────────────────────────────────────────┘ │
│                                                                 │
│    [Abstract ▼]                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Improvements:**
- ✅ Visual badges show access type
- ✅ One-click access through institutional subscription
- ✅ Open access articles clearly marked
- ✅ EZProxy authentication handled automatically

---

## Badge Types

### 🏛️ Institutional Access (Blue)
- **When shown:** Article accessible via Georgia Tech subscription
- **Access method:** EZProxy authentication
- **User action:** Click link → Log in (if off-campus) → Access article
- **Example:** Nature, Science, Cell journals

### ✅ Open Access (Green)
- **When shown:** Free, legal version available
- **Access method:** Direct link to repository/publisher
- **User action:** Click link → Access article (no login!)
- **Example:** PLOS, BMC, PubMed Central articles

### 📥 Access Link
- **Format:** "Access via Georgia Tech Library"
- **Action:** Opens EZProxy URL or direct OA link
- **Tooltip:** "Click to access through institutional subscription (EZProxy)"

---

## Real Examples

### Example 1: High-Impact Paywalled Article

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Multiplex genome engineering using CRISPR/Cas systems                │
│    Authors: Cong, L., Ran, F. A., Cox, D., et al.                      │
│    Journal: Science   Year: 2013   Citations: 8,456                    │
│                                                                         │
│    ┌────────────────┬──────────────────────────────────────────────┐   │
│    │ 🏛️ Institutional│  📥 Access via Georgia Tech Library         │   │
│    └────────────────┴──────────────────────────────────────────────┘   │
│                                                                         │
│    [Abstract ▼]                                                        │
│    CRISPR/Cas systems provide bacteria and archaea with adaptive      │
│    immunity against viruses and plasmids...                           │
│                                                                         │
│    Click "Access via Georgia Tech Library" to open:                    │
│    https://login.ezproxy.gatech.edu/login?url=https://doi.org/10.1126/science.1231143
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**User Flow:**
1. Sees "🏛️ Institutional" badge → Knows GT has subscription
2. Clicks "📥 Access via Georgia Tech Library"
3. **On Campus:** Auto-redirects to Science article (full PDF)
4. **Off Campus:** Login page → Enter GT credentials → Full article access

---

### Example 2: Open Access Article

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. The COVID-19 pandemic and its impact on global health               │
│    Authors: Wang, L., Zhang, Y., Li, M.                                │
│    Journal: PLOS ONE   Year: 2020   Citations: 342                     │
│                                                                         │
│    ┌────────────────┬──────────────────────────────────────────────┐   │
│    │ ✅ Open Access │  📥 Access via Georgia Tech Library         │   │
│    └────────────────┴──────────────────────────────────────────────┘   │
│                                                                         │
│    [Abstract ▼]                                                        │
│    The COVID-19 pandemic has dramatically affected healthcare         │
│    systems worldwide. This study examines...                          │
│                                                                         │
│    Click "Access via Georgia Tech Library" to open:                    │
│    https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0234567
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**User Flow:**
1. Sees "✅ Open Access" badge → Knows it's free!
2. Clicks "📥 Access via Georgia Tech Library"
3. **Any Location:** Direct access to full PDF (no login needed)

---

### Example 3: PubMed Central Article

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. Novel biomarkers for early cancer detection                         │
│    Authors: Martinez, J., Chen, X., Kim, S.                            │
│    Journal: Nature Medicine   Year: 2021   PMCID: PMC8123456           │
│                                                                         │
│    ┌────────────────┬──────────────────────────────────────────────┐   │
│    │ ✅ Open Access │  📥 Access via Georgia Tech Library         │   │
│    └────────────────┴──────────────────────────────────────────────┘   │
│                                                                         │
│    [Abstract ▼]                                                        │
│    Early detection of cancer remains a critical challenge in          │
│    clinical oncology. We identified novel protein biomarkers...       │
│                                                                         │
│    Click "Access via Georgia Tech Library" to open:                    │
│    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8123456/pdf/           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**User Flow:**
1. Sees "✅ Open Access" badge + PMCID
2. Clicks access link
3. Opens PubMed Central free PDF (no subscription or login needed)

---

## UI Components Breakdown

### 1. Access Status Badge (Left Column)

**Component:** `st.success()` or `st.info()`

**Colors:**
- 🟢 **Green** (`st.success`) → Open Access
- 🔵 **Blue** (`st.info`) → Institutional Access

**Code:**
```python
if access_status.get("unpaywall"):
    st.success("✅ Open Access")
elif access_status.get("ezproxy"):
    st.info("🏛️ Institutional")
```

---

### 2. Access Link (Right Column)

**Component:** Markdown link in Streamlit

**Format:**
```python
st.markdown(
    f"**[📥 Access via Georgia Tech Library]({access_url})**",
    help="Click to access through institutional subscription (EZProxy)"
)
```

**Rendered as:**
```
📥 Access via Georgia Tech Library
   ↑ Bold, clickable link
   ↑ Tooltip on hover
```

---

### 3. Layout Structure

**Code:**
```python
# Create two columns: badge + link
access_col1, access_col2 = st.columns([1, 3])

with access_col1:
    # Show badge
    if access_status.get("unpaywall"):
        st.success("✅ Open Access")
    elif access_status.get("ezproxy"):
        st.info("🏛️ Institutional")

with access_col2:
    # Show access link
    if access_url:
        st.markdown(
            f"**[📥 Access via Georgia Tech Library]({access_url})**",
            help="Click to access through institutional subscription (EZProxy)"
        )
```

**Result:**
```
┌───────────────┬─────────────────────────────────────────┐
│🏛️ Institutional│ 📥 Access via Georgia Tech Library     │
└───────────────┴─────────────────────────────────────────┘
     25% width              75% width
```

---

## Access URL Examples

### EZProxy URL Format

**Original DOI:** `10.1038/nbt.2808`

**Generated URL:**
```
https://login.ezproxy.gatech.edu/login?url=https%3A%2F%2Fdoi.org%2F10.1038%2Fnbt.2808
                                        └─────────────────────────────────┘
                                           URL-encoded target (DOI link)
```

**Breakdown:**
- `https://login.ezproxy.gatech.edu/login` - EZProxy login endpoint
- `?url=` - Query parameter for target URL
- `https%3A%2F%2Fdoi.org%2F10.1038%2Fnbt.2808` - Encoded DOI URL
  - `https://` → `https%3A%2F%2F`
  - `/` → `%2F`

---

### OpenURL Format (Alternative)

**For Link Resolver:**
```
https://buzzport.gatech.edu/sfx_local?
  sid=omics_oracle&
  title=CRISPR-Cas9+genome+editing&
  doi=10.1038/nbt.2808&
  date=2014&
  ...
```

**Shows:**
- All access options (databases, repositories, subscriptions)
- PDF links
- HTML full-text links
- Request via ILL option

---

## User Experience Flow

### Flow 1: On-Campus Access (Auto-Login)

```
User clicks "Access via Georgia Tech Library"
    ↓
Browser: https://login.ezproxy.gatech.edu/login?url=...
    ↓
EZProxy detects: Georgia Tech campus IP
    ↓
Auto-authenticates (no login prompt)
    ↓
Redirects to: https://doi.org/10.1038/nbt.2808
    ↓
Publisher recognizes: Georgia Tech subscription
    ↓
Shows: Full article + PDF download button
```

**Time:** ~2 seconds (instant!)

---

### Flow 2: Off-Campus Access (Manual Login)

```
User clicks "Access via Georgia Tech Library"
    ↓
Browser: https://login.ezproxy.gatech.edu/login?url=...
    ↓
EZProxy detects: Non-GT IP
    ↓
Shows: Georgia Tech login page
    ↓
User enters: GT username + password
    ↓
EZProxy authenticates via Shibboleth
    ↓
Redirects to: https://doi.org/10.1038/nbt.2808
    ↓
Publisher recognizes: Georgia Tech subscription
    ↓
Shows: Full article + PDF download button
```

**Time:** ~10-15 seconds (one-time login)

---

### Flow 3: Open Access (Direct Access)

```
User clicks "Access via Georgia Tech Library"
    ↓
Browser: https://journals.plos.org/plosone/article/...
    ↓
Opens: Publisher's free version
    ↓
Shows: Full article + PDF download (no login!)
```

**Time:** ~1 second (immediate!)

---

## Technical Implementation

### Dashboard Code Flow

```python
# 1. Pipeline enriches publication
pub.metadata["access_url"] = "https://login.ezproxy.gatech.edu/..."
pub.metadata["has_access"] = True
pub.metadata["access_status"] = {"ezproxy": True, ...}

# 2. Dashboard extracts metadata (app.py)
pub_dict = {
    "title": pub.title,
    "access_url": pub.metadata.get("access_url"),
    "has_access": pub.metadata.get("has_access"),
    "access_status": pub.metadata.get("access_status"),
}

# 3. ResultsPanel displays (components.py)
if result.get("has_access"):
    # Show badge + link
    if access_status.get("unpaywall"):
        st.success("✅ Open Access")
    elif access_status.get("ezproxy"):
        st.info("🏛️ Institutional")
    
    st.markdown(f"**[📥 Access via Georgia Tech Library]({access_url})**")
```

---

## Troubleshooting Guide

### Issue: Badge not showing

**Cause:** Publication missing DOI or URL

**Debug:**
```python
print(f"DOI: {pub.doi}")
print(f"URL: {pub.url}")
print(f"Access status: {pub.metadata.get('access_status')}")
```

**Solution:** Ensure publication has at least one identifier

---

### Issue: "Access via Georgia Tech Library" link doesn't work

**Cause:** User not on GT network or VPN

**Solution:**
1. Connect to GT WiFi (if on campus)
2. Use GT VPN (if off campus)
3. Enter GT credentials when prompted

---

### Issue: EZProxy login loop

**Cause:** Browser cookies/cache issue

**Solution:**
1. Clear browser cookies for `ezproxy.gatech.edu`
2. Try incognito/private browsing
3. Contact GT library if persistent

---

## Demo Checklist

✅ **Setup:**
- [ ] Services running: `./start_omics_oracle_ssl_bypass.sh`
- [ ] Dashboard accessible: http://localhost:8502
- [ ] Test script passed: `python test_institutional_access.py`

✅ **Visual Verification:**
- [ ] Search returns results with access badges
- [ ] "🏛️ Institutional" badge visible for paywalled articles
- [ ] "✅ Open Access" badge visible for OA articles
- [ ] "📥 Access via Georgia Tech Library" link present
- [ ] Link has hover tooltip

✅ **Functional Testing:**
- [ ] Click access link opens new tab
- [ ] EZProxy URL format correct
- [ ] On-campus: Auto-redirect works
- [ ] Off-campus: Login prompt appears

---

## Summary

**Dashboard now shows:**
1. ✅ Visual badges for access type (OA vs Institutional)
2. ✅ One-click access links with EZProxy authentication
3. ✅ Clear indication of which articles are accessible
4. ✅ Seamless integration with existing search results

**User benefits:**
- 🚀 Faster access to full-text articles
- 🎯 Clear visibility of access options
- 🔐 Secure authentication through GT systems
- 💰 Maximizes value of institutional subscriptions

**Status:** ✅ COMPLETE - Ready for demonstration!

---

**Last Updated:** 2024  
**View in Dashboard:** http://localhost:8502  
**Test Command:** `python test_institutional_access.py`
