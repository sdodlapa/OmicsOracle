# SSL Certificate Workaround for Institutional Networks

**Issue:** "SSL: CERTIFICATE_VERIFY_FAILED - self-signed certificate in certificate chain"

**Cause:** Your network (university/corporate) uses SSL inspection with self-signed certificates.

---

## Quick Fix (TESTING ONLY)

### Method 1: Environment Variable (Recommended for Testing)

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Disable SSL verification for Python (TESTING ONLY)
export PYTHONHTTPSVERIFY=0
```

Then restart terminal or:
```bash
source ~/.zshrc
```

### Method 2: Modify Start Script

Edit `start_omics_oracle.sh`:

```bash
#!/bin/bash
# ... existing code ...

# TESTING ONLY: Disable SSL verification
export PYTHONHTTPSVERIFY=0
export SSL_CERT_FILE=""

# Start servers
python scripts/run_api.py --port 8000 > /tmp/omics_api.log 2>&1 &
# ... rest of script ...
```

---

## Test Results

✅ **PubMed works with SSL disabled:**

```
Query: cancer genomics
Results: 5 publications found in 1.8s

1. HMGB1: From Molecular Functions to Clinical Applications... (2025)
   Medicinal research reviews - Relevance: 66.6/100

2. Senataxin regulates cisplatin resistance... (2025)
   iScience - Relevance: 61.8/100

3. Successful Treatment of Disseminated Carcinomatosis... (2025)
   Cureus - Relevance: 60.5/100
```

---

## Production Solutions

### Option 1: Install Institution Certificate (Best)

1. Get your institution's root CA certificate
   - Georgia Tech: https://oit.gatech.edu/certificates
   - Usually named something like `gatech-ca.crt`

2. Install to Python:
   ```bash
   # Find certifi location
   python -c "import certifi; print(certifi.where())"

   # Append institution cert
   cat ~/Downloads/gatech-ca.crt >> $(python -c "import certifi; print(certifi.where())")
   ```

### Option 2: Use System Certificates

```bash
# Tell Python to use macOS system certificates
export SSL_CERT_FILE=/etc/ssl/cert.pem
```

### Option 3: Proxy Configuration

If institution provides HTTP proxy:

```bash
export HTTP_PROXY=http://proxy.gatech.edu:8080
export HTTPS_PROXY=http://proxy.gatech.edu:8080
```

---

## Current Recommendation

For **immediate testing**, use Method 1 (environment variable):

```bash
# In terminal
export PYTHONHTTPSVERIFY=0

# Restart dashboard
./start_omics_oracle.sh
```

This will make PubMed work immediately!

---

## Testing Commands

### Test PubMed (SSL disabled):
```bash
PYTHONHTTPSVERIFY=0 python test_search_pubmed_only.py
```

### Test with dashboard:
```bash
PYTHONHTTPSVERIFY=0 ./start_omics_oracle.sh
```

Then open http://localhost:8502 and search!

---

## Why This Works

1. **Problem:** Georgia Tech network intercepts HTTPS with self-signed cert
2. **Python sees:** Certificate chain with untrusted self-signed cert
3. **Python fails:** Won't trust the connection
4. **Workaround:** `PYTHONHTTPSVERIFY=0` tells Python to skip verification
5. **Result:** PubMed works!

⚠️ **Security Note:**
- This disables SSL verification completely
- Only use on trusted networks (like campus network)
- For production, install proper certificates

---

## Next Steps

1. **Test now:**
   ```bash
   export PYTHONHTTPSVERIFY=0
   ./start_omics_oracle.sh
   ```

2. **Search in dashboard:**
   - Query: "JOint profiling of HiC and DNA methylation"
   - Database: ✓ PubMed only
   - Should work!

3. **For production:**
   - Contact Georgia Tech IT for root CA certificate
   - Install certificate properly
   - Remove `PYTHONHTTPSVERIFY=0`
