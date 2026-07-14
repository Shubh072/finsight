import { getSuggestions } from '../../js/api/expenseApi.js';
import { formatCurrency } from '../ExpenseDrawer/constants.js';

let debounceTimer = null;

export function initMerchantSuggestions(container, getFormValues, { onCategorySuggest }) {
  if (!container) return;

  async function refresh() {
    const { merchant, category, amount } = getFormValues();
    if (!merchant && !category) {
      container.innerHTML = '';
      return;
    }
    try {
      const res = await getSuggestions(merchant, category, parseFloat(amount) || 0);
      const d = res?.data || {};
      const parts = [];

      if (d.suggested_category && !category) {
        parts.push(`<button type="button" data-suggest-cat="${d.suggested_category}" class="px-3 py-1 rounded-full text-xs font-bold bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30">Suggested: ${d.suggested_category}</button>`);
      }
      if (d.insight) {
        parts.push(`<p class="text-xs text-on-surface-variant italic">${d.insight}</p>`);
      }
      if (d.smart_reminder) {
        parts.push(`<p class="text-xs text-primary/80 flex items-center gap-1"><span class="material-symbols-outlined text-sm">schedule</span>${d.smart_reminder}</p>`);
      }
      if (d.average_amount) {
        parts.push(`<p class="text-xs text-on-surface-variant">Avg similar: ${formatCurrency(d.average_amount)}</p>`);
      }
      if (d.recurring_suggestion) {
        parts.push(`<p class="text-xs text-tertiary flex items-center gap-1"><span class="material-symbols-outlined text-sm">repeat</span>Recurring payment pattern detected</p>`);
      }

      container.innerHTML = parts.length
        ? `<div class="space-y-2 p-3 bg-surface-container-low rounded-xl border border-outline-variant">${parts.join('')}</div>`
        : '';

      container.querySelector('[data-suggest-cat]')?.addEventListener('click', (e) => {
        onCategorySuggest?.(e.target.dataset.suggestCat);
      });
    } catch {
      container.innerHTML = '';
    }
  }

  return {
    scheduleRefresh() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(refresh, 500);
    },
  };
}
