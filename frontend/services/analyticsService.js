/**
 * Analytics Service for FinSight
 * Handles all API calls and data processing for the Analytics dashboard
 */

// Get auth token from localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// API call helper
async function apiCall(endpoint, options = {}) {
    const token = getAuthToken();
    if (!token) {
        throw new Error('No authentication token found');
    }
    
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    };
    
    const response = await fetch(endpoint, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'API request failed' }));
        throw new Error(error.message || 'API request failed');
    }
    
    return response.json();
}

// Date range helper
function getDateRange(filterType) {
    const today = new Date();
    const formatDate = (d) => d.toISOString().split('T')[0];
    
    switch (filterType) {
        case 'today':
            return { date_from: formatDate(today), date_to: formatDate(today) };
        case 'last_7_days':
            const d7 = new Date(today);
            d7.setDate(today.getDate() - 6);
            return { date_from: formatDate(d7), date_to: formatDate(today) };
        case 'last_30_days':
            const d30 = new Date(today);
            d30.setDate(today.getDate() - 29);
            return { date_from: formatDate(d30), date_to: formatDate(today) };
        case 'current_month':
            const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            return { date_from: formatDate(firstOfMonth), date_to: formatDate(today) };
        case 'last_month':
            const firstOfThis = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastOfPrev = new Date(firstOfThis - 1);
            const firstOfPrev = new Date(lastOfPrev.getFullYear(), lastOfPrev.getMonth(), 1);
            return { date_from: formatDate(firstOfPrev), date_to: formatDate(lastOfPrev) };
        case 'last_3_months':
            const d90 = new Date(today);
            d90.setDate(today.getDate() - 90);
            return { date_from: formatDate(d90), date_to: formatDate(today) };
        case 'last_6_months':
            const d180 = new Date(today);
            d180.setDate(today.getDate() - 180);
            return { date_from: formatDate(d180), date_to: formatDate(today) };
        case 'last_12_months':
            const d365 = new Date(today);
            d365.setDate(today.getDate() - 365);
            return { date_from: formatDate(d365), date_to: formatDate(today) };
        default:
            const d30def = new Date(today);
            d30def.setDate(today.getDate() - 29);
            return { date_from: formatDate(d30def), date_to: formatDate(today) };
    }
}

// Fetch all dashboard data
async function fetchDashboardData(filterType = 'last_30_days', customRange = null) {
    const params = new URLSearchParams({ filter: filterType });
    
    if (filterType === 'custom' && customRange) {
        params.set('date_from', customRange.date_from);
        params.set('date_to', customRange.date_to);
    }
    
    try {
        const data = await apiCall(`/api/analytics/dashboard?${params.toString()}`);
        return data.data;
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        throw error;
    }
}

// Fetch individual chart data
async function fetchChartData(chartType, filterType = 'last_30_days', customRange = null) {
    const params = new URLSearchParams({ filter: filterType });
    
    if (filterType === 'custom' && customRange) {
        params.set('date_from', customRange.date_from);
        params.set('date_to', customRange.date_to);
    }
    
    try {
        const data = await apiCall(`/api/analytics/${chartType}?${params.toString()}`);
        return data.data;
    } catch (error) {
        console.error(`Error fetching ${chartType} data:`, error);
        throw error;
    }
}

// Export data
async function exportData(format, filterType = 'last_30_days', customRange = null) {
    const params = new URLSearchParams({ filter: filterType });
    
    if (filterType === 'custom' && customRange) {
        params.set('date_from', customRange.date_from);
        params.set('date_to', customRange.date_to);
    }
    
    try {
        const token = getAuthToken();
        const response = await fetch(`/api/analytics/export?${params.toString()}&format=${format}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error exporting data:', error);
        throw error;
    }
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
    }).format(value);
}

// Format percentage
function formatPercentage(value) {
    return `${value.toFixed(1)}%`;
}

// Get health score color
function getHealthScoreColor(score) {
    if (score >= 80) return 'text-secondary';
    if (score >= 60) return 'text-primary';
    if (score >= 40) return 'text-tertiary';
    return 'text-error';
}

// Get health score background
function getHealthScoreBg(score) {
    if (score >= 80) return 'bg-secondary/20';
    if (score >= 60) return 'bg-primary/20';
    if (score >= 40) return 'bg-tertiary/20';
    return 'bg-error/20';
}

// Chart color palette
const CHART_COLORS = [
    '#8B5CF6', '#10B981', '#3B82F6', '#F59E0B', 
    '#EF4444', '#EC4899', '#14B8A6', '#6366F1', 
    '#F97316', '#84CC16'
];

// Create doughnut chart
function createDoughnutChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: data.colors || CHART_COLORS,
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        padding: 20,
                        font: { size: 12 },
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                }
            },
            ...options,
        }
    });
}

// Create bar chart
function createBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, i) => ({
                ...ds,
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
                borderColor: CHART_COLORS[i % CHART_COLORS.length],
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(71, 85, 105, 0.1)' },
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { display: false },
                }
            },
            ...options,
        }
    });
}

// Create line chart
function createLineChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: data.datasets.map((ds, i) => ({
                ...ds,
                borderColor: CHART_COLORS[i % CHART_COLORS.length],
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4,
                fill: options.fill || false,
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(71, 85, 105, 0.1)' },
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { display: false },
                }
            },
            ...options,
        }
    });
}

// Create horizontal bar chart
function createHorizontalBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: CHART_COLORS,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                }
            },
            scales: {
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { display: false },
                },
                x: {
                    beginAtZero: true,
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(71, 85, 105, 0.1)' },
                }
            },
            ...options,
        }
    });
}

// Create area chart
function createAreaChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Savings',
                data: data.data,
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                }
            },
            scales: {
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(71, 85, 105, 0.1)' },
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { display: false },
                }
            },
            ...options,
        }
    });
}

// Export for use in other modules
window.analyticsService = {
    fetchDashboardData,
    fetchChartData,
    exportData,
    formatCurrency,
    formatPercentage,
    getHealthScoreColor,
    getHealthScoreBg,
    getDateRange,
    createDoughnutChart,
    createBarChart,
    createLineChart,
    createHorizontalBarChart,
    createAreaChart,
};