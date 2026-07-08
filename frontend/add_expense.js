// Minimal Add Expense JS (offline draft + receipt preview + duplicate warning scaffold)
// This repo primarily uses static HTML pages; this script is intended to be wired into frontend/expense.html later.

(function () {
  const DRAFT_KEY = 'finsight_add_expense_draft_v1';

  function qs(sel) {
    return document.querySelector(sel);
  }

  function setText(id, text) {
    const el = qs('#' + id);
    if (el) el.textContent = text;
  }

  function getToken() {
    return localStorage.getItem('access_token');
  }

  async function apiPost(url, body, isFormData = false) {
    const token = getToken();
    const headers = isFormData ? {} : { 'Content-Type': 'application/json' };
    if (!isFormData) headers.Authorization = 'Bearer ' + token;
    else headers.Authorization = 'Bearer ' + token;

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: isFormData ? body : JSON.stringify(body),
    });

    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = json?.message || 'Request failed';
      throw new Error(msg);
    }
    return json;
  }

  function loadDraft() {
    try {
      const s = localStorage.getItem(DRAFT_KEY);
      if (!s) return;
      const draft = JSON.parse(s);
      // Hook into common field names if present
      Object.keys(draft).forEach((k) => {
        const el = qs(`[name="${k}"]`);
        if (el) el.value = draft[k];
      });
    } catch (e) {}
  }

  function saveDraft() {
    const form = document.querySelector('form');
    if (!form) return;

    const data = {};
    new FormData(form).forEach((v, k) => {
      data[k] = v;
    });

    // Receipt file isn't draft-saved
    delete data.receipt;

    localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
  }

  async function duplicateCheck(formValues) {
    // Expect: title, amount, expense_date, merchant_name, currency
    const payload = {
      title: formValues.title,
      amount: formValues.amount,
      expense_date: formValues.expense_date,
      merchant_name: formValues.merchant_name,
      currency: formValues.currency,
    };

    const token = getToken();
    if (!token) return { possible_duplicate: false, duplicates: [] };

    const res = await fetch('/api/expenses/duplicate-check', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + token,
      },
      body: JSON.stringify(payload),
    });

    const json = await res.json().catch(() => ({}));
    return json?.data || { possible_duplicate: false, duplicates: [] };
  }

  function setupReceiptPreview() {
    const fileInput = qs('[name="receipt"], input[type="file"]');
    const preview = qs('#receipt-preview');
    if (!fileInput || !preview) return;

    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;

      const url = URL.createObjectURL(file);
      // Only attempt img preview
      if (file.type && file.type.startsWith('image/')) {
        preview.src = url;
        preview.classList.remove('hidden');
      }
    });
  }

  async function onSubmit(e) {
    e.preventDefault();
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;

    // Basic extraction
    const formValues = {
      title: form.elements['title']?.value,
      amount: form.elements['amount']?.value,
      expense_date: form.elements['expense_date']?.value,
      merchant_name: form.elements['merchant_name']?.value,
      currency: form.elements['currency']?.value,
    };

    // Duplicate warning
    try {
      const dup = await duplicateCheck(formValues);
      if (dup?.possible_duplicate && dup.duplicates?.length) {
        const first = dup.duplicates[0];
        const ok = confirm(
          `Possible duplicate found: ${first.title} (${first.expense_date}) for ${first.amount}. Continue?`
        );
        if (!ok) return;
      }
    } catch (err) {
      // Don't block on duplicate check errors
      console.warn(err);
    }

    // Submit
    const token = getToken();
    if (!token) {
      alert('Please login.');
      window.location.href = '/login.html';
      return;
    }

    const fd = new FormData(form);
    try {
      setText('submit-status', 'Saving...');
      const res = await fetch('/api/expenses', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: fd,
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json?.message || 'Save failed');

      localStorage.removeItem(DRAFT_KEY);
      alert('Expense saved successfully');
      // TODO: redirect to details page
    } catch (err) {
      alert(err.message || 'Save failed');
    } finally {
      setText('submit-status', '');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadDraft();
    setupReceiptPreview();

    const form = document.querySelector('form');
    if (form) {
      form.addEventListener('input', () => saveDraft());
      form.addEventListener('change', () => saveDraft());
      form.addEventListener('submit', onSubmit);
    }
  });
})();

