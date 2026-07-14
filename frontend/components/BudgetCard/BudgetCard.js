import { getBudget } from '../../js/api/expenseApi.js';
import { formatCurrency } from '../ExpenseDrawer/constants.js';

let debounceTimer = null;

export function initBudgetCard(container, getFormValues) {
  if (!container) return;

  async function refresh() {
    const { category, amount } = getFormValues();
    if (!category) {
      container.innerHTML = '<p class="text-xs text-on-surface-variant">Select a category to see budget impact.</p>';
      return;
    }
    container.innerHTML = '<div class="animate-pulse h-16 bg-surface-container rounded-xl"></div>';
    try {
      const res = await getBudget(category, parseFloat(amount) || 0);
      const b = res?.data || {};
      const warn = b.overspending_warning;
      container.innerHTML = `
        <div class="p-4 rounded-xl border ${warn ? 'border-error/40 bg-error/5' : 'border-outline-variant bg-surface-container-low'} space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-on-surface-variant">Budget (${category})</span>
            <span class="font-bold text-on-surface">${formatCurrency(b.current_budget)}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-on-surface-variant">Remaining</span>
            <span class="font-bold ${warn ? 'text-error' : 'text-tertiary'}">${formatCurrency(b.remaining_budget)}</span>
          </div>
          <div class="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
            <div class="h-full ${warn ? 'bg-error' : 'bg-primary'} transition-all" style="width:${Math.min(100, b.percentage_used_after || 0)}%"></div>
          </div>
          <p class="text-[10px] text-on-surface-variant">After expense: ${b.percentage_used_after || 0}% used</p>
          ${warn ? '<p class="text-xs text-error font-bold flex items-center gap-1"><span class="material-symbols-outlined text-sm">warning</span> Overspending warning</p>' : ''}
        </div>`;
    } catch {
      container.innerHTML = '';
    }
  }

  return {
    scheduleRefresh() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(refresh, 400);
    },
    refresh,
  };
}
