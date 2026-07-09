// Expense Handler - Complete UI Management
class ExpenseHandler {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.filters = {};
        this.expenses = [];
        this.editingId = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadMetadata();
        await this.loadExpenses();
        await this.loadDashboard();
    }

    setupEventListeners() {
        // Add Expense Button
        const addBtn = document.querySelector('button[onclick="expenseHandler.openAddModal()"]');
        if (addBtn) {
            addBtn.removeAttribute('onclick');
            addBtn.addEventListener('click', () => this.openAddModal());
        }

        // Modal Form Submit
        const saveBtn = document.getElementById('save-expense-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveExpense());
        }

        // Modal Close
        const closeBtn = document.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }

        // Search
        const searchInput = document.querySelector('input[placeholder*="Search"]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
                this.currentPage = 1;
                this.loadExpenses();
            });
        }

        // Filter Buttons
        const filterBtns = document.querySelectorAll('[data-filter]');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleFilter(btn);
            });
        });

        // Export Buttons
        const exportPdfBtn = document.querySelector('[data-export="pdf"]');
        const exportExcelBtn = document.querySelector('[data-export="excel"]');
        const exportCsvBtn = document.querySelector('[data-export="csv"]');

        if (exportPdfBtn) exportPdfBtn.addEventListener('click', () => this.exportPDF());
        if (exportExcelBtn) exportExcelBtn.addEventListener('click', () => this.exportExcel());
        if (exportCsvBtn) exportCsvBtn.addEventListener('click', () => this.exportCSV());

        // Pagination
        const prevBtn = document.querySelector('.pagination [data-action="prev"]');
        const nextBtn = document.querySelector('.pagination [data-action="next"]');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousPage());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextPage());
    }

    async loadMetadata() {
        try {
            const [categories, paymentMethods, accounts] = await Promise.all([
                expenseService.getCategories(),
                expenseService.getPaymentMethods(),
                expenseService.getAccounts()
            ]);

            this.categories = categories.data.categories || [];
            this.paymentMethods = paymentMethods.data.payment_methods || [];
            this.accounts = accounts.data.accounts || [];
        } catch (error) {
            console.error('Error loading metadata:', error);
            this.showToast('Error loading form data', 'error');
        }
    }

    async loadDashboard() {
        try {
            const response = await expenseService.getDashboardStats();
            const stats = response.data;

            this.updateDashboardCard('total-expenses', stats.total_amount, stats.total_expenses + ' transactions');
            this.updateDashboardCard('today-expenses', stats.today_amount, 'Today');
            this.updateDashboardCard('month-expenses', stats.month_amount, 'This month');
            this.updateDashboardCard('week-expenses', stats.week_amount, 'This week');

            // Update charts
            await this.loadCharts();
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    updateDashboardCard(selector, amount, label) {
        const card = document.querySelector(`[data-card="${selector}"]`);
        if (card) {
            const amountEl = card.querySelector('.amount');
            const labelEl = card.querySelector('.label');
            if (amountEl) amountEl.textContent = `$${parseFloat(amount).toFixed(2)}`;
            if (labelEl) labelEl.textContent = label;
        }
    }

    async loadCharts() {
        try {
            const response = await expenseService.getChartData(this.filters);
            const chartData = response.data;

            this.drawCategoryChart(chartData.category_chart);
            this.drawMonthlyChart(chartData.monthly_chart);
            this.drawPaymentChart(chartData.payment_chart);
            this.drawDailyChart(chartData.daily_chart);
        } catch (error) {
            console.error('Error loading charts:', error);
        }
    }

    drawCategoryChart(data) {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;

        if (window.categoryChartInstance) {
            window.categoryChartInstance.destroy();
        }

        const colors = ['#8B5CF6', '#6366F1', '#10B981', '#F59E0B', '#EF4444', '#EC4899', '#14B8A6'];
        
        window.categoryChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.value),
                    backgroundColor: colors.slice(0, data.length),
                    borderColor: '#0b1326',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f8f9ff',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    drawMonthlyChart(data) {
        const ctx = document.getElementById('monthlyChart');
        if (!ctx) return;

        if (window.monthlyChartInstance) {
            window.monthlyChartInstance.destroy();
        }

        window.monthlyChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.month),
                datasets: [{
                    label: 'Monthly Spending',
                    data: data.map(d => d.total),
                    backgroundColor: '#8B5CF6',
                    borderColor: '#6D28D9',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f8f9ff' }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    drawPaymentChart(data) {
        const ctx = document.getElementById('paymentChart');
        if (!ctx) return;

        if (window.paymentChartInstance) {
            window.paymentChartInstance.destroy();
        }

        const colors = ['#8B5CF6', '#6366F1', '#10B981', '#F59E0B', '#EF4444'];
        
        window.paymentChartInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.value),
                    backgroundColor: colors.slice(0, data.length),
                    borderColor: '#0b1326',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#f8f9ff',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    drawDailyChart(data) {
        const ctx = document.getElementById('dailyChart');
        if (!ctx) return;

        if (window.dailyChartInstance) {
            window.dailyChartInstance.destroy();
        }

        window.dailyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Daily Expenses',
                    data: data.map(d => d.total),
                    borderColor: '#8B5CF6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#8B5CF6',
                    pointBorderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#f8f9ff' }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    async loadExpenses() {
        try {
            const response = await expenseService.getExpenses({
                ...this.filters,
                page: this.currentPage,
                perPage: this.perPage
            });

            this.expenses = response.data.expenses;
            const pagination = response.data.pagination;

            this.renderExpensesTable(this.expenses);
            this.updatePagination(pagination);
        } catch (error) {
            console.error('Error loading expenses:', error);
            this.showToast('Error loading expenses', 'error');
        }
    }

    renderExpensesTable(expenses) {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (expenses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8">No expenses found</td></tr>';
            return;
        }

        expenses.forEach(exp => {
            const categoryIcon = this.getCategoryIcon(exp.category);
            const row = document.createElement('tr');
            row.className = 'group hover:bg-primary/5 transition-colors cursor-pointer';
            row.innerHTML = `
                <td class="px-gutter py-5">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                            <span class="material-symbols-outlined text-primary">${categoryIcon}</span>
                        </div>
                        <div>
                            <p class="font-bold text-on-surface group-hover:text-primary transition-colors">${exp.title}</p>
                            <p class="text-xs text-on-surface-variant">${exp.category}</p>
                        </div>
                    </div>
                </td>
                <td class="px-gutter py-5 font-body-sm text-on-surface-variant">${exp.expense_date}</td>
                <td class="px-gutter py-5 font-body-sm text-on-surface">${exp.payment_method}</td>
                <td class="px-gutter py-5 font-data-mono text-data-mono font-bold text-on-surface">$${parseFloat(exp.amount).toFixed(2)}</td>
                <td class="px-gutter py-5">
                    <div class="flex items-center gap-2 text-tertiary font-bold text-[10px] uppercase tracking-widest">
                        <span class="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_6px_#10b981]"></span>
                        ${exp.status}
                    </div>
                </td>
                <td class="px-gutter py-5 text-right">
                    <div class="opacity-0 group-hover:opacity-100 flex gap-2 transition-all">
                        <button class="p-2 hover:bg-primary/10 rounded-lg transition-all text-on-surface-variant hover:text-primary" onclick="expenseHandler.viewExpense(${exp.id})">
                            <span class="material-symbols-outlined text-sm">visibility</span>
                        </button>
                        <button class="p-2 hover:bg-primary/10 rounded-lg transition-all text-on-surface-variant hover:text-primary" onclick="expenseHandler.editExpense(${exp.id})">
                            <span class="material-symbols-outlined text-sm">edit</span>
                        </button>
                        <button class="p-2 hover:bg-primary/10 rounded-lg transition-all text-on-surface-variant hover:text-primary" onclick="expenseHandler.duplicateExpense(${exp.id})">
                            <span class="material-symbols-outlined text-sm">content_copy</span>
                        </button>
                        <button class="p-2 hover:bg-error/10 rounded-lg transition-all text-on-surface-variant hover:text-error" onclick="expenseHandler.deleteExpense(${exp.id})">
                            <span class="material-symbols-outlined text-sm">delete</span>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    getCategoryIcon(category) {
        const iconMap = {
            'Food': 'restaurant',
            'Travel': 'flight',
            'Shopping': 'shopping_bag',
            'Entertainment': 'theaters',
            'Health': 'local_hospital',
            'Transportation': 'directions_car',
            'Bills': 'receipt_long',
            'Other': 'category'
        };
        return iconMap[category] || 'payments';
    }

    updatePagination(pagination) {
        const paginationEl = document.querySelector('.pagination');
        if (!paginationEl) return;

        const pageNumbers = paginationEl.querySelector('.page-numbers');
        if (pageNumbers) {
            pageNumbers.innerHTML = '';
            for (let i = 1; i <= pagination.pages; i++) {
                const btn = document.createElement('button');
                btn.className = i === pagination.page 
                    ? 'px-4 py-2 bg-primary text-on-primary rounded-lg font-bold text-xs shadow-md shadow-primary/20'
                    : 'px-4 py-2 bg-surface border border-outline-variant hover:bg-primary/10 hover:border-primary rounded-lg font-bold text-xs transition-all text-on-surface';
                btn.textContent = i;
                btn.addEventListener('click', () => {
                    this.currentPage = i;
                    this.loadExpenses();
                });
                pageNumbers.appendChild(btn);
            }
        }

        const info = paginationEl.querySelector('.info');
        if (info) {
            info.textContent = `Showing ${(pagination.page - 1) * pagination.per_page + 1} to ${Math.min(pagination.page * pagination.per_page, pagination.total)} of ${pagination.total} entries`;
        }
    }

    openAddModal() {
        this.editingId = null;
        this.resetForm();
        document.getElementById('expense-modal').classList.remove('hidden');
    }

    async editExpense(id) {
        try {
            const response = await expenseService.getExpense(id);
            const expense = response.data;

            this.editingId = id;
            this.populateForm(expense);
            document.getElementById('expense-modal').classList.remove('hidden');
        } catch (error) {
            console.error('Error loading expense:', error);
            this.showToast('Error loading expense', 'error');
        }
    }

    async viewExpense(id) {
        try {
            const response = await expenseService.getExpense(id);
            const expense = response.data;

            // Show detail drawer
            const drawer = document.getElementById('expense-detail-drawer');
            if (drawer) {
                document.getElementById('detail-merchant').textContent = expense.merchant_name || expense.title;
                document.getElementById('detail-amount').textContent = `$${parseFloat(expense.amount).toFixed(2)}`;
                document.getElementById('detail-category').textContent = expense.category;
                drawer.classList.remove('translate-x-full');
                drawer.classList.add('pointer-events-auto');
            }
        } catch (error) {
            console.error('Error viewing expense:', error);
        }
    }

    async duplicateExpense(id) {
        try {
            const response = await expenseService.duplicateExpense(id);
            this.showToast('Expense duplicated successfully', 'success');
            await this.loadExpenses();
        } catch (error) {
            console.error('Error duplicating expense:', error);
            this.showToast('Error duplicating expense', 'error');
        }
    }

    async deleteExpense(id) {
        if (confirm('Are you sure you want to delete this expense?')) {
            try {
                await expenseService.deleteExpense(id);
                this.showToast('Expense deleted successfully', 'success');
                await this.loadExpenses();
            } catch (error) {
                console.error('Error deleting expense:', error);
                this.showToast('Error deleting expense', 'error');
            }
        }
    }

    async saveExpense() {
        try {
            const formData = this.getFormData();
            const receiptFile = document.getElementById('receipt-input')?.files[0];

            if (this.editingId) {
                await expenseService.updateExpense(this.editingId, formData);
                this.showToast('Expense updated successfully', 'success');
            } else {
                await expenseService.createExpense(formData, receiptFile);
                this.showToast('Expense added successfully', 'success');
            }

            this.closeModal();
            await this.loadExpenses();
            await this.loadDashboard();
        } catch (error) {
            console.error('Error saving expense:', error);
            this.showToast(error.message || 'Error saving expense', 'error');
        }
    }

    getFormData() {
        return {
            title: document.getElementById('expense-title')?.value || '',
            category: document.getElementById('expense-category')?.value || '',
            amount: document.getElementById('expense-amount')?.value || '',
            expense_date: document.getElementById('expense-date')?.value || '',
            payment_method: document.getElementById('expense-payment')?.value || '',
            merchant_name: document.getElementById('expense-merchant')?.value || '',
            location: document.getElementById('expense-location')?.value || '',
            description: document.getElementById('expense-description')?.value || '',
            currency: document.getElementById('expense-currency')?.value || 'USD',
            recurring: document.getElementById('expense-recurring')?.checked || false,
        };
    }

    populateForm(expense) {
        if (document.getElementById('expense-title')) {
            document.getElementById('expense-title').value = expense.title;
            document.getElementById('expense-category').value = expense.category;
            document.getElementById('expense-amount').value = expense.amount;
            document.getElementById('expense-date').value = expense.expense_date;
            document.getElementById('expense-payment').value = expense.payment_method;
            document.getElementById('expense-merchant').value = expense.merchant_name || '';
            document.getElementById('expense-location').value = expense.location || '';
            document.getElementById('expense-description').value = expense.description || '';
            document.getElementById('expense-currency').value = expense.currency || 'USD';
            document.getElementById('expense-recurring').checked = expense.recurring || false;
        }
    }

    resetForm() {
        document.getElementById('expense-form')?.reset();
    }

    closeModal() {
        document.getElementById('expense-modal')?.classList.add('hidden');
        this.resetForm();
        this.editingId = null;
    }

    handleFilter(btn) {
        const filter = btn.dataset.filter;
        if (filter === 'date') {
            // Handle date range filter
            const dateFrom = prompt('From date (YYYY-MM-DD):');
            if (dateFrom) {
                this.filters.dateFrom = dateFrom;
                const dateTo = prompt('To date (YYYY-MM-DD):');
                if (dateTo) {
                    this.filters.dateTo = dateTo;
                }
            }
        } else if (filter === 'category') {
            const category = prompt('Enter category:');
            if (category) this.filters.category = category;
        }
        this.currentPage = 1;
        this.loadExpenses();
    }

    async exportCSV() {
        try {
            const csv = await expenseService.exportCSV(this.expenses);
            this.downloadFile(csv, 'expenses.csv', 'text/csv');
        } catch (error) {
            console.error('Error exporting CSV:', error);
        }
    }

    async exportExcel() {
        try {
            const excel = await expenseService.exportExcel(this.expenses);
            this.downloadFile(excel, 'expenses.xls', 'application/vnd.ms-excel');
        } catch (error) {
            console.error('Error exporting Excel:', error);
        }
    }

    async exportPDF() {
        this.showToast('PDF export requires jsPDF library', 'info');
    }

    downloadFile(content, filename, type) {
        const element = document.createElement('a');
        element.setAttribute('href', `data:${type};charset=utf-8,${encodeURIComponent(content)}`);
        element.setAttribute('download', filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadExpenses();
        }
    }

    nextPage() {
        this.currentPage++;
        this.loadExpenses();
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg font-bold text-sm z-50 ${
            type === 'success' ? 'bg-tertiary text-white' :
            type === 'error' ? 'bg-error text-white' :
            'bg-primary text-white'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize on page load
let expenseHandler;
document.addEventListener('DOMContentLoaded', () => {
    expenseHandler = new ExpenseHandler();
});
