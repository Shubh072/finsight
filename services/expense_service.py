# This file is intentionally kept as a layer for future expansion.
# For milestone 1 (Add Expense), route handlers may call directly into service methods.

from typing import Any, Dict, Optional


def create_expense_record(user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder for future service abstraction."""
    return {"expense_id": None}

