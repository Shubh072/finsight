"""Supabase REST API client for Flask backend.

This module provides a thin wrapper around the Supabase REST API (PostgREST)
using the requests library, since the supabase-py package is not available.
"""

import os
import json
import requests
from config import SUPABASE_URL, SUPABASE_ANON_KEY
from flask import current_app


def _get_config():
    """Get Supabase config from app context or config module."""
    try:
        url = current_app.config.get("SUPABASE_URL") or SUPABASE_URL
        key = current_app.config.get("SUPABASE_ANON_KEY") or SUPABASE_ANON_KEY
    except RuntimeError:
        url = SUPABASE_URL
        key = SUPABASE_ANON_KEY
    return url, key


def _headers():
    _, key = _get_config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _table_url(table: str):
    url, _ = _get_config()
    return f"{url}/rest/v1/{table}"


def select(table: str, columns: str = "*", filters: dict = None, order: str = None,
           limit: int = None, single: bool = False):
    """Select rows from a table."""
    url = _table_url(table)
    params = {}
    headers = _headers()

    params["select"] = columns

    if filters:
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, dict):
                    # Handle operators like {"gte": 10}
                    for op, val in value.items():
                        params[key] = f"{op}.{val}"
                else:
                    params[key] = f"eq.{value}"

    if order:
        params["order"] = order

    if limit:
        params["limit"] = limit

    if single:
        headers["Accept"] = "application/vnd.pgrst.object+json"

    response = requests.get(url, params=params, headers=headers, timeout=30)

    if response.status_code == 200:
        return response.json() if not single else response.json()
    elif response.status_code == 406:
        # No rows found for single
        return None
    else:
        raise Exception(f"Supabase select error: {response.status_code} - {response.text}")


def insert(table: str, data: dict):
    """Insert a row into a table and return the created row."""
    url = _table_url(table)
    headers = _headers()

    response = requests.post(url, json=data, headers=headers, timeout=30)

    if response.status_code in (200, 201):
        result = response.json()
        return result[0] if isinstance(result, list) else result
    else:
        raise Exception(f"Supabase insert error: {response.status_code} - {response.text}")


def update(table: str, filters: dict, data: dict):
    """Update rows in a table."""
    url = _table_url(table)
    headers = _headers()
    params = {}

    if filters:
        for key, value in filters.items():
            if value is not None:
                params[key] = f"eq.{value}"

    response = requests.patch(url, params=params, json=data, headers=headers, timeout=30)

    if response.status_code in (200, 204):
        if response.status_code == 200:
            result = response.json()
            return result[0] if isinstance(result, list) and result else None
        return None
    else:
        raise Exception(f"Supabase update error: {response.status_code} - {response.text}")


def delete(table: str, filters: dict):
    """Delete rows from a table."""
    url = _table_url(table)
    headers = _headers()
    params = {}

    if filters:
        for key, value in filters.items():
            if value is not None:
                params[key] = f"eq.{value}"

    response = requests.delete(url, params=params, headers=headers, timeout=30)

    if response.status_code in (200, 204):
        return True
    else:
        raise Exception(f"Supabase delete error: {response.status_code} - {response.text}")


def rpc(function_name: str, params: dict = None):
    """Call a Postgres function via RPC."""
    url, _ = _get_config()
    rpc_url = f"{url}/rest/v1/rpc/{function_name}"
    headers = _headers()

    response = requests.post(rpc_url, json=params or {}, headers=headers, timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Supabase RPC error: {response.status_code} - {response.text}")
