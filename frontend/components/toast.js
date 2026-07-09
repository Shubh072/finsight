/**
 * Toast Notification Component
 * Shows temporary notification messages
 */
class ToastManager {
  constructor() {
    this.container = null;
    this.init();
  }

  init() {
    if (!document.getElementById('toast-container')) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'fixed top-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none';
      document.body.appendChild(this.container);
    } else {
      this.container = document.getElementById('toast-container');
    }
  }

  show(message, type = 'info', duration = 3500) {
    const toast = document.createElement('div');
    const colors = {
      success: 'bg-tertiary text-white',
      error: 'bg-error text-white',
      info: 'bg-primary text-white',
      warning: 'bg-yellow-500 text-black',
    };
    const icons = {
      success: 'check_circle',
      error: 'error',
      info: 'info',
      warning: 'warning',
    };

    toast.className = `flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl ${colors[type] || colors.info} pointer-events-auto transform translate-x-full opacity-0 transition-all duration-300 max-w-sm`;
    toast.innerHTML = `
      <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1;">${icons[type] || icons.info}</span>
      <span class="font-medium text-sm flex-1">${message}</span>
      <button class="opacity-70 hover:opacity-100 transition-opacity" onclick="this.parentElement.remove()">
        <span class="material-symbols-outlined text-base">close</span>
      </button>
    `;

    this.container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto remove
    const timeout = setTimeout(() => this.remove(toast), duration);

    toast.addEventListener('mouseenter', () => clearTimeout(timeout));
  }

  remove(toast) {
    toast.classList.add('translate-x-full', 'opacity-0');
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 300);
  }

  success(message, duration) { this.show(message, 'success', duration); }
  error(message, duration) { this.show(message, 'error', duration); }
  info(message, duration) { this.show(message, 'info', duration); }
  warning(message, duration) { this.show(message, 'warning', duration); }
}

const toast = new ToastManager();
