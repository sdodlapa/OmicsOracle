/**
 * OmicsOracle Authentication Module
 * Handles user authentication, token management, and session persistence
 */

// ============================================
// Configuration
// ============================================

const AUTH_CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    TOKEN_KEY: 'omics_oracle_token',
    USER_KEY: 'omics_oracle_user',
    TOKEN_REFRESH_BUFFER: 5 * 60 * 1000, // 5 minutes before expiry
};

// ============================================
// Token Management
// ============================================

/**
 * Store authentication token
 */
function setToken(token) {
    localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, token);
}

/**
 * Get authentication token
 */
function getToken() {
    return localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
}

/**
 * Clear authentication token
 */
function clearToken() {
    localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
    localStorage.removeItem(AUTH_CONFIG.USER_KEY);
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    const token = getToken();
    if (!token) return false;

    try {
        return !isTokenExpired(token);
    } catch (e) {
        clearToken();
        return false;
    }
}

/**
 * Decode JWT token
 */
function decodeToken(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('Failed to decode token:', e);
        return null;
    }
}

/**
 * Check if token is expired
 */
function isTokenExpired(token) {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return true;

    const now = Date.now() / 1000;
    return decoded.exp < now;
}

/**
 * Get token expiry time in milliseconds
 */
function getTokenExpiry(token) {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return 0;
    return decoded.exp * 1000;
}

// ============================================
// User Management
// ============================================

/**
 * Store user data
 */
function setUser(user) {
    localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(user));
}

/**
 * Get stored user data
 */
function getUser() {
    const userStr = localStorage.getItem(AUTH_CONFIG.USER_KEY);
    if (!userStr) return null;

    try {
        return JSON.parse(userStr);
    } catch (e) {
        console.error('Failed to parse user data:', e);
        return null;
    }
}

// ============================================
// API Calls
// ============================================

/**
 * Login with email and password
 */
async function login(email, password) {
    const response = await fetch(`${AUTH_CONFIG.API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);

    // Load user data
    const user = await getCurrentUser();
    return { token: data.access_token, user };
}

/**
 * Register new user
 */
async function register(name, email, password) {
    const response = await fetch(`${AUTH_CONFIG.API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }

    return await response.json();
}

/**
 * Logout current user
 */
async function logout() {
    const token = getToken();

    if (token) {
        try {
            await fetch(`${AUTH_CONFIG.API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (e) {
            console.error('Logout error:', e);
        }
    }

    clearToken();
    window.location.href = '/login';
}

/**
 * Get current user data
 */
async function getCurrentUser() {
    const token = getToken();
    if (!token) return null;

    try {
        const response = await fetch(`${AUTH_CONFIG.API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            clearToken();
            return null;
        }

        const user = await response.json();
        setUser(user);
        return user;
    } catch (e) {
        console.error('Failed to get current user:', e);
        clearToken();
        return null;
    }
}

/**
 * Refresh authentication token
 */
async function refreshToken() {
    const token = getToken();
    if (!token) return null;

    try {
        const response = await fetch(`${AUTH_CONFIG.API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            clearToken();
            return null;
        }

        const data = await response.json();
        setToken(data.access_token);
        return data.access_token;
    } catch (e) {
        console.error('Token refresh failed:', e);
        clearToken();
        return null;
    }
}

// ============================================
// Protected API Calls
// ============================================

/**
 * Make authenticated API request
 */
async function authenticatedFetch(url, options = {}) {
    const token = getToken();

    if (!token) {
        throw new Error('Not authenticated');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized
    if (response.status === 401) {
        clearToken();
        window.location.href = '/login';
        throw new Error('Session expired. Please login again.');
    }

    return response;
}

// ============================================
// Route Protection
// ============================================

/**
 * Require authentication for current page
 */
function requireAuth() {
    if (!isAuthenticated()) {
        const currentPath = window.location.pathname;
        const redirect = encodeURIComponent(currentPath);
        window.location.href = `/login?redirect=${redirect}`;
        return false;
    }
    return true;
}

/**
 * Redirect to dashboard if already authenticated
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect') || '/dashboard';
        window.location.href = redirect;
        return true;
    }
    return false;
}

// ============================================
// Auto Token Refresh
// ============================================

/**
 * Setup automatic token refresh
 */
function setupTokenRefresh() {
    const token = getToken();
    if (!token) return;

    const expiresAt = getTokenExpiry(token);
    const now = Date.now();
    const timeUntilExpiry = expiresAt - now;
    const refreshAt = timeUntilExpiry - AUTH_CONFIG.TOKEN_REFRESH_BUFFER;

    if (refreshAt > 0) {
        setTimeout(async () => {
            console.log('Auto-refreshing token...');
            const newToken = await refreshToken();
            if (newToken) {
                console.log('Token refreshed successfully');
                setupTokenRefresh(); // Setup next refresh
            } else {
                console.log('Token refresh failed, redirecting to login');
                window.location.href = '/login';
            }
        }, refreshAt);
    } else {
        // Token expires soon or already expired
        refreshToken().then(newToken => {
            if (newToken) {
                setupTokenRefresh();
            }
        });
    }
}

// ============================================
// UI Helpers
// ============================================

/**
 * Display user profile in UI
 */
function displayUserProfile(elementId = 'user-profile') {
    const user = getUser();
    const element = document.getElementById(elementId);

    if (!element) return;

    if (user) {
        element.innerHTML = `
            <div class="user-info">
                <span class="user-name">${user.name}</span>
                <button onclick="logout()" class="btn-logout">Logout</button>
            </div>
        `;
        element.style.display = 'block';
    } else {
        element.style.display = 'none';
    }
}

/**
 * Show loading state
 */
function showLoading(buttonId, loadingText = 'Loading...') {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="loading-spinner"></span> ${loadingText}`;
    }
}

/**
 * Hide loading state
 */
function hideLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = false;
        button.textContent = button.dataset.originalText || 'Submit';
    }
}

// ============================================
// Initialization
// ============================================

/**
 * Initialize authentication on page load
 */
async function initAuth() {
    // Check if authenticated
    if (isAuthenticated()) {
        // Load user if not cached
        if (!getUser()) {
            await getCurrentUser();
        }

        // Display user profile
        displayUserProfile();

        // Setup auto token refresh
        setupTokenRefresh();
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

// ============================================
// Export for use in other modules
// ============================================

// Make functions globally available
window.OmicsAuth = {
    // Token management
    setToken,
    getToken,
    clearToken,
    isAuthenticated,
    decodeToken,
    isTokenExpired,

    // User management
    setUser,
    getUser,

    // API calls
    login,
    register,
    logout,
    getCurrentUser,
    refreshToken,
    authenticatedFetch,

    // Route protection
    requireAuth,
    redirectIfAuthenticated,

    // UI helpers
    displayUserProfile,
    showLoading,
    hideLoading,

    // Initialization
    initAuth,
    setupTokenRefresh
};
