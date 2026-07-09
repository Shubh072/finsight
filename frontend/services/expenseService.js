// Expense Service - Complete API Integration
class ExpenseService {
    constructor() {
        this.baseURL = '/api/expenses';
        this.token = localStorage.getItem('access_token');
    }

    // Helper method for API calls
    async apiCall(endpoint, method = 'GET', data = null, isFormData = false) {
        const headers = {
            'Authorization': `Bearer ${this.token}`,
        };

        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }

        const options = {
            method,
            headers,
        };

        if (data) {
            if (isFormData) {
                options.body = data;
            } else {
                options.body = JSON.stringify(data);
            }
        }

        try {
            const response = await fetch(endpoint, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'API Error');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // CREATE - Add new expense
    async createExpense(expenseData, receiptFile = null) {
        let formData = null;
        
        if (receiptFile) {
            formData = new FormData();
            formData.append('receipt', receiptFile);
            
            // Add other fields
            Object.keys(expenseData).forEach(key => {
                if (key !== 'tags') {
                    formData.append(key, expenseData[key]);
                } else {
                    formData.append(key, JSON.stringify(expenseData[key]));
                }
            });

            return this.apiCall(`${this.baseURL}/`, 'POST', formData, true);
        } else {
            return this.apiCall(`${this.baseURL}/`, 'POST', expenseData);
        }
    }

    // READ - Get all expenses with filters
    async getExpenses(filters = {}) {
        const params = new URLSearchParams();
        
        if (filters.search) params.append('search', filters.search);
        if (filters.category) params.append('category', filters.category);
        if (filters.paymentMethod) params.append('payment_method', filters.paymentMethod);
        if (filters.status) params.append('status', filters.status);
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        if (filters.amountMin) params.append('amount_min', filters.amountMin);
        if (filters.amountMax) params.append('amount_max', filters.amountMax);
        if (filters.merchant) params.append('merchant', filters.merchant);
        if (filters.sort) params.append('sort', filters.sort);
        if (filters.order) params.append('order', filters.order);
        if (filters.page) params.append('page', filters.page);
        if (filters.perPage) params.append('per_page', filters.perPage);

        const url = params.toString() ? `${this.baseURL}/?${params}` : this.baseURL + '/';
        return this.apiCall(url, 'GET');
    }

    // READ - Get single expense
    async getExpense(id) {
        return this.apiCall(`${this.baseURL}/${id}`, 'GET');
    }

    // UPDATE - Edit expense
    async updateExpense(id, expenseData) {
        return this.apiCall(`${this.baseURL}/${id}`, 'PUT', expenseData);
    }

    // DELETE - Remove expense
    async deleteExpense(id) {
        return this.apiCall(`${this.baseURL}/${id}`, 'DELETE');
    }

    // DUPLICATE - Create a copy of expense
    async duplicateExpense(id, modifications = {}) {
        return this.apiCall(`${this.baseURL}/${id}/duplicate`, 'POST', modifications);
    }

    // ANALYTICS - Get statistics
    async getStatistics(filters = {}) {
        let url = `${this.baseURL}/statistics`;
        const params = new URLSearchParams();
        
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        
        if (params.toString()) {
            url += `?${params}`;
        }
        
        return this.apiCall(url, 'GET');
    }

    // ANALYTICS - Get chart data
    async getChartData(filters = {}) {
        let url = `${this.baseURL}/chart-data`;
        const params = new URLSearchParams();
        
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        
        if (params.toString()) {
            url += `?${params}`;
        }
        
        return this.apiCall(url, 'GET');
    }

    // DASHBOARD - Get dashboard stats
    async getDashboardStats() {
        return this.apiCall(`${this.baseURL}/dashboard-stats`, 'GET');
    }

    // DUPLICATE CHECK - Check for duplicate expenses
    async checkDuplicate(expenseData) {
        return this.apiCall(`${this.baseURL}/duplicate-check`, 'POST', expenseData);
    }

    // METADATA - Get categories
    async getCategories() {
        return this.apiCall(`${this.baseURL}/categories`, 'GET');
    }

    // METADATA - Get payment methods
    async getPaymentMethods() {
        return this.apiCall(`${this.baseURL}/payment-methods`, 'GET');
    }

    // METADATA - Get user accounts
    async getAccounts() {
        return this.apiCall(`${this.baseURL}/accounts`, 'GET');
    }

    // Export - Generate CSV
    async exportCSV(expenses) {
        const headers = ['ID', 'Title', 'Category', 'Amount', 'Date', 'Payment Method', 'Merchant', 'Status'];
        let csv = headers.join(',') + '\n';

        expenses.forEach(exp => {
            csv += `${exp.id},"${exp.title}","${exp.category}",${exp.amount},"${exp.expense_date}","${exp.payment_method}","${exp.merchant_name || ''}","${exp.status}"\n`;
        });

        return csv;
    }

    // Export - Generate Excel (using basic approach)
    async exportExcel(expenses) {
        // For Excel, we'll use a simple approach with formatting
        let excel = 'data:application/vnd.ms-excel;charset=utf-8,';
        excel += 'ID\tTitle\tCategory\tAmount\tDate\tPayment Method\tMerchant\tStatus\n';

        expenses.forEach(exp => {
            excel += `${exp.id}\t${exp.title}\t${exp.category}\t${exp.amount}\t${exp.expense_date}\t${exp.payment_method}\t${exp.merchant_name || ''}\t${exp.status}\n`;
        });

        return encodeURI(excel);
    }

    // Export - Generate PDF (requires jsPDF library)
    async exportPDF(expenses) {
        // This requires jsPDF library to be included
        return {
            expenses: expenses,
            type: 'pdf'
        };
    }
}

// Initialize the service
const expenseService = new ExpenseService();
