/**
 * ExpenseDrawer Component
 * Premium right-side drawer for adding expenses with all features
 */
class ExpenseDrawer {
  constructor(options = {}) {
    this.onSave = options.onSave || (() => {});
    this.onClose = options.onClose || (() => {});
    this.isOpen = false;
    this.formData = {};
    this.categories = [];
    this.paymentMethods = [];
    this.accounts = [];
    this.budgets = [];
    this.favoriteMerchants = [];
    this.quickAddAmounts = [100, 200, 500, 1000];
    this.moods = ['Happy', 'Neutral', 'Stressed', 'Excited', 'Guilty', 'Necessary', 'Impulse'];
    this.splits = [];
    this.currentReceiptFile = null;
    this.draftTimer = null;
    this.aiInsightTimer = null;
    this.budgetCheckTimer = null;
    this.receiptUploader = null;
    this.init();
  }

  init() {
    this._createDrawer();
    this._setupEventListeners();
  }

  _createDrawer() {
    const drawerHTML = `
      <div id="expense-drawer-overlay" class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm opacity-0 pointer-events-none transition-opacity duration-300"></div>
      <div id="expense-drawer" class="fixed right-0 top-0 bottom-0 w-full max-w-[640px] bg-surface border-l border-outline-variant z-[110] transform translate-x-full transition-transform duration-500 flex flex-col shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-lg border-b border-outline-variant bg-surface-container-low/50">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">add_circle</span>
            </div>
            <div>
              <h2 class="text-lg font-bold text-on-surface">Add Expense</h2>
              <p class="text-xs text-on-surface-variant">Track your spending with AI</p>
            </div>
          </div>
          <button id="drawer-close-btn" class="p-2 hover:bg-surface-container-high rounded-lg transition-colors">
            <span class="material-symbols-outlined text-on-surface-variant">close</span>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b border-outline-variant bg-surface-container-lowest/50">
          <button id="tab-manual" class="flex-1 py-3 px-4 font-bold text-primary border-b-2 border-primary transition-all flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-base">edit_note</span>
            Manual Entry
          </button>
          <button id="tab-scan" class="flex-1 py-3 px-4 font-bold text-on-surface-variant border-b-2 border-transparent hover:text-on-surface transition-all flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-base">document_scanner</span>
            Scan Receipt
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-lg space-y-lg" id="drawer-content">
          <!-- Manual Entry Tab -->
          <div id="tab-content-manual" class="space-y-lg">
            <!-- Quick Add Amounts -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Quick Add</label>
              <div class="flex gap-2 flex-wrap" id="quick-add-chips"></div>
            </div>

            <!-- Amount + Currency -->
            <div class="grid grid-cols-3 gap-3">
              <div class="col-span-2">
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Amount *</label>
                <div class="relative">
                  <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">payments</span>
                  <input type="number" name="amount" id="field-amount" step="0.01" min="0.01" placeholder="0.00" class="w-full bg-surface-container-low border border-outline-variant rounded-xl pl-10 pr-4 py-3 text-on-surface font-bold text-lg focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
                </div>
              </div>
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Currency</label>
                <select name="currency" id="field-currency" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all">
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="INR">INR</option>
                  <option value="JPY">JPY</option>
                </select>
              </div>
            </div>

            <!-- Budget Intelligence -->
            <div id="budget-intelligence" class="hidden p-3 rounded-xl border border-outline-variant bg-surface-container-low">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Budget Impact</span>
                <span id="budget-percentage" class="text-xs font-bold"></span>
              </div>
              <div class="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
                <div id="budget-bar" class="h-full rounded-full transition-all duration-500" style="width: 0%"></div>
              </div>
              <div class="flex justify-between mt-2 text-xs">
                <span id="budget-remaining" class="text-on-surface-variant"></span>
                <span id="budget-after" class="text-on-surface-variant"></span>
              </div>
            </div>

            <!-- Title -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Expense Title *</label>
              <input type="text" name="title" id="field-title" minlength="3" placeholder="e.g., Lunch at Pizza Hut" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
            </div>

            <!-- Merchant -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Merchant Name</label>
              <input type="text" name="merchant_name" id="field-merchant" placeholder="e.g., Uber, Amazon" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
              <div id="merchant-suggestions" class="hidden mt-2 space-y-1"></div>
            </div>

            <!-- Category Grid -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Category *</label>
              <div id="category-grid" class="grid grid-cols-4 sm:grid-cols-6 gap-2"></div>
            </div>

            <!-- Sub Category -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Sub Category</label>
              <input type="text" name="sub_category" id="field-sub-category" placeholder="e.g., Fast Food, Ride Share" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
            </div>

            <!-- Date + Payment Method -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Date *</label>
                <input type="date" name="expense_date" id="field-date" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
              </div>
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Payment Method *</label>
                <select name="payment_method" id="field-payment" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all"></select>
              </div>
            </div>

            <!-- Account -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Account</label>
              <select name="account_id" id="field-account" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all">
                <option value="">Select Account</option>
              </select>
            </div>

            <!-- Location -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Location</label>
              <input type="text" name="location" id="field-location" placeholder="e.g., Mumbai, India" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
            </div>

            <!-- Description -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Description</label>
              <textarea name="description" id="field-description" rows="3" maxlength="1000" placeholder="Add notes about this expense..." class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all resize-none"></textarea>
            </div>

            <!-- Tags -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Tags (comma-separated)</label>
              <input type="text" name="tags" id="field-tags" placeholder="e.g., work, food, urgent" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
            </div>

            <!-- Priority + Mood -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Priority (1-5)</label>
                <input type="number" name="priority" id="field-priority" min="1" max="5" placeholder="Optional" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
              </div>
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Mood</label>
                <select name="mood" id="field-mood" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all">
                  <option value="">Select Mood</option>
                </select>
              </div>
            </div>

            <!-- Recurring -->
            <div class="p-3 rounded-xl border border-outline-variant bg-surface-container-low">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-base">repeat</span>
                  Recurring Expense
                </label>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" name="recurring" id="field-recurring" class="sr-only peer" />
                  <div class="w-11 h-6 bg-surface-container-high rounded-full peer peer-checked:bg-primary transition-all after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
                </label>
              </div>
              <select name="recurring_frequency" id="field-recurring-frequency" class="hidden w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2 text-on-surface text-sm focus:border-primary outline-none transition-all">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly" selected>Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <!-- Split Expense -->
            <div class="p-3 rounded-xl border border-outline-variant bg-surface-container-low">
              <div class="flex items-center justify-between mb-3">
                <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary text-base">group</span>
                  Split Expense
                </label>
                <button type="button" id="add-split-btn" class="px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-xs font-bold hover:bg-primary/20 transition-all flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm">add</span>
                  Add Split
                </button>
              </div>
              <div id="splits-container" class="space-y-2"></div>
            </div>

            <!-- Tax + Invoice -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Tax Included</label>
                <input type="number" name="tax_included" id="field-tax" step="0.01" placeholder="0.00" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
              </div>
              <div>
                <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Invoice Number</label>
                <input type="text" name="invoice_number" id="field-invoice" placeholder="Optional" class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all" />
              </div>
            </div>

            <!-- Notes -->
            <div>
              <label class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2 block">Notes</label>
              <textarea name="notes" id="field-notes" rows="2" placeholder="Private notes..." class="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none transition-all resize-none"></textarea>
            </div>

            <!-- AI Insights -->
            <div id="ai-insights" class="hidden space-y-2"></div>

            <!-- Duplicate Warning -->
            <div id="duplicate-warning" class="hidden p-3 rounded-xl border border-yellow-500/30 bg-yellow-500/10">
              <div class="flex items-start gap-2">
                <span class="material-symbols-outlined text-yellow-500">warning</span>
                <div class="flex-1">
                  <p class="text-sm font-bold text-yellow-500">Possible Duplicate Found</p>
                  <div id="duplicate-details" class="text-xs text-on-surface-variant mt-1"></div>
                  <div class="flex gap-2 mt-2">
                    <button type="button" id="dup-ignore-btn" class="px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-lg text-xs font-bold hover:bg-yellow-500/30 transition-all">Ignore & Save</button>
                    <button type="button" id="dup-cancel-btn" class="px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-lg text-xs font-bold hover:bg-surface-container-highest transition-all">Cancel</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Expense Preview -->
            <div id="expense-preview" class="hidden p-4 rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <p class="text-xs font-bold text-primary uppercase tracking-wider mb-3">Expense Preview</p>
              <div class="flex items-center gap-3">
                <div id="preview-icon" class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <span class="material-symbols-outlined text-primary">payments</span>
                </div>
                <div class="flex-1">
                  <p id="preview-title" class="font-bold text-on-surface"></p>
                  <p id="preview-category" class="text-xs text-on-surface-variant"></p>
                </div>
                <p id="preview-amount" class="text-lg font-bold text-primary"></p>
              </div>
            </div>
          </div>

          <!-- Scan Receipt Tab -->
          <div id="tab-content-scan" class="hidden space-y-lg">
            <div id="receipt-uploader-container"></div>
            <div id="ocr-results" class="hidden space-y-3"></div>
          </div>
        </div>

        <!-- Footer Buttons -->
        <div class="p-lg border-t border-outline-variant bg-surface-container-low/50 space-y-2">
          <div class="flex gap-2">
            <button id="btn-save" type="button" class="flex-1 py-3 bg-primary text-white font-bold rounded-xl hover:brightness-110 transition-all active:scale-95 shadow-lg shadow-primary/20 flex items-center justify-center gap-2">
              <span class="material-symbols-outlined">save</span>
              Save Expense
            </button>
            <button id="btn-save-another" type="button" class="px-4 py-3 bg-surface-container border border-outline-variant text-on-surface font-bold rounded-xl hover:bg-surface-container-high transition-all active:scale-95 flex items-center gap-2">
              <span class="material-symbols-outlined">add</span>
              Save & Add
            </button>
          </div>
          <div class="flex gap-2">
            <button id="btn-reset" type="button" class="flex-1 py-2.5 border border-outline-variant text-on-surface-variant font-medium rounded-xl hover:bg-surface-container-high transition-all text-sm flex items-center justify-center gap-2">
              <span class="material-symbols-outlined text-base">refresh</span>
              Reset
            </button>
            <button id="btn-cancel" type="button" class="flex-1 py-2.5 text-on-surface-variant font-medium rounded-xl hover:bg-surface-container-high transition-all text-sm">Cancel</button>
          </div>
        </div>

        <!-- Loading Overlay -->
        <div id="drawer-loading" class="hidden absolute inset-0 z-[120] bg-surface/80 backdrop-blur-sm flex items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            <p id="loading-text" class="text-on-surface-variant font-medium">Saving...</p>
          </div>
        </div>

        <!-- Success Overlay -->
        <div id="drawer-success" class="hidden absolute inset-0 z-[120] bg-surface/90 backdrop-blur-sm flex items-center justify-center">
          <div class="flex flex-col items-center gap-4 animate-bounce-in">
            <div class="w-20 h-20 rounded-full bg-tertiary/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-tertiary text-5xl" style="font-variation-settings: 'FILL' 1;">check_circle</span>
            </div>
            <p class="text-lg font-bold text-on-surface">Expense Added Successfully!</p>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', drawerHTML);
  }

  _setupEventListeners() {
    const overlay = document.getElementById('expense-drawer-overlay');
    const drawer = document.getElementById('expense-drawer');
    const closeBtn = document.getElementById('drawer-close-btn');
    const cancelBtn = document.getElementById('btn-cancel');
    const saveBtn = document.getElementById('btn-save');
    const saveAnotherBtn = document.getElementById('btn-save-another');
    const resetBtn = document.getElementById('btn-reset');
    const tabManual = document.getElementById('tab-manual');
    const tabScan = document.getElementById('tab-scan');

    closeBtn.addEventListener('click', () => this.close());
    cancelBtn.addEventListener('click', () => this.close());
    overlay.addEventListener('click', () => this.close());

    saveBtn.addEventListener('click', () => this._saveExpense(false));
    saveAnotherBtn.addEventListener('click', () => this._saveExpense(true));
    resetBtn.addEventListener('click', () => this._resetForm());

    tabManual.addEventListener('click', () => this._switchTab('manual'));
    tabScan.addEventListener('click', () => this._switchTab('scan'));

    // Form field listeners
    const amountField = document.getElementById('field-amount');
    const titleField = document.getElementById('field-title');
    const merchantField = document.getElementById('field-merchant');
    const recurringCheckbox = document.getElementById('field-recurring');
    const addSplitBtn = document.getElementById('add-split-btn');

    amountField.addEventListener('input', () => {
      this._updatePreview();
      this._debouncedBudgetCheck();
      this._debouncedDuplicateCheck();
    });

    titleField.addEventListener('input', () => {
      this._updatePreview();
      this._debouncedAISuggestions();
      this._debouncedDuplicateCheck();
    });

    merchantField.addEventListener('input', () => {
      this._debouncedAISuggestions();
      this._showMerchantSuggestions();
    });

    recurringCheckbox.addEventListener('change', () => {
      const freqSelect = document.getElementById('field-recurring-frequency');
      if (recurringCheckbox.checked) {
        freqSelect.classList.remove('hidden');
      } else {
        freqSelect.classList.add('hidden');
      }
    });

    addSplitBtn.addEventListener('click', () => this._addSplit());

    // Duplicate warning buttons
    document.getElementById('dup-ignore-btn').addEventListener('click', () => {
      document.getElementById('duplicate-warning').classList.add('hidden');
      this._forceSave = true;
      this._saveExpense(false);
    });

    document.getElementById('dup-cancel-btn').addEventListener('click', () => {
      document.getElementById('duplicate-warning').classList.add('hidden');
    });
  }

  async open() {
    this.isOpen = true;
    await this._loadMetadata();
    this._setDefaultDate();
    this._loadDraft();

    const overlay = document.getElementById('expense-drawer-overlay');
    const drawer = document.getElementById('expense-drawer');

    overlay.classList.remove('opacity-0', 'pointer-events-none');
    drawer.classList.remove('translate-x-full');

    document.body.style.overflow = 'hidden';
  }

  close() {
    this.isOpen = false;
    this._saveDraft();

    const overlay = document.getElementById('expense-drawer-overlay');
    const drawer = document.getElementById('expense-drawer');

    overlay.classList.add('opacity-0', 'pointer-events-none');
    drawer.classList.add('translate-x-full');

    document.body.style.overflow = '';
    this.onClose();
  }

  async _loadMetadata() {
    try {
      const [catRes, pmRes, accRes, quickRes] = await Promise.all([
        expenseAPI.getCategories(),
        expenseAPI.getPaymentMethods(),
        expenseAPI.getAccounts(),
        expenseAPI.getQuickAddAmounts(),
      ]);

      this.categories = catRes.data?.categories || [];
      this.paymentMethods = pmRes.data?.payment_methods || [];
      this.accounts = accRes.data?.accounts || [];
      this.quickAddAmounts = quickRes.data?.amounts || [100, 200, 500, 1000];
      this.moods = quickRes.data?.moods || ['Happy', 'Neutral', 'Stressed', 'Excited', 'Guilty', 'Necessary', 'Impulse'];

      this._renderCategories();
      this._renderPaymentMethods();
      this._renderAccounts();
      this._renderQuickAdd();
      this._renderMoods();
      this._initReceiptUploader();
    } catch (err) {
      toast.error('Failed to load form data');
      console.error(err);
    }
  }

  _renderCategories() {
    const grid = document.getElementById('category-grid');
    grid.innerHTML = this.categories.map(cat => `
      <button type="button" class="category-card group p-2 rounded-xl border border-outline-variant hover:border-primary transition-all flex flex-col items-center gap-1" data-category="${cat.name}" data-icon="${cat.icon}" data-color="${cat.color}">
        <div class="w-10 h-10 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110" style="background: ${cat.color}20;">
          <span class="material-symbols-outlined text-base" style="color: ${cat.color};">${cat.icon}</span>
        </div>
        <span class="text-[10px] font-medium text-on-surface-variant truncate w-full text-center">${cat.name}</span>
      </button>
    `).join('');

    grid.querySelectorAll('.category-card').forEach(card => {
      card.addEventListener('click', () => {
        grid.querySelectorAll('.category-card').forEach(c => {
          c.classList.remove('border-primary', 'bg-primary/10');
        });
        card.classList.add('border-primary', 'bg-primary/10');
        this._selectedCategory = card.dataset.category;
        this._updatePreview();
        this._debouncedBudgetCheck();
      });
    });
  }

  _renderPaymentMethods() {
    const select = document.getElementById('field-payment');
    select.innerHTML = '<option value="">Select Method</option>' +
      this.paymentMethods.map(pm => `<option value="${pm}">${pm}</option>`).join('');
  }

  _renderAccounts() {
    const select = document.getElementById('field-account');
    const current = select.value;
    select.innerHTML = '<option value="">Select Account</option>' +
      this.accounts.map(acc => `<option value="${acc.id}">${acc.name}</option>`).join('');
    if (current) select.value = current;
  }

  _renderQuickAdd() {
    const container = document.getElementById('quick-add-chips');
    container.innerHTML = this.quickAddAmounts.map(amt => `
      <button type="button" class="quick-add-chip px-3 py-1.5 bg-surface-container border border-outline-variant rounded-full text-sm font-bold text-on-surface hover:bg-primary hover:text-white hover:border-primary transition-all" data-amount="${amt}">
        $${amt}
      </button>
    `).join('');

    container.querySelectorAll('.quick-add-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.getElementById('field-amount').value = chip.dataset.amount;
        this._updatePreview();
        this._debouncedBudgetCheck();
      });
    });
  }

  _renderMoods() {
    const select = document.getElementById('field-mood');
    select.innerHTML = '<option value="">Select Mood</option>' +
      this.moods.map(m => `<option value="${m}">${m}</option>`).join('');
  }

  _initReceiptUploader() {
    const container = document.getElementById('receipt-uploader-container');
    if (!container || this.receiptUploader) return;

    this.receiptUploader = new ReceiptUploader(
      container,
      (file) => { this.currentReceiptFile = file; },
      (file) => this._scanReceipt(file)
    );
  }

  _setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('field-date').value = today;
  }

  _switchTab(tab) {
    const tabManual = document.getElementById('tab-manual');
    const tabScan = document.getElementById('tab-scan');
    const contentManual = document.getElementById('tab-content-manual');
    const contentScan = document.getElementById('tab-content-scan');

    if (tab === 'manual') {
      tabManual.classList.add('text-primary', 'border-primary');
      tabManual.classList.remove('text-on-surface-variant', 'border-transparent');
      tabScan.classList.remove('text-primary', 'border-primary');
      tabScan.classList.add('text-on-surface-variant', 'border-transparent');
      contentManual.classList.remove('hidden');
      contentScan.classList.add('hidden');
    } else {
      tabScan.classList.add('text-primary', 'border-primary');
      tabScan.classList.remove('text-on-surface-variant', 'border-transparent');
      tabManual.classList.remove('text-primary', 'border-primary');
      tabManual.classList.add('text-on-surface-variant', 'border-transparent');
      contentScan.classList.remove('hidden');
      contentManual.classList.add('hidden');
    }
  }

  async _scanReceipt(file) {
    const ocrResults = document.getElementById('ocr-results');
    ocrResults.classList.remove('hidden');
    ocrResults.innerHTML = `
      <div class="flex items-center justify-center py-8">
        <div class="flex flex-col items-center gap-3">
          <div class="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
          <p class="text-on-surface-variant text-sm">Scanning receipt with AI...</p>
        </div>
      </div>
    `;

    try {
      const result = await expenseAPI.scanReceipt(file);
      const data = result.data;

      ocrResults.innerHTML = `
        <div class="p-4 rounded-xl border border-primary/20 bg-primary/5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-bold text-primary flex items-center gap-2">
              <span class="material-symbols-outlined text-base">auto_awesome</span>
              OCR Results
            </p>
            <span class="px-2 py-1 bg-primary/10 text-primary rounded-lg text-xs font-bold">${Math.round(data.confidence * 100)}% Confidence</span>
          </div>
          <div class="space-y-2 text-sm">
            ${data.merchant ? `<div class="flex justify-between"><span class="text-on-surface-variant">Merchant:</span><span class="font-medium text-on-surface">${data.merchant}</span></div>` : ''}
            ${data.amount ? `<div class="flex justify-between"><span class="text-on-surface-variant">Amount:</span><span class="font-medium text-on-surface">$${data.amount}</span></div>` : ''}
            ${data.date ? `<div class="flex justify-between"><span class="text-on-surface-variant">Date:</span><span class="font-medium text-on-surface">${data.date}</span></div>` : ''}
            ${data.tax ? `<div class="flex justify-between"><span class="text-on-surface-variant">Tax:</span><span class="font-medium text-on-surface">$${data.tax}</span></div>` : ''}
            ${data.category ? `<div class="flex justify-between"><span class="text-on-surface-variant">Category:</span><span class="font-medium text-on-surface">${data.category}</span></div>` : ''}
            ${data.payment_method ? `<div class="flex justify-between"><span class="text-on-surface-variant">Payment:</span><span class="font-medium text-on-surface">${data.payment_method}</span></div>` : ''}
          </div>
          <button type="button" id="apply-ocr-btn" class="w-full mt-3 py-2.5 bg-primary text-white rounded-xl font-bold text-sm hover:brightness-110 transition-all">
            Auto-Fill Form
          </button>
        </div>
      `;

      document.getElementById('apply-ocr-btn').addEventListener('click', () => {
        this._applyOCRData(data);
        this._switchTab('manual');
        toast.success('Receipt data applied to form');
      });
    } catch (err) {
      ocrResults.innerHTML = `
        <div class="p-4 rounded-xl border border-error/20 bg-error/5">
          <p class="text-sm text-error">Failed to scan receipt. Please enter details manually.</p>
        </div>
      `;
    }
  }

  _applyOCRData(data) {
    if (data.merchant) document.getElementById('field-merchant').value = data.merchant;
    if (data.amount) document.getElementById('field-amount').value = data.amount;
    if (data.date) document.getElementById('field-date').value = data.date;
    if (data.tax) document.getElementById('field-tax').value = data.tax;
    if (data.invoice_number) document.getElementById('field-invoice').value = data.invoice_number;
    if (data.category) {
      const catCard = document.querySelector(`[data-category="${data.category}"]`);
      if (catCard) catCard.click();
    }
    if (data.payment_method) {
      const pmSelect = document.getElementById('field-payment');
      pmSelect.value = data.payment_method;
    }
    if (data.merchant && !document.getElementById('field-title').value) {
      document.getElementById('field-title').value = data.merchant;
    }
    this._updatePreview();
  }

  _updatePreview() {
    const title = document.getElementById('field-title').value;
    const amount = document.getElementById('field-amount').value;
    const category = this._selectedCategory || 'Others';
    const preview = document.getElementById('expense-preview');

    if (title && amount) {
      preview.classList.remove('hidden');
      document.getElementById('preview-title').textContent = title;
      document.getElementById('preview-amount').textContent = `$${parseFloat(amount).toFixed(2)}`;
      document.getElementById('preview-category').textContent = category;

      const catMeta = this.categories.find(c => c.name === category);
      if (catMeta) {
        const icon = document.getElementById('preview-icon');
        icon.innerHTML = `<span class="material-symbols-outlined" style="color: ${catMeta.color};">${catMeta.icon}</span>`;
        icon.style.background = catMeta.color + '20';
      }
    } else {
      preview.classList.add('hidden');
    }
  }

  _debouncedBudgetCheck() {
    clearTimeout(this.budgetCheckTimer);
    this.budgetCheckTimer = setTimeout(() => this._checkBudget(), 500);
  }

  async _checkBudget() {
    const category = this._selectedCategory;
    const amount = document.getElementById('field-amount').value;

    if (!category || !amount) {
      document.getElementById('budget-intelligence').classList.add('hidden');
      return;
    }

    try {
      const result = await expenseAPI.budgetCheck(category, amount);
      const data = result.data;

      if (!data.has_budget) {
        document.getElementById('budget-intelligence').classList.add('hidden');
        return;
      }

      const panel = document.getElementById('budget-intelligence');
      panel.classList.remove('hidden');

      const pct = data.percentage_after || 0;
      const bar = document.getElementById('budget-bar');
      const pctLabel = document.getElementById('budget-percentage');

      bar.style.width = Math.min(pct, 100) + '%';
      pctLabel.textContent = pct.toFixed(1) + '% used';

      if (data.is_overspending) {
        bar.style.background = '#ef4444';
        pctLabel.classList.add('text-error');
        pctLabel.classList.remove('text-tertiary', 'text-primary');
      } else if (pct > 80) {
        bar.style.background = '#f59e0b';
        pctLabel.classList.add('text-yellow-500');
        pctLabel.classList.remove('text-error', 'text-tertiary', 'text-primary');
      } else {
        bar.style.background = '#10b981';
        pctLabel.classList.add('text-tertiary');
        pctLabel.classList.remove('text-error', 'text-yellow-500');
      }

      document.getElementById('budget-remaining').textContent = `Remaining: $${data.remaining}`;
      document.getElementById('budget-after').textContent = `After: $${data.after_expense}`;
    } catch (err) {
      // Silent fail
    }
  }

  _debouncedAISuggestions() {
    clearTimeout(this.aiInsightTimer);
    this.aiInsightTimer = setTimeout(() => this._fetchAISuggestions(), 600);
  }

  async _fetchAISuggestions() {
    const title = document.getElementById('field-title').value;
    const merchant = document.getElementById('field-merchant').value;
    const amount = document.getElementById('field-amount').value;

    if (!title && !merchant) {
      document.getElementById('ai-insights').classList.add('hidden');
      return;
    }

    try {
      const result = await expenseAPI.getAISuggestions({ title, merchant, amount });
      const data = result.data;
      const container = document.getElementById('ai-insights');

      const insights = [];
      if (data.suggested_category && data.suggested_category !== 'Others') {
        insights.push(`<div class="p-2.5 rounded-lg bg-primary/5 border border-primary/20 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-base">auto_awesome</span>
          <span class="text-xs text-on-surface">Suggested category: <strong class="text-primary">${data.suggested_category}</strong></span>
        </div>`);
      }
      if (data.insight) {
        insights.push(`<div class="p-2.5 rounded-lg bg-yellow-500/5 border border-yellow-500/20 flex items-center gap-2">
          <span class="material-symbols-outlined text-yellow-500 text-base">insights</span>
          <span class="text-xs text-on-surface">${data.insight}</span>
        </div>`);
      }
      if (data.recurring_suggestion) {
        insights.push(`<div class="p-2.5 rounded-lg bg-tertiary/5 border border-tertiary/20 flex items-center gap-2">
          <span class="material-symbols-outlined text-tertiary text-base">repeat</span>
          <span class="text-xs text-on-surface">${data.recurring_suggestion}</span>
        </div>`);
      }
      if (data.average_amount) {
        insights.push(`<div class="p-2.5 rounded-lg bg-surface-container border border-outline-variant flex items-center gap-2">
          <span class="material-symbols-outlined text-on-surface-variant text-base">analytics</span>
          <span class="text-xs text-on-surface-variant">Average: <strong class="text-on-surface">$${data.average_amount}</strong></span>
        </div>`);
      }

      if (insights.length > 0) {
        container.innerHTML = insights.join('');
        container.classList.remove('hidden');
      } else {
        container.classList.add('hidden');
      }
    } catch (err) {
      // Silent fail
    }
  }

  _debouncedDuplicateCheck() {
    clearTimeout(this.duplicateCheckTimer);
    this.duplicateCheckTimer = setTimeout(() => this._checkDuplicate(), 800);
  }

  async _checkDuplicate() {
    const title = document.getElementById('field-title').value;
    const amount = document.getElementById('field-amount').value;
    const date = document.getElementById('field-date').value;
    const merchant = document.getElementById('field-merchant').value;

    if (!title || !amount || !date) return;

    try {
      const result = await expenseAPI.checkDuplicate({ title, amount, expense_date: date, merchant_name: merchant });
      const data = result.data;

      if (data.possible_duplicate && data.duplicates.length > 0) {
        const warning = document.getElementById('duplicate-warning');
        const details = document.getElementById('duplicate-details');
        const dup = data.duplicates[0];
        details.innerHTML = `"${dup.title}" - $${dup.amount} on ${dup.expense_date}`;
        warning.classList.remove('hidden');
      } else {
        document.getElementById('duplicate-warning').classList.add('hidden');
      }
    } catch (err) {
      // Silent fail
    }
  }

  _showMerchantSuggestions() {
    const merchant = document.getElementById('field-merchant').value.toLowerCase();
    const container = document.getElementById('merchant-suggestions');

    if (!merchant || merchant.length < 2) {
      container.classList.add('hidden');
      return;
    }

    // Simple keyword-based suggestions
    const knownMerchants = ['Uber', 'Amazon', 'Netflix', 'Spotify', 'Pizza Hut', 'Swiggy', 'Zomato', 'Flipkart', 'Airbnb', 'Starbucks'];
    const matches = knownMerchants.filter(m => m.toLowerCase().includes(merchant)).slice(0, 3);

    if (matches.length > 0) {
      container.innerHTML = matches.map(m => `
        <button type="button" class="w-full text-left px-3 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-sm text-on-surface hover:bg-surface-container-high transition-all merchant-suggestion" data-merchant="${m}">
          ${m}
        </button>
      `).join('');
      container.classList.remove('hidden');

      container.querySelectorAll('.merchant-suggestion').forEach(btn => {
        btn.addEventListener('click', () => {
          document.getElementById('field-merchant').value = btn.dataset.merchant;
          container.classList.add('hidden');
          this._debouncedAISuggestions();
        });
      });
    } else {
      container.classList.add('hidden');
    }
  }

  _addSplit() {
    const container = document.getElementById('splits-container');
    const splitId = `split-${Date.now()}`;
    const splitHTML = `
      <div id="${splitId}" class="flex gap-2 items-center p-2 bg-surface-container rounded-lg border border-outline-variant">
        <input type="text" placeholder="Name" class="split-name flex-1 bg-surface-container-low border border-outline-variant rounded-lg px-2 py-1.5 text-sm text-on-surface outline-none focus:border-primary" />
        <select class="split-type bg-surface-container-low border border-outline-variant rounded-lg px-2 py-1.5 text-sm text-on-surface outline-none focus:border-primary">
          <option value="friends">Friends</option>
          <option value="family">Family</option>
          <option value="office">Office</option>
          <option value="custom">Custom</option>
        </select>
        <input type="number" placeholder="Amount" class="split-amount w-24 bg-surface-container-low border border-outline-variant rounded-lg px-2 py-1.5 text-sm text-on-surface outline-none focus:border-primary" />
        <button type="button" class="p-1.5 text-error hover:bg-error/10 rounded-lg transition-colors split-remove-btn">
          <span class="material-symbols-outlined text-base">delete</span>
        </button>
      </div>
    `;
    container.insertAdjacentHTML('beforeend', splitHTML);

    container.querySelector(`#${splitId} .split-remove-btn`).addEventListener('click', () => {
      document.getElementById(splitId).remove();
    });
  }

  _getSplits() {
    const splits = [];
    document.querySelectorAll('#splits-container > div').forEach(splitEl => {
      const name = splitEl.querySelector('.split-name')?.value;
      const type = splitEl.querySelector('.split-type')?.value;
      const amount = splitEl.querySelector('.split-amount')?.value;
      if (name && amount) {
        splits.push({
          split_with_name: name,
          split_type: type,
          split_method: 'custom',
          amount: parseFloat(amount),
        });
      }
    });
    return splits;
  }

  _getFormData() {
    const tagsStr = document.getElementById('field-tags').value;
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

    return {
      title: document.getElementById('field-title').value.trim(),
      merchant_name: document.getElementById('field-merchant').value.trim() || null,
      category: this._selectedCategory || 'Others',
      sub_category: document.getElementById('field-sub-category').value.trim() || null,
      amount: document.getElementById('field-amount').value,
      currency: document.getElementById('field-currency').value,
      expense_date: document.getElementById('field-date').value,
      payment_method: document.getElementById('field-payment').value,
      account_id: document.getElementById('field-account').value || null,
      location: document.getElementById('field-location').value.trim() || null,
      description: document.getElementById('field-description').value.trim() || null,
      tags: tags,
      priority: document.getElementById('field-priority').value || null,
      mood: document.getElementById('field-mood').value || null,
      recurring: document.getElementById('field-recurring').checked,
      recurring_frequency: document.getElementById('field-recurring').checked ? document.getElementById('field-recurring-frequency').value : null,
      tax_included: document.getElementById('field-tax').value || null,
      invoice_number: document.getElementById('field-invoice').value.trim() || null,
      notes: document.getElementById('field-notes').value.trim() || null,
      splits: this._getSplits(),
    };
  }

  _validateForm(data) {
    const errors = {};
    if (!data.title || data.title.length < 3) {
      errors.title = 'Title must be at least 3 characters';
    }
    if (!data.amount || parseFloat(data.amount) <= 0) {
      errors.amount = 'Amount must be greater than 0';
    }
    if (!data.expense_date) {
      errors.expense_date = 'Date is required';
    } else {
      const inputDate = new Date(data.expense_date);
      const today = new Date();
      today.setHours(23, 59, 59);
      if (inputDate > today) {
        errors.expense_date = 'Date cannot be in the future';
      }
    }
    if (!data.payment_method) {
      errors.payment_method = 'Payment method is required';
    }
    return errors;
  }

  async _saveExpense(addAnother) {
    const data = this._getFormData();
    const errors = this._validateForm(data);

    if (Object.keys(errors).length > 0) {
      Object.values(errors).forEach(err => toast.error(err));
      return;
    }

    // Check for duplicates if not forced
    if (!this._forceSave) {
      try {
        const dupResult = await expenseAPI.checkDuplicate({
          title: data.title,
          amount: data.amount,
          expense_date: data.expense_date,
          merchant_name: data.merchant_name,
        });
        if (dupResult.data.possible_duplicate) {
          document.getElementById('duplicate-warning').classList.remove('hidden');
          return;
        }
      } catch (err) {
        // Continue with save
      }
    }

    this._showLoading('Saving expense...');

    try {
      await expenseAPI.createExpense(data, this.currentReceiptFile);

      this._hideLoading();
      this._showSuccess();

      // Delete draft
      try { await expenseAPI.deleteDraft(); } catch (e) {}

      setTimeout(() => {
        this._hideSuccess();
        if (addAnother) {
          this._resetForm();
        } else {
          this.close();
        }
        this.onSave();
      }, 1500);
    } catch (err) {
      this._hideLoading();
      toast.error(err.message || 'Failed to save expense');
    }

    this._forceSave = false;
  }

  _showLoading(text = 'Loading...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('drawer-loading').classList.remove('hidden');
  }

  _hideLoading() {
    document.getElementById('drawer-loading').classList.add('hidden');
  }

  _showSuccess() {
    document.getElementById('drawer-success').classList.remove('hidden');
  }

  _hideSuccess() {
    document.getElementById('drawer-success').classList.add('hidden');
  }

  _resetForm() {
    document.querySelectorAll('#tab-content-manual input, #tab-content-manual textarea').forEach(el => {
      if (el.type !== 'checkbox') el.value = '';
    });
    document.querySelectorAll('#tab-content-manual select').forEach(el => {
      el.value = el.querySelector('option')?.value || '';
    });
    document.getElementById('field-recurring').checked = false;
    document.getElementById('field-recurring-frequency').classList.add('hidden');
    document.querySelectorAll('.category-card').forEach(c => {
      c.classList.remove('border-primary', 'bg-primary/10');
    });
    this._selectedCategory = null;
    this.splits = [];
    document.getElementById('splits-container').innerHTML = '';
    document.getElementById('ai-insights').classList.add('hidden');
    document.getElementById('duplicate-warning').classList.add('hidden');
    document.getElementById('expense-preview').classList.add('hidden');
    document.getElementById('budget-intelligence').classList.add('hidden');
    if (this.receiptUploader) this.receiptUploader.clear();
    this.currentReceiptFile = null;
    this._setDefaultDate();
  }

  async _saveDraft() {
    const data = this._getFormData();
    if (!data.title && !data.amount) return;

    try {
      await expenseAPI.saveDraft(data);
    } catch (err) {
      // Silent fail
    }
  }

  async _loadDraft() {
    try {
      const result = await expenseAPI.getDraft();
      if (result.data?.draft) {
        const draft = typeof result.data.draft === 'string' ? JSON.parse(result.data.draft) : result.data.draft;
        Object.keys(draft).forEach(key => {
          const el = document.querySelector(`[name="${key}"]`);
          if (el) {
            if (el.type === 'checkbox') {
              el.checked = draft[key];
            } else {
              el.value = draft[key] || '';
            }
          }
        });
        if (draft.category) {
          const catCard = document.querySelector(`[data-category="${draft.category}"]`);
          if (catCard) catCard.click();
        }
        this._updatePreview();
      }
    } catch (err) {
      // Silent fail
    }
  }
}
