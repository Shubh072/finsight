/**
 * FinSight Layout Engine v3.0
 * Generates consistent sidebar, header, and shared layout structures
 * across all app pages. Handles auth guard, user population, and navigation.
 */

const FSLayout = (() => {
  'use strict';

  const NAV_ITEMS = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', href: '/dashboard.html', section: 'Main' },
    { id: 'analytics', icon: 'monitoring', label: 'Analytics', href: '/analytics.html', section: 'Main' },
    { id: 'expenses', icon: 'payments', label: 'Expenses', href: '/expense.html', section: 'Main' },
    { id: 'income', icon: 'account_balance_wallet', label: 'Income', href: '/income.html', section: 'Main' },
    { id: 'budget', icon: 'account_balance', label: 'Budget', href: '/budget.html', section: 'Main' },
    { id: 'investments', icon: 'trending_up', label: 'Investments', href: '/investment.html', section: 'Planning' },
    { id: 'goals', icon: 'flag', label: 'Goals', href: '/goal.html', section: 'Planning' },
    { id: 'reports', icon: 'description', label: 'Reports', href: '/report_document.html', section: 'Planning' },
    { id: 'notifications', icon: 'notifications', label: 'Notifications', href: '/notification.html', section: 'Account', badge: '3' },
    { id: 'settings', icon: 'settings', label: 'Settings', href: '/setting.html', section: 'Account' },
    { id: 'help', icon: 'help', label: 'Help Center', href: '/help.html', section: 'Account' },
  ];

  function detectCurrentPage() {
    const path = window.location.pathname;
    const file = path.split('/').pop().replace('.html', '');
    const map = {
      'dashboard': 'dashboard', 'analytics': 'analytics', 'expense': 'expenses',
      'income': 'income', 'budget': 'budget', 'investment': 'investments',
      'goal': 'goals', 'report_document': 'reports', 'notification': 'notifications',
      'setting': 'settings', 'help': 'help'
    };
    return map[file] || 'dashboard';
  }

  function renderSidebar() {
    const currentPage = detectCurrentPage();
    const sections = {};
    NAV_ITEMS.forEach(item => {
      if (!sections[item.section]) sections[item.section] = [];
      sections[item.section].push(item);
    });

    const sectionsHTML = Object.entries(sections).map(([title, items]) => `
      <div class="nav-section">
        <div class="nav-section-title">${title}</div>
        ${items.map(item => `
          <a href="${item.href}" class="nav-item${currentPage === item.id ? ' active' : ''}">
            <span class="nav-icon material-symbols-outlined">${item.icon}</span>
            <span class="nav-label">${item.label}</span>
            ${item.badge ? `<span class="nav-badge" id="nav-badge-${item.id}">${item.badge}</span>` : ''}
          </a>
        `).join('')}
      </div>
    `).join('');

    return `
      <aside class="app-sidebar" id="app-sidebar">
        <div class="sidebar-header">
          <a href="/dashboard.html" class="sidebar-logo">
            <div class="logo-icon">
              <span class="material-symbols-outlined" style="font-size:18px;color:white">insights</span>
            </div>
            <span>FinSight</span>
          </a>
          <button class="btn-icon btn-ghost btn-sm hide-mobile" id="sidebar-toggle-btn" aria-label="Collapse sidebar" title="Collapse (Ctrl+B)">
            <span class="material-symbols-outlined">menu_open</span>
          </button>
        </div>
        <nav class="sidebar-nav" aria-label="Main navigation">
          ${sectionsHTML}
        </nav>
        <div class="sidebar-footer">
          <div class="sidebar-upgrade-card">
            <h4>✨ Unlock Premium</h4>
            <p>AI insights, unlimited reports & more</p>
            <button class="btn btn-primary btn-sm btn-full" onclick="FSLayout.showUpgradeModal()">Upgrade to Pro</button>
          </div>
          <div class="flex items-center gap-3 mt-4 px-1" id="sidebar-user-mini" style="cursor:pointer" onclick="window.location.href='/setting.html'">
            <img id="sidebar-avatar" src="https://ui-avatars.com/api/?name=User&background=7c3aed&color=fff&size=80" alt="User" style="width:32px;height:32px;border-radius:50%;object-fit:cover;flex-shrink:0"/>
            <div style="flex:1;min-width:0">
              <div class="nav-label" id="sidebar-user-name" style="font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Loading...</div>
              <div style="font-size:11px;color:var(--on-surface-muted)">Free Plan</div>
            </div>
            <button class="btn-icon btn-ghost btn-sm" data-logout title="Sign out" onclick="event.stopPropagation()">
              <span class="material-symbols-outlined" style="font-size:18px">logout</span>
            </button>
          </div>
        </div>
      </aside>
    `;
  }

  function renderHeader(opts) {
    opts = opts || {};
    const { title = 'Dashboard', subtitle = '', actions = '' } = opts;
    return `
      <header class="app-header" role="banner">
        <button class="header-action-btn hide-desktop" data-mobile-menu aria-label="Open navigation menu">
          <span class="material-symbols-outlined">menu</span>
        </button>
        <div class="header-search" role="search">
          <span class="material-symbols-outlined search-icon" aria-hidden="true">search</span>
          <input type="text" id="global-search-input" placeholder="Search transactions, budgets, reports..." aria-label="Global search" autocomplete="off"/>
          <span class="search-shortcut" aria-hidden="true">Ctrl+K</span>
          <div id="search-dropdown" style="display:none;position:absolute;top:calc(100% + 8px);left:0;right:0;background:var(--surface-base);border:1px solid var(--outline);border-radius:var(--radius-lg);box-shadow:var(--shadow-xl);z-index:200;max-height:360px;overflow-y:auto;padding:8px"></div>
        </div>
        <div class="header-actions">
          <button class="header-action-btn" data-theme-toggle aria-label="Toggle dark/light mode">
            <span class="material-symbols-outlined">light_mode</span>
          </button>
          <button class="header-action-btn" onclick="window.location.href='/notification.html'" aria-label="Notifications" style="position:relative">
            <span class="material-symbols-outlined">notifications</span>
            <span class="notification-dot" id="header-notif-dot"></span>
          </button>
          <div class="header-avatar dropdown" data-dropdown role="button" aria-haspopup="true" aria-label="User menu">
            <img id="header-avatar-img" src="https://ui-avatars.com/api/?name=User&background=7c3aed&color=fff&size=80" alt="User avatar"/>
            <div class="avatar-info hide-mobile">
              <div class="avatar-name" id="header-user-name">Loading...</div>
              <div class="avatar-role" id="header-user-role">MEMBER</div>
            </div>
            <span class="material-symbols-outlined hide-mobile" style="font-size:16px;color:var(--on-surface-muted)">expand_more</span>
            <div class="dropdown-menu" role="menu">
              <div class="dropdown-header">Account</div>
              <a class="dropdown-item" href="/setting.html" role="menuitem">
                <span class="material-symbols-outlined">manage_accounts</span> My Profile
              </a>
              <a class="dropdown-item" href="/setting.html" role="menuitem">
                <span class="material-symbols-outlined">settings</span> Settings
              </a>
              <a class="dropdown-item" href="/notification.html" role="menuitem">
                <span class="material-symbols-outlined">notifications</span> Notifications
              </a>
              <a class="dropdown-item" href="/help.html" role="menuitem">
                <span class="material-symbols-outlined">help</span> Help Center
              </a>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" data-logout role="menuitem" style="color:var(--color-error)">
                <span class="material-symbols-outlined" style="color:var(--color-error)">logout</span> Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>
    `;
  }

  function renderCommandPalette() {
    return `
      <div id="command-palette-overlay" style="display:none;position:fixed;inset:0;background:var(--surface-overlay);z-index:600;align-items:flex-start;justify-content:center;padding-top:80px">
        <div style="width:100%;max-width:600px;background:var(--surface-base);border:1px solid var(--outline);border-radius:var(--radius-2xl);box-shadow:var(--shadow-2xl);overflow:hidden">
          <div style="display:flex;align-items:center;gap:12px;padding:16px 20px;border-bottom:1px solid var(--outline)">
            <span class="material-symbols-outlined" style="color:var(--on-surface-muted)">search</span>
            <input id="cmd-input" type="text" placeholder="Type a command or search..." style="flex:1;background:transparent;border:none;outline:none;font-size:15px;color:var(--on-surface);font-family:inherit"/>
            <kbd style="padding:2px 8px;background:var(--surface-container);border:1px solid var(--outline);border-radius:6px;font-size:12px;color:var(--on-surface-muted)">ESC</kbd>
          </div>
          <div id="cmd-results" style="max-height:400px;overflow-y:auto;padding:8px"></div>
        </div>
      </div>
    `;
  }

  function renderAIAssistant() {
    return `
      <div id="ai-fab" title="AI Financial Assistant" aria-label="Open AI Assistant" style="position:fixed;bottom:32px;right:32px;z-index:500;cursor:pointer" onclick="FSLayout.toggleAI()">
        <div style="width:56px;height:56px;background:var(--color-primary-gradient);border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow-xl),var(--shadow-neon);transition:transform 0.2s ease">
          <span class="material-symbols-outlined" style="color:white;font-size:26px">auto_awesome</span>
        </div>
        <div id="ai-pulse" style="position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--color-primary);opacity:0.4;animation:ai-pulse 2s ease-in-out infinite"></div>
      </div>
      <div id="ai-panel" style="display:none;position:fixed;bottom:104px;right:32px;width:380px;max-height:520px;background:var(--surface-base);border:1px solid var(--outline);border-radius:var(--radius-2xl);box-shadow:var(--shadow-2xl);z-index:500;flex-direction:column;overflow:hidden">
        <div style="padding:16px 20px;border-bottom:1px solid var(--outline);display:flex;align-items:center;gap:12px;background:var(--color-primary-gradient)">
          <span class="material-symbols-outlined" style="color:white;font-size:22px">auto_awesome</span>
          <div style="flex:1">
            <div style="color:white;font-weight:700;font-size:14px">FinSight AI</div>
            <div style="color:rgba(255,255,255,0.7);font-size:11px">Your financial intelligence assistant</div>
          </div>
          <button onclick="FSLayout.toggleAI()" style="color:rgba(255,255,255,0.7);width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:50%;transition:all 0.2s">
            <span class="material-symbols-outlined" style="font-size:18px">close</span>
          </button>
        </div>
        <div id="ai-messages" style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;min-height:200px;max-height:340px">
          <div class="ai-msg ai-msg-bot">
            <div style="background:var(--surface-container);padding:12px 14px;border-radius:var(--radius-lg);font-size:13px;line-height:1.5">
              👋 Hi! I'm your AI financial assistant. Ask me anything about your finances — spending patterns, budget advice, investment insights, or goal planning.
            </div>
          </div>
        </div>
        <div style="padding:12px;border-top:1px solid var(--outline)">
          <div style="display:flex;gap-2;margin-bottom:8px;flex-wrap:wrap">
            ${['Spending summary', 'Budget tips', 'Investment advice', 'Goal progress'].map(q =>
              `<button onclick="FSLayout.sendAIMessage('${q}')" style="padding:4px 10px;background:var(--color-primary-bg);color:var(--color-primary);border:1px solid rgba(124,58,237,0.2);border-radius:var(--radius-full);font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s">${q}</button>`
            ).join('')}
          </div>
          <div style="display:flex;gap:8px">
            <input id="ai-input" type="text" placeholder="Ask me anything..." style="flex:1;padding:8px 12px;background:var(--surface-container);border:1px solid var(--outline);border-radius:var(--radius-lg);font-size:13px;color:var(--on-surface);font-family:inherit;outline:none" onkeydown="if(event.key==='Enter')FSLayout.sendAIMessage()"/>
            <button onclick="FSLayout.sendAIMessage()" style="width:36px;height:36px;background:var(--color-primary-gradient);border-radius:var(--radius-lg);display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <span class="material-symbols-outlined" style="color:white;font-size:18px">send</span>
            </button>
          </div>
        </div>
      </div>
      <style>
        @keyframes ai-pulse { 0%,100%{transform:scale(1);opacity:0.4} 50%{transform:scale(1.15);opacity:0.1} }
        .ai-msg { display:flex; flex-direction:column; }
        .ai-msg-bot { align-items:flex-start; }
        .ai-msg-user { align-items:flex-end; }
        .ai-msg-user > div { background:var(--color-primary-gradient);color:white;padding:10px 14px;border-radius:var(--radius-lg);font-size:13px;line-height:1.5;max-width:90%; }
        #ai-fab:hover > div { transform:scale(1.08) translateY(-2px); }
      </style>
    `;
  }

  function populateUser() {
    try {
      const raw = localStorage.getItem('finsight_user') || localStorage.getItem('finsight_token');
      let user = null;
      if (localStorage.getItem('finsight_user')) {
        user = JSON.parse(localStorage.getItem('finsight_user'));
      }
      if (!user) return;
      const name = user.full_name || user.name || 'User';
      const email = user.email || '';
      const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=7c3aed&color=fff&size=80`;
      document.querySelectorAll('#header-user-name, #sidebar-user-name').forEach(el => el.textContent = name);
      document.querySelectorAll('#header-avatar-img, #sidebar-avatar').forEach(img => img.src = avatarUrl);
      const roleEl = document.getElementById('header-user-role');
      if (roleEl) roleEl.textContent = (user.role || 'user').toUpperCase();
    } catch (e) {}
  }

  const CMD_ITEMS = [
    { label: 'Go to Dashboard', icon: 'dashboard', href: '/dashboard.html', category: 'Navigate' },
    { label: 'Go to Analytics', icon: 'monitoring', href: '/analytics.html', category: 'Navigate' },
    { label: 'Go to Expenses', icon: 'payments', href: '/expense.html', category: 'Navigate' },
    { label: 'Go to Budget', icon: 'account_balance', href: '/budget.html', category: 'Navigate' },
    { label: 'Go to Investments', icon: 'trending_up', href: '/investment.html', category: 'Navigate' },
    { label: 'Go to Goals', icon: 'flag', href: '/goal.html', category: 'Navigate' },
    { label: 'Go to Reports', icon: 'description', href: '/report_document.html', category: 'Navigate' },
    { label: 'Go to Settings', icon: 'settings', href: '/setting.html', category: 'Navigate' },
    { label: 'Toggle Dark/Light Mode', icon: 'dark_mode', action: () => FinSight.theme.toggle(), category: 'Actions' },
    { label: 'Sign Out', icon: 'logout', action: () => document.querySelector('[data-logout]')?.click(), category: 'Actions' },
  ];

  function setupCommandPalette() {
    const overlay = document.getElementById('command-palette-overlay');
    if (!overlay) return;
    const input = document.getElementById('cmd-input');
    const results = document.getElementById('cmd-results');

    function renderCMD(query) {
      const filtered = query
        ? CMD_ITEMS.filter(i => i.label.toLowerCase().includes(query.toLowerCase()))
        : CMD_ITEMS;
      const grouped = {};
      filtered.forEach(i => { if (!grouped[i.category]) grouped[i.category] = []; grouped[i.category].push(i); });
      results.innerHTML = Object.entries(grouped).map(([cat, items]) => `
        <div style="padding:4px 12px 4px;font-size:11px;font-weight:700;color:var(--on-surface-muted);text-transform:uppercase;letter-spacing:0.08em">${cat}</div>
        ${items.map((item, idx) => `
          <div class="cmd-item" data-idx="${idx}" data-href="${item.href || ''}" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:var(--radius-md);cursor:pointer;transition:all 0.15s" onmouseenter="this.style.background='var(--surface-container)'" onmouseleave="this.style.background=''" onclick="FSLayout.execCMD(this)">
            <span class="material-symbols-outlined" style="font-size:18px;color:var(--color-primary)">${item.icon}</span>
            <span style="font-size:13px;font-weight:500">${item.label}</span>
            <span style="margin-left:auto;font-size:11px;color:var(--on-surface-muted)">↵</span>
          </div>
        `).join('')}
      `).join('') || '<div style="padding:32px;text-align:center;color:var(--on-surface-muted);font-size:13px">No results found</div>';
    }

    input?.addEventListener('input', e => renderCMD(e.target.value));
    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        overlay.style.display = 'flex';
        input?.focus();
        renderCMD('');
      }
      if (e.key === 'Escape' && overlay.style.display === 'flex') {
        overlay.style.display = 'none';
      }
    });
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.style.display = 'none'; });
    renderCMD('');
  }

  function setupSearch() {
    const input = document.getElementById('global-search-input');
    const dropdown = document.getElementById('search-dropdown');
    if (!input || !dropdown) return;
    const pages = [
      { label: 'Dashboard', href: '/dashboard.html', icon: 'dashboard' },
      { label: 'Expenses', href: '/expense.html', icon: 'payments' },
      { label: 'Budget Overview', href: '/budget.html', icon: 'account_balance' },
      { label: 'Investments Portfolio', href: '/investment.html', icon: 'trending_up' },
      { label: 'Financial Goals', href: '/goal.html', icon: 'flag' },
      { label: 'Analytics & Reports', href: '/analytics.html', icon: 'monitoring' },
      { label: 'Income Sources', href: '/income.html', icon: 'account_balance_wallet' },
      { label: 'Notifications', href: '/notification.html', icon: 'notifications' },
      { label: 'Settings', href: '/setting.html', icon: 'settings' },
      { label: 'Help Center', href: '/help.html', icon: 'help' },
    ];
    input.addEventListener('focus', () => { dropdown.style.display = 'block'; renderSearch(''); });
    input.addEventListener('input', e => renderSearch(e.target.value));
    document.addEventListener('click', e => { if (!e.target.closest('.header-search')) dropdown.style.display = 'none'; });
    function renderSearch(q) {
      const res = q ? pages.filter(p => p.label.toLowerCase().includes(q.toLowerCase())) : pages.slice(0, 6);
      dropdown.innerHTML = res.map(p => `
        <a href="${p.href}" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:var(--radius-md);cursor:pointer;text-decoration:none;color:var(--on-surface);transition:background 0.15s" onmouseenter="this.style.background='var(--surface-container)'" onmouseleave="this.style.background=''">
          <span class="material-symbols-outlined" style="font-size:18px;color:var(--color-primary);flex-shrink:0">${p.icon}</span>
          <span style="font-size:13px;font-weight:500">${p.label}</span>
          <span class="material-symbols-outlined" style="margin-left:auto;font-size:14px;color:var(--on-surface-muted)">arrow_outward</span>
        </a>
      `).join('') || '<div style="padding:16px;text-align:center;font-size:13px;color:var(--on-surface-muted)">No results</div>';
    }
  }

  function init() {
    populateUser();
    setupCommandPalette();
    setupSearch();
    const toggle = document.getElementById('sidebar-toggle-btn');
    if (toggle) toggle.addEventListener('click', () => FinSight?.sidebar?.toggle());
  }

  const AI_RESPONSES = {
    'spending summary': 'Based on your data, you\'ve spent ₹64,230 this month — 12% higher than last month. Food & Dining is your biggest category at ₹18,500.',
    'budget tips': 'You\'re on track with most budgets! Entertainment is 180% over budget. Consider setting a stricter limit or redistributing from Healthcare which is only 30% used.',
    'investment advice': 'Your portfolio has grown 19.2% overall. Your Bitcoin ETF is your top performer. Consider diversifying into more Index Funds for lower risk.',
    'goal progress': 'You\'re 80% towards your Emergency Fund goal — great progress! Your Dream House goal needs an extra ₹5,000/month to hit the Jun 2028 target.',
  };

  return {
    renderSidebar,
    renderHeader,
    renderCommandPalette,
    renderAIAssistant,
    init,
    showUpgradeModal() {
      FinSight?.modal?.open(`
        <div style="text-align:center">
          <div style="width:64px;height:64px;background:var(--color-primary-gradient);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px">
            <span class="material-symbols-outlined" style="color:white;font-size:28px">workspace_premium</span>
          </div>
          <h3 style="font-size:20px;font-weight:700;margin-bottom:8px">Upgrade to FinSight Pro</h3>
          <p style="font-size:14px;color:var(--on-surface-muted);margin-bottom:24px">Unlock AI-powered insights, unlimited reports, and premium features.</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:24px">
            ${['AI Financial Insights', 'Unlimited Reports', 'Receipt Scanner', 'Priority Support', 'Advanced Analytics', 'Export to PDF/Excel'].map(f =>
              `<div style="display:flex;align-items:center;gap:8px;padding:8px;background:var(--surface-container);border-radius:var(--radius-md);font-size:13px"><span class="material-symbols-outlined" style="font-size:16px;color:var(--color-secondary)">check_circle</span>${f}</div>`
            ).join('')}
          </div>
          <div style="display:flex;gap:12px;justify-content:center">
            <button class="btn btn-outline btn-md" onclick="FinSight.modal.close()">Maybe Later</button>
            <button class="btn btn-primary btn-md" onclick="FinSight.toast.success('Coming Soon','Pro plans launching soon!');FinSight.modal.close()">Upgrade Now — ₹499/mo</button>
          </div>
        </div>
      `, { title: '', width: '520px' });
    },
    toggleAI() {
      const panel = document.getElementById('ai-panel');
      if (!panel) return;
      const isOpen = panel.style.display === 'flex';
      panel.style.display = isOpen ? 'none' : 'flex';
    },
    sendAIMessage(text) {
      const input = document.getElementById('ai-input');
      const messages = document.getElementById('ai-messages');
      const msg = text || input?.value?.trim();
      if (!msg) return;
      if (input) input.value = '';

      const userDiv = document.createElement('div');
      userDiv.className = 'ai-msg ai-msg-user';
      userDiv.innerHTML = `<div>${msg}</div>`;
      messages?.appendChild(userDiv);

      const typingDiv = document.createElement('div');
      typingDiv.className = 'ai-msg ai-msg-bot';
      typingDiv.innerHTML = `<div style="background:var(--surface-container);padding:10px 14px;border-radius:var(--radius-lg);font-size:13px;color:var(--on-surface-muted)">Thinking<span style="animation:pulse 1s infinite">...</span></div>`;
      messages?.appendChild(typingDiv);
      messages.scrollTop = messages.scrollHeight;

      setTimeout(() => {
        typingDiv.remove();
        const key = Object.keys(AI_RESPONSES).find(k => msg.toLowerCase().includes(k));
        const response = key ? AI_RESPONSES[key] : `I've analyzed your financial data for "${msg}". Based on your spending patterns, you're doing well overall. Your savings rate of 65.3% is above the recommended 20%. Keep tracking consistently for more personalized insights!`;
        const botDiv = document.createElement('div');
        botDiv.className = 'ai-msg ai-msg-bot';
        botDiv.innerHTML = `<div style="background:var(--surface-container);padding:12px 14px;border-radius:var(--radius-lg);font-size:13px;line-height:1.5">${response}</div>`;
        messages?.appendChild(botDiv);
        messages.scrollTop = messages.scrollHeight;
      }, 1200);
    },
    execCMD(el) {
      const href = el.dataset.href;
      if (href) window.location.href = href;
      document.getElementById('command-palette-overlay').style.display = 'none';
    },
  };
})();

document.addEventListener('DOMContentLoaded', () => FSLayout.init());
