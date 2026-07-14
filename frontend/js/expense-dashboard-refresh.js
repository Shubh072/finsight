import { listExpenses, getExpenseSummary } from '../api/expenseApi.js';
import { formatCurrency } from '../../components/ExpenseDrawer/constants.js';

const CATEGORY_ICONS = {
  Food: 'restaurant', Travel: 'local_taxi', Shopping: 'shopping_bag',
  Entertainment: 'movie', Healthcare: 'medical_services', Bills: 'receipt_long',
  Fuel: 'local_gas_station', Education: 'school', Investment: 'trending_up',
  Subscription: 'subscriptions', Others: 'category', Infrastructure: 'cloud',
  Software: 'forum', Dining: 'lunch_dining',
};

const CATEGORY_COLORS = ['#8B5CF6', '#6366f1', '#10b981', '#ef4444', '#f97316', '#3b82f6'];

function statusBadge(status) {
  const map = {
    active: { cls: 'text-tertiary', dot: 'bg-tertiary', label: 'Completed' },
    pending: { cls: 'text-primary', dot: 'bg-primary animate-pulse', label: 'Pending' },
    flagged: { cls: 'text-error', dot: 'bg-error', label: 'Flagged' },
  };
  const s = map[status] || map.active;
  return `<div class="flex items-center gap-2 ${s.cls} font-bold text-[10px] uppercase tracking-widest"><span class="w-2 h-2 rounded-full ${s.dot} shadow-[0_0_6px_currentColor]"></span>${s.label}</div>`;
}

export function renderExpenseRow(exp) {
  const icon = CATEGORY_ICONS[exp.category] || 'payments';
  const title = exp.merchant_name || exp.title;
  const amt = formatCurrency(exp.amount, exp.currency || 'INR');
  const date = exp.expense_date ? new Date(exp.expense_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';
  return `
    <tr class="group hover:bg-primary/5 transition-colors cursor-pointer" onclick="showExpenseDetail('${title.replace(/'/g, "\\'")}', '${amt}', '${exp.category}')">
      <td class="px-gutter py-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
            <span class="material-symbols-outlined text-primary">${icon}</span>
          </div>
          <div>
            <p class="font-bold text-on-surface group-hover:text-primary transition-colors">${title}</p>
            <p class="text-xs text-on-surface-variant">ID: TXN-${String(exp.id).padStart(6, '0')}</p>
          </div>
        </div>
      </td>
      <td class="px-gutter py-5 font-body-sm text-on-surface-variant">${date}</td>
      <td class="px-gutter py-5">
        <span class="px-3 py-1 bg-surface-container-high/50 text-on-surface text-[10px] font-bold rounded-full uppercase tracking-wider border border-outline-variant">${exp.category}</span>
      </td>
      <td class="px-gutter py-5 font-data-mono text-data-mono font-bold text-on-surface">${amt}</td>
      <td class="px-gutter py-5">${statusBadge(exp.status)}</td>
      <td class="px-gutter py-5 text-right">
        <button class="opacity-0 group-hover:opacity-100 p-2 hover:bg-primary/10 rounded-lg transition-all text-on-surface-variant hover:text-primary" type="button">
          <span class="material-symbols-outlined">more_vert</span>
        </button>
      </td>
    </tr>`;
}

function updateDonutChart(byCategory, total) {
  const svg = document.querySelector('#category-donut-chart');
  if (!svg || !byCategory?.length) return;

  const circles = svg.querySelectorAll('circle[data-segment]');
  let offset = 0;
  byCategory.slice(0, 4).forEach((item, i) => {
    const pct = total > 0 ? (item.total / total) * 100 : 0;
    const circle = circles[i];
    if (!circle) return;
    circle.setAttribute('stroke-dasharray', `${pct} ${100 - pct}`);
    circle.setAttribute('stroke-dashoffset', String(-offset));
    circle.setAttribute('stroke', CATEGORY_COLORS[i % CATEGORY_COLORS.length]);
    offset += pct;
  });

  const legend = document.getElementById('category-legend');
  if (legend) {
    legend.innerHTML = byCategory.slice(0, 4).map((item, i) => `
      <div class="flex items-center gap-3">
        <div class="w-3 h-3 rounded-full" style="background:${CATEGORY_COLORS[i % CATEGORY_COLORS.length]};box-shadow:0 0 4px ${CATEGORY_COLORS[i % CATEGORY_COLORS.length]}"></div>
        <div>
          <p class="text-xs font-bold text-on-surface">${item.category}</p>
          <p class="text-xs text-on-surface-variant">${formatCurrency(item.total)}</p>
        </div>
      </div>`).join('');
  }
}

export async function refreshExpenseDashboard() {
  try {
    const [summaryRes, listRes] = await Promise.all([
      getExpenseSummary(),
      listExpenses({ limit: 10, sort: '-expense_date' }),
    ]);

    const summary = summaryRes?.data || {};
    const items = listRes?.data?.items || [];

    const totalEl = document.getElementById('stat-total-expenses');
    if (totalEl) totalEl.textContent = formatCurrency(summary.total_this_month || 0);

    const barEl = document.getElementById('budget-util-bar');
    if (barEl) barEl.style.width = `${Math.min(100, summary.budget_used_pct || 0)}%`;

    const pctEl = document.getElementById('budget-util-text');
    if (pctEl) pctEl.textContent = `${summary.budget_used_pct || 0}% of monthly budget utilized`;

    const trendEl = document.getElementById('expense-trend-badge');
    if (trendEl && summary.change_pct_vs_last_month != null) {
      const c = summary.change_pct_vs_last_month;
      trendEl.innerHTML = `<span class="material-symbols-outlined text-sm">${c <= 0 ? 'trending_down' : 'trending_up'}</span> ${Math.abs(c)}% vs LM`;
    }

    updateDonutChart(summary.by_category || [], summary.total_this_month || 0);

    const tbody = document.getElementById('expense-table-body');
    if (tbody) {
      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="px-gutter py-12 text-center text-on-surface-variant">No expenses yet. Click <strong>Add Expense</strong> to get started.</td></tr>`;
      } else {
        tbody.innerHTML = items.map(renderExpenseRow).join('');
      }
    }

    const countEl = document.getElementById('expense-table-count');
    if (countEl) {
      const total = listRes?.data?.total || items.length;
      countEl.innerHTML = `Showing <span class="text-on-surface font-bold">1 to ${Math.min(items.length, 10)}</span> of ${total} entries`;
    }
  } catch (err) {
    console.warn('Dashboard refresh failed:', err.message);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('expense-table-body')) {
    refreshExpenseDashboard();
  }
});

window.addEventListener('expense:saved', () => refreshExpenseDashboard());
