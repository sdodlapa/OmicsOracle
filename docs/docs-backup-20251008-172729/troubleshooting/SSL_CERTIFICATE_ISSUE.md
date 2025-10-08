# SSL Certificate Issue - PubMed Search (macOS)

**Issue:** PubMed searches failing with SSL certificate verification error
**Platform:** macOS
**Date:** October 7, 2025

---

## Error Message

```
PubMed search error: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate chain
(_ssl.c:1006)>
```

---

## Root Cause

This is a **macOS-specific SSL certificate issue** with Python's SSL verification. It occurs when:
1. Python's SSL certificates are not properly installed
2. macOS system certificates are not accessible to Python
3. The Python installation is missing the `certifi` package

This is NOT a bug in OmicsOracle - it's a Python/macOS configuration issue.

---

## Solutions (Choose One)

### Solution 1: Install Python Certificates (Recommended)

Run the certificate installer that comes with Python:

```bash
# For Python 3.11 (adjust version as needed)
/Applications/Python\ 3.11/Install\ Certificates.command

# Or if installed via Homebrew:
$(brew --prefix python)/bin/pip install --upgrade certifi
```

### Solution 2: Install/Upgrade certifi Package

```bash
# In your virtual environment
source venv/bin/activate
pip install --upgrade certifi
```

### Solution 3: Use System Certificates (Quick Fix)

Add to your `.env` file:

```bash
# Disable SSL verification (NOT RECOMMENDED for production)
export SSL_CERT_FILE=""
export REQUESTS_CA_BUNDLE=""
```

### Solution 4: Manual Certificate Installation

```bash
# 1. Install OpenSSL certificates
brew install openssl

# 2. Link certificates
export SSL_CERT_FILE=$(python -m certifi)

# 3. Add to your shell profile (~/.zshrc or ~/.bash_profile)
echo 'export SSL_CERT_FILE=$(python -m certifi)' >> ~/.zshrc
source ~/.zshrc
```

---

## Verification

After applying a solution, test PubMed connectivity:

```python
python << 'EOF'
from Bio import Entrez
Entrez.email = "test@example.com"
handle = Entrez.esearch(db="pubmed", term="cancer", retmax=1)
print("✅ PubMed SSL connection successful!")
EOF
```

Expected output:
```
✅ PubMed SSL connection successful!
```

---

## Quick Test via Dashboard

1. Restart the dashboard:
   ```bash
   pkill -f streamlit
   ./start_omics_oracle.sh
   ```

2. Open http://localhost:8502

3. Try a search with:
   - Query: "cancer"
   - Database: PubMed
   - Max Results: 10

4. Check for SSL errors in logs:
   ```bash
   tail -f /tmp/omics_dashboard.log
   ```

---

## Related Issues

### Similar Error Messages

All these indicate the same SSL certificate problem:

```
SSL: CERTIFICATE_VERIFY_FAILED
SSLError: certificate verify failed
urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]
```

### Affected Services

This SSL issue can affect:
- ✅ PubMed API (Biopython/Entrez)
- ✅ Google Scholar scraping
- ✅ OpenAI API calls
- ✅ Any HTTPS requests from Python

---

## Prevention

### For New Python Installations

Always run certificate installation after installing Python:

```bash
# macOS Python installer includes this script
/Applications/Python\ 3.*/Install\ Certificates.command
```

### For Virtual Environments

Include certifi in requirements:

```bash
# requirements.txt
certifi>=2024.0.0
```

### For Production Deployments

Use system Python or containerization (Docker) which handles certificates properly.

---

## Why This Happens on macOS

1. **macOS doesn't include SSL certificates** in Python by default
2. **Python uses its own certificate store** (via certifi)
3. **Biopython/Entrez** requires valid SSL certificates
4. **Corporate/VPN networks** may inject their own certificates

---

## Troubleshooting

### Still Getting Errors?

1. **Check Python version:**
   ```bash
   python --version
   which python
   ```

2. **Verify certifi installation:**
   ```bash
   python -m certifi
   # Should print path to certificates
   ```

3. **Check environment variables:**
   ```bash
   echo $SSL_CERT_FILE
   echo $REQUESTS_CA_BUNDLE
   ```

4. **Test with requests library:**
   ```python
   import requests
   r = requests.get('https://www.ncbi.nlm.nih.gov')
   print(r.status_code)  # Should be 200
   ```

### Network-Specific Issues

If on corporate/university network:

```bash
# Check if proxy is interfering
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Bypass proxy for NCBI (if applicable)
export NO_PROXY="ncbi.nlm.nih.gov,*.ncbi.nlm.nih.gov"
```

---

## Permanent Fix (Recommended)

Add to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
# Python SSL Certificate Configuration
export SSL_CERT_FILE=$(python -m certifi)
export REQUESTS_CA_BUNDLE=$(python -m certifi)

# Optionally, set NCBI-specific config
export NCBI_EMAIL="your.email@example.com"
export NCBI_API_KEY="your_ncbi_api_key"
```

Then reload:
```bash
source ~/.zshrc
```

---

## For OmicsOracle Users

### Current Workaround

The dashboard will show PubMed errors but continue to work with Google Scholar:

```
⚠️ PubMed search failed: SSL error
✅ Google Scholar returned 10 results
```

### Full Fix

Follow **Solution 1** (Install Python Certificates) above, then restart:

```bash
# Stop servers
pkill -f omics_oracle

# Apply fix
/Applications/Python\ 3.11/Install\ Certificates.command

# Restart
./start_omics_oracle.sh
```

---

## Summary

| Issue | SSL Certificate Verification Failed |
|-------|-------------------------------------|
| **Cause** | Missing macOS Python SSL certificates |
| **Impact** | PubMed searches fail, other searches work |
| **Fix** | Install Python certificates or upgrade certifi |
| **Time** | < 5 minutes |
| **Permanent** | Yes, if added to shell profile |

---

## Additional Resources

- [Python SSL Documentation](https://docs.python.org/3/library/ssl.html)
- [Certifi Package](https://pypi.org/project/certifi/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [macOS Python Issues](https://bugs.python.org/issue28150)

---

**Next Steps:**
1. Choose a solution from above
2. Apply the fix
3. Restart OmicsOracle
4. Test PubMed search
5. If still failing, check troubleshooting section
