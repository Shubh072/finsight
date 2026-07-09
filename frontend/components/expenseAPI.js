/**
 * Expense API Service - Handles all expense-related API calls
 * Uses fetch API with JWT authentication
 */
class ExpenseAPIService {
  constructor() {
    this.baseURL = '/api/expenses';
  }

  _getToken() {
    return localStorage.getItem('access_token');
  }

  _getHeaders(isFormData = false) {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const token = this._getToken();
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    return headers;
  }

  async _request(url, options = {}) {
    try {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.message || `Request failed (${response.status})`);
      }
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // CREATE - Add new expense with optional receipt
  async createExpense(expenseData, receiptFile = null) {
    if (receiptFile) {
      const formData = new FormData();
      formData.append('receipt', receiptFile);
      Object.keys(expenseData).forEach(key => {
        const val = expenseData[key];
        if (key === 'tags' || key === 'splits') {
          formData.append(key, JSON.stringify(val));
        } else {
          formData.append(key, val);
        }
      });
      return this._request(`${this.baseURL}/`, {
        method: 'POST',
        headers: this._getHeaders(true),
        body: formData,
      });
    } else {
      return this._request(`${this.baseURL}/`, {
        method: 'POST',
        headers: this._getHeaders(),
        body: JSON.stringify(expenseData),
      });
    }
  }

  // READ - Get expenses with filters
  async getExpenses(filters = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
        params.append(key, filters[key]);
      }
    });
    const url = `${this.baseURL}/?${params.toString()}`;
    return this._request(url, { headers: this._getHeaders() });
  }

  // READ - Get single expense
  async getExpense(id) {
    return this._request(`${this.baseURL}/${id}`, { headers: this._getHeaders() });
  }

  // UPDATE
  async updateExpense(id, data) {
    return this._request(`${this.baseURL}/${id}`, {
      method: 'PUT',
      headers: this._getHeaders(),
      body: JSON.stringify(data),
    });
  }

  // DELETE (soft delete)
  async deleteExpense(id) {
    return this._request(`${this.baseURL}/${id}`, {
      method: 'DELETE',
      headers: this._getHeaders(),
    });
  }

  // DUPLICATE
  async duplicateExpense(id, modifications = {}) {
    return this._request(`${this.baseURL}/${id}/duplicate`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(modifications),
    });
  }

  // UNDO
  async undoExpense(id) {
    return this._request(`${this.baseURL}/undo/${id}`, {
      method: 'POST',
      headers: this._getHeaders(),
    });
  }

  // SCAN RECEIPT (OCR)
  async scanReceipt(receiptFile) {
    const formData = new FormData();
    formData.append('receipt', receiptFile);
    return this._request(`${this.baseURL}/scan-receipt`, {
      method: 'POST',
      headers: this._getHeaders(true),
      body: formData,
    });
  }

  // DUPLICATE CHECK
  async checkDuplicate(data) {
    return this._request(`${this.baseURL}/duplicate-check`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(data),
    });
  }

  // AI SUGGESTIONS
  async getAISuggestions(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this._request(`${this.baseURL}/ai-suggestions?${query}`, {
      headers: this._getHeaders(),
    });
  }

  // BUDGET CHECK
  async budgetCheck(category, amount) {
    const params = new URLSearchParams({ category, amount });
    return this._request(`${this.baseURL}/budget-check?${params}`, {
      headers: this._getHeaders(),
    });
  }

  // BUDGETS
  async getBudgets() {
    return this._request(`${this.baseURL}/budgets`, { headers: this._getHeaders() });
  }

  async createBudget(data) {
    return this._request(`${this.baseURL}/budgets`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(data),
    });
  }

  // CATEGORIES
  async getCategories() {
    return this._request(`${this.baseURL}/categories`, { headers: this._getHeaders() });
  }

  // PAYMENT METHODS
  async getPaymentMethods() {
    return this._request(`${this.baseURL}/payment-methods`, { headers: this._getHeaders() });
  }

  // ACCOUNTS
  async getAccounts() {
    return this._request(`${this.baseURL}/accounts`, { headers: this._getHeaders() });
  }

  async createAccount(data) {
    return this._request(`${this.baseURL}/accounts`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(data),
    });
  }

  // FAVORITE MERCHANTS
  async getFavoriteMerchants() {
    return this._request(`${this.baseURL}/favorite-merchants`, { headers: this._getHeaders() });
  }

  // TEMPLATES
  async getTemplates() {
    return this._request(`${this.baseURL}/templates`, { headers: this._getHeaders() });
  }

  async createTemplate(data) {
    return this._request(`${this.baseURL}/templates`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(data),
    });
  }

  // DRAFTS
  async getDraft() {
    return this._request(`${this.baseURL}/drafts`, { headers: this._getHeaders() });
  }

  async saveDraft(draftData) {
    return this._request(`${this.baseURL}/drafts`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify({ draft_data: draftData }),
    });
  }

  async deleteDraft() {
    return this._request(`${this.baseURL}/drafts`, {
      method: 'DELETE',
      headers: this._getHeaders(),
    });
  }

  // RECENT
  async getRecentExpenses() {
    return this._request(`${this.baseURL}/recent`, { headers: this._getHeaders() });
  }

  // QUICK ADD
  async getQuickAddAmounts() {
    return this._request(`${this.baseURL}/quick-add-amounts`, { headers: this._getHeaders() });
  }

  // DASHBOARD STATS
  async getDashboardStats() {
    return this._request(`${this.baseURL}/dashboard-stats`, { headers: this._getHeaders() });
  }

  // CHART DATA
  async getChartData(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    const url = `${this.baseURL}/chart-data${params ? '?' + params : ''}`;
    return this._request(url, { headers: this._getHeaders() });
  }

  // STATISTICS
  async getStatistics(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    const url = `${this.baseURL}/statistics${params ? '?' + params : ''}`;
    return this._request(url, { headers: this._getHeaders() });
  }
}

// Export singleton instance
const expenseAPI = new ExpenseAPIService();
