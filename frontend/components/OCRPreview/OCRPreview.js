import { formatCurrency } from '../ExpenseDrawer/constants.js';

export function renderOCRPreview(container, data, { onApply }) {
  if (!container || !data) return;

  const fields = [
    ['Merchant', data.merchant],
    ['Amount', data.amount != null ? formatCurrency(data.amount, data.currency) : null],
    ['Date', data.expense_date],
    ['Category', data.category],
    ['Tax', data.tax != null ? formatCurrency(data.tax, data.currency) : null],
    ['Payment', data.payment_method],
    ['Invoice #', data.invoice_number],
    ['GST', data.gst],
    ['Receipt #', data.receipt_number],
  ].filter(([, v]) => v != null && v !== '');

  const confidence = data.confidence ?? 0;
  const confColor = confidence >= 80 ? 'text-tertiary' : confidence >= 50 ? 'text-amber-400' : 'text-error';

  container.innerHTML = `
    <div class="p-4 bg-surface-container-low rounded-xl border border-outline-variant space-y-3">
      <div class="flex justify-between items-center">
        <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">OCR Extraction</p>
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${confColor} bg-surface-container border border-outline-variant">
          ${confidence}% confidence
        </span>
      </div>
      <div class="grid grid-cols-2 gap-2">
        ${fields.map(([label, val]) => `
          <div class="p-2 bg-surface rounded-lg border border-outline-variant/50">
            <p class="text-[9px] text-on-surface-variant uppercase font-bold">${label}</p>
            <p class="text-sm text-on-surface font-medium truncate">${val}</p>
          </div>`).join('')}
      </div>
      ${data.items?.length ? `<p class="text-xs text-on-surface-variant">${data.items.length} line item(s) detected</p>` : ''}
      <button type="button" data-apply-ocr class="w-full py-2.5 bg-primary text-on-primary rounded-xl font-bold text-sm hover:bg-primary/90 transition-all">
        Apply to Form
      </button>
    </div>`;

  container.querySelector('[data-apply-ocr]')?.addEventListener('click', () => onApply?.(data));
}
