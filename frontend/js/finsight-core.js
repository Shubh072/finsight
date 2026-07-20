/**
 * ============================================================
 * FinSight Core v3.0 - Premium Fintech Application Framework
 * ============================================================
 * Handles: State Management, Routing, Components, Toast,
 * Modal, Drawer, Charts, Theme, Animations, API Client
 * ============================================================
 */
const FinSight = (() => {
  'use strict';

  const CONFIG = {
    apiBase: '',
    tokenKey: 'finsight_token',
    userKey: 'finsight_user',
    themeKey: 'finsight_theme',
    sidebarKey: 'finsight_sidebar',
    toastDuration: 4000,
    toastMax: 5,
    drawerDuration: 300,
    modalDuration: 200,
    apiTimeout: 30000,
    currency: 'INR',
    locale: 'en-IN',
    dateFormat: { year: 'numeric', month: 'short', day: 'numeric' },
  };

  const state = {
    user: null,
    theme: localStorage.getItem(CONFIG.themeKey) || 'dark',
    sidebarOpen: false,
    sidebarCollapsed: localStorage.getItem(CONFIG.sidebarKey) === 'true',
    currentPage: 'dashboard',
    notifications: 3,
    isLoading: false,
    observers: {},
    modals: 0,
  };

  document.documentElement.classList.toggle('dark', state.theme === 'dark');

  const store = {
    get(key) { return state[key]; },
    set(key, value) { state[key] = value; this.notify(key, value); },
    subscribe(key, fn) {
      if (!state.observers[key]) state.observers[key] = [];
      state.observers[key].push(fn);
      return () => { state.observers[key] = state.observers[key].filter(f => f !== fn); };
    },
    notify(key, value) { (state.observers[key] || []).forEach(fn => fn(value)); },
  };

  const utils = {
    getToken() {
      return localStorage.getItem('finsight_token') || localStorage.getItem('access_token');
    },
    getUser() {
      try {
        const raw = localStorage.getItem('finsight_user') || localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    },
    formatCurrency(amount) {
      const num = parseFloat(amount) || 0;
      return new Intl.NumberFormat(CONFIG.locale, { style: 'currency', currency: CONFIG.currency, minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(num);
    },
    formatNumber(num) { return new Intl.NumberFormat(CONFIG.locale).format(num || 0); },
    formatDate(date, format) {
      if (!date) return '-';
      return new Date(date).toLocaleDateString(CONFIG.locale, format || CONFIG.dateFormat);
    },
    formatRelativeTime(date) {
      const now = new Date();
      const d = new Date(date);
      const diff = now - d;
      const mins = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);
      if (mins < 1) return 'Just now';
      if (mins < 60) return `${mins}m ago`;
      if (hours < 24) return `${hours}h ago`;
      if (days < 7) return `${days}d ago`;
      return d.toLocaleDateString(CONFIG.locale, { month: 'short', day: 'numeric' });
    },
    formatPercentage(value, decimals) {
      const num = parseFloat(value) || 0;
      return `${num >= 0 ? '+' : ''}${num.toFixed(decimals || 1)}%`;
    },
    truncate(str, len) {
      if (!str) return '';
      return str.length > (len || 30) ? str.substring(0, (len || 30)) + '...' : str;
    },
    generateId() { return Date.now().toString(36) + Math.random().toString(36).substring(2, 9); },
    getInitials(name) {
      if (!name) return '?';
      return name.split(' ').map(w => w[0]).join('').toUpperCase().substring(0, 2);
    },
    randomBetween(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; },
  };

  const toast = {
    container: null,
    init() {
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
      }
    },
    show(title, message, type, duration) {
      this.init();
      duration = duration || CONFIG.toastDuration;
      const toasts = this.container.querySelectorAll('.toast');
      if (toasts.length >= CONFIG.toastMax) {
        toasts[0].classList.add('removing');
        setTimeout(() => toasts[0].remove(), 300);
      }
      const icons = { success: 'check_circle', error: 'error', warning: 'warning', info: 'info' };
      const el = document.createElement('div');
      el.className = 'toast';
      el.innerHTML = `<div class="toast-icon ${type}"><span class="material-symbols-outlined">${icons[type] || 'info'}</span></div><div class="toast-content"><div class="toast-title">${title}</div><div class="toast-message">${message}</div></div><button class="toast-close" onclick="this.closest('.toast').classList.add('removing');setTimeout(()=>this.closest('.toast').remove(),300)"><span class="material-symbols-outlined">close</span></button>`;
      this.container.appendChild(el);
      if (duration > 0) {
        setTimeout(() => {
          if (el.parentNode) { el.classList.add('removing'); setTimeout(() => el.remove(), 300); }
        }, duration);
      }
      return el;
    },
    success(title, message, duration) { return this.show(title, message, 'success', duration); },
    error(title, message, duration) { return this.show(title, message, 'error', duration || 6000); },
    warning(title, message, duration) { return this.show(title, message, 'warning', duration); },
    info(title, message, duration) { return this.show(title, message, 'info', duration); },
    apiError(err) {
      let message = 'An error occurred';
      if (err.response?.data?.message) {
        message = err.response.data.message;
      } else if (err.response?.data?.error) {
        message = err.response.data.error;
      } else if (err.message) {
        message = err.message;
      } else if (typeof err === 'string') {
        message = err;
      }
      return this.show('Error', message, 'error');
    },
  };

  const modal = {
    overlay: null,
    init() {
      if (!this.overlay) {
        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';
        this.overlay.addEventListener('click', (e) => { if (e.target === this.overlay) this.close(); });
        document.body.appendChild(this.overlay);
      }
    },
    open(content, options) {
      options = options || {};
      this.init();
      const { title = '', width = '480px', showClose = true } = options;
      this.overlay.innerHTML = `<div class="modal" style="max-width:${width}"><div class="modal-header"><div class="modal-title">${title}</div>${showClose ? '<button class="modal-close" data-modal-close><span class="material-symbols-outlined">close</span></button>' : ''}</div><div class="modal-body">${content}</div></div>`;
      const closeBtn = this.overlay.querySelector('[data-modal-close]');
      if (closeBtn) closeBtn.addEventListener('click', () => this.close());
      requestAnimationFrame(() => this.overlay.classList.add('active'));
      this.activeModal = this.overlay;
      document.body.style.overflow = 'hidden';
      state.modals++;
      return this.overlay;
    },
    confirm(options) {
      options = options || {};
      const { title = 'Confirm', message = 'Are you sure?', confirmText = 'Confirm', cancelText = 'Cancel', variant = 'primary', onConfirm, onCancel } = options;
      const content = `<div style="text-align:center"><div class="empty-state-icon" style="margin:0 auto 16px;width:56px;height:56px;font-size:24px;background:var(--color-warning-bg);color:var(--color-warning)"><span class="material-symbols-outlined">help</span></div><h3 style="margin-bottom:8px;font-size:16px;font-weight:600">${title}</h3><p style="font-size:14px;color:var(--on-surface-muted);margin-bottom:24px">${message}</p><div class="flex gap-3 justify-center"><button class="btn btn-outline btn-md" data-cancel>${cancelText}</button><button class="btn ${variant === 'danger' ? 'btn-danger' : 'btn-primary'} btn-md" data-confirm>${confirmText}</button></div></div>`;
      const el = this.open(content, { title: '', showClose: false, width: '400px' });
      el.querySelector('[data-cancel]').addEventListener('click', () => { this.close(); if (onCancel) onCancel(); });
      el.querySelector('[data-confirm]').addEventListener('click', () => { this.close(); if (onConfirm) onConfirm(); });
    },
    close() {
      if (this.overlay) {
        this.overlay.classList.remove('active');
        state.modals = Math.max(0, state.modals - 1);
        if (state.modals === 0) document.body.style.overflow = '';
        setTimeout(() => { this.overlay.innerHTML = ''; }, CONFIG.modalDuration);
      }
    },
  };

  const drawer = {
    overlay: null,
    drawerEl: null,
    init() {
      if (!this.overlay) {
        this.overlay = document.createElement('div');
        this.overlay.className = 'drawer-overlay';
        this.overlay.addEventListener('click', (e) => { if (e.target === this.overlay) this.close(); });
        document.body.appendChild(this.overlay);
      }
      if (!this.drawerEl) {
        this.drawerEl = document.createElement('div');
        this.drawerEl.className = 'drawer';
        document.body.appendChild(this.drawerEl);
      }
    },
    open(content, options) {
      options = options || {};
      this.init();
      const { title = '', footer = '' } = options;
      this.drawerEl.innerHTML = `<div class="drawer-header"><div class="heading-2">${title}</div><button class="modal-close" data-drawer-close><span class="material-symbols-outlined">close</span></button></div><div class="drawer-body">${content}</div>${footer ? `<div class="drawer-footer">${footer}</div>` : ''}`;
      this.drawerEl.querySelector('[data-drawer-close]').addEventListener('click', () => this.close());
      requestAnimationFrame(() => { this.overlay.classList.add('active'); this.drawerEl.classList.add('active'); });
      document.body.style.overflow = 'hidden';
    },
    close() {
      this.overlay.classList.remove('active');
      this.drawerEl.classList.remove('active');
      document.body.style.overflow = '';
    },
    updateContent(content) {
      const body = this.drawerEl?.querySelector('.drawer-body');
      if (body) body.innerHTML = content;
    },
  };

  const theme = {
    toggle() {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      state.theme = newTheme;
      document.documentElement.classList.toggle('dark', newTheme === 'dark');
      localStorage.setItem(CONFIG.themeKey, newTheme);
      this.updateIcons();
      store.notify('theme', newTheme);
    },
    updateIcons() {
      document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
        const icon = btn.querySelector('.material-symbols-outlined');
        if (icon) icon.textContent = state.theme === 'dark' ? 'light_mode' : 'dark_mode';
      });
    },
    getCurrent() { return state.theme; },
  };

  const sidebar = {
    toggle() {
      state.sidebarCollapsed = !state.sidebarCollapsed;
      localStorage.setItem(CONFIG.sidebarKey, state.sidebarCollapsed);
      document.querySelector('.app-sidebar')?.classList.toggle('collapsed', state.sidebarCollapsed);
      document.querySelector('.app-main')?.classList.toggle('expanded', state.sidebarCollapsed);
    },
    toggleMobile() {
      state.sidebarOpen = !state.sidebarOpen;
      document.querySelector('.app-sidebar')?.classList.toggle('mobile-open', state.sidebarOpen);
      if (state.sidebarOpen) {
        const overlay = document.createElement('div');
        overlay.className = 'drawer-overlay mobile-sidebar-overlay active';
        overlay.style.position = 'fixed';
        overlay.style.zIndex = '299';
        overlay.addEventListener('click', () => sidebar.toggleMobile());
        document.body.appendChild(overlay);
      } else {
        document.querySelector('.mobile-sidebar-overlay')?.remove();
      }
    },
  };

  function addRippleEffect() {
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn');
      if (!btn) return;
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
      ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }

  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.header-search input');
        if (searchInput) searchInput.focus();
      }
      if (e.key === 'Escape') {
        if (state.modals > 0) modal.close();
        if (document.querySelector('.drawer.active')) drawer.close();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        sidebar.toggle();
      }
    });
  }

  function setupDropdowns() {
    document.addEventListener('click', (e) => {
      const dropdown = e.target.closest('[data-dropdown]');
      document.querySelectorAll('[data-dropdown].active').forEach(d => { if (d !== dropdown) d.classList.remove('active'); });
      if (dropdown) { dropdown.classList.toggle('active'); e.stopPropagation(); }
    });
    document.addEventListener('click', () => {
      document.querySelectorAll('[data-dropdown].active').forEach(d => d.classList.remove('active'));
    });
  }

  function init() {
    addRippleEffect();
    setupKeyboardShortcuts();
    setupDropdowns();

    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.addEventListener('click', () => theme.toggle());
    });
    theme.updateIcons();

    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    document.querySelectorAll('.search-shortcut').forEach(el => {
      el.textContent = isMac ? '⌘K' : 'Ctrl+K';
    });

    document.querySelectorAll('[data-mobile-menu]').forEach(btn => {
      btn.addEventListener('click', () => sidebar.toggleMobile());
    });

    document.querySelectorAll('[data-logout]').forEach(btn => {
      btn.addEventListener('click', () => {
        modal.confirm({
          title: 'Sign Out',
          message: 'Are you sure you want to sign out?',
          confirmText: 'Sign Out',
          variant: 'danger',
          onConfirm: () => {
            localStorage.removeItem(CONFIG.tokenKey);
            localStorage.removeItem(CONFIG.userKey);
            toast.success('Signed Out', 'You have been signed out successfully');
            setTimeout(() => { window.location.href = '/login.html'; }, 800);
          },
        });
      });
    });

    const userData = localStorage.getItem(CONFIG.userKey);
    if (userData) {
      try {
        const user = JSON.parse(userData);
        document.querySelectorAll('[data-user-name]').forEach(el => { el.textContent = user.name || 'User'; });
        document.querySelectorAll('.header-avatar img').forEach(img => {
          img.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || 'User')}&background=7c3aed&color=fff&size=80`;
        });
      } catch (e) {}
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  return {
    config: CONFIG, state, store, utils, toast, modal, drawer, theme, sidebar,
    showLoading(skeletonId, contentId, delay) {
      delay = delay || 800;
      const skeleton = document.getElementById(skeletonId);
      const content = document.getElementById(contentId);
      if (skeleton) skeleton.style.display = '';
      if (content) content.style.display = 'none';
      setTimeout(() => {
        if (skeleton) skeleton.style.display = 'none';
        if (content) { content.style.display = ''; content.classList.add('fade-in'); }
      }, delay);
    },
    showEmpty(containerId, options) {
      options = options || {};
      const { icon = 'inbox', title = 'No data', message = 'Nothing to show yet', action = '' } = options;
      const container = document.getElementById(containerId);
      if (!container) return;
      container.innerHTML = `<div class="empty-state"><div class="empty-state-icon"><span class="material-symbols-outlined">${icon}</span></div><h3>${title}</h3><p>${message}</p>${action}</div>`;
    },
    showError(containerId, options) {
      options = options || {};
      const { message = 'Something went wrong', onRetry } = options;
      const container = document.getElementById(containerId);
      if (!container) return;
      const retryBtn = onRetry ? `<button class="btn btn-primary btn-md" data-retry>Retry</button>` : '';
      container.innerHTML = `<div class="error-state"><div class="error-state-icon"><span class="material-symbols-outlined">error_outline</span></div><h3>Oops! An error occurred</h3><p>${message}</p>${retryBtn}</div>`;
      if (onRetry) container.querySelector('[data-retry]').addEventListener('click', onRetry);
    },
  };
})();

window.FinSight = FinSight;