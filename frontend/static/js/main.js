// FinSight Core JavaScript

// Theme Management
function getTheme() {
    return localStorage.getItem('finsight_theme') || 'system';
}

function setTheme(mode) {
    localStorage.setItem('finsight_theme', mode);
    applyTheme(mode);
}

function applyTheme(mode) {
    const isDark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', isDark);
}

function toggleTheme() {
    const current = getTheme();
    const modes = { dark: 'light', light: 'system', system: 'dark' };
    setTheme(modes[current] || 'light');
}

// Initialize theme
applyTheme(getTheme());
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (getTheme() === 'system') applyTheme('system');
});

// Sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('main-content');
    const collapsed = sidebar.classList.toggle('collapsed');
    localStorage.setItem('finsight_sidebar_collapsed', collapsed);
    if (collapsed) {
        sidebar.style.width = '72px';
        main.style.paddingLeft = '72px';
    } else {
        sidebar.style.width = '260px';
        main.style.paddingLeft = '260px';
    }
}

function toggleMobileSidebar() {
    document.getElementById('mobile-overlay').classList.toggle('hidden');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        const div = document.createElement('div');
        div.id = 'toast-container';
        div.className = 'toast-container';
        document.body.appendChild(div);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = message;
    document.getElementById('toast-container').appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// API Helper
const API_BASE = window.location.origin + '/api';

async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('finsight_token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        if (response.status === 401) {
            localStorage.removeItem('finsight_token');
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || 'Request failed');
        return data;
    } catch (error) {
        throw error;
    }
}

// Auth
async function handleLogout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } catch (e) {}
    localStorage.removeItem('finsight_token');
    window.location.href = '/login';
}

// Formatting Utilities
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2 }).format(amount);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTimeAgo(date) {
    const now = new Date();
    const d = new Date(date);
    const diff = now - d;
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return formatDate(date);
}

function getInitials(name) {
    return name ? name.charAt(0).toUpperCase() : 'U';
}

// Modal
function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// Drawer
function openDrawer(id) { document.getElementById(id).classList.remove('hidden'); }
function closeDrawer(id) { document.getElementById(id).classList.add('hidden'); }

// Load user data
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('finsight_token');
    if (token) {
        try {
            const res = await apiRequest('/auth/profile');
            const user = res.data || res;
            const avatar = document.getElementById('user-avatar');
            if (avatar) avatar.textContent = getInitials(user.firstName);
        } catch (e) {}
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="text"]');
        if (searchInput) searchInput.focus();
    }
});
