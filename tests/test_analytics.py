"""
Test analytics routes for FinSight.
"""
import pytest
from datetime import date, timedelta
from app import create_app
app = create_app()
from database.db import db
from models.user import User
from models.expense import Expense
from models.income import Income
from models.budget import Budget
from models.investment import Investment
from extensions import bcrypt, jwt


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


@pytest.fixture
def test_user():
    """Create a test user."""
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        if user:
            return user
        user = User(
            full_name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash=bcrypt.generate_password_hash("password123").decode('utf-8'),
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token for test user."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    return response.get_json().get('access_token') or response.get_json().get('data', {}).get('access_token')


class TestAnalyticsRoutes:
    """Test analytics API endpoints."""
    
    def test_dashboard_endpoint_exists(self, client):
        """Test that dashboard endpoint exists."""
        response = client.get('/api/analytics/dashboard')
        assert response.status_code in [200, 401]  # 401 if not authenticated
    
    def test_category_endpoint_exists(self, client):
        """Test that category endpoint exists."""
        response = client.get('/api/analytics/category')
        assert response.status_code in [200, 401]
    
    def test_monthly_endpoint_exists(self, client):
        """Test that monthly endpoint exists."""
        response = client.get('/api/analytics/monthly')
        assert response.status_code in [200, 401]
    
    def test_income_expense_endpoint_exists(self, client):
        """Test that income-expense endpoint exists."""
        response = client.get('/api/analytics/income-expense')
        assert response.status_code in [200, 401]
    
    def test_payment_method_endpoint_exists(self, client):
        """Test that payment-method endpoint exists."""
        response = client.get('/api/analytics/payment-method')
        assert response.status_code in [200, 401]
    
    def test_budget_endpoint_exists(self, client):
        """Test that budget endpoint exists."""
        response = client.get('/api/analytics/budget')
        assert response.status_code in [200, 401]
    
    def test_investments_endpoint_exists(self, client):
        """Test that investments endpoint exists."""
        response = client.get('/api/analytics/investments')
        assert response.status_code in [200, 401]
    
    def test_financial_health_endpoint_exists(self, client):
        """Test that financial-health endpoint exists."""
        response = client.get('/api/analytics/financial-health')
        assert response.status_code in [200, 401]
    
    def test_export_endpoint_exists(self, client):
        """Test that export endpoint exists."""
        response = client.get('/api/analytics/export?format=csv')
        assert response.status_code in [200, 401]


class TestAnalyticsWithAuth:
    """Test analytics with authentication."""
    
    def test_dashboard_with_auth(self, client, test_user, auth_token):
        """Test dashboard endpoint with authentication."""
        response = client.get('/api/analytics/dashboard', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'data' in data
        assert 'cards' in data['data']
        assert 'charts' in data['data']
        assert 'insights' in data['data']
    
    def test_dashboard_cards_structure(self, client, test_user, auth_token):
        """Test dashboard cards structure."""
        response = client.get('/api/analytics/dashboard', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        data = response.get_json()['data']['cards']
        
        assert 'total_income' in data
        assert 'total_expense' in data
        assert 'current_balance' in data
        assert 'monthly_savings' in data
        assert 'budget_utilization' in data
        assert 'total_investments' in data
        assert 'total_budgets' in data
        assert 'total_transactions' in data
        assert 'financial_health_score' in data
    
    def test_dashboard_charts_structure(self, client, test_user, auth_token):
        """Test dashboard charts structure."""
        response = client.get('/api/analytics/dashboard', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        data = response.get_json()['data']['charts']
        
        assert 'expense_by_category' in data
        assert 'income_vs_expense' in data
        assert 'monthly_expense_trend' in data
        assert 'monthly_income_trend' in data
        assert 'budget_vs_expense' in data
        assert 'payment_method_distribution' in data
        assert 'top_spending_categories' in data
        assert 'monthly_savings_trend' in data
        assert 'investment_allocation' in data
        assert 'daily_expense_trend' in data
    
    def test_export_csv(self, client, test_user, auth_token):
        """Test CSV export."""
        response = client.get('/api/analytics/export?format=csv', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
    
    def test_filter_parameter(self, client, test_user, auth_token):
        """Test filter parameter."""
        response = client.get('/api/analytics/dashboard?filter=today', headers={
            'Authorization': f'Bearer {auth_token}'
        })
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])