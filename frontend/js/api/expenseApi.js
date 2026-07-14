const api = axios.create({ baseURL: '/api/expenses', timeout: 60000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.message || err.message || 'Request failed';
    const errors = err.response?.data?.errors;
    const e = new Error(msg);
    e.errors = errors;
    e.status = err.response?.status;
    throw e;
  }
);

export async function createExpense(formData) {
  const { data } = await api.post('/', formData);
  return data;
}

export async function scanReceipt(file) {
  const fd = new FormData();
  fd.append('receipt', file);
  const { data } = await api.post('/scan-receipt', fd);
  return data;
}

export async function checkDuplicate(payload) {
  const { data } = await api.post('/duplicate-check', payload);
  return data;
}

export async function listExpenses(params = {}) {
  const { data } = await api.get('/', { params });
  return data;
}

export async function getExpenseSummary() {
  const { data } = await api.get('/summary');
  return data;
}

export async function getBudget(category, amount = 0) {
  const { data } = await api.get('/budget', { params: { category, amount } });
  return data;
}

export async function getSuggestions(merchant, category, amount) {
  const { data } = await api.get('/suggestions', {
    params: { merchant, category, amount },
  });
  return data;
}

export async function undoLastExpense() {
  const { data } = await api.delete('/last');
  return data;
}
