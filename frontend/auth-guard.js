// auth-guard.js
(function () {
    const publicPages = ['/login.html', '/create_account.html', '/verify_email.html'];
    const currentPath = window.location.pathname;
    
    // Check if the current page is public
    const isPublic = publicPages.some(page => currentPath.endsWith(page));
    
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    if (!isPublic) {
        if (!token || !userStr) {
            // Redirect to login if not authenticated
            window.location.href = '/login.html';
            return;
        }
        
        const user = JSON.parse(userStr);
        
        // Wait for DOM content to load to patch dynamic elements
        document.addEventListener('DOMContentLoaded', () => {
            // 1. Update User Profile Name & Role/Tier in the DOM
            document.body.querySelectorAll('*').forEach(el => {
                if (el.children.length === 0) {
                    const txt = el.textContent.trim();
                    if (txt === 'Alex Thompson' || txt === 'Alexander Vance') {
                        el.textContent = user.full_name;
                    }
                    if (txt === 'PREMIUM MEMBER' || txt === 'Obsidian Tier' || txt === 'PREMIUM') {
                        el.textContent = (user.role || 'user').toUpperCase() + ' MEMBER';
                    }
                }
            });
            
            // 2. Interconnect all panel links dynamically
            document.querySelectorAll('aside nav a, nav a').forEach(a => {
                const text = a.textContent.trim().toLowerCase();
                if (text.includes('dashboard')) {
                    a.setAttribute('href', '/dashboard.html');
                } else if (text.includes('expenses')) {
                    a.setAttribute('href', '/expense.html');
                } else if (text.includes('budgets')) {
                    a.setAttribute('href', '/budget.html');
                } else if (text.includes('investments')) {
                    a.setAttribute('href', '/investment.html');
                } else if (text.includes('goals')) {
                    a.setAttribute('href', '/goal.html');
                } else if (text.includes('analytics')) {
                    a.setAttribute('href', '/analytics.html');
                } else if (text.includes('reports')) {
                    a.setAttribute('href', '/report_document.html');
                } else if (text.includes('notifications')) {
                    a.setAttribute('href', '/notification.html');
                } else if (text.includes('settings')) {
                    a.setAttribute('href', '/setting.html');
                }
            });
            
            // 3. Inject Sign Out button into the navigation menu
            const nav = document.querySelector('aside nav') || document.querySelector('nav');
            if (nav) {
                // Check if sign out button is already injected
                if (!document.getElementById('dynamic-signout')) {
                    const signOutLink = document.createElement('a');
                    signOutLink.id = 'dynamic-signout';
                    // Match existing sidebar link styles
                    signOutLink.className = "flex items-center gap-3 text-error hover:bg-error-container/20 px-4 py-3 transition-colors rounded-lg group cursor-pointer mt-lg border border-error/10 hover:border-error/30";
                    signOutLink.innerHTML = `
                        <span class="material-symbols-outlined text-error">logout</span>
                        <span class="font-body-md font-bold text-error">Sign Out</span>
                    `;
                    signOutLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        localStorage.clear();
                        window.location.href = '/login.html';
                    });
                    nav.appendChild(signOutLink);
                }
            }
        });
    }
})();
