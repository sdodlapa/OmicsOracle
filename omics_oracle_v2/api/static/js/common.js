/**
 * OmicsOracle Common JavaScript Library
 * Shared utilities for all frontend pages
 */

// ============================================================================
// AUTHENTICATION & API
// ============================================================================

/**
 * Get authentication token from localStorage
 * @returns {string|null} JWT token or null if not authenticated
 */
function getAuthToken() {
    return localStorage.getItem('access_token');
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if user has valid token
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Make authenticated fetch request with auto token injection
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Response>} Fetch response
 */
async function authenticatedFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, {
        ...options,
        headers
    });
}

/**
 * Get current user profile
 * @returns {Promise<object|null>} User object or null if not authenticated
 */
async function getCurrentUser() {
    try {
        const response = await authenticatedFetch('/api/users/me');
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Failed to fetch user profile:', error);
        return null;
    }
}

/**
 * Logout user - clear token and redirect
 */
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// ============================================================================
// UI UTILITIES
// ============================================================================

/**
 * Show loading spinner on element
 * @param {HTMLElement} element - Element to show spinner on
 * @param {string} message - Loading message
 */
function showLoading(element, message = 'Loading...') {
    element.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">${message}</span>
            </div>
            <p class="mt-3 text-muted">${message}</p>
        </div>
    `;
}

/**
 * Show error message in element
 * @param {HTMLElement} element - Element to show error in
 * @param {string} message - Error message
 */
function showError(element, message) {
    element.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Show success message in element
 * @param {HTMLElement} element - Element to show success in
 * @param {string} message - Success message
 */
function showSuccess(element, message) {
    element.innerHTML = `
        <div class="alert alert-success" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i>
            ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date to human-readable string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    if (!date) return 'Unknown';
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Get time ago string from date
 * @param {string|Date} date - Date to calculate from
 * @returns {string} Time ago string (e.g., "2 days ago")
 */
function getTimeAgo(date) {
    if (!date) return 'Unknown';
    const d = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const seconds = Math.floor((now - d) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }

    return 'just now';
}

/**
 * Format duration in milliseconds to human-readable string
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration (e.g., "2.5s", "1m 30s")
 */
function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;

    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} True if successful
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
    }
}

// ============================================================================
// DATA FORMATTING
// ============================================================================

/**
 * Format large numbers with commas
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return num.toLocaleString('en-US');
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text with ellipsis
 */
function truncate(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Get quality class for score badge
 * @param {number} score - Relevance score (0-1)
 * @returns {string} Bootstrap badge class
 */
function getQualityClass(score) {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'primary';
    if (score >= 0.4) return 'warning';
    return 'secondary';
}

// ============================================================================
// FILE DOWNLOAD
// ============================================================================

/**
 * Download file from blob
 * @param {Blob} blob - File blob
 * @param {string} filename - Filename for download
 */
function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Export data as JSON file
 * @param {object} data - Data to export
 * @param {string} filename - Filename for download
 */
function exportAsJson(data, filename = 'data.json') {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    downloadFile(blob, filename);
}

/**
 * Export data as CSV file
 * @param {Array<object>} data - Array of objects to export
 * @param {string} filename - Filename for download
 */
function exportAsCsv(data, filename = 'data.csv') {
    if (!data || data.length === 0) {
        console.error('No data to export');
        return;
    }

    // Get headers from first object
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row =>
            headers.map(header => {
                const value = row[header] || '';
                // Escape quotes and wrap in quotes if contains comma/newline
                const escaped = String(value).replace(/"/g, '""');
                return /[",\n]/.test(escaped) ? `"${escaped}"` : escaped;
            }).join(',')
        )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    downloadFile(blob, filename);
}

// ============================================================================
// LOCAL STORAGE HELPERS
// ============================================================================

/**
 * Get item from localStorage with JSON parsing
 * @param {string} key - Storage key
 * @param {*} defaultValue - Default value if not found
 * @returns {*} Parsed value or default
 */
function getLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error(`Failed to get ${key} from localStorage:`, error);
        return defaultValue;
    }
}

/**
 * Set item in localStorage with JSON stringification
 * @param {string} key - Storage key
 * @param {*} value - Value to store
 */
function setLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error(`Failed to set ${key} in localStorage:`, error);
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    // Update UI based on auth status
    const authButtons = document.querySelectorAll('[data-requires-auth]');
    const isLoggedIn = isAuthenticated();

    authButtons.forEach(button => {
        if (!isLoggedIn) {
            button.disabled = true;
            button.title = 'Please log in to use this feature';
        }
    });

    // Add logout handlers
    document.querySelectorAll('[data-logout]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });
});

console.log('OmicsOracle common.js loaded successfully');
