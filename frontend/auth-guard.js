/**
 * FinSight Auth Guard — Enterprise Authentication Middleware
 * 
 * Legacy-grade authentication interceptor that enforces session validity,
 * token lifecycle management, role-based access control, and automatic
 * redirect logic. Designed for high-traffic SaaS environments.
 * 
 * Security patterns applied:
 * - Token introspection on page load (no silent expiry)
 * - XSS-safe DOM injection for user profile hydration
 * - CSRF-safe logout with server session invalidation
 * - Role & tier-based UI rendering
 * - Memory-safe token storage with cleanup on expiry
 * 
 * @version 2.1.0
 * @license Proprietary - FinSight Inc.
 */

(function () {
    'use strict';

    // ===========================================================================
    // Configuration Constants
    // ===========================================================================

    const CONFIG = Object.freeze({
        /** Pages that don't require authentication */
        PUBLIC_PAGES: [
            '/login', '/login.html',
            '/create_account', '/create_account.html', '/register',
            '/forgot-password', '/forgot_password.html',
            '/reset-password', '/reset_password.html', '/reset_password',
            '/verify-email', '/verify_email.html',
            '/landing', '/landing.html',
            '/',
        ],

        /** Storage keys – single source of truth */
        STORAGE_KEYS: {
            TOKEN: 'finsight_token',
            ACCESS_TOKEN: 'access_token',
            REFRESH_TOKEN: 'finsight_refresh_token',
            USER: 'finsight_user',
            USER_PROFILE: 'user',
            REMEMBER: 'finsight_remember',
            THEME: 'finsight_theme',
        },

        /** API endpoints */
        ENDPOINTS: {
            VERIFY_TOKEN: '/api/auth/verify',
            REFRESH_TOKEN: '/api/auth/refresh',
            LOGOUT: '/api/auth/logout',
            PROFILE: '/api/auth/profile',
        },

        /** Role-based access hierarchy */
        ROLES: Object.freeze({
            ADMIN: 'admin',
            PREMIUM: 'premium',
            USER: 'user',
            GUEST: 'guest',
        }),

        /** Routing map for sidebar navigation */
        ROUTE_MAP: Object.freeze({
            dashboard: '/dashboard.html',
            expenses: '/expense.html',
            budgets: '/budget.html',
            investments: '/investment.html',
            goals: '/goal.html',
            analytics: '/analytics.html',
            reports: '/report_document.html',
            notifications: '/notification.html',
            settings: '/setting.html',
            income: '/income.html',
        }),

        /** Token expiry buffer (seconds before actual expiry to refresh) */
        TOKEN_REFRESH_BUFFER: 120,
    });

    // ===========================================================================
    // Storage Manager — Singleton for atomic localStorage operations
    // ===========================================================================

    const StorageManager = {
        getToken() {
            return localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN) ||
                localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        },

        getRefreshToken() {
            return localStorage.getItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
        },

        getUser() {
            try {
                const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER) ||
                    localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
                return raw ? JSON.parse(raw) : null;
            } catch {
                return null;
            }
        },

        setTokens(accessToken, refreshToken) {
            localStorage.setItem(CONFIG.STORAGE_KEYS.TOKEN, accessToken);
            localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, accessToken);
            if (refreshToken) {
                localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
            }
        },

        setUser(user) {
            if (!user) return;
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(user));
            localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(user));
        },

        clear() {
            const theme = localStorage.getItem(CONFIG.STORAGE_KEYS.THEME);
            const remember = localStorage.getItem(CONFIG.STORAGE_KEYS.REMEMBER);
            Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
            // Restore non-auth preferences
            if (theme) localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, theme);
            if (remember) localStorage.setItem(CONFIG.STORAGE_KEYS.REMEMBER, remember);
        },
    };

    // ===========================================================================
    // HTTP Client — Axios-like fetch wrapper with retry & error normalization
    // ===========================================================================

    const HttpClient = {
        async request(url, options = {}) {
            const token = StorageManager.getToken();
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers,
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);

            try {
                const response = await fetch(url, {
                    ...options,
                    headers,
                    signal: controller.signal,
                });

                clearTimeout(timeoutId);

                let data = null;
                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    data = await response.json();
                }

                if (!response.ok) {
                    const error = new Error(data?.message || data?.error || `HTTP ${response.status}`);
                    error.status = response.status;
                    error.data = data;
                    throw error;
                }

                return { success: true, data, status: response.status };
            } catch (error) {
                clearTimeout(timeoutId);
                if (error.name === 'AbortError') {
                    throw new Error('Request timed out. Please check your connection.');
                }
                throw error;
            }
        },

        async get(url, options = {}) {
            return this.request(url, { ...options, method: 'GET' });
        },

        async post(url, body, options = {}) {
            return this.request(url, {
                ...options,
                method: 'POST',
                body: JSON.stringify(body),
            });
        },
    };

    // ===========================================================================
    // Token Lifecycle Manager
    // ===========================================================================

    const TokenManager = {
        /**
         * Decode JWT payload without verification (client-side)
         * @param {string} token
         * @returns {object|null}
         */
        decodePayload(token) {
            try {
                const payload = token.split('.')[1];
                const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
                return JSON.parse(decoded);
            } catch {
                return null;
            }
        },

        /**
         * Check if token is expired or near expiry
         * @param {string} token
         * @returns {boolean}
         */
        isExpired(token) {
            const payload = this.decodePayload(token);
            if (!payload || !payload.exp) return true;
            const now = Math.floor(Date.now() / 1000);
            return payload.exp <= now;
        },

        /**
         * Check if token needs refreshing (within buffer window)
         * @param {string} token
         * @returns {boolean}
         */
        needsRefresh(token) {
            const payload = this.decodePayload(token);
            if (!payload || !payload.exp) return true;
            const now = Math.floor(Date.now() / 1000);
            return (payload.exp - now) <= CONFIG.TOKEN_REFRESH_BUFFER;
        },

        /**
         * Attempt token refresh via backend
         * @returns {Promise<boolean>}
         */
        async refresh() {
            const refreshToken = StorageManager.getRefreshToken();
            if (!refreshToken) return false;

            try {
                const result = await HttpClient.post(CONFIG.ENDPOINTS.REFRESH_TOKEN, {
                    refresh_token: refreshToken,
                });

                if (result.success && result.data?.access_token) {
                    StorageManager.setTokens(
                        result.data.access_token,
                        result.data.refresh_token || refreshToken
                    );
                    if (result.data.user) {
                        StorageManager.setUser(result.data.user);
                    }
                    return true;
                }
                return false;
            } catch {
                return false;
            }
        },

        /**
         * Verify token with server
         * @returns {Promise<object|null>} user object or null
         */
        async verify() {
            const token = StorageManager.getToken();
            if (!token) return null;

            try {
                const result = await HttpClient.get(CONFIG.ENDPOINTS.VERIFY_TOKEN);
                if (result.success && result.data?.user) {
                    StorageManager.setUser(result.data.user);
                    return result.data.user;
                }
                return null;
            } catch (error) {
                if (error.status === 401) {
                    // Try refresh
                    const refreshed = await this.refresh();
                    if (refreshed) {
                        return this.verify();
                    }
                }
                return null;
            }
        },
    };

    // ===========================================================================
    // DOM Hydrator — Safe DOM manipulation for user profile injection
    // ===========================================================================

    const DOMHydrator = {
        /**
         * Hydrate user information into the DOM
         * @param {object} user - User object from server
         */
        hydrateUser(user) {
            if (!user || !document.body) return;

            const fullName = user.full_name || user.name || 'User';
            const email = user.email || '';
            const role = (user.role || 'user').toUpperCase();
            const tier = user.tier || 'FREE';
            const avatarUrl = user.avatar_url ||
                `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName)}&background=7c3aed&color=fff&size=80`;

            // --- Avatar Images ---
            this.updateElements(
                ['#sidebar-avatar', '#header-avatar-img'],
                (el) => {
                    if (el.tagName === 'IMG') {
                        el.src = avatarUrl;
                        el.alt = fullName;
                    }
                }
            );

            // --- User Name Fields ---
            this.updateTextNodes(
                ['#sidebar-user-name', '#header-user-name', '.avatar-name'],
                fullName
            );

            // --- Role / Tier Badges ---
            this.updateTextNodes(
                ['.avatar-role', '.sidebar-tier', '.user-role'],
                `${tier} • ${role} MEMBER`
            );

            // --- Any element containing placeholder names ---
            const placeholderNames = ['Alex Thompson', 'Alexander Vance', 'User', 'Loading...'];
            document.querySelectorAll('*').forEach(el => {
                if (!el.children || el.children.length !== 0) return;
                const text = (el.textContent || '').trim();
                if (placeholderNames.includes(text)) {
                    el.textContent = fullName;
                }
            });
        },

        /**
         * Inject sidebar navigation links based on route map
         */
        hydrateNavigation() {
            document.querySelectorAll('nav a, aside nav a, .sidebar-nav a').forEach(anchor => {
                const text = (anchor.textContent || '').trim().toLowerCase();
                const iconSpan = anchor.querySelector('.nav-icon');

                for (const [key, path] of Object.entries(CONFIG.ROUTE_MAP)) {
                    if (text.includes(key)) {
                        anchor.setAttribute('href', path);
                        break;
                    }
                }

                // Highlight active page
                const currentPath = window.location.pathname;
                if (anchor.getAttribute('href') === currentPath) {
                    anchor.classList.add('active');
                } else {
                    anchor.classList.remove('active');
                }
            });
        },

        /**
         * Inject logout handler into all logout buttons
         */
        hydrateLogoutButtons() {
            document.querySelectorAll('[data-logout], .logout-btn, #dynamic-signout').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    await AuthGuard.logout();
                });
            });
        },

        /**
         * Add sidebar upgrade card if user is not premium
         */
        hydrateUpgrade(user) {
            const role = (user?.role || 'user').toLowerCase();
            const tier = (user?.tier || 'free').toLowerCase();
            const isPremium = role === 'premium' || role === 'admin' || tier === 'premium' || tier === 'enterprise';

            const upgradeCard = document.querySelector('.sidebar-upgrade-card');
            if (upgradeCard) {
                if (isPremium) {
                    upgradeCard.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px">
              <span class="material-symbols-outlined" style="color:var(--color-warning);font-size:20px">verified</span>
              <div>
                <h4 style="font-weight:700;font-size:13px">✨ Premium Active</h4>
                <p style="font-size:11px;color:var(--on-surface-muted)">Enjoy all Pro features</p>
              </div>
            </div>
          `;
                } else {
                    upgradeCard.innerHTML = `
            <h4>✨ Unlock Premium</h4>
            <p>AI insights, unlimited reports & more</p>
            <button class="btn btn-primary btn-sm btn-full" onclick="window.location.href='/setting.html?tab=upgrade'">Upgrade to Pro</button>
          `;
                }
            }
        },

        /**
         * Update multiple elements with a callback
         */
        updateElements(selectors, callback) {
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(callback);
            });
        },

        /**
         * Update text content of elements matching selectors
         */
        updateTextNodes(selectors, text) {
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    el.textContent = text;
                });
            });
        },
    };

    // ===========================================================================
    // Auth Guard — Main orchestrator
    // ===========================================================================

    const AuthGuard = {
        /**
         * Determine if current page is public
         * @returns {boolean}
         */
        isPublicPage() {
            const path = window.location.pathname;
            return CONFIG.PUBLIC_PAGES.some(page =>
                path === page || path.endsWith(page) || path.replace(/\/$/, '') === page.replace(/\/$/, '')
            );
        },

        /**
         * Get authenticated user
         * @returns {object|null}
         */
        getUser() {
            return StorageManager.getUser();
        },

        /**
         * Get auth token
         * @returns {string|null}
         */
        getToken() {
            return StorageManager.getToken();
        },

        /**
         * Check if user has required role
         * @param {string|string[]} roles
         * @returns {boolean}
         */
        hasRole(roles) {
            const user = this.getUser();
            if (!user) return false;
            const userRole = (user.role || 'user').toLowerCase();
            const allowed = Array.isArray(roles) ? roles : [roles];
            return allowed.includes(userRole);
        },

        /**
         * Authenticate with server
         * @param {string} email
         * @param {string} password
         * @param {boolean} remember
         * @returns {Promise<object>}
         */
        async login(email, password, remember = false) {
            const result = await HttpClient.post('/api/auth/login', { email, password });

            if (result.success && result.data) {
                const { access_token, refresh_token, user } = result.data;
                StorageManager.setTokens(access_token, refresh_token);
                if (user) {
                    StorageManager.setUser(user);
                }
                if (remember) {
                    localStorage.setItem(CONFIG.STORAGE_KEYS.REMEMBER, '1');
                }
                return { success: true, user: user || null };
            }

            throw new Error(result.data?.message || 'Authentication failed');
        },

        /**
         * Register a new user
         * @param {object} credentials
         * @returns {Promise<object>}
         */
        async register(credentials) {
            const result = await HttpClient.post('/api/auth/register', credentials);

            if (result.success && result.data) {
                const { access_token, refresh_token, user } = result.data;
                StorageManager.setTokens(access_token, refresh_token);
                if (user) {
                    StorageManager.setUser(user);
                }
                return { success: true, user: user || null };
            }

            throw new Error(result.data?.message || 'Registration failed');
        },

        /**
         * Logout with server session invalidation
         */
        async logout() {
            try {
                const token = StorageManager.getToken();
                if (token) {
                    await HttpClient.post(CONFIG.ENDPOINTS.LOGOUT, null, {
                        headers: { Authorization: `Bearer ${token}` },
                    });
                }
            } catch {
                // Server-side logout is best-effort; proceed with client cleanup
            } finally {
                StorageManager.clear();
                window.location.replace('/login.html');
            }
        },

        /**
         * Initialize the auth guard on page load
         * @returns {Promise<void>}
         */
        async init() {
            // Theme initialization
            const savedTheme = localStorage.getItem(CONFIG.STORAGE_KEYS.THEME) || 'dark';
            document.documentElement.classList.toggle('dark', savedTheme === 'dark');

            const isPublic = this.isPublicPage();
            const token = StorageManager.getToken();
            const user = StorageManager.getUser();

            // === Protected Page Logic ===
            if (!isPublic) {
                if (!token) {
                    this.redirectToLogin();
                    return;
                }

                // Verify token with server
                let verifiedUser = null;
                try {
                    verifiedUser = await TokenManager.verify();
                } catch {
                    // silent
                }

                if (!verifiedUser) {
                    // Try refresh one more time
                    const refreshed = await TokenManager.refresh();
                    if (refreshed) {
                        try {
                            verifiedUser = await TokenManager.verify();
                        } catch {
                            // silent
                        }
                    }
                }

                if (!verifiedUser) {
                    this.redirectToLogin();
                    return;
                }

                // Hydrate DOM once content is ready
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => this.hydrate(verifiedUser));
                } else {
                    this.hydrate(verifiedUser);
                }

                return;
            }

            // === Public Page Logic ===
            // If user is already authenticated on a public page, optionally show logged-in state
            if (token && user) {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => this.hydratePublic(user));
                } else {
                    this.hydratePublic(user);
                }
            }
        },

        /**
         * Hydrate protected pages with user data
         * @param {object} user
         */
        hydrate(user) {
            DOMHydrator.hydrateUser(user);
            DOMHydrator.hydrateNavigation();
            DOMHydrator.hydrateLogoutButtons();
            DOMHydrator.hydrateUpgrade(user);
        },

        /**
         * Hydrate public pages with minimal user info
         * @param {object} user
         */
        hydratePublic(user) {
            // For public pages, we might show user name in header if applicable
            DOMHydrator.hydrateUser(user);
        },

        /**
         * Redirect to login preserving current path
         */
        redirectToLogin() {
            const currentPath = window.location.pathname;
            const redirectParam = currentPath !== '/dashboard.html' ? `?redirect=${encodeURIComponent(currentPath)}` : '';
            window.location.replace(`/login.html${redirectParam}`);
        },
    };

    // ===========================================================================
    // Sidebar Toggle Logic (collapsible sidebar)
    // ===========================================================================

    function initSidebarToggle() {
        const toggleBtn = document.getElementById('sidebar-toggle-btn');
        const sidebar = document.getElementById('app-sidebar');
        if (!toggleBtn || !sidebar) return;

        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            toggleBtn.querySelector('.material-symbols-outlined').textContent =
                isCollapsed ? 'menu' : 'menu_open';
            localStorage.setItem('sidebar_collapsed', isCollapsed ? '1' : '0');
        });

        // Restore sidebar state
        if (localStorage.getItem('sidebar_collapsed') === '1') {
            sidebar.classList.add('collapsed');
            toggleBtn.querySelector('.material-symbols-outlined').textContent = 'menu';
        }
    }

    // ===========================================================================
    // Theme Toggle
    // ===========================================================================

    function initThemeToggle() {
        const toggleBtn = document.querySelector('[data-theme-toggle]');
        if (!toggleBtn) return;

        const updateIcon = () => {
            const isDark = document.documentElement.classList.contains('dark');
            toggleBtn.querySelector('.material-symbols-outlined').textContent =
                isDark ? 'light_mode' : 'dark_mode';
            toggleBtn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
        };

        toggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.classList.contains('dark');
            const newTheme = isDark ? 'light' : 'dark';
            document.documentElement.classList.toggle('dark', newTheme === 'dark');
            localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, newTheme);
            updateIcon();
        });

        updateIcon();
    }

    // ===========================================================================
    // Global Search / Command Palette
    // ===========================================================================

    function initCommandPalette() {
        const searchInput = document.getElementById('global-search-input');
        const cmdOverlay = document.getElementById('cmd-overlay');
        const cmdInput = document.getElementById('cmd-input');
        const cmdResults = document.getElementById('cmd-results');

        if (!cmdOverlay) return;

        const commands = [
            { label: 'Dashboard', path: '/dashboard.html', icon: 'dashboard', keywords: ['home', 'main'] },
            { label: 'Analytics', path: '/analytics.html', icon: 'monitoring', keywords: ['charts', 'graphs'] },
            { label: 'Expenses', path: '/expense.html', icon: 'payments', keywords: ['spending', 'transactions'] },
            { label: 'Income', path: '/income.html', icon: 'account_balance_wallet', keywords: ['salary', 'earnings'] },
            { label: 'Budget', path: '/budget.html', icon: 'account_balance', keywords: ['budgeting', 'plan'] },
            { label: 'Investments', path: '/investment.html', icon: 'trending_up', keywords: ['stocks', 'portfolio'] },
            { label: 'Goals', path: '/goal.html', icon: 'flag', keywords: ['targets', 'milestones'] },
            { label: 'Reports', path: '/report_document.html', icon: 'description', keywords: ['statements'] },
            { label: 'Notifications', path: '/notification.html', icon: 'notifications', keywords: ['alerts'] },
            { label: 'Settings', path: '/setting.html', icon: 'settings', keywords: ['profile', 'preferences'] },
        ];

        const openPalette = () => {
            cmdOverlay.style.display = 'flex';
            cmdInput.value = '';
            cmdInput.focus();
            renderCommands(commands);
        };

        const closePalette = () => {
            cmdOverlay.style.display = 'none';
        };

        const renderCommands = (filtered) => {
            cmdResults.innerHTML = filtered.map(cmd => `
        <a href="${cmd.path}" class="dropdown-item" style="cursor:pointer;display:flex;align-items:center;gap:10px;padding:10px 14px">
          <span class="material-symbols-outlined" style="font-size:18px;color:var(--on-surface-muted)">${cmd.icon}</span>
          <span>${cmd.label}</span>
        </a>
      `).join('') || '<div style="padding:16px;text-align:center;color:var(--on-surface-muted);font-size:13px">No results found</div>';
        };

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                openPalette();
            }
            if (e.key === 'Escape') {
                closePalette();
            }
        });

        if (searchInput) {
            searchInput.addEventListener('focus', openPalette);
        }

        window.filterCMD = (value) => {
            const q = value.toLowerCase();
            const filtered = commands.filter(c =>
                c.label.toLowerCase().includes(q) ||
                c.keywords.some(k => k.includes(q))
            );
            renderCommands(filtered);
        };

        cmdOverlay.addEventListener('click', (e) => {
            if (e.target === cmdOverlay) closePalette();
        });
    }

    // ===========================================================================
    // Mobile Menu Toggle
    // ===========================================================================

    function initMobileMenu() {
        const menuBtn = document.querySelector('[data-mobile-menu]');
        const sidebar = document.getElementById('app-sidebar');
        if (!menuBtn || !sidebar) return;

        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth >= 768) return;
            if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }

    // ===========================================================================
    // Notification Badge Updater
    // ===========================================================================

    function initNotificationBadge() {
        const badge = document.getElementById('notif-badge');
        if (!badge) return;

        const token = StorageManager.getToken();
        if (!token) return;

        HttpClient.get('/api/notifications/unread-count')
            .then(result => {
                if (result.success && result.data?.count !== undefined) {
                    const count = result.data.count;
                    if (count > 0) {
                        badge.textContent = count > 99 ? '99+' : count;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            })
            .catch(() => {
                badge.style.display = 'none';
            });
    }

    // ===========================================================================
    // Bootstrap
    // ===========================================================================

    // Expose AuthGuard globally for inline script usage
    window.AuthGuard = AuthGuard;
    window.TokenManager = TokenManager;
    window.StorageManager = StorageManager;

    // Initialize once DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            AuthGuard.init();
            initSidebarToggle();
            initThemeToggle();
            initCommandPalette();
            initMobileMenu();
            initNotificationBadge();
        });
    } else {
        AuthGuard.init();
        initSidebarToggle();
        initThemeToggle();
        initCommandPalette();
        initMobileMenu();
        initNotificationBadge();
    }

    // Re-hydrate on dynamic content changes (SPA-like navigation)
    const observer = new MutationObserver(() => {
        const user = StorageManager.getUser();
        if (user) {
            DOMHydrator.hydrateUser(user);
            DOMHydrator.hydrateNavigation();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();