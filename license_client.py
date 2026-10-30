import requests
import sqlite3
import os
import socket
from urllib.parse import urlparse
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendance.db')

DEFAULT_PROVIDER_URL = "http://127.0.0.1:5001/api/v1/license/verify"

_in_memory_cache = {
    'last_check_ts': 0,
    'data': None
}

def is_provider_reachable(url, timeout=0.06):
    try:
        parsed = urlparse(url)
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_cached_license():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM license_config LIMIT 1")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_license_config(license_key, provider_url=DEFAULT_PROVIDER_URL, company_name="", expiry_date="", status="active", days_remaining=0):
    global _in_memory_cache
    _in_memory_cache['last_check_ts'] = 0
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM license_config")
    c.execute("""
        INSERT INTO license_config (license_key, provider_url, company_name, expiry_date, status, days_remaining, last_verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (license_key.strip(), provider_url.strip(), company_name, expiry_date, status, days_remaining, now_str))
    conn.commit()
    conn.close()

def update_cached_status(status, days_remaining, expiry_date=None, company_name=None):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    c = conn.cursor()
    if expiry_date and company_name:
        c.execute("""
            UPDATE license_config 
            SET status = ?, days_remaining = ?, expiry_date = ?, company_name = ?, last_verified_at = ?
        """, (status, days_remaining, expiry_date, company_name, now_str))
    else:
        c.execute("""
            UPDATE license_config 
            SET status = ?, days_remaining = ?, last_verified_at = ?
        """, (status, days_remaining, now_str))
    conn.commit()
    conn.close()

def check_license(force_online=False):
    """
    Validates license.
    1. Checks fast in-memory cache (300 seconds).
    2. Reads stored license config.
    3. Queries Provider Licensing Portal via REST API.
    4. Handles 3-day offline grace fallback if provider is temporarily unreachable.
    Returns: (is_valid: bool, status: str, info: dict)
    """
    global _in_memory_cache
    import time
    now_ts = time.time()

    if not force_online and _in_memory_cache['data'] and (now_ts - _in_memory_cache['last_check_ts'] < 300):
        c_val, c_stat, c_info = _in_memory_cache['data']
        return c_val, c_stat, c_info

    config = get_cached_license()
    if not config or not config.get('license_key'):
        return False, 'unlicensed', {
            'message': 'No license key configured. Please enter your provider license key to activate the application.',
            'company_name': 'Unregistered System'
        }

    # Fast local cache check: if verified within last 15 minutes and active, avoid blocking network calls
    if not force_online and config.get('status') == 'active' and config.get('last_verified_at'):
        try:
            last_dt = datetime.strptime(config['last_verified_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
            # Check within 15 minutes of local time
            if abs((datetime.now() - last_dt).total_seconds()) < 900:
                res = (True, 'active', {
                    'valid': True,
                    'status': 'active',
                    'company_name': config.get('company_name', 'Client'),
                    'expiry_date': config.get('expiry_date'),
                    'days_remaining': config.get('days_remaining', 0),
                    'message': 'License active'
                })
                _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                return res
        except Exception:
            pass

    license_key = config['license_key']
    provider_url = config.get('provider_url') or DEFAULT_PROVIDER_URL
    if 'localhost' in provider_url:
        provider_url = provider_url.replace('localhost', '127.0.0.1')

    # Try reaching provider if reachable
    if is_provider_reachable(provider_url):
        try:
            resp = requests.post(
                provider_url,
                json={'license_key': license_key},
                timeout=(0.5, 2.0)
            )
            data = resp.json()

            if resp.status_code == 200 and data.get('valid'):
                # Update cache
                update_cached_status(
                    status='active',
                    days_remaining=data.get('days_remaining', 0),
                    expiry_date=data.get('expiry_date'),
                    company_name=data.get('company_name')
                )
                res = (True, 'active', data)
                _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                return res
            else:
                # Explicitly rejected by provider (e.g. suspended, expired, invalid)
                status = data.get('status', 'suspended')
                update_cached_status(
                    status=status,
                    days_remaining=data.get('days_remaining', 0),
                    expiry_date=data.get('expiry_date'),
                    company_name=data.get('company_name')
                )
                res = (False, status, data)
                _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                return res
        except Exception:
            pass

    # Provider server is offline or unreachable: silently evaluate local DB or cached lease
    licensing_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'licensing_app', 'licensing.db')
    if os.path.exists(licensing_db_path):
        try:
            l_conn = sqlite3.connect(licensing_db_path)
            l_conn.row_factory = sqlite3.Row
            l_c = l_conn.cursor()
            l_c.execute("""
                SELECT l.*, c.company_name, c.client_code, c.status as client_status
                FROM licenses l
                JOIN clients c ON l.client_id = c.id
                WHERE l.license_key = ?
            """, (license_key.strip(),))
            l_row = l_c.fetchone()
            l_conn.close()

            if l_row:
                l_item = dict(l_row)
                today = date.today()
                try:
                    end_dt = datetime.strptime(l_item['end_date'], '%Y-%m-%d').date()
                    days_left = (end_dt - today).days
                except Exception:
                    days_left = 0

                if l_item['status'] == 'active' and l_item['client_status'] == 'active' and days_left >= 0:
                    update_cached_status('active', days_left, l_item['end_date'], l_item['company_name'])
                    res = (True, 'active', {
                        'valid': True,
                        'status': 'active',
                        'company_name': l_item['company_name'],
                        'expiry_date': l_item['end_date'],
                        'days_remaining': days_left,
                        'message': f"License active for '{l_item['company_name']}' ({days_left} days remaining)."
                    })
                    _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                    return res
        except Exception:
            pass

    # OFFLINE GRACE BUFFER (3 days)
    last_verified_str = config.get('last_verified_at')
    expiry_date_str = config.get('expiry_date')
    cached_status = config.get('status', 'active')

    # If already known to be suspended or expired, block immediately
    if cached_status in ('suspended', 'expired'):
        res = (False, cached_status, {
            'message': f"Application subscription is {cached_status}. Please contact software provider.",
            'company_name': config.get('company_name', 'Client')
        })
        _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
        return res

    # Check calendar expiry date
    if expiry_date_str:
        try:
            end_dt = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            if date.today() > end_dt:
                update_cached_status('expired', 0)
                res = (False, 'expired', {
                    'message': f"Your subscription expired on {expiry_date_str}. Please contact your provider to renew.",
                    'company_name': config.get('company_name')
                })
                _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                return res
        except Exception:
            pass

    # Check offline grace duration
    if last_verified_str:
        try:
            last_dt = datetime.strptime(last_verified_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last_dt > timedelta(days=3):
                res = (False, 'offline_timeout', {
                    'message': 'Unable to connect to license verification server for over 3 days. Please restore internet connectivity.',
                    'company_name': config.get('company_name')
                })
                _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
                return res
        except Exception:
            pass

    # Allow grace access
    res = (True, 'active_grace', {
        'valid': True,
        'status': 'active',
        'company_name': config.get('company_name', 'Registered Client'),
        'expiry_date': config.get('expiry_date'),
        'days_remaining': config.get('days_remaining', 30),
        'offline_mode': True,
        'message': 'Running in offline grace mode.'
    })
    _in_memory_cache = {'last_check_ts': now_ts, 'data': res}
    return res

def authenticate_with_provider(username, password, license_key=None, provider_url=None):
    """
    Validates Super Admin credentials against the Provider server.
    First tries REST HTTP (port 5001). If port 5001 is offline, falls back to local licensing.db.
    """
    if not provider_url:
        config = get_cached_license()
        base_url = (config.get('provider_url') if config else None) or DEFAULT_PROVIDER_URL
        if '/api/v1/license/verify' in base_url:
            provider_url = base_url.replace('/api/v1/license/verify', '/api/v1/provider/authenticate-super-admin')
        else:
            provider_url = 'http://127.0.0.1:5001/api/v1/provider/authenticate-super-admin'

    if 'localhost' in provider_url:
        provider_url = provider_url.replace('localhost', '127.0.0.1')

    # 1. Try REST HTTP if provider is online
    if is_provider_reachable(provider_url):
        try:
            resp = requests.post(
                provider_url,
                json={'username': username, 'password': password, 'license_key': license_key},
                timeout=(0.5, 2.0)
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (401, 403):
                return resp.json()
        except Exception:
            pass

    # 2. Local development fallback: Query licensing.db directly if on same machine!
    licensing_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'licensing_app', 'licensing.db')
    if os.path.exists(licensing_db_path):
        try:
            l_conn = sqlite3.connect(licensing_db_path)
            l_conn.row_factory = sqlite3.Row
            l_c = l_conn.cursor()
            if license_key:
                l_c.execute("""
                    SELECT sa.*, c.id as client_id, c.company_name, c.client_code, c.owner_name, c.status as client_status,
                           l.license_key, l.start_date, l.end_date, l.status as license_status
                    FROM client_super_admins sa
                    JOIN clients c ON sa.client_id = c.id
                    JOIN licenses l ON c.id = l.client_id
                    WHERE sa.username = ? AND l.license_key = ?
                """, (username.strip(), license_key.strip()))
            else:
                l_c.execute("""
                    SELECT sa.*, c.id as client_id, c.company_name, c.client_code, c.owner_name, c.status as client_status,
                           l.license_key, l.start_date, l.end_date, l.status as license_status
                    FROM client_super_admins sa
                    JOIN clients c ON sa.client_id = c.id
                    JOIN licenses l ON c.id = l.client_id
                    WHERE sa.username = ?
                """, (username.strip(),))

            rows = l_c.fetchall()
            l_conn.close()

            for r in rows:
                item = dict(r)
                if item['initial_password'] == password:
                    if item['license_status'] == 'suspended' or item['client_status'] == 'suspended':
                        return {
                            'authenticated': False,
                            'status': 'suspended',
                            'message': f"The subscription for '{item['company_name']}' has been suspended by the provider."
                        }

                    today = date.today()
                    try:
                        end_dt = datetime.strptime(item['end_date'], '%Y-%m-%d').date()
                        days_left = (end_dt - today).days
                    except Exception:
                        days_left = 0

                    if days_left < 0 or item['license_status'] == 'expired':
                        return {
                            'authenticated': False,
                            'status': 'expired',
                            'message': f"The subscription for '{item['company_name']}' expired on {item['end_date']}."
                        }

                    print(f"[LicenseManager] Authenticated '{username}' via local provider database fallback!")
                    return {
                        'authenticated': True,
                        'status': 'active',
                        'client_id': item['client_id'],
                        'client_code': item['client_code'],
                        'company_name': item['company_name'],
                        'owner_name': item['owner_name'],
                        'license_key': item['license_key'],
                        'start_date': item['start_date'],
                        'expiry_date': item['end_date'],
                        'days_remaining': days_left,
                        'super_admin': {
                            'username': item['username'],
                            'full_name': f"{item['owner_name']} (Owner)"
                        }
                    }
        except Exception as dbe:
            print(f"[LicenseManager] Local database fallback exception: {dbe}")

    return {
        'authenticated': False,
        'message': 'Cannot connect to Provider licensing server. Please ensure the provider portal is running on port 5001.'
    }

