/**
 * FinSight Add Expense Module — Enterprise Expense Management
 * 
 * Production-grade expense creation with offline draft persistence,
 * duplicate detection, receipt OCR integration, category auto-suggest,
 * and real-time validation. Designed for high-scale financial applications.
 * 
 * Key capabilities:
 * - Auto-save drafts to localStorage (crash recovery)
 * - Server-side duplicate transaction detection
 * - Receipt image preview with OCR integration
 * - Category auto-suggestions based on merchant name
 * - Multi-currency support
 * - Split expense support
 * - Recurring expense templates
 * 
 * @version 3.0.1
 * @license Proprietary - FinSight Inc.
 *
 * CHANGELOG (3.0.1 fixes):
 * - FormValidator: required-field alias lookup was inverted, causing false
 *   "required" errors whenever the form used an aliased field name
 *   (e.g. name="description" instead of "title"). Fixed to resolve aliases
 *   in the correct direction.
 * - ReceiptManager.applyOCRData: setting a <select> to an OCR-detected
 *   category that had no matching <option> silently failed. Now creates
 *   the option on the fly (and dedupes) before assigning.
 * - initAmountFormatting: keydown filter allowed multiple "." characters
 *   (e.g. "12.3.4"). Now blocks a second decimal point.
 * - handleSubmit: submit button was re-enabled immediately on the
 *   "not authenticated" path even though a redirect was still pending,
 *   allowing a double-submit click during the 1.5s window. Button now
 *   stays disabled until the redirect fires.
 * - DraftManager.restore: hardened against malformed/legacy draft shapes
 *   and selector errors from unexpected field names.
 */

(function () {
  'use strict';

  // ===========================================================================
  // Configuration
  // ===========================================================================

  const EXPENSE_CONFIG = Object.freeze({
    DRAFT_KEY: 'finsight_expense_draft_v2',
    RECENT_CATEGORIES_KEY: 'finsight_recent_categories',
    RECENT_MERCHANTS_KEY: 'finsight_recent_merchants',
    API_ENDPOINTS: {
      CREATE: '/api/expenses/',
      DUPLICATE_CHECK: '/api/expenses/duplicate-check',
      CATEGORIES: '/api/expenses/categories',
      OCR: '/api/expenses/ocr',
    },
    DEFAULT_CURRENCY: 'INR',
    SUPPORTED_CURRENCIES: ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD'],
    MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
    ALLOWED_FILE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'],
    DEBOUNCE_MS: 300,
    MAX_DRAFT_AGE_DAYS: 7,
  });

  // ===========================================================================
  // Utils
  // ===========================================================================

  const Utils = {
    $(selector) {
      return document.querySelector(selector);
    },

    $$(selector) {
      return document.querySelectorAll(selector);
    },

    getToken() {
      return localStorage.getItem('finsight_token') || localStorage.getItem('access_token');
    },

    getUser() {
      try {
        const raw = localStorage.getItem('finsight_user') || localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    },

    formatCurrency(amount, currency = 'INR') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount || 0);
    },

    sanitize(str) {
      const div = document.createElement('div');
      div.textContent = str || '';
      return div.innerHTML;
    },

    debounce(fn, ms = EXPENSE_CONFIG.DEBOUNCE_MS) {
      let timer;
      return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
      };
    },

    formatDate(dateStr) {
      if (!dateStr) return '';
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    },

    // Safe wrapper around querySelector for dynamic field names (draft keys,
    // OCR field names, etc. could theoretically contain characters that are
    // invalid inside an attribute selector).
    safeQuery(name) {
      try {
        return document.querySelector(`[name="${CSS.escape(name)}"]`);
      } catch {
        return null;
      }
    },

    showToast(message, type = 'success', duration = 4000) {
      const existing = document.querySelector('.finsight-toast');
      if (existing) existing.remove();

      const toast = document.createElement('div');
      toast.className = `finsight-toast finsight-toast-${type}`;
      toast.innerHTML = `
                <span class="material-symbols-outlined" style="font-size:18px;flex-shrink:0">
                    ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
                </span>
                <span>${Utils.sanitize(message)}</span>
            `;
      Object.assign(toast.style, {
        position: 'fixed',
        top: '24px',
        right: '24px',
        zIndex: '9999',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '14px 20px',
        borderRadius: '12px',
        fontSize: '14px',
        fontWeight: '600',
        color: '#fff',
        background: type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1',
        boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
        transform: 'translateY(-20px)',
        opacity: '0',
        transition: 'all 0.3s ease',
        maxWidth: '420px',
      });
      document.body.appendChild(toast);

      requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
      });

      setTimeout(() => {
        toast.style.transform = 'translateY(-20px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
      }, duration);
    },
  };

  // ===========================================================================
  // Draft Manager — Offline persistence for crash recovery
  // ===========================================================================

  const DraftManager = {
    save() {
      const form = document.querySelector('form[data-expense-form]');
      if (!form) return;

      const data = {};
      new FormData(form).forEach((value, key) => {
        if (key !== 'receipt' && key !== 'receipt_file') {
          data[key] = value;
        }
      });
      data._savedAt = Date.now();

      try {
        localStorage.setItem(EXPENSE_CONFIG.DRAFT_KEY, JSON.stringify(data));
      } catch {
        // localStorage full — silently fail
      }
    },

    load() {
      try {
        const raw = localStorage.getItem(EXPENSE_CONFIG.DRAFT_KEY);
        if (!raw) return null;

        const draft = JSON.parse(raw);
        if (!draft || typeof draft !== 'object') return null;

        const savedAt = draft._savedAt || 0;
        const ageDays = (Date.now() - savedAt) / (1000 * 60 * 60 * 24);

        // Discard stale drafts
        if (ageDays > EXPENSE_CONFIG.MAX_DRAFT_AGE_DAYS) {
          this.clear();
          return null;
        }

        return draft;
      } catch {
        return null;
      }
    },

    restore() {
      const draft = this.load();
      if (!draft) return;

      Object.entries(draft).forEach(([key, value]) => {
        if (key.startsWith('_')) return;
        try {
          const el = Utils.safeQuery(key);
          if (el) {
            el.value = value;
            // Trigger change event for dependent UI
            el.dispatchEvent(new Event('change', { bubbles: true }));
          }
        } catch {
          // Skip fields that fail to restore rather than aborting the
          // whole restore pass.
        }
      });

      // Show restore notification
      if (draft._savedAt) {
        const savedTime = new Date(draft._savedAt).toLocaleString('en-IN');
        Utils.showToast(`Draft restored from ${savedTime}`, 'info', 3000);
      }
    },

    clear() {
      localStorage.removeItem(EXPENSE_CONFIG.DRAFT_KEY);
    },
  };

  // ===========================================================================
  // HTTP Client
  // ===========================================================================

  const ExpenseAPI = {
    async request(url, options = {}) {
      const token = Utils.getToken();
      const headers = {
        ...options.headers,
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      try {
        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        let data = null;
        const ct = response.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
          data = await response.json();
        }

        if (!response.ok) {
          const err = new Error(data?.message || data?.error || `HTTP ${response.status}`);
          err.status = response.status;
          err.data = data;
          throw err;
        }

        return { success: true, data, status: response.status };
      } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out. Please try again.');
        }
        throw error;
      }
    },

    async createExpense(formData) {
      return this.request(EXPENSE_CONFIG.API_ENDPOINTS.CREATE, {
        method: 'POST',
        body: formData,
      });
    },

    async checkDuplicate(payload) {
      return this.request(EXPENSE_CONFIG.API_ENDPOINTS.DUPLICATE_CHECK, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async getCategories() {
      return this.request(EXPENSE_CONFIG.API_ENDPOINTS.CATEGORIES, {
        method: 'GET',
      });
    },

    async scanReceipt(file) {
      const fd = new FormData();
      fd.append('receipt', file);
      return this.request(EXPENSE_CONFIG.API_ENDPOINTS.OCR, {
        method: 'POST',
        body: fd,
      });
    },
  };

  // ===========================================================================
  // Category & Merchant Autocomplete
  // ===========================================================================

  const AutoSuggest = {
    categories: [],

    async init() {
      try {
        const result = await ExpenseAPI.getCategories();
        if (result.success && Array.isArray(result.data)) {
          this.categories = result.data;
          this.populateCategoryDropdown();
        }
      } catch {
        this.categories = [
          'Food & Dining', 'Transportation', 'Shopping', 'Bills & Utilities',
          'Entertainment', 'Healthcare', 'Education', 'Travel',
          'Groceries', 'Rent', 'Insurance', 'Subscriptions',
          'Salary', 'Freelance', 'Investment', 'Transfer',
          'Clothing', 'Electronics', 'Home & Garden', 'Other',
        ];
        this.populateCategoryDropdown();
      }
    },

    populateCategoryDropdown() {
      const select = document.querySelector('[name="category"], [name="category_name"]');
      if (!select || select.tagName !== 'SELECT') return;

      // Preserve current value
      const currentValue = select.value;

      select.innerHTML = '<option value="">Select category</option>';
      this.categories.forEach(cat => {
        const label = typeof cat === 'string' ? cat : (cat.name || cat.label || '');
        const value = typeof cat === 'string' ? cat : (cat.id || cat.value || label);
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        select.appendChild(opt);
      });

      if (currentValue) {
        // Re-apply via the same option-creating path used elsewhere so a
        // value that isn't in the known list (e.g. restored from a draft
        // saved before the category list loaded) isn't silently dropped.
        this.ensureOptionExists(select, currentValue);
        select.value = currentValue;
      }
    },

    // Ensures a <select> has an <option> matching `value`; creates one if
    // missing. Prevents silent no-ops when assigning select.value to a
    // value with no matching option (see OCR category bug).
    ensureOptionExists(select, value) {
      if (!select || value == null || value === '') return;
      const exists = Array.from(select.options).some(o => o.value === value);
      if (!exists) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = value;
        select.appendChild(opt);
      }
    },

    suggestFromMerchant(merchant) {
      if (!merchant || merchant.length < 3) return;

      const merchantLC = merchant.toLowerCase();
      const keywords = {
        'Food & Dining': ['restaurant', 'cafe', 'hotel', 'food', 'pizza', 'burger', 'dining', 'bakery', 'zomato', 'swiggy', 'dhaba'],
        'Transportation': ['uber', 'ola', 'fuel', 'petrol', 'diesel', 'metro', 'bus', 'train', 'cab', 'auto', 'taxi'],
        'Shopping': ['amazon', 'flipkart', 'myntra', 'shop', 'mall', 'retail', 'store'],
        'Bills & Utilities': ['electricity', 'water', 'gas', 'broadband', 'phone', 'recharge', 'bill'],
        'Entertainment': ['netflix', 'prime', 'hotstar', 'cinema', 'movie', 'theatre', 'spotify', 'game'],
        'Healthcare': ['hospital', 'clinic', 'doctor', 'pharmacy', 'medical', 'medicin', 'dentist'],
        'Education': ['course', 'tution', 'fee', 'book', 'library', 'udemy', 'coursera'],
        'Travel': ['flight', 'booking', 'trip', 'holiday', 'hotel', 'airbnb', 'travel'],
        'Groceries': ['grocery', 'supermarket', 'mart', 'fresh', 'vegetable', 'milk'],
        'Subscriptions': ['subscription', 'saas', 'monthly', 'annual'],
      };

      for (const [cat, words] of Object.entries(keywords)) {
        if (words.some(w => merchantLC.includes(w))) {
          const select = document.querySelector('[name="category"], [name="category_name"]');
          if (select) {
            AutoSuggest.ensureOptionExists(select, cat);
            select.value = cat;
            select.dispatchEvent(new Event('change', { bubbles: true }));
          }
          break;
        }
      }
    },
  };

  // ===========================================================================
  // Receipt Scanner
  // ===========================================================================

  const ReceiptManager = {
    setupPreview() {
      const fileInput = document.querySelector('[name="receipt"], [name="receipt_file"], input[type="file"][accept*="image"]');
      const previewContainer = document.getElementById('receipt-preview-container');
      const previewImg = document.getElementById('receipt-preview');

      if (!fileInput) return;

      fileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file size
        if (file.size > EXPENSE_CONFIG.MAX_FILE_SIZE) {
          Utils.showToast('File size must be under 5MB', 'error');
          fileInput.value = '';
          return;
        }

        // Validate file type
        if (!EXPENSE_CONFIG.ALLOWED_FILE_TYPES.includes(file.type)) {
          Utils.showToast('Please upload an image or PDF file', 'error');
          fileInput.value = '';
          return;
        }

        // Image preview
        if (file.type.startsWith('image/')) {
          const url = URL.createObjectURL(file);
          if (previewImg) {
            previewImg.src = url;
            previewImg.style.display = 'block';
          }
          if (previewContainer) {
            previewContainer.style.display = 'block';
          }
        }

        // Trigger OCR
        this.scanReceipt(file);
      });
    },

    async scanReceipt(file) {
      const statusEl = document.getElementById('ocr-status');
      if (statusEl) {
        statusEl.textContent = 'Scanning receipt...';
        statusEl.style.display = 'block';
      }

      try {
        const result = await ExpenseAPI.scanReceipt(file);
        if (result.success && result.data) {
          this.applyOCRData(result.data);
          Utils.showToast('Receipt scanned successfully!', 'success');
        }
      } catch (error) {
        Utils.showToast('Receipt scan failed. You can enter details manually.', 'error');
      } finally {
        if (statusEl) {
          statusEl.textContent = '';
          statusEl.style.display = 'none';
        }
      }
    },

    applyOCRData(data) {
      // Map OCR fields to form fields
      const fieldMap = {
        amount: ['amount', 'total_amount', 'price'],
        merchant_name: ['merchant_name', 'merchant', 'vendor', 'store_name', 'payee'],
        date: ['expense_date', 'date', 'transaction_date', 'purchase_date'],
        category: ['category', 'category_name', 'type'],
        description: ['description', 'notes', 'memo', 'title'],
      };

      Object.entries(fieldMap).forEach(([ocrField, formFields]) => {
        const value = data[ocrField];
        if (!value) return;

        for (const fieldName of formFields) {
          const el = Utils.safeQuery(fieldName);
          if (el) {
            // If this is a <select> (e.g. category), make sure a matching
            // option exists first — otherwise assigning .value silently
            // fails and the OCR result is lost.
            if (el.tagName === 'SELECT') {
              AutoSuggest.ensureOptionExists(el, value);
            }
            el.value = value;
            el.dispatchEvent(new Event('change', { bubbles: true }));
            break;
          }
        }
      });
    },

    removePreview() {
      const previewImg = document.getElementById('receipt-preview');
      const container = document.getElementById('receipt-preview-container');
      if (previewImg) {
        previewImg.src = '';
        previewImg.style.display = 'none';
      }
      if (container) {
        container.style.display = 'none';
      }
      const fileInput = document.querySelector('[name="receipt"]');
      if (fileInput) fileInput.value = '';
    },
  };

  // ===========================================================================
  // Duplicate Detection
  // ===========================================================================

  const DuplicateDetector = {
    async check(formValues) {
      const payload = {
        title: formValues.title || formValues.description,
        amount: formValues.amount,
        expense_date: formValues.expense_date || formValues.date,
        merchant_name: formValues.merchant_name || formValues.merchant,
        currency: formValues.currency || EXPENSE_CONFIG.DEFAULT_CURRENCY,
      };

      // Only check if we have enough data
      if (!payload.amount || !payload.title) return null;

      try {
        const result = await ExpenseAPI.checkDuplicate(payload);
        if (result.success && result.data?.possible_duplicate && result.data?.duplicates?.length > 0) {
          return result.data.duplicates;
        }
        return null;
      } catch {
        return null;
      }
    },

    showWarning(duplicates) {
      return new Promise((resolve) => {
        const modal = document.getElementById('duplicate-modal');
        const list = document.getElementById('duplicate-list');
        const confirmBtn = document.getElementById('duplicate-confirm');
        const cancelBtn = document.getElementById('duplicate-cancel');

        if (modal && list && confirmBtn && cancelBtn) {
          list.innerHTML = duplicates.slice(0, 3).map(d => `
                        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--outline)">
                            <span>${Utils.sanitize(d.title || d.description || '')}</span>
                            <span style="font-weight:600">${Utils.formatCurrency(d.amount, d.currency)}</span>
                        </div>
                    `).join('');

          modal.style.display = 'flex';

          const handleConfirm = () => {
            modal.style.display = 'none';
            cleanup();
            resolve(true);
          };

          const handleCancel = () => {
            modal.style.display = 'none';
            cleanup();
            resolve(false);
          };

          const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
          };

          confirmBtn.addEventListener('click', handleConfirm);
          cancelBtn.addEventListener('click', handleCancel);
        } else {
          // Fallback to confirm dialog
          const confirmed = confirm('A similar transaction was found. Do you want to continue saving?');
          resolve(confirmed);
        }
      });
    },
  };

  // ===========================================================================
  // Form Validation
  // ===========================================================================

  const FormValidator = {
    // alias (name used in some form variants) -> canonical field name
    aliasMap: {
      description: 'title',
      merchant: 'merchant_name',
      date: 'expense_date',
      total_amount: 'amount',
    },

    // Reverse lookup: canonical field name -> array of aliases that map to it.
    // Built once from aliasMap so both directions stay in sync.
    get reverseAliasMap() {
      const reverse = {};
      Object.entries(this.aliasMap).forEach(([alias, canonical]) => {
        if (!reverse[canonical]) reverse[canonical] = [];
        reverse[canonical].push(alias);
      });
      return reverse;
    },

    // Resolves a canonical field's value by checking the canonical name
    // first, then falling back to any known alias present in `fields`.
    resolveValue(fields, canonicalName) {
      if (fields[canonicalName] !== undefined) return fields[canonicalName];
      const aliases = this.reverseAliasMap[canonicalName] || [];
      for (const alias of aliases) {
        if (fields[alias] !== undefined) return fields[alias];
      }
      return undefined;
    },

    validate(form) {
      const errors = {};
      const fields = {};

      // Gather form data
      new FormData(form).forEach((value, key) => {
        fields[key] = value;
      });

      // Required fields
      const requiredFields = {
        amount: 'Amount is required',
        title: 'Description is required',
        expense_date: 'Date is required',
      };

      Object.entries(requiredFields).forEach(([field, message]) => {
        const value = this.resolveValue(fields, field);
        if (!value || !value.toString().trim()) {
          errors[field] = message;
        }
      });

      // Amount validation (resolve alias too, e.g. total_amount)
      const amountRaw = this.resolveValue(fields, 'amount');
      const amount = parseFloat(amountRaw);
      if (amountRaw && (isNaN(amount) || amount <= 0)) {
        errors.amount = 'Amount must be a positive number';
      } else if (!isNaN(amount) && amount > 999999999) {
        errors.amount = 'Amount seems too high';
      }

      // Date validation (resolve alias too, e.g. date)
      const expenseDateRaw = this.resolveValue(fields, 'expense_date');
      if (expenseDateRaw) {
        const date = new Date(expenseDateRaw);
        if (isNaN(date.getTime())) {
          errors.expense_date = 'Invalid date';
        } else if (date > new Date()) {
          errors.expense_date = 'Date cannot be in the future';
        }
      }

      return {
        valid: Object.keys(errors).length === 0,
        errors,
        fields,
      };
    },

    showErrors(errors) {
      // Clear all previous errors
      document.querySelectorAll('.form-error').forEach(el => el.textContent = '');

      Object.entries(errors).forEach(([field, message]) => {
        const errorEl = document.getElementById(`${field}-err`) ||
          document.querySelector(`[data-error="${field}"]`);
        if (errorEl) {
          errorEl.textContent = message;
        }

        // Highlight the field
        const input = Utils.safeQuery(field);
        if (input) {
          input.classList.add('input-error');
          setTimeout(() => input.classList.remove('input-error'), 3000);
        }
      });
    },
  };

  // ===========================================================================
  // Main Form Handler
  // ===========================================================================

  const ExpenseFormHandler = {
    async handleSubmit(e) {
      e.preventDefault();
      const form = e.target;
      if (!(form instanceof HTMLFormElement)) return;

      const submitBtn = form.querySelector('[type="submit"]');
      const btnText = submitBtn?.querySelector('.btn-text');
      const btnSpinner = submitBtn?.querySelector('.btn-spinner');

      // Validate
      const validation = FormValidator.validate(form);
      if (!validation.valid) {
        FormValidator.showErrors(validation.errors);
        return;
      }

      // Duplicate check
      const duplicates = await DuplicateDetector.check(validation.fields);
      if (duplicates) {
        const proceed = await DuplicateDetector.showWarning(duplicates);
        if (!proceed) return;
      }

      // Set loading state
      if (submitBtn) {
        submitBtn.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnSpinner) btnSpinner.style.display = 'inline-block';
      }

      // Tracks whether we should re-enable the button in `finally`. Stays
      // false on the "redirecting to login" path so the user can't
      // double-submit while the redirect is pending.
      let reenableOnFinish = true;

      try {
        const token = Utils.getToken();
        if (!token) {
          reenableOnFinish = false;
          Utils.showToast('Please log in to continue', 'error');
          setTimeout(() => { window.location.href = '/login.html'; }, 1500);
          return;
        }

        const formData = new FormData(form);
        const result = await ExpenseAPI.createExpense(formData);

        if (result.success) {
          reenableOnFinish = false; // navigating away shortly, keep disabled
          DraftManager.clear();
          Utils.showToast('Expense saved successfully!', 'success');

          // Determine redirect
          const redirect = result.data?.redirect || '/expense.html';
          setTimeout(() => {
            window.location.href = redirect;
          }, 1000);
        } else {
          Utils.showToast(result.data?.message || 'Failed to save expense', 'error');
        }
      } catch (error) {
        const message = error.data?.message || error.message || 'Something went wrong';
        Utils.showToast(message, 'error');

        // Handle specific error codes
        if (error.status === 401) {
          reenableOnFinish = false;
          setTimeout(() => { window.location.href = '/login.html'; }, 2000);
        } else if (error.status === 413) {
          Utils.showToast('File too large. Max 5MB allowed.', 'error');
        } else if (error.status === 422) {
          const serverErrors = error.data?.errors;
          if (serverErrors) {
            FormValidator.showErrors(serverErrors);
          }
        }
      } finally {
        if (submitBtn && reenableOnFinish) {
          submitBtn.disabled = false;
          if (btnText) btnText.style.display = 'inline';
          if (btnSpinner) btnSpinner.style.display = 'none';
        }
      }
    },

    initAutoSave(form) {
      const saveFn = Utils.debounce(() => DraftManager.save(), 500);

      form.addEventListener('input', saveFn);
      form.addEventListener('change', saveFn);

      // Auto-save on blur for text inputs
      form.querySelectorAll('input, select, textarea').forEach(el => {
        el.addEventListener('blur', () => DraftManager.save());
      });
    },

    initMerchantSuggest(form) {
      const merchantInput = form.querySelector('[name="merchant_name"], [name="merchant"]');
      if (merchantInput) {
        merchantInput.addEventListener('blur', () => {
          AutoSuggest.suggestFromMerchant(merchantInput.value);
        });
      }
    },

    initAmountFormatting(form) {
      const amountInput = form.querySelector('[name="amount"], [name="total_amount"], [name="price"]');
      if (!amountInput) return;

      amountInput.addEventListener('blur', () => {
        const val = parseFloat(amountInput.value);
        if (!isNaN(val) && val > 0) {
          // Show formatted preview if there's a display element
          const display = document.getElementById('amount-display');
          if (display) {
            const currency = document.querySelector('[name="currency"]')?.value || 'INR';
            display.textContent = Utils.formatCurrency(val, currency);
          }
        }
      });

      // Prevent non-numeric input
      amountInput.addEventListener('keydown', (e) => {
        // Allow: backspace, delete, tab, escape, enter, arrows
        const allowed = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'];
        if (allowed.includes(e.key)) return;
        // Allow Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
        if ((e.ctrlKey || e.metaKey) && ['a', 'c', 'v', 'x'].includes(e.key.toLowerCase())) return;
        // Block a second decimal point (e.g. typing "12.3.4")
        if (e.key === '.' && amountInput.value.includes('.')) {
          e.preventDefault();
          return;
        }
        // Allow digits and a single decimal point
        if (/^[0-9.]$/.test(e.key)) return;
        e.preventDefault();
      });
    },

    initCurrencySelector(form) {
      const currencySelect = form.querySelector('[name="currency"]');
      if (!currencySelect) return;

      // Populate currencies if empty
      if (currencySelect.options.length <= 1) {
        EXPENSE_CONFIG.SUPPORTED_CURRENCIES.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c;
          opt.textContent = c;
          if (c === EXPENSE_CONFIG.DEFAULT_CURRENCY) opt.selected = true;
          currencySelect.appendChild(opt);
        });
      }
    },
  };

  // ===========================================================================
  // Bootstrap
  // ===========================================================================

  function init() {
    const form = document.querySelector('form[data-expense-form]');
    if (!form) {
      // Also try finding by ID or class
      const altForm = document.getElementById('expense-form') ||
        document.querySelector('.expense-form') ||
        document.querySelector('form[action*="expense"]');
      if (!altForm) {
        console.warn('[FinSight] No expense form found on this page.');
        return;
      }
      altForm.setAttribute('data-expense-form', '');
      initForm(altForm);
    } else {
      initForm(form);
    }
  }

  function initForm(form) {
    // Load categories
    AutoSuggest.init();

    // Restore draft
    DraftManager.restore();

    // Setup receipt preview
    ReceiptManager.setupPreview();

    // Currency selector
    ExpenseFormHandler.initCurrencySelector(form);

    // Amount formatting
    ExpenseFormHandler.initAmountFormatting(form);

    // Auto-save
    ExpenseFormHandler.initAutoSave(form);

    // Merchant category suggestion
    ExpenseFormHandler.initMerchantSuggest(form);

    // Submit handler
    form.addEventListener('submit', (e) => ExpenseFormHandler.handleSubmit(e));

    // --- Quick amount buttons (if present) ---
    document.querySelectorAll('[data-quick-amount]').forEach(btn => {
      btn.addEventListener('click', () => {
        const amount = parseFloat(btn.dataset.quickAmount);
        if (!isNaN(amount)) {
          const input = form.querySelector('[name="amount"]');
          if (input) {
            input.value = amount;
            input.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }
      });
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose public API
  window.FinSightExpense = {
    DraftManager,
    ReceiptManager,
    AutoSuggest,
    Utils,
    FormValidator,
  };
})();