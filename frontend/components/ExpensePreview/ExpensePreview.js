import { formatCurrency } from '../ExpenseDrawer/constants.js';

export function renderExpensePreview(container, form, ocrConfidence) {
  if (!container || !form) return;

  const fd = new FormData(form);
  const title = fd.get('title') || fd.get('merchant_name') || 'Untitled';
  const amount = fd.get('amount');
  const category = fd.get('category') || '—';
  const merchant = fd.get('merchant_name') || title;
  const currency = fd.get('currency') || 'INR';

  container.innerHTML = `
    <div class="glass-card p-4 rounded-xl border border-primary/20">
      <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-3">Preview</p>
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
          <span class="material-symbols-outlined text-primary">receipt</span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-bold text-on-surface truncate">${merchant}</p>
          <p class="text-xs text-on-surface-variant">${category}</p>
        </div>
        <p class="text-xl font-extrabold text-primary">${amount ? formatCurrency(amount, currency) : '—'}</p>
      </div>
      ${ocrConfidence ? `<p class="text-[10px] text-tertiary mt-2">AI confidence: ${ocrConfidence}%</p>` : ''}
    </div>`;
}
