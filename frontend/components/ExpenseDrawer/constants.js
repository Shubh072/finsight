export const CATEGORIES = [
  { id: 'Food', icon: 'restaurant', color: '#f97316' },
  { id: 'Travel', icon: 'flight', color: '#3b82f6' },
  { id: 'Shopping', icon: 'shopping_bag', color: '#ec4899' },
  { id: 'Entertainment', icon: 'movie', color: '#a855f7' },
  { id: 'Healthcare', icon: 'medical_services', color: '#14b8a6' },
  { id: 'Bills', icon: 'receipt_long', color: '#ef4444' },
  { id: 'Fuel', icon: 'local_gas_station', color: '#eab308' },
  { id: 'Education', icon: 'school', color: '#6366f1' },
  { id: 'Investment', icon: 'trending_up', color: '#10b981' },
  { id: 'Salary', icon: 'payments', color: '#22c55e' },
  { id: 'Gift', icon: 'redeem', color: '#f472b6' },
  { id: 'Insurance', icon: 'shield', color: '#64748b' },
  { id: 'EMI', icon: 'account_balance', color: '#0ea5e9' },
  { id: 'Rent', icon: 'home', color: '#8b5cf6' },
  { id: 'Utilities', icon: 'bolt', color: '#fbbf24' },
  { id: 'Subscription', icon: 'subscriptions', color: '#8B5CF6' },
  { id: 'Others', icon: 'category', color: '#94a3b8' },
];

export const PAYMENT_METHODS = [
  'Cash', 'UPI', 'Debit Card', 'Credit Card', 'Wallet',
  'Bank Transfer', 'Net Banking', 'Cheque', 'Crypto',
];

export const ACCOUNTS = [
  'Cash Wallet', 'Savings', 'Current', 'Credit Card', 'Business Account', 'Custom Account',
];

export const QUICK_AMOUNTS = [100, 200, 500, 1000];

export const MOODS = ['Happy', 'Neutral', 'Stressed', 'Regretful', 'Excited'];

export const RECURRING_FREQUENCIES = [
  'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly', 'Custom',
];

export const MERCHANT_CATEGORY_MAP = {
  uber: 'Travel', ola: 'Travel', lyft: 'Travel',
  swiggy: 'Food', zomato: 'Food', 'pizza hut': 'Food', dominos: 'Food',
  amazon: 'Shopping', flipkart: 'Shopping',
  netflix: 'Subscription', spotify: 'Subscription',
  apollo: 'Healthcare', medplus: 'Healthcare',
  electricity: 'Bills', bescom: 'Bills',
  'fuel station': 'Fuel', iocl: 'Fuel', hp: 'Fuel',
};

export const CATEGORY_SUBCATEGORIES = {
  Food: ['Dining Out', 'Groceries', 'Delivery', 'Snacks'],
  Travel: ['Cab', 'Flight', 'Hotel', 'Train'],
  Shopping: ['Clothing', 'Electronics', 'Online', 'Retail'],
  Bills: ['Electricity', 'Water', 'Internet', 'Phone'],
};

export const DRAFT_KEY = 'finsight_add_expense_draft_v2';

export function suggestCategoryFromMerchant(merchant) {
  const m = (merchant || '').toLowerCase();
  for (const [key, cat] of Object.entries(MERCHANT_CATEGORY_MAP)) {
    if (m.includes(key)) return cat;
  }
  return null;
}

export function formatCurrency(amount, currency = 'INR') {
  const sym = currency === 'INR' ? '₹' : currency === 'USD' ? '$' : currency + ' ';
  const n = parseFloat(amount) || 0;
  return sym + n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
