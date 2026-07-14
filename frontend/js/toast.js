export function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('finsight-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'finsight-toast-container';
    container.className = 'fixed top-20 right-6 z-[200] flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(container);
  }

  const colors = {
    success: 'bg-tertiary/90 border-tertiary text-white',
    error: 'bg-error/90 border-error text-white',
    info: 'bg-primary/90 border-primary text-white',
    warning: 'bg-amber-500/90 border-amber-500 text-white',
  };

  const toast = document.createElement('div');
  toast.className = `pointer-events-auto px-5 py-3 rounded-xl border shadow-2xl backdrop-blur-md text-sm font-bold flex items-center gap-2 animate-slide-in ${colors[type] || colors.info}`;
  toast.innerHTML = `<span class="material-symbols-outlined text-base">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
