#!/usr/bin/env python3
"""
FinSight Complete Frontend Generator
Generates all HTML templates, CSS, JS for the FinSight platform
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'frontend', 'static')
CSS_DIR = os.path.join(STATIC_DIR, 'css')
JS_DIR = os.path.join(STATIC_DIR, 'js')
IMG_DIR = os.path.join(STATIC_DIR, 'images')

def ensure_dirs():
    for d in [TEMPLATES_DIR, CSS_DIR, JS_DIR, IMG_DIR,
              os.path.join(TEMPLATES_DIR, 'auth'),
              os.path.join(TEMPLATES_DIR, 'dashboard'),
              os.path.join(TEMPLATES_DIR, 'expenses'),
              os.path.join(TEMPLATES_DIR, 'budget'),
              os.path.join(TEMPLATES_DIR, 'investments'),
              os.path.join(TEMPLATES_DIR, 'goals'),
              os.path.join(TEMPLATES_DIR, 'analytics'),
              os.path.join(TEMPLATES_DIR, 'reports'),
              os.path.join(TEMPLATES_DIR, 'notifications'),
              os.path.join(TEMPLATES_DIR, 'profile'),
              os.path.join(TEMPLATES_DIR, 'settings'),
              os.path.join(TEMPLATES_DIR, 'help'),
              os.path.join(TEMPLATES_DIR, 'landing'),
              os.path.join(TEMPLATES_DIR, 'components')]:
        os.makedirs(d, exist_ok=True)

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Created: {os.path.relpath(path, BASE_DIR)}")

def generate_base_template():
    return """<!DOCTYPE html>
<html lang="en" data-theme="emerald">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="FinSight - AI-Powered Personal Finance & Investment Intelligence Platform">
    <title>{% block title %}FinSight{% endblock %} - FinSight</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
                    colors: {
                        primary: { DEFAULT: '#10B981', 50: '#ECFDF5', 100: '#D1FAE5', 200: '#A7F3D0', 300: '#6EE7B7', 400: '#34D399', 500: '#10B981', 600: '#059669', 700: '#047857', 800: '#065F46', 900: '#064E3B' }
                    }
                }
            }
        }
    </script>
    {% block head_extra %}{% endblock %}
</head>
<body class="bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 font-sans antialiased">
    {% block content %}{% endblock %}
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>"""

def generate_auth_base():
    return """{% extends "base.html" %}
{% block content %}
<div class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <a href="/" class="inline-block">
                <h1 class="text-3xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-600 bg-clip-text text-transparent">FinSight</h1>
            </a>
            <p class="text-gray-500 dark:text-gray-400 mt-2">{% block auth_subtitle %}{% endblock %}</p>
        </div>
        <div class="bg-white dark:bg-gray-900 rounded-2xl p-8 shadow-lg border border-gray-100 dark:border-gray-800">
            {% block auth_content %}{% endblock %}
        </div>
    </div>
</div>
{% endblock %}"""

def generate_dashboard_base():
    return """{% extends "base.html" %}
{% block content %}
<div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside id="sidebar" class="fixed left-0 top-0 h-full w-[260px] bg-white dark:bg-gray-950 border-r border-gray-100 dark:border-gray-800 z-40 flex flex-col transition-all duration-300">
        <div class="flex items-center justify-between h-16 px-4 border-b border-gray-100 dark:border-gray-800">
            <span class="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-600 bg-clip-text text-transparent">FinSight</span>
            <button onclick="toggleSidebar()" class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/></svg>
            </button>
        </div>
        <nav class="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
            {% set nav_items = [
                ('/dashboard', 'LayoutDashboard', 'Dashboard'),
                ('/expenses', 'Wallet', 'Expenses'),
                ('/budget', 'PiggyBank', 'Budget'),
                ('/investments', 'TrendingUp', 'Investments'),
                ('/goals', 'Target', 'Goals'),
                ('/analytics', 'BarChart3', 'Analytics'),
                ('/reports', 'FileText', 'Reports')
            ] %}
            {% for href, icon, label in nav_items %}
            <a href="{{ href }}" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 {% if request.path == href %}bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400{% else %}text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50{% endif %}">
                <span class="nav-icon" data-icon="{{ icon }}"></span>
                <span>{{ label }}</span>
            </a>
            {% endfor %}
        </nav>
        <div class="py-4 space-y-1 px-2 border-t border-gray-100 dark:border-gray-800">
            {% set bottom_items = [
                ('/notifications', 'Bell', 'Notifications'),
                ('/settings', 'Settings', 'Settings'),
                ('/help', 'CircleHelp', 'Help Center')
            ] %}
            {% for href, icon, label in bottom_items %}
            <a href="{{ href }}" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 {% if request.path == href %}bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400{% else %}text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50{% endif %}">
                <span class="nav-icon" data-icon="{{ icon }}"></span>
                <span>{{ label }}</span>
            </a>
            {% endfor %}
            <button onclick="handleLogout()" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                <span>Logout</span>
            </button>
        </div>
    </aside>

    <!-- Main Content -->
    <div id="main-content" class="flex-1 lg:pl-[260px] transition-all duration-300">
        <!-- Navbar -->
        <header class="h-16 bg-white dark:bg-gray-950 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between px-4 lg:px-8">
            <div class="flex items-center gap-4 flex-1">
                <button onclick="toggleMobileSidebar()" class="lg:hidden p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                </button>
                <div class="relative max-w-md w-full">
                    <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <input type="text" placeholder="Search transactions, budgets..." class="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="toggleTheme()" class="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800">
                    <svg class="h-4 w-4 dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                    <svg class="h-4 w-4 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                </button>
                <a href="/notifications" class="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 relative">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                    <span class="absolute top-1.5 right-1.5 h-2 w-2 bg-red-500 rounded-full"></span>
                </a>
                <a href="/profile" class="flex items-center gap-2 p-1.5 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800">
                    <div class="h-8 w-8 rounded-full bg-emerald-500 flex items-center justify-center text-white text-sm font-medium" id="user-avatar">U</div>
                </a>
            </div>
        </header>

        <!-- Page Content -->
        <main class="p-4 lg:p-8 max-w-7xl mx-auto">
            {% block dashboard_content %}{% endblock %}
        </main>
    </div>
</div>

<!-- Mobile Sidebar Overlay -->
<div id="mobile-overlay" class="fixed inset-0 bg-black/50 z-50 hidden lg:hidden" onclick="toggleMobileSidebar()">
    <div class="w-[260px] h-full bg-white dark:bg-gray-950" onclick="event.stopPropagation()">
        <div class="flex items-center justify-between h-16 px-4 border-b border-gray-100 dark:border-gray-800">
            <span class="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-600 bg-clip-text text-transparent">FinSight</span>
            <button onclick="toggleMobileSidebar()" class="p-1.5 rounded-lg hover:bg-gray-100"><svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <nav class="py-4 space-y-1 px-2">
            {% for href, icon, label in nav_items + bottom_items %}
            <a href="{{ href }}" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50">{{ label }}</a>
            {% endfor %}
        </nav>
    </div>
</div>
{% endblock %}"""

def generate_css():
    return """/* FinSight Design System */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', system-ui, -apple-system, sans-serif; -webkit-font-smoothing: antialiased; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
.dark ::-webkit-scrollbar-thumb { background: #4b5563; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

.animate-fade-in { animation: fadeIn 0.3s ease-out; }
.animate-slide-in { animation: slideIn 0.3s ease-out; }
.animate-scale-in { animation: scaleIn 0.2s ease-out; }
.animate-spin { animation: spin 1s linear infinite; }
.animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }

/* Skeleton Loading */
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}
.dark .skeleton {
    background: linear-gradient(90deg, #1f2937 25%, #374151 50%, #1f2937 75%);
    background-size: 200% 100%;
}

/* Card Styles */
.card {
    background: white;
    border: 1px solid #f3f4f6;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.dark .card {
    background: #111827;
    border-color: #1f2937;
}
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.dark .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.3); }

/* Glass Effect */
.glass {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.2);
}
.dark .glass {
    background: rgba(17,24,39,0.8);
    border-color: rgba(31,41,55,0.5);
}

/* Stat Card */
.stat-card { @apply card; }
.stat-card .stat-value { font-size: 1.75rem; font-weight: 700; }
.stat-card .stat-label { font-size: 0.875rem; color: #6b7280; }
.stat-card .stat-change { font-size: 0.8rem; display: flex; align-items: center; gap: 4px; }

/* Button Styles */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-weight: 500;
    border-radius: 12px;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
    font-family: inherit;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-sm { padding: 8px 12px; font-size: 0.8rem; }
.btn-md { padding: 10px 16px; font-size: 0.875rem; }
.btn-lg { padding: 12px 24px; font-size: 1rem; }
.btn-primary { background: #10B981; color: white; }
.btn-primary:hover { background: #059669; }
.btn-secondary { background: #f3f4f6; color: #111827; }
.dark .btn-secondary { background: #1f2937; color: #f3f4f6; }
.btn-secondary:hover { background: #e5e7eb; }
.dark .btn-secondary:hover { background: #374151; }
.btn-outline { border: 2px solid #e5e7eb; color: #374151; background: transparent; }
.dark .btn-outline { border-color: #374151; color: #d1d5db; }
.btn-outline:hover { background: #f9fafb; }
.dark .btn-outline:hover { background: #1f2937; }
.btn-ghost { color: #6b7280; background: transparent; }
.btn-ghost:hover { background: #f3f4f6; }
.dark .btn-ghost:hover { background: #1f2937; }
.btn-danger { background: #EF4444; color: white; }
.btn-danger:hover { background: #DC2626; }

/* Input Styles */
.input-group { margin-bottom: 16px; }
.input-label { display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 6px; }
.dark .input-label { color: #d1d5db; }
.input-field {
    width: 100%;
    padding: 10px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    font-size: 0.875rem;
    background: white;
    color: #111827;
    transition: all 0.2s;
    font-family: inherit;
}
.dark .input-field { background: #111827; border-color: #374151; color: #f3f4f6; }
.input-field:focus { outline: none; border-color: #10B981; box-shadow: 0 0 0 3px rgba(16,185,129,0.1); }
.input-field.error { border-color: #EF4444; }
.input-error { font-size: 0.8rem; color: #EF4444; margin-top: 4px; }

/* Badge */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
}
.badge-success { background: #ECFDF5; color: #059669; }
.dark .badge-success { background: rgba(16,185,129,0.1); color: #34D399; }
.badge-warning { background: #FFFBEB; color: #D97706; }
.dark .badge-warning { background: rgba(245,158,11,0.1); color: #FBBF24; }
.badge-danger { background: #FEF2F2; color: #DC2626; }
.dark .badge-danger { background: rgba(239,68,68,0.1); color: #F87171; }
.badge-info { background: #EFF6FF; color: #2563EB; }
.dark .badge-info { background: rgba(59,130,246,0.1); color: #60A5FA; }

/* Table */
.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 12px 16px; font-size: 0.75rem; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #f3f4f6; }
.dark th { border-color: #1f2937; }
td { padding: 12px 16px; font-size: 0.875rem; border-bottom: 1px solid #f9fafb; }
.dark td { border-color: rgba(31,41,55,0.5); }
tr:hover td { background: #f9fafb; }
.dark tr:hover td { background: rgba(31,41,55,0.5); }

/* Modal */
.modal-overlay {
    position: fixed; inset: 0; z-index: 50;
    display: flex; align-items: center; justify-content: center;
    background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
}
.modal-content {
    background: white; border-radius: 16px; padding: 24px;
    max-width: 500px; width: 90%; max-height: 90vh; overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.dark .modal-content { background: #111827; }

/* Progress Bar */
.progress-bar { width: 100%; background: #f3f4f6; border-radius: 9999px; overflow: hidden; }
.dark .progress-bar { background: #1f2937; }
.progress-fill { height: 100%; border-radius: 9999px; transition: width 0.5s ease; }
.progress-fill.primary { background: #10B981; }
.progress-fill.warning { background: #F59E0B; }
.progress-fill.danger { background: #EF4444; }

/* Toast */
.toast-container { position: fixed; top: 16px; right: 16px; z-index: 100; display: flex; flex-direction: column; gap: 8px; }
.toast {
    padding: 12px 16px; border-radius: 12px; font-size: 0.875rem;
    display: flex; align-items: center; gap: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideIn 0.3s ease-out;
    min-width: 300px;
}
.toast-success { background: #10B981; color: white; }
.toast-error { background: #EF4444; color: white; }
.toast-info { background: #3B82F6; color: white; }

/* Chart Container */
.chart-container { width: 100%; height: 300px; position: relative; }

/* Page Header */
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 1.5rem; font-weight: 700; }
.page-subtitle { font-size: 0.875rem; color: #6b7280; margin-top: 4px; }

/* Grid Layouts */
.stats-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.charts-grid { display: grid; gap: 24px; grid-template-columns: 2fr 1fr; }
@media (max-width: 768px) { .charts-grid { grid-template-columns: 1fr; } }

/* Empty State */
.empty-state { text-align: center; padding: 48px 24px; }
.empty-state svg { margin: 0 auto 16px; color: #9CA3AF; }
.empty-state h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 8px; }
.empty-state p { color: #6b7280; font-size: 0.875rem; margin-bottom: 16px; }

/* Loading Spinner */
.spinner { border: 3px solid #f3f4f6; border-top-color: #10B981; border-radius: 50%; width: 24px; height: 24px; animation: spin 0.8s linear infinite; }
.dark .spinner { border-color: #1f2937; border-top-color: #34D399; }
"""

def generate_js():
    return """// FinSight Core JavaScript

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
"""

def generate_login():
    return """{% extends "auth_base.html" %}
{% block auth_subtitle %}Welcome back! Sign in to your account{% endblock %}
{% block auth_content %}
<form id="loginForm" onsubmit="handleLogin(event)" class="space-y-5">
    <div class="input-group">
        <label class="input-label">Email</label>
        <input type="email" name="email" class="input-field" placeholder="you@example.com" required>
    </div>
    <div class="input-group">
        <label class="input-label">Password</label>
        <input type="password" name="password" class="input-field" placeholder="Enter your password" required>
    </div>
    <div class="flex items-center justify-between">
        <label class="flex items-center gap-2 cursor-pointer text-sm text-gray-600 dark:text-gray-400">
            <input type="checkbox" name="remember" class="rounded border-gray-300"> Remember me
        </label>
        <a href="/forgot-password" class="text-sm text-emerald-600 dark:text-emerald-400 hover:underline">Forgot password?</a>
    </div>
    <button type="submit" class="btn btn-primary btn-lg w-full">Sign In</button>
</form>
<p class="text-center text-sm text-gray-500 mt-6">
    Don't have an account? <a href="/register" class="text-emerald-600 dark:text-emerald-400 font-medium hover:underline">Create one</a>
</p>
<script>
async function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true; btn.textContent = 'Signing in...';
    try {
        const res = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email: form.email.value, password: form.password.value })
        });
        localStorage.setItem('finsight_token', res.data.token);
        showToast('Welcome back!', 'success');
        window.location.href = '/dashboard';
    } catch (err) {
        showToast(err.message || 'Login failed', 'error');
        btn.disabled = false; btn.textContent = 'Sign In';
    }
}
</script>
{% endblock %}"""

def generate_register():
    return """{% extends "auth_base.html" %}
{% block auth_subtitle %}Create your account to get started{% endblock %}
{% block auth_content %}
<form id="registerForm" onsubmit="handleRegister(event)" class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
        <div class="input-group">
            <label class="input-label">First Name</label>
            <input type="text" name="firstName" class="input-field" placeholder="John" required>
        </div>
        <div class="input-group">
            <label class="input-label">Last Name</label>
            <input type="text" name="lastName" class="input-field" placeholder="Doe" required>
        </div>
    </div>
    <div class="input-group">
        <label class="input-label">Email</label>
        <input type="email" name="email" class="input-field" placeholder="you@example.com" required>
    </div>
    <div class="input-group">
        <label class="input-label">Password</label>
        <input type="password" name="password" class="input-field" placeholder="Create a strong password" required minlength="8">
    </div>
    <div class="input-group">
        <label class="input-label">Confirm Password</label>
        <input type="password" name="confirmPassword" class="input-field" placeholder="Confirm your password" required>
    </div>
    <label class="flex items-start gap-2 cursor-pointer text-sm text-gray-600 dark:text-gray-400">
        <input type="checkbox" name="terms" class="mt-1" required>
        <span>I agree to the <a href="/terms" class="text-emerald-600">Terms of Service</a> and <a href="/privacy" class="text-emerald-600">Privacy Policy</a></span>
    </label>
    <button type="submit" class="btn btn-primary btn-lg w-full">Create Account</button>
</form>
<p class="text-center text-sm text-gray-500 mt-6">
    Already have an account? <a href="/login" class="text-emerald-600 dark:text-emerald-400 font-medium hover:underline">Sign in</a>
</p>
<script>
async function handleRegister(e) {
    e.preventDefault();
    const form = e.target;
    if (form.password.value !== form.confirmPassword.value) {
        showToast('Passwords do not match', 'error'); return;
    }
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true; btn.textContent = 'Creating account...';
    try {
        const res = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                firstName: form.firstName.value, lastName: form.lastName.value,
                email: form.email.value, password: form.password.value
            })
        });
        localStorage.setItem('finsight_token', res.data.token);
        showToast('Account created successfully!', 'success');
        window.location.href = '/dashboard';
    } catch (err) {
        showToast(err.message || 'Registration failed', 'error');
        btn.disabled = false; btn.textContent = 'Create Account';
    }
}
</script>
{% endblock %}"""

def generate_forgot_password():
    return """{% extends "auth_base.html" %}
{% block auth_subtitle %}Reset your password{% endblock %}
{% block auth_content %}
{% if sent %}
<div class="text-center space-y-4 animate-fade-in">
    <div class="h-16 w-16 rounded-full bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center mx-auto">
        <svg class="h-8 w-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
    </div>
    <p class="text-gray-600 dark:text-gray-400">We've sent a password reset link to your email. Please check your inbox.</p>
    <a href="/login" class="btn btn-outline btn-md">Back to Login</a>
</div>
{% else %}
<form onsubmit="handleForgotPassword(event)" class="space-y-5">
    <div class="input-group">
        <label class="input-label">Email</label>
        <input type="email" name="email" class="input-field" placeholder="you@example.com" required>
    </div>
    <button type="submit" class="btn btn-primary btn-lg w-full">Send Reset Link</button>
    <a href="/login" class="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700 mt-4">Back to Login</a>
</form>
{% endif %}
<script>
async function handleForgotPassword(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.disabled = true; btn.textContent = 'Sending...';
    try {
        await apiRequest('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email: e.target.email.value })
        });
        showToast('Reset link sent!', 'success');
        window.location.reload();
    } catch (err) {
        showToast(err.message || 'Failed', 'error');
        btn.disabled = false; btn.textContent = 'Send Reset Link';
    }
}
</script>
{% endblock %}"""

def generate_reset_password():
    return """{% extends "auth_base.html" %}
{% block auth_subtitle %}Set your new password{% endblock %}
{% block auth_content %}
<form onsubmit="handleResetPassword(event)" class="space-y-5">
    <input type="hidden" name="token" value="{{ token }}">
    <div class="input-group">
        <label class="input-label">New Password</label>
        <input type="password" name="password" class="input-field" placeholder="Enter new password" required minlength="8">
    </div>
    <div class="input-group">
        <label class="input-label">Confirm Password</label>
        <input type="password" name="confirmPassword" class="input-field" placeholder="Confirm new password" required>
    </div>
    <button type="submit" class="btn btn-primary btn-lg w-full">Reset Password</button>
</form>
<script>
async function handleResetPassword(e) {
    e.preventDefault();
    const form = e.target;
    if (form.password.value !== form.confirmPassword.value) {
        showToast('Passwords do not match', 'error'); return;
    }
    const btn = form.querySelector('button');
    btn.disabled = true; btn.textContent = 'Resetting...';
    try {
        await apiRequest('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token: form.token.value, password: form.password.value })
        });
        showToast('Password reset successfully!', 'success');
        window.location.href = '/login';
    } catch (err) {
        showToast(err.message || 'Failed', 'error');
        btn.disabled = false; btn.textContent = 'Reset Password';
    }
}
</script>
{% endblock %}"""

def generate_landing():
    return """{% extends "base.html" %}
{% block title %}AI-Powered Personal Finance{% endblock %}
{% block content %}
<!-- Header -->
<header class="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-100 dark:border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
            <span class="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-600 bg-clip-text text-transparent">FinSight</span>
            <div class="flex items-center gap-4">
                <a href="/login" class="btn btn-ghost btn-md">Sign In</a>
                <a href="/register" class="btn btn-primary btn-md">Get Started</a>
            </div>
        </div>
    </div>
</header>

<!-- Hero -->
<section class="pt-32 pb-20 px-4">
    <div class="max-w-7xl mx-auto text-center">
        <div class="max-w-3xl mx-auto animate-fade-in">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 text-sm font-medium mb-6">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
                AI-Powered Finance Intelligence
            </div>
            <h1 class="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
                Your Financial Future,<br>
                <span class="text-emerald-500">Intelligently Managed</span>
            </h1>
            <p class="text-xl text-gray-500 dark:text-gray-400 mb-10 max-w-2xl mx-auto">
                Track expenses, manage investments, set goals, and get AI-powered insights to make smarter financial decisions.
            </p>
            <div class="flex items-center justify-center gap-4">
                <a href="/register" class="btn btn-primary btn-lg">Start Free Trial</a>
                <a href="#features" class="btn btn-outline btn-lg">See How It Works</a>
            </div>
        </div>
    </div>
</section>

<!-- Features -->
<section id="features" class="py-20 px-4 bg-gray-50 dark:bg-gray-900/50">
    <div class="max-w-7xl mx-auto">
        <div class="text-center mb-16">
            <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">Everything You Need to Master Your Finances</h2>
            <p class="text-lg text-gray-500 max-w-2xl mx-auto">Professional tools and AI-powered features to help you take control of your financial life.</p>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {% set features = [
                ('Brain', 'AI-Powered Insights', 'Get intelligent recommendations and spending analysis powered by advanced AI.'),
                ('TrendingUp', 'Investment Tracking', 'Track stocks, mutual funds, crypto, and more with real-time portfolio analytics.'),
                ('PieChart', 'Smart Budgeting', 'Create intelligent budgets that adapt to your spending patterns automatically.'),
                ('Target', 'Financial Goals', 'Set and track financial goals with milestones, projections, and AI recommendations.'),
                ('BarChart3', 'Advanced Analytics', 'Deep dive into your finances with professional-grade charts and reports.'),
                ('Shield', 'Bank-Grade Security', 'Your financial data is encrypted and protected with enterprise-level security.')
            ] %}
            {% for icon, title, desc in features %}
            <div class="p-8 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 hover:shadow-lg transition-shadow">
                <div class="h-12 w-12 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-500 mb-5">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ title }}</h3>
                <p class="text-gray-500 dark:text-gray-400">{{ desc }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- CTA -->
<section class="py-20 px-4">
    <div class="max-w-7xl mx-auto text-center">
        <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">Ready to Transform Your Finances?</h2>
        <p class="text-lg text-gray-500 mb-8 max-w-xl mx-auto">Join thousands of users who trust FinSight to manage their financial life.</p>
        <a href="/register" class="btn btn-primary btn-lg">Get Started Free</a>
    </div>
</section>

<!-- Footer -->
<footer class="py-12 px-4 border-t border-gray-100 dark:border-gray-800">
    <div class="max-w-7xl mx-auto text-center text-sm text-gray-500">
        <p>&copy; 2026 FinSight. All rights reserved.</p>
    </div>
</footer>
{% endblock %}"""

def generate_dashboard():
    return """{% extends "dashboard_base.html" %}
{% block title %}Dashboard{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Welcome back, <span id="userName">User</span></h1>
            <p class="text-gray-500 mt-1">Here's your financial overview for today</p>
        </div>
        <div class="flex items-center gap-3">
            <button class="btn btn-outline btn-md">This Month</button>
            <button class="btn btn-primary btn-md" onclick="openModal('addTransactionModal')">Add Transaction</button>
        </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
        <div class="card">
            <div class="flex items-start justify-between">
                <div class="space-y-2">
                    <p class="text-sm text-gray-500">Total Income</p>
                    <p class="text-2xl font-bold" id="totalIncome">$12,450</p>
                    <p class="text-sm text-emerald-500 flex items-center gap-1">↑ 12.5% from last month</p>
                </div>
                <div class="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 text-emerald-500">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="flex items-start justify-between">
                <div class="space-y-2">
                    <p class="text-sm text-gray-500">Total Expenses</p>
                    <p class="text-2xl font-bold">$8,450</p>
                    <p class="text-sm text-red-500 flex items-center gap-1">↑ 8.2% from last month</p>
                </div>
                <div class="p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-500">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="flex items-start justify-between">
                <div class="space-y-2">
                    <p class="text-sm text-gray-500">Total Savings</p>
                    <p class="text-2xl font-bold">$4,000</p>
                    <p class="text-sm text-emerald-500 flex items-center gap-1">↑ 15.3% from last month</p>
                </div>
                <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-500">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="flex items-start justify-between">
                <div class="space-y-2">
                    <p class="text-sm text-gray-500">Net Worth</p>
                    <p class="text-2xl font-bold">$125,000</p>
                    <p class="text-sm text-emerald-500 flex items-center gap-1">↑ 5.7% from last month</p>
                </div>
                <div class="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20 text-purple-500">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                </div>
            </div>
        </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
        <div class="card">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold">Monthly Spending</h3>
                <span class="badge badge-info">+12.5% vs last month</span>
            </div>
            <div class="chart-container" id="spendingChart"></div>
        </div>
        <div class="card">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold">Spending by Category</h3>
            </div>
            <div class="chart-container" id="categoryChart"></div>
        </div>
    </div>

    <!-- Recent Transactions & AI Insights -->
    <div class="grid lg:grid-cols-2 gap-6">
        <div class="card">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold">Recent Transactions</h3>
                <a href="/expenses" class="btn btn-ghost btn-sm">View All</a>
            </div>
            <div class="space-y-1" id="recentTransactions">
                <div class="flex items-center justify-between p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="h-10 w-10 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                            <svg class="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
                        </div>
                        <div><p class="text-sm font-medium">Grocery Store</p><p class="text-xs text-gray-500">Groceries · 2h ago</p></div>
                    </div>
                    <span class="text-sm font-semibold text-red-500">-$156.00</span>
                </div>
                <div class="flex items-center justify-between p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="h-10 w-10 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
                            <svg class="h-4 w-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>
                        </div>
                        <div><p class="text-sm font-medium">Salary Deposit</p><p class="text-xs text-gray-500">Income · 1d ago</p></div>
                    </div>
                    <span class="text-sm font-semibold text-emerald-500">+$5,000.00</span>
                </div>
                <div class="flex items-center justify-between p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="h-10 w-10 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                            <svg class="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
                        </div>
                        <div><p class="text-sm font-medium">Netflix Subscription</p><p class="text-xs text-gray-500">Subscription · 2d ago</p></div>
                    </div>
                    <span class="text-sm font-semibold text-red-500">-$15.99</span>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold">AI Insights</h3>
                <svg class="h-4 w-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
            </div>
            <div class="space-y-4">
                <div class="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/10 space-y-1">
                    <div class="flex items-center gap-2"><div class="h-2 w-2 rounded-full bg-amber-500"></div><p class="text-sm font-medium">Spending Pattern Detected</p></div>
                    <p class="text-xs text-gray-500">Your dining expenses increased 23% this month. Consider setting a dining budget.</p>
                </div>
                <div class="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-900/10 space-y-1">
                    <div class="flex items-center gap-2"><div class="h-2 w-2 rounded-full bg-emerald-500"></div><p class="text-sm font-medium">Savings Opportunity</p></div>
                    <p class="text-xs text-gray-500">You could save $120/month by reducing subscription services.</p>
                </div>
                <div class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/10 space-y-1">
                    <div class="flex items-center gap-2"><div class="h-2 w-2 rounded-full bg-blue-500"></div><p class="text-sm font-medium">Investment Tip</p></div>
                    <p class="text-xs text-gray-500">Your portfolio is 65% in stocks. Consider diversifying into bonds.</p>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Add Transaction Modal -->
<div id="addTransactionModal" class="modal-overlay hidden">
    <div class="modal-content animate-scale-in">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold">Add Transaction</h2>
            <button onclick="closeModal('addTransactionModal')" class="p-1 rounded-lg hover:bg-gray-100"><svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <form class="space-y-4">
            <div class="input-group"><label class="input-label">Amount</label><input type="number" class="input-field" placeholder="0.00" step="0.01"></div>
            <div class="input-group"><label class="input-label">Description</label><input type="text" class="input-field" placeholder="Enter description"></div>
            <div class="input-group"><label class="input-label">Category</label>
                <select class="input-field">
                    <option>Food & Dining</option><option>Transportation</option><option>Shopping</option>
                    <option>Bills & Utilities</option><option>Entertainment</option><option>Healthcare</option>
                </select>
            </div>
            <div class="flex gap-3 justify-end pt-4">
                <button type="button" onclick="closeModal('addTransactionModal')" class="btn btn-secondary btn-md">Cancel</button>
                <button type="submit" class="btn btn-primary btn-md">Add Transaction</button>
            </div>
        </form>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Spending Chart
new Chart(document.getElementById('spendingChart'), {
    type: 'bar',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Spending',
            data: [2400, 1398, 3800, 2908, 4800, 3800],
            backgroundColor: '#10B981',
            borderRadius: 6,
            barThickness: 32
        }]
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: '#f0f0f0' } }, x: { grid: { display: false } } }
    }
});

// Category Chart
new Chart(document.getElementById('categoryChart'), {
    type: 'doughnut',
    data: {
        labels: ['Food', 'Transport', 'Shopping', 'Bills'],
        datasets: [{
            data: [35, 20, 25, 20],
            backgroundColor: ['#EF4444', '#F97316', '#6366F1', '#22C55E'],
            borderWidth: 0
        }]
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        cutout: '65%'
    }
});
</script>
{% endblock %}"""

def generate_expenses():
    return """{% extends "dashboard_base.html" %}
{% block title %}Expenses{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Expenses</h1>
            <p class="text-gray-500 mt-1">Track and manage all your expenses</p>
        </div>
        <div class="flex items-center gap-3">
            <button class="btn btn-outline btn-md">Export</button>
            <button class="btn btn-primary btn-md" onclick="openModal('addExpenseModal')">Add Expense</button>
        </div>
    </div>

    <!-- Filters -->
    <div class="card">
        <div class="flex flex-wrap gap-3">
            <input type="text" class="input-field flex-1 min-w-[200px]" placeholder="Search expenses...">
            <select class="input-field w-auto"><option>All Categories</option><option>Food</option><option>Transport</option><option>Shopping</option></select>
            <select class="input-field w-auto"><option>All Time</option><option>This Month</option><option>Last Month</option><option>This Year</option></select>
            <button class="btn btn-secondary btn-md">Search</button>
        </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
        <div class="card"><p class="text-sm text-gray-500">Total Expenses</p><p class="text-2xl font-bold">$8,450</p><p class="text-sm text-red-500">↑ 8.2% vs last month</p></div>
        <div class="card"><p class="text-sm text-gray-500">Monthly Average</p><p class="text-2xl font-bold">$2,816</p><p class="text-sm text-gray-500">Last 3 months</p></div>
        <div class="card"><p class="text-sm text-gray-500">Highest Category</p><p class="text-2xl font-bold">Food</p><p class="text-sm text-gray-500">$2,450 this month</p></div>
        <div class="card"><p class="text-sm text-gray-500">Transactions</p><p class="text-2xl font-bold">47</p><p class="text-sm text-gray-500">This month</p></div>
    </div>

    <!-- Expenses Table -->
    <div class="card p-0">
        <div class="table-container">
            <table>
                <thead>
                    <tr><th><input type="checkbox"></th><th>Description</th><th>Category</th><th>Date</th><th>Amount</th><th>Status</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    {% for i in range(10) %}
                    <tr>
                        <td><input type="checkbox"></td>
                        <td class="font-medium">Expense {{ i + 1 }}</td>
                        <td><span class="badge badge-info">Food</span></td>
                        <td>Jul {{ 15 - i }}, 2026</td>
                        <td class="font-semibold text-red-500">-${{ range(10, 500) | random }}</td>
                        <td><span class="badge badge-success">Completed</span></td>
                        <td><button class="btn btn-ghost btn-sm">Edit</button></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="flex items-center justify-between p-4 border-t border-gray-100 dark:border-gray-800">
            <p class="text-sm text-gray-500">Showing 1-10 of 47</p>
            <div class="flex gap-1">
                <button class="btn btn-ghost btn-sm">Previous</button>
                <button class="btn btn-primary btn-sm">1</button>
                <button class="btn btn-ghost btn-sm">2</button>
                <button class="btn btn-ghost btn-sm">3</button>
                <button class="btn btn-ghost btn-sm">Next</button>
            </div>
        </div>
    </div>
</div>

<!-- Add Expense Modal -->
<div id="addExpenseModal" class="modal-overlay hidden">
    <div class="modal-content animate-scale-in">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold">Add Expense</h2>
            <button onclick="closeModal('addExpenseModal')" class="p-1 rounded-lg hover:bg-gray-100"><svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <form class="space-y-4">
            <div class="input-group"><label class="input-label">Amount</label><input type="number" class="input-field" placeholder="0.00" step="0.01"></div>
            <div class="input-group"><label class="input-label">Description</label><input type="text" class="input-field" placeholder="Enter description"></div>
            <div class="grid grid-cols-2 gap-4">
                <div class="input-group"><label class="input-label">Category</label><select class="input-field"><option>Food</option><option>Transport</option><option>Shopping</option><option>Bills</option></select></div>
                <div class="input-group"><label class="input-label">Date</label><input type="date" class="input-field"></div>
            </div>
            <div class="input-group"><label class="input-label">Notes</label><textarea class="input-field" rows="3" placeholder="Optional notes"></textarea></div>
            <div class="flex gap-3 justify-end pt-4">
                <button type="button" onclick="closeModal('addExpenseModal')" class="btn btn-secondary btn-md">Cancel</button>
                <button type="submit" class="btn btn-primary btn-md">Add Expense</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}"""

def generate_budget():
    return """{% extends "dashboard_base.html" %}
{% block title %}Budget{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Budget</h1>
            <p class="text-gray-500 mt-1">Manage your budgets and track spending</p>
        </div>
        <button class="btn btn-primary btn-md" onclick="openModal('createBudgetModal')">Create Budget</button>
    </div>

    <div class="stats-grid">
        <div class="card"><p class="text-sm text-gray-500">Monthly Budget</p><p class="text-2xl font-bold">$5,000</p><p class="text-sm text-emerald-500">On track</p></div>
        <div class="card"><p class="text-sm text-gray-500">Spent</p><p class="text-2xl font-bold">$3,450</p><p class="text-sm text-amber-500">69% used</p></div>
        <div class="card"><p class="text-sm text-gray-500">Remaining</p><p class="text-2xl font-bold">$1,550</p><p class="text-sm text-emerald-500">31% remaining</p></div>
        <div class="card"><p class="text-sm text-gray-500">Daily Average</p><p class="text-2xl font-bold">$115</p><p class="text-sm text-gray-500">$167 budgeted</p></div>
    </div>

    <div class="card">
        <h3 class="text-lg font-semibold mb-4">Budget Progress</h3>
        <div class="space-y-4">
            {% set budgets = [
                ('Food & Dining', 800, 650, 'emerald'),
                ('Transportation', 400, 320, 'blue'),
                ('Shopping', 600, 580, 'amber'),
                ('Bills & Utilities', 1000, 850, 'purple'),
                ('Entertainment', 300, 280, 'rose'),
                ('Healthcare', 500, 200, 'teal')
            ] %}
            {% for name, total, spent, color in budgets %}
            <div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium">{{ name }}</span>
                    <span class="text-sm text-gray-500">${{ spent }}/${{ total }}</span>
                </div>
                <div class="progress-bar h-2">
                    <div class="progress-fill {{ color }}" style="width: {{ (spent / total * 100) | int }}%"></div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<div id="createBudgetModal" class="modal-overlay hidden">
    <div class="modal-content animate-scale-in">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold">Create Budget</h2>
            <button onclick="closeModal('createBudgetModal')" class="p-1 rounded-lg hover:bg-gray-100"><svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <form class="space-y-4">
            <div class="input-group"><label class="input-label">Budget Name</label><input type="text" class="input-field" placeholder="e.g., Monthly Budget"></div>
            <div class="input-group"><label class="input-label">Amount</label><input type="number" class="input-field" placeholder="0.00"></div>
            <div class="grid grid-cols-2 gap-4">
                <div class="input-group"><label class="input-label">Category</label><select class="input-field"><option>All Categories</option><option>Food</option><option>Transport</option></select></div>
                <div class="input-group"><label class="input-label">Period</label><select class="input-field"><option>Monthly</option><option>Weekly</option><option>Yearly</option></select></div>
            </div>
            <div class="flex gap-3 justify-end pt-4">
                <button type="button" onclick="closeModal('createBudgetModal')" class="btn btn-secondary btn-md">Cancel</button>
                <button type="submit" class="btn btn-primary btn-md">Create Budget</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}"""

def generate_investments():
    return """{% extends "dashboard_base.html" %}
{% block title %}Investments{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Investments</h1>
            <p class="text-gray-500 mt-1">Track your investment portfolio</p>
        </div>
        <button class="btn btn-primary btn-md" onclick="openModal('addInvestmentModal')">Add Investment</button>
    </div>

    <div class="stats-grid">
        <div class="card"><p class="text-sm text-gray-500">Total Invested</p><p class="text-2xl font-bold">$45,000</p></div>
        <div class="card"><p class="text-sm text-gray-500">Current Value</p><p class="text-2xl font-bold">$52,300</p><p class="text-sm text-emerald-500">↑ 16.2% return</p></div>
        <div class="card"><p class="text-sm text-gray-500">Total Profit/Loss</p><p class="text-2xl font-bold text-emerald-500">+$7,300</p><p class="text-sm text-emerald-500">↑ 16.2%</p></div>
        <div class="card"><p class="text-sm text-gray-500">Daily Change</p><p class="text-2xl font-bold text-emerald-500">+$245</p><p class="text-sm text-emerald-500">↑ 0.47%</p></div>
    </div>

    <div class="grid lg:grid-cols-2 gap-6">
        <div class="card">
            <h3 class="text-lg font-semibold mb-4">Portfolio Allocation</h3>
            <div class="chart-container" id="portfolioChart"></div>
        </div>
        <div class="card">
            <h3 class="text-lg font-semibold mb-4">Holdings</h3>
            <div class="table-container">
                <table>
                    <thead><tr><th>Name</th><th>Type</th><th>Invested</th><th>Current</th><th>Return</th></tr></thead>
                    <tbody>
                        <tr><td class="font-medium">Apple Inc.</td><td>Stock</td><td>$5,000</td><td>$6,200</td><td class="text-emerald-500">+24%</td></tr>
                        <tr><td class="font-medium">Vanguard Total Market</td><td>ETF</td><td>$10,000</td><td>$11,500</td><td class="text-emerald-500">+15%</td></tr>
                        <tr><td class="font-medium">Bitcoin</td><td>Crypto</td><td>$3,000</td><td>$4,800</td><td class="text-emerald-500">+60%</td></tr>
                        <tr><td class="font-medium">Gold ETF</td><td>Gold</td><td>$5,000</td><td>$5,300</td><td class="text-emerald-500">+6%</td></tr>
                        <tr><td class="font-medium">FD - HDFC Bank</td><td>FD</td><td>$10,000</td><td>$10,800</td><td class="text-emerald-500">+8%</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('portfolioChart'), {
    type: 'doughnut',
    data: {
        labels: ['Stocks', 'Mutual Funds', 'Crypto', 'Gold', 'FD', 'Bonds'],
        datasets: [{
            data: [35, 25, 15, 10, 10, 5],
            backgroundColor: ['#22C55E', '#3B82F6', '#F97316', '#EAB308', '#06B6D4', '#6366F1'],
            borderWidth: 0
        }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, cutout: '65%' }
});
</script>
{% endblock %}"""

def generate_goals():
    return """{% extends "dashboard_base.html" %}
{% block title %}Financial Goals{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Financial Goals</h1>
            <p class="text-gray-500 mt-1">Track your financial goals and milestones</p>
        </div>
        <button class="btn btn-primary btn-md" onclick="openModal('addGoalModal')">Add Goal</button>
    </div>

    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {% set goals = [
            ('Emergency Fund', 'Shield', 10000, 6500, '#EF4444', '65%'),
            ('Retirement', 'Umbrella', 500000, 125000, '#3B82F6', '25%'),
            ('Dream Vacation', 'Plane', 15000, 8500, '#06B6D4', '57%'),
            ('New House', 'Home', 100000, 35000, '#F97316', '35%'),
            ('Education Fund', 'GraduationCap', 50000, 15000, '#8B5CF6', '30%'),
            ('New Car', 'Car', 35000, 12000, '#22C55E', '34%')
        ] %}
        {% for name, icon, target, current, color, pct in goals %}
        <div class="card hover:shadow-md transition-shadow">
            <div class="flex items-start justify-between mb-4">
                <div class="h-12 w-12 rounded-xl flex items-center justify-center" style="background: {{ color }}15; color: {{ color }}">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
                </div>
                <span class="text-sm font-semibold" style="color: {{ color }}">{{ pct }}</span>
            </div>
            <h3 class="text-lg font-semibold mb-1">{{ name }}</h3>
            <p class="text-sm text-gray-500 mb-4">${{ '{:,}'.format(current) }} of ${{ '{:,}'.format(target) }}</p>
            <div class="progress-bar h-2.5">
                <div class="progress-fill" style="width: {{ pct.strip('%') }}%; background: {{ color }}"></div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

def generate_analytics():
    return """{% extends "dashboard_base.html" %}
{% block title %}Analytics{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Analytics</h1>
            <p class="text-gray-500 mt-1">Deep dive into your financial data</p>
        </div>
        <div class="flex gap-3">
            <select class="input-field w-auto"><option>Last 6 Months</option><option>Last Year</option><option>All Time</option></select>
            <button class="btn btn-outline btn-md">Export</button>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card"><p class="text-sm text-gray-500">Financial Health Score</p><p class="text-2xl font-bold text-emerald-500">78/100</p><p class="text-sm text-emerald-500">Good</p></div>
        <div class="card"><p class="text-sm text-gray-500">Savings Rate</p><p class="text-2xl font-bold">32%</p><p class="text-sm text-emerald-500">↑ 5% vs last month</p></div>
        <div class="card"><p class="text-sm text-gray-500">Expense Ratio</p><p class="text-2xl font-bold">68%</p><p class="text-sm text-amber-500">Needs attention</p></div>
        <div class="card"><p class="text-sm text-gray-500">Investment Ratio</p><p class="text-2xl font-bold">45%</p><p class="text-sm text-emerald-500">On track</p></div>
    </div>

    <div class="grid lg:grid-cols-2 gap-6">
        <div class="card">
            <h3 class="text-lg font-semibold mb-4">Income vs Expenses</h3>
            <div class="chart-container" id="incomeExpenseChart"></div>
        </div>
        <div class="card">
            <h3 class="text-lg font-semibold mb-4">Spending Trends</h3>
            <div class="chart-container" id="trendChart"></div>
        </div>
    </div>

    <div class="card">
        <h3 class="text-lg font-semibold mb-4">Category Breakdown</h3>
        <div class="chart-container" id="categoryBreakdownChart"></div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('incomeExpenseChart'), {
    type: 'line',
    data: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun'],
        datasets: [
            { label: 'Income', data: [5000, 5200, 4800, 5100, 5300, 5000], borderColor: '#10B981', tension: 0.4, fill: false },
            { label: 'Expenses', data: [3200, 2800, 3500, 3100, 3800, 3400], borderColor: '#EF4444', tension: 0.4, fill: false }
        ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
});

new Chart(document.getElementById('trendChart'), {
    type: 'bar',
    data: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun'],
        datasets: [{ label: 'Spending', data: [3200, 2800, 3500, 3100, 3800, 3400], backgroundColor: '#10B981', borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
});
</script>
{% endblock %}"""

def generate_reports():
    return """{% extends "dashboard_base.html" %}
{% block title %}Reports{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Reports</h1>
            <p class="text-gray-500 mt-1">Generate and download financial reports</p>
        </div>
        <div class="flex gap-3">
            <button class="btn btn-outline btn-md">PDF</button>
            <button class="btn btn-outline btn-md">Excel</button>
            <button class="btn btn-outline btn-md">CSV</button>
        </div>
    </div>

    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {% set reports = [
            ('Expense Report', 'Detailed breakdown of all expenses', 'Wallet', 'emerald'),
            ('Budget Report', 'Budget performance and analysis', 'PiggyBank', 'blue'),
            ('Investment Report', 'Portfolio performance summary', 'TrendingUp', 'purple'),
            ('Goal Report', 'Progress on financial goals', 'Target', 'amber'),
            ('Tax Report', 'Tax-related financial summary', 'FileText', 'rose'),
            ('Financial Report', 'Comprehensive financial overview', 'BarChart3', 'teal')
        ] %}
        {% for title, desc, icon, color in reports %}
        <div class="card hover:shadow-md transition-shadow cursor-pointer">
            <div class="flex items-start justify-between mb-4">
                <div class="h-12 w-12 rounded-xl flex items-center justify-center" style="background: var(--{{ color }}-50); color: var(--{{ color }}-500)">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </div>
            </div>
            <h3 class="text-lg font-semibold mb-1">{{ title }}</h3>
            <p class="text-sm text-gray-500 mb-4">{{ desc }}</p>
            <button class="btn btn-secondary btn-sm w-full">Generate Report</button>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

def generate_notifications():
    return """{% extends "dashboard_base.html" %}
{% block title %}Notifications{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Notifications</h1>
            <p class="text-gray-500 mt-1">Stay updated with your financial activity</p>
        </div>
        <button class="btn btn-secondary btn-md">Mark All Read</button>
    </div>

    <div class="card p-0">
        {% set notifications = [
            ('budget_alert', 'Budget Alert', 'You have used 85% of your Food budget', 'warning', '2h ago'),
            ('goal_alert', 'Goal Milestone', 'Congratulations! You reached 50% of your Emergency Fund goal', 'success', '5h ago'),
            ('investment_alert', 'Investment Update', 'Apple stock is up 3.2% today', 'info', '1d ago'),
            ('bill_reminder', 'Bill Reminder', 'Your Netflix subscription renews tomorrow', 'warning', '1d ago'),
            ('monthly_summary', 'Monthly Summary', 'Your June financial summary is ready', 'info', '3d ago'),
            ('security_alert', 'Security Alert', 'New login from Chrome on Windows', 'danger', '5d ago'),
            ('ai_recommendation', 'AI Recommendation', 'Consider increasing your emergency fund contribution', 'info', '1w ago')
        ] %}
        {% for type, title, message, severity, time in notifications %}
        <div class="flex items-start gap-4 p-4 border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer">
            <div class="h-10 w-10 rounded-xl flex items-center justify-center shrink-0
                {% if severity == 'warning' %}bg-amber-50 dark:bg-amber-900/20 text-amber-500
                {% elif severity == 'success' %}bg-emerald-50 dark:bg-emerald-900/20 text-emerald-500
                {% elif severity == 'danger' %}bg-red-50 dark:bg-red-900/20 text-red-500
                {% else %}bg-blue-50 dark:bg-blue-900/20 text-blue-500{% endif %}">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                    <p class="text-sm font-medium">{{ title }}</p>
                    <span class="text-xs text-gray-500">{{ time }}</span>
                </div>
                <p class="text-sm text-gray-500 mt-0.5">{{ message }}</p>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

def generate_profile():
    return """{% extends "dashboard_base.html" %}
{% block title %}Profile{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Profile</h1>
            <p class="text-gray-500 mt-1">Manage your personal information</p>
        </div>
    </div>

    <div class="grid lg:grid-cols-3 gap-6">
        <div class="card text-center">
            <div class="h-24 w-24 rounded-full bg-emerald-500 flex items-center justify-center text-white text-3xl font-bold mx-auto mb-4">U</div>
            <h2 class="text-xl font-semibold">User Name</h2>
            <p class="text-gray-500">user@example.com</p>
            <button class="btn btn-secondary btn-md mt-4">Change Photo</button>
        </div>
        <div class="card lg:col-span-2">
            <h3 class="text-lg font-semibold mb-6">Personal Information</h3>
            <form class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="input-group"><label class="input-label">First Name</label><input type="text" class="input-field" value="User"></div>
                    <div class="input-group"><label class="input-label">Last Name</label><input type="text" class="input-field" value="Name"></div>
                </div>
                <div class="input-group"><label class="input-label">Email</label><input type="email" class="input-field" value="user@example.com"></div>
                <div class="input-group"><label class="input-label">Phone</label><input type="tel" class="input-field" placeholder="+1 (555) 000-0000"></div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="input-group"><label class="input-label">Occupation</label><input type="text" class="input-field" placeholder="Software Engineer"></div>
                    <div class="input-group"><label class="input-label">Risk Profile</label><select class="input-field"><option>Moderate</option><option>Conservative</option><option>Aggressive</option></select></div>
                </div>
                <button type="submit" class="btn btn-primary btn-md">Save Changes</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}"""

def generate_settings():
    return """{% extends "dashboard_base.html" %}
{% block title %}Settings{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Settings</h1>
            <p class="text-gray-500 mt-1">Customize your experience</p>
        </div>
    </div>

    <div class="grid lg:grid-cols-4 gap-6">
        <div class="card lg:col-span-1">
            <nav class="space-y-1">
                {% set settings_tabs = [
                    ('Appearance', 'Sun'),
                    ('Notifications', 'Bell'),
                    ('Security', 'Lock'),
                    ('Privacy', 'Shield'),
                    ('Preferences', 'Settings'),
                    ('API & Integrations', 'Link')
                ] %}
                {% for label, icon in settings_tabs %}
                <button class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors {% if loop.first %}bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100{% endif %}">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
                    {{ label }}
                </button>
                {% endfor %}
            </nav>
        </div>
        <div class="card lg:col-span-3">
            <h3 class="text-lg font-semibold mb-6">Appearance</h3>
            <div class="space-y-6">
                <div>
                    <label class="text-sm font-medium block mb-3">Theme</label>
                    <div class="flex gap-3">
                        <button onclick="setTheme('light')" class="flex-1 p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-emerald-500 transition-colors text-center">
                            <svg class="h-6 w-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                            <span class="text-sm">Light</span>
                        </button>
                        <button onclick="setTheme('dark')" class="flex-1 p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-emerald-500 transition-colors text-center">
                            <svg class="h-6 w-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                            <span class="text-sm">Dark</span>
                        </button>
                        <button onclick="setTheme('system')" class="flex-1 p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-emerald-500 transition-colors text-center">
                            <svg class="h-6 w-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                            <span class="text-sm">System</span>
                        </button>
                    </div>
                </div>
                <div>
                    <label class="text-sm font-medium block mb-3">Currency</label>
                    <select class="input-field w-48"><option>USD ($)</option><option>EUR (€)</option><option>GBP (£)</option><option>INR (₹)</option></select>
                </div>
                <div>
                    <label class="text-sm font-medium block mb-3">Language</label>
                    <select class="input-field w-48"><option>English</option><option>Spanish</option><option>French</option><option>German</option></select>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

def generate_help():
    return """{% extends "dashboard_base.html" %}
{% block title %}Help Center{% endblock %}
{% block dashboard_content %}
<div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Help Center</h1>
            <p class="text-gray-500 mt-1">Find answers and get support</p>
        </div>
    </div>

    <div class="card">
        <div class="max-w-xl mx-auto text-center">
            <h2 class="text-xl font-semibold mb-2">How can we help you?</h2>
            <div class="relative mt-4">
                <input type="text" class="input-field pl-10" placeholder="Search for help articles...">
                <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
        </div>
    </div>

    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {% set help_items = [
            ('Getting Started', 'Learn the basics of FinSight', 'BookOpen'),
            ('Managing Expenses', 'How to track and categorize expenses', 'Wallet'),
            ('Creating Budgets', 'Set up and manage your budgets', 'PiggyBank'),
            ('Investment Tracking', 'Monitor your investment portfolio', 'TrendingUp'),
            ('Financial Goals', 'Set and achieve financial goals', 'Target'),
            ('Reports & Analytics', 'Generate financial reports', 'BarChart3'),
            ('Account Settings', 'Manage your account preferences', 'Settings'),
            ('Security', 'Keep your account secure', 'Shield'),
            ('FAQs', 'Frequently asked questions', 'HelpCircle')
        ] %}
        {% for title, desc, icon in help_items %}
        <div class="card hover:shadow-md transition-shadow cursor-pointer">
            <div class="h-12 w-12 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-500 mb-4">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
            </div>
            <h3 class="text-lg font-semibold mb-1">{{ title }}</h3>
            <p class="text-sm text-gray-500">{{ desc }}</p>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

def generate_verify_email():
    return """{% extends "base.html" %}
{% block title %}Verify Email{% endblock %}
{% block content %}
<div class="min-h-screen flex items-center justify-center p-4">
    <div class="text-center max-w-md animate-fade-in">
        {% if status == 'loading' %}
        <div class="spinner h-12 w-12 mx-auto"></div>
        {% elif status == 'success' %}
        <div class="h-16 w-16 rounded-full bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center mx-auto mb-4">
            <svg class="h-8 w-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
        <h1 class="text-2xl font-bold mb-2">Email Verified!</h1>
        <p class="text-gray-500 mb-6">Your email has been verified successfully.</p>
        <a href="/dashboard" class="btn btn-primary btn-md">Go to Dashboard</a>
        {% else %}
        <div class="h-16 w-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mx-auto mb-4">
            <svg class="h-8 w-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
        <h1 class="text-2xl font-bold mb-2">Verification Failed</h1>
        <p class="text-gray-500 mb-6">The verification link is invalid or expired.</p>
        <a href="/login" class="btn btn-primary btn-md">Back to Login</a>
        {% endif %}
    </div>
</div>
{% endblock %}"""

def generate_app_py():
    return """from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, 
    template_folder='frontend/templates',
    static_folder='frontend/static'
)
CORS(app)

# ============================
# Page Routes
# ============================

@app.route('/')
def landing():
    return render_template('landing/landing.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('auth/forgot_password.html')

@app.route('/reset-password')
def reset_password():
    token = request.args.get('token', '')
    return render_template('auth/reset_password.html', token=token)

@app.route('/verify-email')
def verify_email():
    return render_template('auth/verify_email.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard/dashboard.html')

@app.route('/expenses')
def expenses():
    return render_template('expenses/expenses.html')

@app.route('/budget')
def budget():
    return render_template('budget/budget.html')

@app.route('/investments')
def investments():
    return render_template('investments/investments.html')

@app.route('/goals')
def goals():
    return render_template('goals/goals.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics/analytics.html')

@app.route('/reports')
def reports():
    return render_template('reports/reports.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications/notifications.html')

@app.route('/profile')
def profile():
    return render_template('profile/profile.html')

@app.route('/settings')
def settings():
    return render_template('settings/settings.html')

@app.route('/help')
def help_center():
    return render_template('help/help.html')

# ============================
# API Routes (Proxied to Backend)
# ============================

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def api_proxy(path):
    import requests
    backend_url = f"http://localhost:5000/api/{path}"
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'content-length']}
    try:
        resp = requests.request(
            method=request.method,
            url=backend_url,
            headers=headers,
            json=request.get_json(silent=True) if request.method in ['POST', 'PUT', 'PATCH'] else None,
            params=request.args,
            cookies=request.cookies
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'message': 'Backend service unavailable'}), 503

# ============================
# Error Handlers
# ============================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
"""

def generate_error_pages():
    return """{% extends "base.html" %}
{% block title %}Page Not Found{% endblock %}
{% block content %}
<div class="min-h-screen flex items-center justify-center p-4">
    <div class="text-center max-w-md">
        <div class="text-8xl font-bold text-emerald-500 mb-4">404</div>
        <h1 class="text-2xl font-bold mb-2">Page Not Found</h1>
        <p class="text-gray-500 mb-8">The page you're looking for doesn't exist or has been moved.</p>
        <a href="/dashboard" class="btn btn-primary btn-md">Go to Dashboard</a>
    </div>
</div>
{% endblock %}"""

def generate_500():
    return """{% extends "base.html" %}
{% block title %}Server Error{% endblock %}
{% block content %}
<div class="min-h-screen flex items-center justify-center p-4">
    <div class="text-center max-w-md">
        <div class="text-8xl font-bold text-red-500 mb-4">500</div>
        <h1 class="text-2xl font-bold mb-2">Something went wrong</h1>
        <p class="text-gray-500 mb-8">Our team has been notified. Please try again later.</p>
        <a href="/dashboard" class="btn btn-primary btn-md">Go to Dashboard</a>
    </div>
</div>
{% endblock %}"""

def main():
    print("=" * 60)
    print("  FinSight Complete Frontend Generator")
    print("=" * 60)
    
    ensure_dirs()
    
    print("\n[1/5] Creating base templates...")
    write_file(os.path.join(TEMPLATES_DIR, 'base.html'), generate_base_template())
    write_file(os.path.join(TEMPLATES_DIR, 'auth_base.html'), generate_auth_base())
    write_file(os.path.join(TEMPLATES_DIR, 'dashboard_base.html'), generate_dashboard_base())
    write_file(os.path.join(TEMPLATES_DIR, '404.html'), generate_error_pages())
    write_file(os.path.join(TEMPLATES_DIR, '500.html'), generate_500())
    
    print("\n[2/5] Creating static files...")
    write_file(os.path.join(CSS_DIR, 'main.css'), generate_css())
    write_file(os.path.join(JS_DIR, 'main.js'), generate_js())
    
    print("\n[3/5] Creating auth pages...")
    write_file(os.path.join(TEMPLATES_DIR, 'auth', 'login.html'), generate_login())
    write_file(os.path.join(TEMPLATES_DIR, 'auth', 'register.html'), generate_register())
    write_file(os.path.join(TEMPLATES_DIR, 'auth', 'forgot_password.html'), generate_forgot_password())
    write_file(os.path.join(TEMPLATES_DIR, 'auth', 'reset_password.html'), generate_reset_password())
    write_file(os.path.join(TEMPLATES_DIR, 'auth', 'verify_email.html'), generate_verify_email())
    
    print("\n[4/5] Creating application pages...")
    write_file(os.path.join(TEMPLATES_DIR, 'landing', 'landing.html'), generate_landing())
    write_file(os.path.join(TEMPLATES_DIR, 'dashboard', 'dashboard.html'), generate_dashboard())
    write_file(os.path.join(TEMPLATES_DIR, 'expenses', 'expenses.html'), generate_expenses())
    write_file(os.path.join(TEMPLATES_DIR, 'budget', 'budget.html'), generate_budget())
    write_file(os.path.join(TEMPLATES_DIR, 'investments', 'investments.html'), generate_investments())
    write_file(os.path.join(TEMPLATES_DIR, 'goals', 'goals.html'), generate_goals())
    write_file(os.path.join(TEMPLATES_DIR, 'analytics', 'analytics.html'), generate_analytics())
    write_file(os.path.join(TEMPLATES_DIR, 'reports', 'reports.html'), generate_reports())
    write_file(os.path.join(TEMPLATES_DIR, 'notifications', 'notifications.html'), generate_notifications())
    write_file(os.path.join(TEMPLATES_DIR, 'profile', 'profile.html'), generate_profile())
    write_file(os.path.join(TEMPLATES_DIR, 'settings', 'settings.html'), generate_settings())
    write_file(os.path.join(TEMPLATES_DIR, 'help', 'help.html'), generate_help())
    
    print("\n[5/5] Creating Flask application...")
    write_file(os.path.join(BASE_DIR, 'app.py'), generate_app_py())
    
    print("\n" + "=" * 60)
    print("  ✅ FinSight Frontend Generated Successfully!")
    print("=" * 60)
    print(f"\n  Templates: {TEMPLATES_DIR}")
    print(f"  Static:    {STATIC_DIR}")
    print(f"  App:       {os.path.join(BASE_DIR, 'app.py')}")
    print("\n  Run: python app.py")
    print("  Open: http://localhost:3000")
    print("=" * 60)

if __name__ == '__main__':
    main()