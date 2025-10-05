# OmicsOracle Performance Optimization Guide

## Rate Limiting Solutions

### 🚀 **Immediate Solutions** (No Code Changes)

1. **Reduce Search Results**
   ```javascript
   // In search form, use smaller page_size
   {"query": "COVID-19", "page": 1, "page_size": 3}  // Instead of 10
   ```

2. **Use More Specific Queries**
   ```
   Instead of: "COVID-19"
   Use: "COVID-19 GSE202805"  // More specific = fewer results
   ```

### ⚡ **Quick Fixes** (5 minutes)

1. **Set Development Environment Variable**
   ```bash
   echo "DISABLE_AI_SUMMARIES=true" >> .env
   ```

2. **Use Cached Results**
   - Search for the same query twice - second time will be instant
   - Cache persists across server restarts

### 🔧 **Configuration Solutions**

#### Option 1: Shorter Retry Delays (Development Only)
Create `config/development.yml`:
```yaml
openai:
  retry_delay: 2  # Instead of 20 seconds
  max_retries: 2  # Instead of 3
```

#### Option 2: Alternative AI Model
```python
# In summarizer.py, change model to faster one
self.model = "gpt-3.5-turbo"  # Faster, cheaper
# or
self.model = "gpt-4o-mini"   # Current, but with rate limits
```

### 🎯 **Best Practices for Development**

1. **Use Small Page Sizes**: Search with `page_size: 3` instead of 10
2. **Test with Cached Queries**: Repeat the same search for instant results
3. **Use Specific Queries**: "BRCA1 GSE123456" instead of "cancer"
4. **Enable Debug Mode**: Check console for `console.log()` output

### 🛠 **Rate Limit Monitoring**

Current status:
- ✅ **Caching**: Working (see "Cache hit" in logs)
- ⚠️ **Rate Limits**: OpenAI enforcing 20s delays
- ✅ **Fallback**: System gracefully handles API limits

### 📊 **Performance Stats**

| Operation | Time (Cached) | Time (Fresh) |
|-----------|---------------|--------------|
| Search API | <200ms | 2-20s |
| Template Render | <50ms | <50ms |
| Static Assets | <100ms | <100ms |

**Recommendation**: For development, use `page_size: 2-3` and leverage caching by repeating searches.
