# Phase 4: Authentication & Production Features - Kickoff Plan

**Date:** October 8, 2025
**Status:** 🚀 READY TO START
**Duration:** 2 weeks (10 working days)
**Goal:** Add authentication and unlock 80%+ of backend features

---

## 🎯 Phase 4 Overview

**Primary Objective:** Add authentication support to integration layer and unlock all LLM & ML features

**Success Criteria:**
- ✅ Authentication working (login, token management, refresh)
- ✅ All AnalysisClient methods working (7/7)
- ✅ All MLClient methods working (6/6)
- ✅ Streamlit dashboard using integration layer
- ✅ LLM analysis visible in UI
- ✅ ML recommendations visible in UI

---

## 📅 Two-Week Plan

### **Week 1: Authentication & API Validation**

#### **Day 1-2: Authentication Implementation (16 hours)**

**Task 1.1: Add Auth to Integration Layer (8 hours)**

Create `omics_oracle_v2/integration/auth.py`:
```python
"""
Authentication client for OmicsOracle integration layer
"""
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Auth token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None


class AuthClient:
    """
    Authentication client for integration layer.
    
    Handles:
    - User registration
    - Login/logout
    - Token management
    - Auto-refresh
    - Token storage
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[TokenResponse] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> dict:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            full_name: User's full name
            
        Returns:
            User info
        """
        response = await self._client.post(
            f"{self.base_url}/api/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def login(self, username: str, password: str) -> TokenResponse:
        """
        Login and get access token.
        
        Args:
            username: Email address
            password: User password
            
        Returns:
            TokenResponse with access token
        """
        response = await self._client.post(
            f"{self.base_url}/api/auth/login",
            data={  # Note: form data, not JSON
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self._token = TokenResponse(**data)
        
        # Calculate expiration
        self._token_expires_at = datetime.utcnow() + timedelta(
            seconds=self._token.expires_in
        )
        
        return self._token
    
    async def logout(self) -> None:
        """Logout and invalidate token."""
        if self._token:
            await self._client.post(
                f"{self.base_url}/api/auth/logout",
                headers={"Authorization": f"Bearer {self._token.access_token}"}
            )
            self._token = None
            self._token_expires_at = None
    
    async def refresh_token(self) -> TokenResponse:
        """
        Refresh access token.
        
        Returns:
            New TokenResponse
        """
        if not self._token or not self._token.refresh_token:
            raise ValueError("No refresh token available")
        
        response = await self._client.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self._token.refresh_token}
        )
        response.raise_for_status()
        
        data = response.json()
        self._token = TokenResponse(**data)
        self._token_expires_at = datetime.utcnow() + timedelta(
            seconds=self._token.expires_in
        )
        
        return self._token
    
    def get_token(self) -> Optional[str]:
        """Get current access token."""
        return self._token.access_token if self._token else None
    
    def is_token_expired(self) -> bool:
        """Check if token is expired or about to expire."""
        if not self._token_expires_at:
            return True
        
        # Consider expired if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        return datetime.utcnow() + buffer >= self._token_expires_at
    
    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid token, refreshing if needed.
        
        Returns:
            Valid access token
        """
        if not self._token:
            raise ValueError("Not logged in")
        
        if self.is_token_expired():
            await self.refresh_token()
        
        return self._token.access_token


# Convenience function for quick auth
async def create_test_user(
    email: str = "test@omicsoracle.com",
    password: str = "test123",
    full_name: str = "Test User"
) -> str:
    """
    Create test user and return access token.
    
    Args:
        email: User email
        password: User password  
        full_name: User's full name
        
    Returns:
        Access token
    """
    async with AuthClient() as auth:
        # Try to register (might fail if exists)
        try:
            await auth.register(email, password, full_name)
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 400:  # Already exists
                raise
        
        # Login
        token_response = await auth.login(email, password)
        return token_response.access_token
```

**Task 1.2: Update Base Client for Auth (4 hours)**

Modify `omics_oracle_v2/integration/base_client.py`:
```python
class APIClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_version: str = "v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_ttl: int = 300,
        api_key: Optional[str] = None,
        auth_client: Optional[AuthClient] = None,  # NEW!
    ):
        # ... existing code ...
        self.auth_client = auth_client
        
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {
                "User-Agent": "OmicsOracle-Integration-Layer/2.0.0",
                "Accept": "application/json",
            }

            # Add auth header
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.auth_client:
                # Auto-refresh token if needed
                token = await self.auth_client.ensure_valid_token()
                headers["Authorization"] = f"Bearer {token}"

            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
            )
```

**Task 1.3: Create Auth Test Script (4 hours)**

Create `test_authentication.py`:
```python
"""
Test authentication flow
"""
import asyncio
from omics_oracle_v2.integration.auth import AuthClient, create_test_user
from omics_oracle_v2.integration import AnalysisClient, MLClient


async def test_auth():
    """Test complete authentication flow"""
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION")
    print("="*80)
    
    # Test 1: Register and login
    print("\n[TEST 1] Register and login")
    async with AuthClient() as auth:
        try:
            # Register
            user = await auth.register(
                email="phase4test@omicsoracle.com",
                password="secure123",
                full_name="Phase 4 Tester"
            )
            print(f"  ✅ Registered: {user['email']}")
        except Exception as e:
            print(f"  ⚠️ User exists: {e}")
        
        # Login
        token = await auth.login("phase4test@omicsoracle.com", "secure123")
        print(f"  ✅ Logged in")
        print(f"  Token: {token.access_token[:20]}...")
        print(f"  Expires in: {token.expires_in} seconds")
    
    # Test 2: Use token with clients
    print("\n[TEST 2] Use token with authenticated clients")
    token = await create_test_user()
    
    async with AnalysisClient(api_key=token) as client:
        print("  ✅ AnalysisClient initialized with token")
    
    async with MLClient(api_key=token) as client:
        print("  ✅ MLClient initialized with token")
    
    print("\n" + "="*80)
    print("AUTHENTICATION TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_auth())
```

---

#### **Day 3-4: LLM Features Validation (16 hours)**

**Task 2.1: Test LLM Analysis (4 hours)**

Create `test_llm_features.py`:
```python
"""
Test LLM analysis features with authentication
"""
import asyncio
from omics_oracle_v2.integration import SearchClient, AnalysisClient
from omics_oracle_v2.integration.auth import create_test_user


async def test_llm_features():
    """Test all LLM features"""
    print("\n" + "="*80)
    print("TESTING LLM FEATURES (AUTHENTICATED)")
    print("="*80)
    
    # Get auth token
    token = await create_test_user()
    print(f"✅ Authenticated")
    
    # Get search results for context
    async with SearchClient() as search:
        results = await search.search("CRISPR gene editing", max_results=5)
        print(f"✅ Got {len(results.results)} search results")
    
    async with AnalysisClient(api_key=token) as analysis:
        # Test 1: LLM Analysis
        print("\n[TEST 1] LLM Analysis")
        insights = await analysis.analyze_with_llm(
            query="CRISPR gene editing",
            results=results.results[:3]
        )
        print(f"  ✅ Analysis complete!")
        print(f"  Overview: {insights.overview[:200]}...")
        print(f"  Key findings: {len(insights.key_findings)}")
        print(f"  Research gaps: {len(insights.research_gaps)}")
        
        # Test 2: Q&A
        print("\n[TEST 2] Q&A System")
        answer = await analysis.ask_question(
            question="What are the main applications of CRISPR?",
            context=results.results[:3]
        )
        print(f"  ✅ Answer received!")
        print(f"  Answer: {answer.answer[:200]}...")
        print(f"  Confidence: {answer.confidence}")
        
        # Test 3: Report Generation
        print("\n[TEST 3] Report Generation")
        report = await analysis.generate_report(
            query="CRISPR",
            results=results.results[:3]
        )
        print(f"  ✅ Report generated!")
        print(f"  Report length: {len(report)} characters")
    
    print("\n" + "="*80)
    print("LLM FEATURES TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_llm_features())
```

**Task 2.2: Create Adapters for LLM Responses (8 hours)**

Update `omics_oracle_v2/integration/adapters.py`:
```python
def adapt_analysis_response(backend_response: Dict[str, Any]) -> AnalysisResponse:
    """
    Adapt backend analysis response to integration layer format.
    
    Backend format (to be determined after testing):
    {
        "analysis": "...",
        "key_points": [...],
        "gaps": [...],
        "confidence": 0.85
    }
    
    Integration layer format:
    AnalysisResponse(
        overview="...",
        key_findings=[...],
        research_gaps=[...],
        confidence=0.85
    )
    """
    # TODO: Implement after seeing actual backend response
    return AnalysisResponse(**backend_response)


def adapt_qa_response(backend_response: Dict[str, Any]) -> QAResponse:
    """Adapt Q&A response."""
    # TODO: Implement after testing
    return QAResponse(**backend_response)
```

**Task 2.3: Document Findings (4 hours)**

Create validation report documenting:
- What works with auth
- What still needs adapters
- Performance metrics
- Any issues found

---

#### **Day 5: ML Features Validation (8 hours)**

**Task 3.1: Test All ML Endpoints (6 hours)**

Create `test_ml_features_authenticated.py`:
```python
"""
Test ML features with authentication
"""
import asyncio
from omics_oracle_v2.integration import SearchClient, MLClient
from omics_oracle_v2.integration.auth import create_test_user


async def test_ml_features():
    """Test all ML features"""
    print("\n" + "="*80)
    print("TESTING ML FEATURES (AUTHENTICATED)")
    print("="*80)
    
    # Get auth token
    token = await create_test_user()
    print(f"✅ Authenticated")
    
    # Get search results for seed papers
    async with SearchClient() as search:
        results = await search.search("machine learning genomics", max_results=5)
        seed_papers = [r.id for r in results.results[:2] if r.id]
        print(f"✅ Got {len(seed_papers)} seed papers")
    
    async with MLClient(api_key=token) as ml:
        # Test 1: Recommendations
        print("\n[TEST 1] Paper Recommendations")
        recs = await ml.get_recommendations(seed_papers=seed_papers, count=5)
        print(f"  ✅ Got {len(recs.recommendations)} recommendations")
        
        # Test 2: Citation Prediction
        print("\n[TEST 2] Citation Prediction")
        if results.results:
            pred = await ml.predict_citations(
                pub_id=results.results[0].id,
                years_ahead=5
            )
            print(f"  ✅ Predicted citations: {pred.predicted_count}")
        
        # Test 3: Trending Topics
        print("\n[TEST 3] Trending Topics")
        trends = await ml.get_trending_topics()
        print(f"  ✅ Got {len(trends.topics)} trending topics")
        
        # Test 4: Emerging Authors
        print("\n[TEST 4] Emerging Authors")
        authors = await ml.get_emerging_authors()
        print(f"  ✅ Got {len(authors.authors)} emerging authors")
    
    print("\n" + "="*80)
    print("ML FEATURES TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_ml_features())
```

**Task 3.2: Create ML Response Adapters (2 hours)**

Add to `adapters.py`:
```python
def adapt_recommendation_response(backend_response: Dict[str, Any]) -> RecommendationResponse:
    """Adapt recommendation response."""
    # TODO: Implement after testing
    return RecommendationResponse(**backend_response)


def adapt_prediction_response(backend_response: Dict[str, Any]) -> PredictionResponse:
    """Adapt prediction response."""
    # TODO: Implement after testing
    return PredictionResponse(**backend_response)
```

---

### **Week 2: Dashboard Integration**

#### **Day 6-7: Update Streamlit Dashboard (16 hours)**

**Task 4.1: Add Authentication to Dashboard (6 hours)**

Create new file `omics_oracle_v2/web/pages/login.py`:
```python
"""
Login page for Streamlit dashboard
"""
import streamlit as st
import asyncio
from omics_oracle_v2.integration.auth import AuthClient


def login_page():
    """Display login page"""
    st.title("🔐 OmicsOracle Login")
    
    # Check if already logged in
    if "access_token" in st.session_state:
        st.success("✅ Already logged in!")
        if st.button("Logout"):
            del st.session_state["access_token"]
            st.rerun()
        return
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            async def do_login():
                async with AuthClient() as auth:
                    token = await auth.login(email, password)
                    return token.access_token
            
            try:
                token = asyncio.run(do_login())
                st.session_state["access_token"] = token
                st.success("✅ Logged in successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
    
    # Registration link
    st.markdown("---")
    st.markdown("Don't have an account? Register below:")
    
    with st.expander("Register New Account"):
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_name = st.text_input("Full Name")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                async def do_register():
                    async with AuthClient() as auth:
                        await auth.register(reg_email, reg_password, reg_name)
                        token = await auth.login(reg_email, reg_password)
                        return token.access_token
                
                try:
                    token = asyncio.run(do_register())
                    st.session_state["access_token"] = token
                    st.success("✅ Registered and logged in!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration failed: {e}")


if __name__ == "__main__":
    login_page()
```

**Task 4.2: Add LLM Analysis Tab (6 hours)**

Update `omics_oracle_v2/web/main.py` to add new tab:
```python
# In main dashboard
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Search",
    "📊 Analytics", 
    "🤖 AI Analysis",  # NEW!
    "🧬 Biomarkers"
])

with tab3:
    st.header("🤖 AI-Powered Analysis")
    
    if "access_token" not in st.session_state:
        st.warning("⚠️ Please login to use AI features")
        st.page_link("pages/login.py", label="Go to Login")
    else:
        # LLM analysis interface
        if "search_results" in st.session_state:
            if st.button("🧠 Analyze with AI"):
                with st.spinner("Analyzing with LLM..."):
                    async def analyze():
                        async with AnalysisClient(
                            api_key=st.session_state["access_token"]
                        ) as client:
                            return await client.analyze_with_llm(
                                query=st.session_state["last_query"],
                                results=st.session_state["search_results"][:10]
                            )
                    
                    insights = asyncio.run(analyze())
                    
                    # Display results
                    st.success("✅ Analysis complete!")
                    
                    st.subheader("📝 Overview")
                    st.write(insights.overview)
                    
                    st.subheader("🔑 Key Findings")
                    for finding in insights.key_findings:
                        st.markdown(f"- {finding}")
                    
                    st.subheader("🔬 Research Gaps")
                    for gap in insights.research_gaps:
                        st.markdown(f"- {gap}")
                    
                    st.subheader("💡 Recommendations")
                    for rec in insights.recommendations:
                        st.markdown(f"- {rec}")
        else:
            st.info("Run a search first to analyze results")
```

**Task 4.3: Add ML Recommendations Sidebar (4 hours)**

Add to dashboard sidebar:
```python
# In sidebar
if "access_token" in st.session_state and "search_results" in st.session_state:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Recommended Papers")
    
    if st.sidebar.button("Get Recommendations"):
        with st.spinner("Finding similar papers..."):
            seed_papers = [r.id for r in st.session_state["search_results"][:3] if r.id]
            
            async def get_recs():
                async with MLClient(
                    api_key=st.session_state["access_token"]
                ) as client:
                    return await client.get_recommendations(
                        seed_papers=seed_papers,
                        count=5
                    )
            
            recs = asyncio.run(get_recs())
            
            for rec in recs.recommendations[:5]:
                st.sidebar.markdown(f"**{rec.publication.title}**")
                st.sidebar.caption(f"Score: {rec.score:.2f}")
                st.sidebar.markdown("---")
```

---

#### **Day 8-9: Testing & Polish (16 hours)**

**Task 5.1: End-to-End Testing (8 hours)**
- Test complete workflow: Login → Search → Analyze → Recommend
- Test error handling
- Test token refresh
- Load testing

**Task 5.2: Documentation Updates (4 hours)**
- Update README with authentication instructions
- Create user guide for new features
- Update API documentation

**Task 5.3: Performance Optimization (4 hours)**
- Add caching for LLM responses
- Optimize token refresh logic
- Add request debouncing

---

#### **Day 10: Final Validation & Documentation (8 hours)**

**Task 6.1: Create Phase 4 Validation Report (4 hours)**
- Document all working features
- Performance benchmarks
- Known issues and limitations
- Recommendations for Phase 5

**Task 6.2: Update Project Documentation (4 hours)**
- Update main README
- Create Phase 5 kickoff plan
- Document lessons learned

---

## 📊 Success Metrics

### Week 1 Goals:
- ✅ Authentication working (register, login, token management)
- ✅ All AnalysisClient methods tested with auth
- ✅ All MLClient methods tested with auth
- ✅ Response adapters created for all endpoints
- ✅ Comprehensive test coverage

### Week 2 Goals:
- ✅ Streamlit dashboard has login page
- ✅ LLM analysis visible in UI
- ✅ ML recommendations visible in UI
- ✅ Q&A interface working
- ✅ Complete end-to-end workflow tested

---

## 🎯 Expected Outcomes

### By End of Phase 4:
1. **Authentication** ✅
   - Users can register and login
   - Tokens automatically managed
   - Auto-refresh working

2. **Integration Layer** ✅
   - All 19 client methods working
   - Response adapters for all endpoints
   - Error handling comprehensive

3. **Dashboard** ✅
   - 89% of backend features accessible
   - LLM analysis displayed
   - ML recommendations shown
   - Better user experience

4. **Documentation** ✅
   - Complete user guide
   - API documentation updated
   - Phase 5 plan ready

---

## 💡 Quick Start Commands

### Push Phase 3 to Remote:
```bash
git push origin phase-4-production-features
# (Enter SSH passphrase when prompted)
```

### Start Phase 4:
```bash
# Create auth implementation
code omics_oracle_v2/integration/auth.py

# Create test script
code test_authentication.py

# Run tests
python test_authentication.py
```

---

## 🚨 Potential Blockers

1. **Backend Auth Might Require Changes**
   - Solution: Work with backend team or adjust integration layer

2. **Schema Mismatches in LLM Responses**
   - Solution: Create adapters (like we did for SearchClient)

3. **Token Management Complexity**
   - Solution: Keep it simple - auto-refresh on expiry

4. **Streamlit Async Handling**
   - Solution: Use `asyncio.run()` wrapper (already proven)

---

## 📈 Phase 4 vs Phase 3

| Aspect | Phase 3 | Phase 4 |
|--------|---------|---------|
| Duration | 4 hours | 2 weeks |
| Files Changed | 135 | ~50 expected |
| New Features | 0 (validation only) | Authentication, LLM UI, ML UI |
| Backend Coverage | 30% | 80%+ |
| User Impact | None (internal) | High (new features visible) |
| Complexity | Medium | High |

---

## 🎯 Definition of Done

Phase 4 is complete when:
- ✅ User can login to dashboard
- ✅ User can run LLM analysis on search results
- ✅ User can see ML recommendations
- ✅ User can ask questions via Q&A
- ✅ All features work end-to-end
- ✅ Documentation is complete
- ✅ Tests pass
- ✅ Code is committed and pushed

---

**Phase 4 Status:** 🚀 READY TO START
**Estimated Completion:** October 22, 2025 (2 weeks from now)
**Confidence:** 90% (high - Phase 3 validation proved the approach)

**Let's build this!** 💪
