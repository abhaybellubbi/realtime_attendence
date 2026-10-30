import sqlite3
import os
import calendar
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendance.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # License configuration cached from Provider
    c.execute('''
        CREATE TABLE IF NOT EXISTS license_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT NOT NULL,
            provider_url TEXT DEFAULT 'http://localhost:5001/api/v1/license/verify',
            company_name TEXT,
            status TEXT DEFAULT 'active',
            expiry_date TEXT,
            days_remaining INTEGER DEFAULT 0,
            last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Users (Super Admin & Admin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Granular Permissions for Admin users (Configured dynamically by Super Admin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_permissions (
            user_id INTEGER PRIMARY KEY,
            can_view_dashboard INTEGER DEFAULT 1,
            can_view_attendance INTEGER DEFAULT 1,
            can_export_excel INTEGER DEFAULT 1,
            can_manage_workers INTEGER DEFAULT 0,
            can_manage_shifts INTEGER DEFAULT 0,
            can_trigger_sync INTEGER DEFAULT 0,
            can_edit_attendance INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Shifts
    c.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            grace_period_mins INTEGER DEFAULT 15,
            half_day_threshold_mins INTEGER DEFAULT 120,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Departments (Master Registry)
    c.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT DEFAULT '',
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Workers (Biometric users)
    c.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enroll_number INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT DEFAULT 'General',
            shift_id INTEGER,
            joining_date TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shift_id) REFERENCES shifts (id) ON DELETE SET NULL
        )
    ''')

    # Attendance logs from biometric machine
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER DEFAULT 1,
            enroll_number INTEGER NOT NULL,
            event_timestamp TEXT NOT NULL,
            punch_type INTEGER DEFAULT 0,
            verify_mode INTEGER DEFAULT 1,
            work_code INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_id, enroll_number, event_timestamp)
        )
    ''')

    # Biometric Devices
    c.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT,
            device_name TEXT NOT NULL,
            ip_address TEXT DEFAULT '192.168.1.224',
            port INTEGER DEFAULT 5005,
            machine_id INTEGER DEFAULT 1,
            sync_interval_mins INTEGER DEFAULT 15,
            last_sync_time TIMESTAMP,
            last_status TEXT DEFAULT 'OFFLINE',
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Sync History
    c.execute('''
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            records_fetched INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            message TEXT
        )
    ''')

    # Leave Types
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_types (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            default_days REAL DEFAULT 12,
            color TEXT DEFAULT '#3b82f6'
        )
    ''')

    # Worker Leave Balances
    c.execute('''
        CREATE TABLE IF NOT EXISTS worker_leave_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            leave_type_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            allocated_days REAL NOT NULL DEFAULT 12,
            used_days REAL NOT NULL DEFAULT 0,
            UNIQUE(worker_id, leave_type_code, year),
            FOREIGN KEY (worker_id) REFERENCES workers (id) ON DELETE CASCADE
        )
    ''')

    # Leave Applications
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            leave_type_code TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days_count REAL NOT NULL DEFAULT 1.0,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            applied_by TEXT NOT NULL DEFAULT 'worker',
            applied_by_user_id INTEGER,
            document_ref TEXT,
            admin_notes TEXT,
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers (id) ON DELETE CASCADE
        )
    ''')

    # Flexible Shift Policy (Single Global Policy)
    c.execute('''
        CREATE TABLE IF NOT EXISTS flexible_shift_policy (
            id INTEGER PRIMARY KEY,
            full_day_hours REAL DEFAULT 8.0,
            half_day_hours REAL DEFAULT 4.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Official Holidays Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS official_holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT NOT NULL UNIQUE,
            holiday_name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Migrations for existing tables
    c.execute("PRAGMA table_info(workers)")
    worker_cols = [col[1] for col in c.fetchall()]
    if 'password_hash' not in worker_cols:
        c.execute("ALTER TABLE workers ADD COLUMN password_hash TEXT DEFAULT NULL")
    if 'email' not in worker_cols:
        c.execute("ALTER TABLE workers ADD COLUMN email TEXT DEFAULT NULL")
    if 'phone' not in worker_cols:
        c.execute("ALTER TABLE workers ADD COLUMN phone TEXT DEFAULT NULL")
    if 'is_flexible' not in worker_cols:
        c.execute("ALTER TABLE workers ADD COLUMN is_flexible INTEGER DEFAULT 0")
    if 'photo' not in worker_cols:
        c.execute("ALTER TABLE workers ADD COLUMN photo TEXT DEFAULT ''")

    c.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in c.fetchall()]
    if 'phone' not in user_cols:
        c.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT NULL")

    c.execute("PRAGMA table_info(admin_permissions)")
    admin_cols = [col[1] for col in c.fetchall()]
    if 'can_manage_leaves' not in admin_cols:
        c.execute("ALTER TABLE admin_permissions ADD COLUMN can_manage_leaves INTEGER DEFAULT 1")
    if 'can_manual_punch' not in admin_cols:
        c.execute("ALTER TABLE admin_permissions ADD COLUMN can_manual_punch INTEGER DEFAULT 1")
    if 'can_manage_holidays' not in admin_cols:
        c.execute("ALTER TABLE admin_permissions ADD COLUMN can_manage_holidays INTEGER DEFAULT 1")
    if 'can_view_reports' not in admin_cols:
        c.execute("ALTER TABLE admin_permissions ADD COLUMN can_view_reports INTEGER DEFAULT 1")
    if 'department_access' not in admin_cols:
        c.execute("ALTER TABLE admin_permissions ADD COLUMN department_access TEXT DEFAULT 'ALL'")

    # Migrations for attendance_logs (Manual Check-In / Check-Out)
    c.execute("PRAGMA table_info(attendance_logs)")
    log_cols = [col[1] for col in c.fetchall()]
    if 'is_manual' not in log_cols:
        c.execute("ALTER TABLE attendance_logs ADD COLUMN is_manual INTEGER DEFAULT 0")
    if 'recorded_by_user_id' not in log_cols:
        c.execute("ALTER TABLE attendance_logs ADD COLUMN recorded_by_user_id INTEGER DEFAULT NULL")
    if 'manual_reason' not in log_cols:
        c.execute("ALTER TABLE attendance_logs ADD COLUMN manual_reason TEXT DEFAULT NULL")

    # Migrations for leave_types (Custom Categories & Policy Config)
    c.execute("PRAGMA table_info(leave_types)")
    lt_cols = [col[1] for col in c.fetchall()]
    if 'is_paid' not in lt_cols:
        c.execute("ALTER TABLE leave_types ADD COLUMN is_paid INTEGER DEFAULT 1")
    if 'description' not in lt_cols:
        c.execute("ALTER TABLE leave_types ADD COLUMN description TEXT DEFAULT ''")
    if 'is_active' not in lt_cols:
        c.execute("ALTER TABLE leave_types ADD COLUMN is_active INTEGER DEFAULT 1")

    conn.commit()
    conn.close()

def seed_default_data():
    conn = get_connection()
    c = conn.cursor()

    # Initial License Config
    c.execute("SELECT id FROM license_config LIMIT 1")
    if not c.fetchone():
        c.execute("""
            INSERT INTO license_config (license_key, provider_url, company_name, status, expiry_date, days_remaining, last_verified_at)
            VALUES (?, ?, ?, 'active', ?, 365, CURRENT_TIMESTAMP)
        """, ('LIC-SAI-KRISHNA-2026', 'http://localhost:5001/api/v1/license/verify', 'Sai Krishna Enterprises', (date.today() + timedelta(days=365)).strftime('%Y-%m-%d')))

    # Master Super Admin
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (?, ?, ?, ?, 'super_admin', 1)
        """, ('admin', generate_password_hash('admin123'), 'Administrator (Sai Krishna Enterprises)', 'admin@saikrishna.local'))

    # Biometric Terminal Device Config
    c.execute("SELECT id FROM devices WHERE id = 1")
    if not c.fetchone():
        c.execute("""
            INSERT INTO devices (id, serial_number, device_name, ip_address, port, machine_id, sync_interval_mins, last_status)
            VALUES (1, 'SBXPC-DEV-001', 'Front Counter Biometric Terminal', '192.168.1.224', 5005, 1, 2, 'READY')
        """)

    # Standard Shifts
    c.execute("SELECT COUNT(*) FROM shifts")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO shifts (name, start_time, end_time, grace_period_mins, half_day_threshold_mins)
            VALUES 
            ('General Shift', '09:00', '18:00', 15, 120),
            ('Morning Shift', '08:00', '16:30', 15, 120),
            ('Evening Shift', '13:30', '22:00', 15, 120)
        """)

    # Standard Initial Departments
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        default_depts = [
            ('Production & CNC Machining', 'CNC', 'Precision Turning, Milling & 4-Axis VMC Operations'),
            ('Production & Fabrication', 'FAB', 'Laser Cutting, Press Brake Bending & Heavy Robotic Welding'),
            ('Quality Assurance & QC', 'QC', '3D CMM Metrology, Optical Profile & Batch Audit'),
            ('Packaging & Logistics', 'LOG', 'Finished Goods Dispatch, Palletizing & Material Handling'),
            ('Accounts & Finance', 'ACC', 'Corporate Accounting, Invoicing & Payroll Processing'),
            ('Sales & Procurement', 'SALES', 'Client Relationships, Vendor Management & Raw Material Procurement'),
            ('General', 'GEN', 'General Operations & Administration Support')
        ]
        for name, code, desc in default_depts:
            c.execute("""
                INSERT OR IGNORE INTO departments (name, code, description, is_active)
                VALUES (?, ?, ?, 1)
            """, (name, code, desc))

    # Also import any distinct departments from existing workers
    try:
        c.execute("SELECT DISTINCT department FROM workers WHERE department IS NOT NULL AND TRIM(department) != ''")
        for row in c.fetchall():
            d_name = row[0].strip()
            if d_name:
                c.execute("""
                    INSERT OR IGNORE INTO departments (name, code, description, is_active)
                    VALUES (?, ?, ?, 1)
                """, (d_name, d_name[:4].upper(), f'{d_name} Operations'))
    except Exception:
        pass

    # Standard Leave Types
    c.execute("SELECT COUNT(*) FROM leave_types")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO leave_types (code, name, default_days, color, is_paid, description, is_active) VALUES
            ('CL', 'Casual Leave', 12, '#3b82f6', 1, 'Standard annual casual leave quota', 1),
            ('SL', 'Sick Leave', 6, '#10b981', 1, 'Medical recovery and health leave', 1),
            ('PL', 'Paid Leave', 6, '#8b5cf6', 1, 'Earned annual paid time off', 1)
        """)

    # Default Flexible Shift Policy
    c.execute("SELECT id FROM flexible_shift_policy WHERE id = 1")
    if not c.fetchone():
        c.execute("""
            INSERT INTO flexible_shift_policy (id, full_day_hours, half_day_hours)
            VALUES (1, 8.0, 4.0)
        """)

    # Seed Default 2026 National & Official Holidays if empty
    c.execute("SELECT COUNT(*) FROM official_holidays")
    if c.fetchone()[0] == 0:
        default_holidays = [
            ('2026-01-26', 'Republic Day', 'National Holiday - Constitution of India'),
            ('2026-05-01', 'May Day / Labor Day', 'International Workers Day'),
            ('2026-08-15', 'Independence Day', 'National Holiday - Independence Celebrations'),
            ('2026-10-02', 'Mahatma Gandhi Jayanti', 'National Holiday - Father of the Nation Birthday'),
            ('2026-11-08', 'Diwali / Deepavali', 'Festival of Lights - Official Government Holiday'),
            ('2026-12-25', 'Christmas Day', 'Public Holiday - Christmas Celebrations')
        ]
        for h_date, h_name, h_notes in default_holidays:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO official_holidays (holiday_date, holiday_name, notes, created_by)
                    VALUES (?, ?, ?, 1)
                """, (h_date, h_name, h_notes))
            except Exception:
                pass

    conn.commit()
    conn.close()


# ----------------- Verification Method Intelligence -----------------

def get_verify_method_info(verify_mode, is_manual=0):
    """
    Maps hardware biometric verify_mode code or manual flag into human-readable details.
    Modes:
      - 15, 20-22: Face Recognition
      - 1: Fingerprint Scan
      - 2: RFID / Proximity Card
      - 0: PIN / Password
      - is_manual=1: Manual Admin Punch
    """
    if is_manual:
        return {
            'code': 'manual',
            'label': 'Manual Punch',
            'short': 'Manual',
            'icon': 'bi-pencil-square',
            'badge_class': 'bg-warning text-dark'
        }
    try:
        vm = int(verify_mode) if verify_mode is not None else 1
    except (ValueError, TypeError):
        vm = 1

    if vm in [15, 20, 21, 22]:
        return {
            'code': 'face',
            'label': 'Face Recognition',
            'short': 'Face',
            'icon': 'bi-person-bounding-box',
            'badge_class': 'bg-info text-dark'
        }
    elif vm == 1:
        return {
            'code': 'finger',
            'label': 'Fingerprint Scan',
            'short': 'Finger',
            'icon': 'bi-fingerprint',
            'badge_class': 'bg-primary'
        }
    elif vm == 2:
        return {
            'code': 'card',
            'label': 'RFID / Card Badge',
            'short': 'Card',
            'icon': 'bi-credit-card-2-front',
            'badge_class': 'bg-success'
        }
    elif vm == 0:
        return {
            'code': 'password',
            'label': 'PIN / Password',
            'short': 'PIN',
            'icon': 'bi-key',
            'badge_class': 'bg-secondary'
        }
    else:
        return {
            'code': 'biometric',
            'label': f'Biometric Device ({vm})',
            'short': f'Mode {vm}',
            'icon': 'bi-cpu',
            'badge_class': 'bg-secondary'
        }

# ----------------- Official Holidays Management -----------------

def get_holidays(year=None):
    """
    Fetches official government/company holidays, optionally filtered by year.
    Ordered chronologically by date.
    """
    conn = get_connection()
    c = conn.cursor()
    if year:
        c.execute("""
            SELECT h.*, u.full_name as created_by_name
            FROM official_holidays h
            LEFT JOIN users u ON h.created_by = u.id
            WHERE h.holiday_date LIKE ?
            ORDER BY h.holiday_date ASC
        """, (f"{year}-%",))
    else:
        c.execute("""
            SELECT h.*, u.full_name as created_by_name
            FROM official_holidays h
            LEFT JOIN users u ON h.created_by = u.id
            ORDER BY h.holiday_date ASC
        """)
    rows = c.fetchall()
    conn.close()

    results = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    today_dt = date.today()

    for r in rows:
        d = dict(r)
        try:
            dt = datetime.strptime(d['holiday_date'], '%Y-%m-%d').date()
            d['day_of_week'] = day_names[dt.weekday()]
            d['is_past'] = dt < today_dt
            d['is_today'] = dt == today_dt
            d['is_upcoming'] = dt > today_dt
        except Exception:
            d['day_of_week'] = ''
            d['is_past'] = False
            d['is_today'] = False
            d['is_upcoming'] = False
        results.append(d)
    return results

def get_holidays_map(start_date=None, end_date=None):
    """
    Returns a lookup dictionary mapping 'YYYY-MM-DD' -> {'id': ..., 'name': ..., 'notes': ...}.
    """
    conn = get_connection()
    c = conn.cursor()
    if start_date and end_date:
        c.execute("""
            SELECT id, holiday_date, holiday_name, notes
            FROM official_holidays
            WHERE holiday_date >= ? AND holiday_date <= ?
        """, (start_date, end_date))
    elif start_date:
        c.execute("""
            SELECT id, holiday_date, holiday_name, notes
            FROM official_holidays
            WHERE holiday_date = ?
        """, (start_date,))
    else:
        c.execute("""
            SELECT id, holiday_date, holiday_name, notes
            FROM official_holidays
        """)
    rows = c.fetchall()
    conn.close()

    h_map = {}
    for r in rows:
        h_map[r['holiday_date']] = {
            'id': r['id'],
            'name': r['holiday_name'],
            'notes': r['notes'] or ''
        }
    return h_map

def add_holiday(holiday_date, holiday_name, notes='', user_id=None):
    """
    Adds a new official government/company holiday. Super Admin only.
    """
    holiday_date = (holiday_date or '').strip()
    holiday_name = (holiday_name or '').strip()
    notes = (notes or '').strip()

    if not holiday_date or not holiday_name:
        return False, "Holiday date and name are required."

    try:
        datetime.strptime(holiday_date, '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD."

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO official_holidays (holiday_date, holiday_name, notes, created_by)
            VALUES (?, ?, ?, ?)
        """, (holiday_date, holiday_name, notes, user_id))
        h_id = c.lastrowid
        conn.commit()
        conn.close()
        return True, h_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"A holiday on {holiday_date} is already registered."
    except Exception as e:
        conn.close()
        return False, str(e)

def update_holiday(holiday_id, holiday_date, holiday_name, notes=''):
    """
    Updates an existing official holiday.
    """
    holiday_date = (holiday_date or '').strip()
    holiday_name = (holiday_name or '').strip()
    notes = (notes or '').strip()

    if not holiday_date or not holiday_name:
        return False, "Holiday date and name are required."

    try:
        datetime.strptime(holiday_date, '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD."

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE official_holidays
            SET holiday_date = ?, holiday_name = ?, notes = ?
            WHERE id = ?
        """, (holiday_date, holiday_name, notes, holiday_id))
        conn.commit()
        conn.close()
        return True, "Holiday updated successfully"
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Another holiday is already registered on {holiday_date}."
    except Exception as e:
        conn.close()
        return False, str(e)

def delete_holiday(holiday_id):
    """
    Deletes an official holiday by ID.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM official_holidays WHERE id = ?", (holiday_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def bulk_import_holidays(holidays_list, user_id=None):
    """
    Bulk inserts or updates official holidays from a list of dicts:
    [{'holiday_date': 'YYYY-MM-DD', 'holiday_name': '...', 'notes': '...'}]
    Returns (True, count_inserted, count_updated) or (False, error_message, 0).
    """
    if not holidays_list:
        return False, "No holiday records provided for import.", 0

    conn = get_connection()
    c = conn.cursor()
    inserted = 0
    updated = 0
    try:
        for item in holidays_list:
            h_date = str(item.get('holiday_date') or item.get('date') or '').strip()
            h_name = str(item.get('holiday_name') or item.get('name') or '').strip()
            notes = str(item.get('notes') or '').strip()
            if not h_date or not h_name:
                continue

            try:
                datetime.strptime(h_date, '%Y-%m-%d')
            except ValueError:
                continue

            c.execute("SELECT id FROM official_holidays WHERE holiday_date = ?", (h_date,))
            existing = c.fetchone()
            if existing:
                c.execute("""
                    UPDATE official_holidays
                    SET holiday_name = ?, notes = ?
                    WHERE id = ?
                """, (h_name, notes, existing['id']))
                updated += 1
            else:
                c.execute("""
                    INSERT INTO official_holidays (holiday_date, holiday_name, notes, created_by)
                    VALUES (?, ?, ?, ?)
                """, (h_date, h_name, notes, user_id))
                inserted += 1

        conn.commit()
        conn.close()
        return True, inserted, updated
    except Exception as e:
        conn.close()
        return False, str(e), 0

def seed_karnataka_national_holidays(user_id=None):
    """
    Seeds comprehensive Karnataka State & National Government Holidays for 2026.
    """
    karnataka_holidays = [
        ('2026-01-14', 'Makara Sankranti / Pongal (ಮಕರ ಸಂಕ್ರಾಂತಿ)', 'Harvest Festival - Karnataka State Holiday'),
        ('2026-01-26', 'Republic Day (ಗಣರಾಜ್ಯೋತ್ಸವ)', 'National Gazetted Holiday'),
        ('2026-02-15', 'Maha Shivaratri (ಮಹಾ ಶಿವರಾತ್ರಿ)', 'Religious Festival - Karnataka Public Holiday'),
        ('2026-03-20', 'Ugadi (ಯುಗಾದಿ ಹಬ್ಬ)', 'Karnataka New Year - State Gazetted Holiday'),
        ('2026-03-21', 'Eid-ul-Fitr / Ramzan (ರಂಜಾನ್)', 'Public Gazetted Holiday'),
        ('2026-04-03', 'Good Friday (ಗುಡ್ ಫ್ರೈಡೇ)', 'Public Holiday'),
        ('2026-04-14', 'Dr. B.R. Ambedkar Jayanti (ಡಾ. ಬಿ.ಆರ್. ಅಂಬೇಡ್ಕರ್ ಜಯಂತಿ)', 'National & State Observance'),
        ('2026-04-20', 'Basava Jayanti (ಬಸವ ಜಯಂತಿ)', 'Karnataka State Official Holiday'),
        ('2026-05-01', 'May Day / Labor Day (ಕಾರ್ಮಿಕರ ದಿನಾಚರಣೆ)', 'International Workers Day - Mandatory Paid Holiday'),
        ('2026-05-28', 'Bakrid / Eid-ul-Adha (ಬಕ್ರೀದ್)', 'Public Holiday'),
        ('2026-08-15', 'Independence Day (ಸ್ವಾತಂತ್ರ್ಯ ದಿನಾಚರಣೆ)', 'National Gazetted Holiday'),
        ('2026-09-04', 'Ganesh Chaturthi (ಗಣೇಶ ಚತುರ್ಥಿ)', 'State Festival Holiday'),
        ('2026-10-02', 'Mahatma Gandhi Jayanti (ಮಹಾತ್ಮ ಗಾಂಧಿ ಜಯಂತಿ)', 'National Gazetted Holiday'),
        ('2026-10-20', 'Mahanavami / Ayudha Pooja (ಆಯುಧ ಪೂಜೆ)', 'Karnataka State Festival'),
        ('2026-10-21', 'Vijayadashami / Dasara (ವಿಜಯದಶಮಿ)', 'Mysore Dasara Festival'),
        ('2026-11-01', 'Kannada Rajyotsava (ಕನ್ನಡ ರಾಜ್ಯೋತ್ಸವ)', 'Karnataka State Formation Day - Mandatory Paid Holiday'),
        ('2026-11-08', 'Deepavali / Naraka Chaturdashi (ನರಕ ಚತುರ್ದಶಿ)', 'Festival of Lights - State Holiday'),
        ('2026-11-10', 'Deepavali / Balipadyami (ಬಲಿಪಾಡ್ಯಮಿ)', 'Festival of Lights - State Holiday'),
        ('2026-11-26', 'Kanakadasa Jayanti (ಕನಕದಾಸ ಜಯಂತಿ)', 'Karnataka State Official Holiday'),
        ('2026-12-25', 'Christmas Day (ಕ್ರಿಸ್‌ಮಸ್)', 'Public Gazetted Holiday')
    ]
    h_list = [{'holiday_date': d, 'holiday_name': n, 'notes': note} for d, n, note in karnataka_holidays]
    return bulk_import_holidays(h_list, user_id=user_id)

def get_weekoff_workers_summary(year=None):
    """
    Returns summary of workers who clocked in on Sundays (weekoffs),
    the dates they worked, and their current COMP leave balance.
    """
    if not year:
        year = date.today().year
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT enroll_number, substr(event_timestamp, 1, 10) as punch_date
        FROM attendance_logs
        WHERE substr(event_timestamp, 1, 4) = ?
        ORDER BY punch_date ASC
    """, (str(year),))
    rows = c.fetchall()

    sunday_punches = {}
    for r in rows:
        dt_str = r['punch_date']
        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%d').date()
            if dt.weekday() == 6:
                enr = r['enroll_number']
                if enr not in sunday_punches:
                    sunday_punches[enr] = []
                sunday_punches[enr].append(dt_str)
        except Exception:
            pass

    workers = get_workers()
    results = []
    for w in workers:
        enr = w['enroll_number']
        w_id = w['id']
        worked_dates = sunday_punches.get(enr, [])
        c.execute("""
            SELECT allocated_days, used_days FROM worker_leave_balances
            WHERE worker_id = ? AND leave_type_code = 'COMP' AND year = ?
        """, (w_id, year))
        bal = c.fetchone()
        allocated = bal['allocated_days'] if bal else 0.0
        used = bal['used_days'] if bal else 0.0
        available = max(0.0, allocated - used)
        results.append({
            'worker_id': w_id,
            'enroll_number': enr,
            'name': w['name'],
            'department': w['department'],
            'worked_sundays_count': len(worked_dates),
            'worked_dates': worked_dates,
            'comp_allocated': allocated,
            'comp_used': used,
            'comp_available': available
        })
    conn.close()
    return results

def sync_weekoff_earned_compoffs(year=None):
    """
    Scans attendance logs for all workers who worked on Sundays in the given year
    and ensures their COMP (Compensatory Off) leave balance reflects their worked Sundays.
    """
    if not year:
        year = date.today().year
    summary = get_weekoff_workers_summary(year=year)
    conn = get_connection()
    c = conn.cursor()
    updated_count = 0

    for item in summary:
        w_id = item['worker_id']
        worked_count = item['worked_sundays_count']
        if worked_count > 0:
            c.execute("""
                SELECT allocated_days, used_days FROM worker_leave_balances
                WHERE worker_id = ? AND leave_type_code = 'COMP' AND year = ?
            """, (w_id, year))
            row = c.fetchone()
            base_allocated = 4.0
            new_allocated = max(base_allocated, base_allocated + float(worked_count))
            if row:
                if row['allocated_days'] < new_allocated:
                    c.execute("""
                        UPDATE worker_leave_balances
                        SET allocated_days = ?
                        WHERE worker_id = ? AND leave_type_code = 'COMP' AND year = ?
                    """, (new_allocated, w_id, year))
                    updated_count += 1
            else:
                c.execute("""
                    INSERT INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                    VALUES (?, 'COMP', ?, ?, 0.0)
                """, (w_id, year, new_allocated))
                updated_count += 1
    conn.commit()
    conn.close()
    return updated_count

# ----------------- User & Customizable RBAC -----------------

def provision_or_update_super_admin(username, password, full_name, email):
    conn = get_connection()
    c = conn.cursor()
    pwd_hash = generate_password_hash(password)
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing = c.fetchone()
    if existing:
        c.execute("""
            UPDATE users SET password_hash = ?, full_name = ?, email = ?, role = 'super_admin', is_active = 1
            WHERE id = ?
        """, (pwd_hash, full_name, email, existing['id']))
        user_id = existing['id']
    else:
        c.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (?, ?, ?, ?, 'super_admin', 1)
        """, (username, pwd_hash, full_name, email))
        user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_profile(user_id, full_name, email=None, new_password=None, phone=None):
    conn = get_connection()
    c = conn.cursor()
    if new_password:
        pwd_hash = generate_password_hash(new_password)
        c.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ?, password_hash = ?
            WHERE id = ?
        """, (full_name, email, phone, pwd_hash, user_id))
    else:
        c.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ?
            WHERE id = ?
        """, (full_name, email, phone, user_id))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def get_user_permissions(user_id):
    """Returns permission dictionary for a specific user ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return {}

    # Super admin has all permissions granted unconditionally
    if user['role'] == 'super_admin':
        conn.close()
        return {
            'can_view_dashboard': True,
            'can_view_attendance': True,
            'can_export_excel': True,
            'can_manage_workers': True,
            'can_manage_shifts': True,
            'can_trigger_sync': True,
            'can_edit_attendance': True,
            'can_manual_punch': True,
            'can_manage_leaves': True,
            'can_manage_holidays': True,
            'can_view_reports': True,
            'department_access': 'ALL',
            'is_super_admin': True
        }

    # Admin: load custom permissions
    c.execute("SELECT * FROM admin_permissions WHERE user_id = ?", (user_id,))
    perm = c.fetchone()
    conn.close()
    if not perm:
        return {
            'can_view_dashboard': True,
            'can_view_attendance': True,
            'can_export_excel': False,
            'can_manage_workers': False,
            'can_manage_shifts': False,
            'can_trigger_sync': False,
            'can_edit_attendance': False,
            'can_manual_punch': True,
            'can_manage_leaves': True,
            'can_manage_holidays': False,
            'can_view_reports': True,
            'department_access': 'ALL',
            'is_super_admin': False
        }

    perm_keys = perm.keys() if hasattr(perm, 'keys') else []
    can_leaves = bool(perm['can_manage_leaves']) if 'can_manage_leaves' in perm_keys else True
    can_punch = bool(perm['can_manual_punch']) if 'can_manual_punch' in perm_keys else True
    can_holidays = bool(perm['can_manage_holidays']) if 'can_manage_holidays' in perm_keys else True
    can_reports = bool(perm['can_view_reports']) if 'can_view_reports' in perm_keys else True
    dept_access = perm['department_access'] if ('department_access' in perm_keys and perm['department_access']) else 'ALL'

    return {
        'can_view_dashboard': bool(perm['can_view_dashboard']),
        'can_view_attendance': bool(perm['can_view_attendance']),
        'can_export_excel': bool(perm['can_export_excel']),
        'can_manage_workers': bool(perm['can_manage_workers']),
        'can_manage_shifts': bool(perm['can_manage_shifts']),
        'can_trigger_sync': bool(perm['can_trigger_sync']),
        'can_edit_attendance': bool(perm['can_edit_attendance']),
        'can_manual_punch': can_punch,
        'can_manage_leaves': can_leaves,
        'can_manage_holidays': can_holidays,
        'can_view_reports': can_reports,
        'department_access': dept_access,
        'is_super_admin': False
    }

def has_permission(user_id, perm_name):
    perms = get_user_permissions(user_id)
    if perms.get('is_super_admin'):
        return True
    return perms.get(perm_name, False)

def get_all_admins():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, u.full_name, u.email, u.role, u.is_active, u.created_at,
               p.can_view_dashboard, p.can_view_attendance, p.can_export_excel,
               p.can_manage_workers, p.can_manage_shifts, p.can_trigger_sync, p.can_edit_attendance,
               p.can_manual_punch, p.can_manage_leaves, p.can_manage_holidays, p.can_view_reports,
               COALESCE(p.department_access, 'ALL') as department_access
        FROM users u
        LEFT JOIN admin_permissions p ON u.id = p.user_id
        WHERE u.role = 'admin'
        ORDER BY u.id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_admin_user(username, password, full_name, email, permissions):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, 'admin')
        """, (username, generate_password_hash(password), full_name, email))
        user_id = c.lastrowid

        dept_access = permissions.get('department_access', 'ALL') or 'ALL'

        c.execute("""
            INSERT INTO admin_permissions (
                user_id, can_view_dashboard, can_view_attendance, can_export_excel,
                can_manage_workers, can_manage_shifts, can_trigger_sync, can_edit_attendance,
                can_manual_punch, can_manage_leaves, can_manage_holidays, can_view_reports,
                department_access
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            1 if permissions.get('can_view_dashboard', True) else 0,
            1 if permissions.get('can_view_attendance', True) else 0,
            1 if permissions.get('can_export_excel', False) else 0,
            1 if permissions.get('can_manage_workers', False) else 0,
            1 if permissions.get('can_manage_shifts', False) else 0,
            1 if permissions.get('can_trigger_sync', False) else 0,
            1 if permissions.get('can_edit_attendance', False) else 0,
            1 if permissions.get('can_manual_punch', True) else 0,
            1 if permissions.get('can_manage_leaves', True) else 0,
            1 if permissions.get('can_manage_holidays', False) else 0,
            1 if permissions.get('can_view_reports', True) else 0,
            dept_access
        ))
        conn.commit()
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists"

def update_admin_permissions(user_id, permissions):
    conn = get_connection()
    c = conn.cursor()
    dept_access = permissions.get('department_access', 'ALL') or 'ALL'
    c.execute("""
        INSERT INTO admin_permissions (
            user_id, can_view_dashboard, can_view_attendance, can_export_excel,
            can_manage_workers, can_manage_shifts, can_trigger_sync, can_edit_attendance,
            can_manual_punch, can_manage_leaves, can_manage_holidays, can_view_reports,
            department_access
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            can_view_dashboard = excluded.can_view_dashboard,
            can_view_attendance = excluded.can_view_attendance,
            can_export_excel = excluded.can_export_excel,
            can_manage_workers = excluded.can_manage_workers,
            can_manage_shifts = excluded.can_manage_shifts,
            can_trigger_sync = excluded.can_trigger_sync,
            can_edit_attendance = excluded.can_edit_attendance,
            can_manual_punch = excluded.can_manual_punch,
            can_manage_leaves = excluded.can_manage_leaves,
            can_manage_holidays = excluded.can_manage_holidays,
            can_view_reports = excluded.can_view_reports,
            department_access = excluded.department_access
    """, (
        user_id,
        1 if permissions.get('can_view_dashboard') else 0,
        1 if permissions.get('can_view_attendance') else 0,
        1 if permissions.get('can_export_excel') else 0,
        1 if permissions.get('can_manage_workers') else 0,
        1 if permissions.get('can_manage_shifts') else 0,
        1 if permissions.get('can_trigger_sync') else 0,
        1 if permissions.get('can_edit_attendance') else 0,
        1 if permissions.get('can_manual_punch', True) else 0,
        1 if permissions.get('can_manage_leaves', True) else 0,
        1 if permissions.get('can_manage_holidays', False) else 0,
        1 if permissions.get('can_view_reports', True) else 0,
        dept_access
    ))
    conn.commit()
    conn.close()
    return True

def get_departments():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT d.id, d.name, d.name as department, d.code, d.description, d.is_active, d.created_at,
               COUNT(w.id) as headcount
        FROM departments d
        LEFT JOIN workers w ON LOWER(TRIM(w.department)) = LOWER(TRIM(d.name)) AND w.is_active = 1
        WHERE d.is_active = 1
        GROUP BY d.id
        ORDER BY d.name ASC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_department(dept_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def add_department(name, code='', description=''):
    name = (name or '').strip()
    if not name:
        return False, "Department name cannot be empty"
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM departments WHERE LOWER(name) = LOWER(?)", (name,))
    if c.fetchone():
        conn.close()
        return False, f"Department '{name}' already exists"
    c.execute("""
        INSERT INTO departments (name, code, description, is_active)
        VALUES (?, ?, ?, 1)
    """, (name, (code or '').strip().upper(), (description or '').strip()))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return True, new_id

def update_department(dept_id, name, code='', description=''):
    name = (name or '').strip()
    if not name:
        return False, "Department name cannot be empty"
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments WHERE id = ?", (dept_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        return False, "Department not found"
    old_name = existing['name']

    # Check for name collision
    c.execute("SELECT id FROM departments WHERE LOWER(name) = LOWER(?) AND id != ?", (name, dept_id))
    if c.fetchone():
        conn.close()
        return False, f"Another department named '{name}' already exists"

    c.execute("""
        UPDATE departments
        SET name = ?, code = ?, description = ?
        WHERE id = ?
    """, (name, (code or '').strip().upper(), (description or '').strip(), dept_id))

    # If department name changed, automatically update workers assigned to old name
    if old_name.lower() != name.lower():
        c.execute("""
            UPDATE workers
            SET department = ?
            WHERE LOWER(TRIM(department)) = LOWER(TRIM(?))
        """, (name, old_name))

    conn.commit()
    conn.close()
    return True, "Department updated successfully"

def delete_department(dept_id, reassign_to='General'):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments WHERE id = ?", (dept_id,))
    dept = c.fetchone()
    if not dept:
        conn.close()
        return False, "Department not found"
    dept_name = dept['name']

    # Count workers assigned to this department
    c.execute("SELECT COUNT(*) FROM workers WHERE LOWER(TRIM(department)) = LOWER(TRIM(?)) AND is_active = 1", (dept_name,))
    assigned_count = c.fetchone()[0]

    # Reassign active workers if any exist
    if assigned_count > 0:
        target_dept = (reassign_to or 'General').strip()
        c.execute("""
            UPDATE workers
            SET department = ?
            WHERE LOWER(TRIM(department)) = LOWER(TRIM(?))
        """, (target_dept, dept_name))

    c.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
    conn.commit()
    conn.close()
    return True, f"Department '{dept_name}' removed. {assigned_count} worker(s) reassigned to '{reassign_to}'."

def delete_admin_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ? AND role = 'admin'", (user_id,))
    conn.commit()
    conn.close()
    return True

# ----------------- Shifts & Workers -----------------

def get_shifts():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM shifts WHERE is_active = 1 ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_shift(name, start_time, end_time, grace_period_mins=15, half_day_threshold_mins=120):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO shifts (name, start_time, end_time, grace_period_mins, half_day_threshold_mins)
        VALUES (?, ?, ?, ?, ?)
    """, (name, start_time, end_time, grace_period_mins, half_day_threshold_mins))
    shift_id = c.lastrowid
    conn.commit()
    conn.close()
    return shift_id

def update_shift(shift_id, name, start_time, end_time, grace_period_mins, half_day_threshold_mins):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE shifts 
        SET name = ?, start_time = ?, end_time = ?, grace_period_mins = ?, half_day_threshold_mins = ?
        WHERE id = ?
    """, (name, start_time, end_time, grace_period_mins, half_day_threshold_mins, shift_id))
    conn.commit()
    conn.close()
    return True

def delete_shift(shift_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE workers SET shift_id = NULL WHERE shift_id = ?", (shift_id,))
    c.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
    conn.commit()
    conn.close()
    return True

# ----------------- Flexible Shift Global Policy -----------------

def get_flexible_shift_policy():
    """Retrieves the single global full-day and half-day duration thresholds for flexible workers"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM flexible_shift_policy WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'full_day_hours': float(row['full_day_hours']),
            'half_day_hours': float(row['half_day_hours'])
        }
    return {'full_day_hours': 8.0, 'half_day_hours': 4.0}

def update_flexible_shift_policy(full_day_hours, half_day_hours):
    """Updates the single global duration policy for flexible workers"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO flexible_shift_policy (id, full_day_hours, half_day_hours, updated_at)
        VALUES (1, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            full_day_hours = excluded.full_day_hours,
            half_day_hours = excluded.half_day_hours,
            updated_at = CURRENT_TIMESTAMP
    """, (float(full_day_hours), float(half_day_hours)))
    conn.commit()
    conn.close()
    return get_flexible_shift_policy()

def get_workers():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT w.*, s.name as shift_name, s.start_time, s.end_time
        FROM workers w
        LEFT JOIN shifts s ON w.shift_id = s.id
        WHERE w.is_active = 1
        ORDER BY w.enroll_number ASC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_worker(enroll_number, name, department='General', shift_id=None, joining_date=None, password='worker123', email=None, phone=None, photo=''):
    conn = get_connection()
    c = conn.cursor()
    if not joining_date:
        joining_date = date.today().strftime('%Y-%m-%d')
    if not email:
        email = f"worker{enroll_number}@company.local"
    pw_hash = generate_password_hash(password or 'worker123')
    try:
        c.execute("""
            INSERT INTO workers (enroll_number, name, department, shift_id, joining_date, password_hash, email, phone, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (enroll_number, name, department, shift_id, joining_date, pw_hash, email, phone, photo or ''))
        w_id = c.lastrowid

        # Initialize leave balances for all active leave types for current year
        cur_year = date.today().year
        c.execute("SELECT code, default_days FROM leave_types WHERE is_active = 1")
        active_lts = c.fetchall()
        for lt in active_lts:
            c.execute("""
                INSERT OR IGNORE INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                VALUES (?, ?, ?, ?, 0)
            """, (w_id, lt['code'], cur_year, lt['default_days']))

        conn.commit()
        conn.close()
        return True, w_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Enroll Number already registered"

def update_worker(worker_id, name, department, shift_id=None, is_flexible=None, email=None, phone=None, photo=None):
    conn = get_connection()
    c = conn.cursor()
    updates = ["name = ?", "department = ?"]
    params = [name.strip(), department.strip()]

    if photo is not None:
        updates.append("photo = ?")
        params.append(photo.strip())

    if shift_id is not None:
        updates.append("shift_id = ?")
        params.append(shift_id if shift_id != '' else None)

    if is_flexible is not None:
        updates.append("is_flexible = ?")
        params.append(1 if is_flexible else 0)

    if email is not None:
        updates.append("email = ?")
        params.append(email.strip() if email else None)

    if phone is not None:
        updates.append("phone = ?")
        params.append(phone.strip() if phone else None)

    params.append(worker_id)
    c.execute(f"UPDATE workers SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return True

def update_worker_photo(worker_id, photo):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE workers SET photo = ? WHERE id = ?", (photo or '', worker_id))
    conn.commit()
    conn.close()
    return True

def update_worker_shift(worker_id, shift_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE workers SET shift_id = ? WHERE id = ?", (shift_id if shift_id else None, worker_id))
    conn.commit()
    conn.close()
    return True

def set_worker_flexibility(worker_id, is_flexible):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE workers SET is_flexible = ? WHERE id = ?", (1 if is_flexible else 0, worker_id))
    conn.commit()
    conn.close()
    return True

def adjust_worker_leave_balance(worker_id, leave_type_code, year, allocated_days=None, used_days=None, add_allocated=None, add_used=None):
    clean_code = str(leave_type_code).strip().upper()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM worker_leave_balances
        WHERE worker_id = ? AND leave_type_code = ? AND year = ?
    """, (worker_id, clean_code, year))
    row = c.fetchone()
    if not row:
        c.execute("SELECT default_days FROM leave_types WHERE code = ?", (clean_code,))
        lt = c.fetchone()
        def_days = float(lt['default_days']) if lt else 12.0
        c.execute("""
            INSERT INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
            VALUES (?, ?, ?, ?, 0)
        """, (worker_id, clean_code, year, def_days))
        cur_alloc = def_days
        cur_used = 0.0
    else:
        cur_alloc = float(row['allocated_days'])
        cur_used = float(row['used_days'])

    new_alloc = cur_alloc
    new_used = cur_used

    if allocated_days is not None:
        new_alloc = max(0.0, float(allocated_days))
    elif add_allocated is not None:
        new_alloc = max(0.0, cur_alloc + float(add_allocated))

    if used_days is not None:
        new_used = max(0.0, float(used_days))
    elif add_used is not None:
        new_used = max(0.0, cur_used + float(add_used))

    c.execute("""
        UPDATE worker_leave_balances
        SET allocated_days = ?, used_days = ?
        WHERE worker_id = ? AND leave_type_code = ? AND year = ?
    """, (new_alloc, new_used, worker_id, clean_code, year))
    conn.commit()
    conn.close()
    return True, f"Leave '{clean_code}' quota updated: Allocated={new_alloc}d, Used={new_used}d, Net={max(0.0, new_alloc - new_used)}d"

def reset_worker_password(worker_id, new_password):
    conn = get_connection()
    c = conn.cursor()
    pw_hash = generate_password_hash(new_password)
    c.execute("UPDATE workers SET password_hash = ? WHERE id = ?", (pw_hash, worker_id))
    conn.commit()
    conn.close()
    return True

def delete_worker(worker_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
    conn.commit()
    conn.close()
    return True

def authenticate_worker(enroll_or_username, password):
    """
    Checks if a worker can log in using enroll_number (e.g. 101) or name.
    Default password is 'worker123' if not explicitly set.
    """
    conn = get_connection()
    c = conn.cursor()
    
    enroll_num = None
    try:
        enroll_num = int(enroll_or_username)
    except (ValueError, TypeError):
        pass

    if enroll_num is not None:
        c.execute("""
            SELECT w.*, s.name as shift_name, s.start_time, s.end_time
            FROM workers w
            LEFT JOIN shifts s ON w.shift_id = s.id
            WHERE w.enroll_number = ? AND w.is_active = 1
        """, (enroll_num,))
    else:
        clean_name = str(enroll_or_username).replace('worker_', '').strip()
        c.execute("""
            SELECT w.*, s.name as shift_name, s.start_time, s.end_time
            FROM workers w
            LEFT JOIN shifts s ON w.shift_id = s.id
            WHERE (w.enroll_number = ? OR lower(w.name) = ?) AND w.is_active = 1
        """, (int(clean_name) if clean_name.isdigit() else -1, str(enroll_or_username).lower().strip()))
    
    worker = c.fetchone()
    conn.close()

    if not worker:
        return None

    worker_dict = dict(worker)
    pw_hash = worker_dict.get('password_hash')
    if pw_hash:
        if check_password_hash(pw_hash, password):
            return worker_dict
    else:
        if password in ('worker123', str(worker_dict['enroll_number'])):
            return worker_dict

    return None

# ----------------- Attendance Intelligence -----------------

def parse_time(time_str):
    parts = time_str.split(':')
    return int(parts[0]) * 60 + int(parts[1])

def evaluate_daily_status(first_punch_time, shift, is_flexible=False, duration_mins=0, is_in_progress=False):
    """
    Evaluates P, HD, or A based on shift rules or flexible policy.
    first_punch_time: 'HH:MM:SS'
    """
    if not first_punch_time or first_punch_time == '-':
        return 'A'

    if is_flexible:
        policy = get_flexible_shift_policy()
        full_mins = int((policy.get('full_day_hours') or 8.0) * 60)
        half_mins = int((policy.get('half_day_hours') or 4.0) * 60)

        if duration_mins >= full_mins:
            return 'P'
        elif duration_mins >= half_mins:
            return 'HD'
        else:
            if is_in_progress:
                return 'P'
            return 'HD' if duration_mins > 0 else ('HD' if (first_punch_time and first_punch_time != '-') else 'A')

    if not shift:
        return 'P'

    punch_mins = parse_time(first_punch_time[:5])
    shift_start_mins = parse_time(shift['start_time'])
    grace = shift['grace_period_mins'] or 15
    hd_threshold = shift['half_day_threshold_mins'] or 120

    lateness = punch_mins - shift_start_mins
    if lateness <= grace:
        return 'P'
    elif lateness <= hd_threshold:
        return 'P' # Late but present
    else:
        return 'HD' # Half day due to severe lateness

# ----------------- Leave Management System & Categories -----------------

def get_leave_types(include_inactive=False):
    conn = get_connection()
    c = conn.cursor()
    if include_inactive:
        c.execute("SELECT * FROM leave_types ORDER BY code ASC")
    else:
        c.execute("SELECT * FROM leave_types WHERE is_active = 1 ORDER BY code ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def create_leave_type(code, name, default_days=12, color='#3b82f6', is_paid=1, description=''):
    clean_code = str(code).strip().upper()
    clean_name = str(name).strip()
    if not clean_code or not clean_name:
        return False, "Leave code and name are required"
    try:
        default_days = float(default_days)
    except (ValueError, TypeError):
        default_days = 0.0

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT code, is_active FROM leave_types WHERE code = ?", (clean_code,))
    existing = c.fetchone()
    if existing:
        if existing['is_active'] == 0:
            # Reactivate
            c.execute("""
                UPDATE leave_types
                SET name = ?, default_days = ?, color = ?, is_paid = ?, description = ?, is_active = 1
                WHERE code = ?
            """, (clean_name, default_days, color, 1 if is_paid else 0, description, clean_code))
        else:
            conn.close()
            return False, f"Leave category code '{clean_code}' already exists"
    else:
        c.execute("""
            INSERT INTO leave_types (code, name, default_days, color, is_paid, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (clean_code, clean_name, default_days, color, 1 if is_paid else 0, description))

    # Provision this category into worker balances for current year
    cur_year = date.today().year
    c.execute("SELECT id FROM workers WHERE is_active = 1")
    workers = c.fetchall()
    for w in workers:
        c.execute("""
            INSERT INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(worker_id, leave_type_code, year) DO UPDATE SET
            allocated_days = excluded.allocated_days
        """, (w['id'], clean_code, cur_year, default_days))

    conn.commit()
    conn.close()
    return True, clean_code

def update_leave_type(code, name, default_days, color='#3b82f6', is_paid=1, description='', update_workers=True, year=None):
    clean_code = str(code).strip().upper()
    clean_name = str(name).strip()
    if not clean_name:
        return False, "Leave category name cannot be empty"
    try:
        default_days = float(default_days)
    except (ValueError, TypeError):
        default_days = 0.0

    if not year:
        year = date.today().year

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT code FROM leave_types WHERE code = ?", (clean_code,))
    if not c.fetchone():
        conn.close()
        return False, f"Leave category '{clean_code}' not found"

    c.execute("""
        UPDATE leave_types
        SET name = ?, default_days = ?, color = ?, is_paid = ?, description = ?
        WHERE code = ?
    """, (clean_name, default_days, color, 1 if is_paid else 0, description, clean_code))

    # If update_workers is requested, adjust active workers' allocated days for this year
    if update_workers:
        c.execute("""
            UPDATE worker_leave_balances
            SET allocated_days = ?
            WHERE leave_type_code = ? AND year = ?
        """, (default_days, clean_code, year))

        c.execute("SELECT id FROM workers WHERE is_active = 1")
        workers = c.fetchall()
        for w in workers:
            c.execute("""
                INSERT INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(worker_id, leave_type_code, year) DO UPDATE SET
                allocated_days = excluded.allocated_days
            """, (w['id'], clean_code, year, default_days))

    conn.commit()
    conn.close()
    return True, "Leave category updated successfully"

def delete_leave_type(code):
    clean_code = str(code).strip().upper()
    conn = get_connection()
    c = conn.cursor()

    # Check if applications exist with this leave type
    c.execute("SELECT COUNT(*) FROM leave_applications WHERE leave_type_code = ?", (clean_code,))
    app_count = c.fetchone()[0]

    if app_count > 0:
        c.execute("UPDATE leave_types SET is_active = 0 WHERE code = ?", (clean_code,))
        conn.commit()
        conn.close()
        return True, f"Category '{clean_code}' archived (soft-deleted because {app_count} application(s) exist)"
    else:
        c.execute("DELETE FROM worker_leave_balances WHERE leave_type_code = ?", (clean_code,))
        c.execute("DELETE FROM leave_types WHERE code = ?", (clean_code,))
        conn.commit()
        conn.close()
        return True, f"Category '{clean_code}' permanently deleted"

def get_worker_leave_balance(worker_id, year=None):
    if not year:
        year = date.today().year
    conn = get_connection()
    c = conn.cursor()

    # Dynamically ensure all active leave types have balance rows for this worker
    c.execute("SELECT code, default_days FROM leave_types WHERE is_active = 1")
    active_types = c.fetchall()
    for lt in active_types:
        c.execute("""
            INSERT OR IGNORE INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
            VALUES (?, ?, ?, ?, 0)
        """, (worker_id, lt['code'], year, lt['default_days']))
    conn.commit()

    c.execute("""
        SELECT b.*, lt.name as leave_type_name, lt.color as leave_color, lt.is_paid, lt.description as leave_description
        FROM worker_leave_balances b
        JOIN leave_types lt ON b.leave_type_code = lt.code
        WHERE b.worker_id = ? AND b.year = ? AND lt.is_active = 1
        ORDER BY b.leave_type_code ASC
    """, (worker_id, year))
    rows = c.fetchall()

    c.execute("""
        SELECT leave_type_code, SUM(days_count) as pending_days
        FROM leave_applications
        WHERE worker_id = ? AND status = 'PENDING' AND strftime('%Y', start_date) = ?
        GROUP BY leave_type_code
    """, (worker_id, str(year)))
    pending_map = {r['leave_type_code']: (r['pending_days'] or 0.0) for r in c.fetchall()}

    conn.close()

    total_allocated = 0.0
    total_used = 0.0
    total_remaining = 0.0
    total_pending = 0.0
    balances = []

    for r in rows:
        alloc = float(r['allocated_days'])
        used = float(r['used_days'])
        rem = max(0.0, alloc - used)
        pend = float(pending_map.get(r['leave_type_code'], 0.0))
        total_allocated += alloc
        total_used += used
        total_remaining += rem
        total_pending += pend

        r_keys = r.keys() if hasattr(r, 'keys') else []
        is_paid = bool(r['is_paid']) if 'is_paid' in r_keys else True
        desc = r['leave_description'] if 'leave_description' in r_keys else ''

        balances.append({
            'code': r['leave_type_code'],
            'leave_type_code': r['leave_type_code'],
            'name': r['leave_type_name'],
            'leave_type_name': r['leave_type_name'],
            'color': r['leave_color'],
            'is_paid': is_paid,
            'description': desc,
            'allocated': alloc,
            'allocated_days': alloc,
            'used': used,
            'used_days': used,
            'remaining': rem,
            'remaining_days': rem,
            'pending': pend,
            'pending_days': pend
        })

    return {
        'worker_id': worker_id,
        'year': year,
        'total_allocated': total_allocated,
        'total_used': total_used,
        'total_remaining': total_remaining,
        'total_pending': total_pending,
        'balances': balances
    }

def get_all_workers_leave_balances(year=None):
    if not year:
        year = date.today().year
    workers = get_workers()
    results = []
    for w in workers:
        bal = get_worker_leave_balance(w['id'], year)
        results.append({
            'worker_id': w['id'],
            'enroll_number': w['enroll_number'],
            'name': w['name'],
            'department': w['department'],
            'shift_name': w['shift_name'],
            'balance': bal
        })
    return results

def get_worker_by_enroll_or_id(identifier):
    conn = get_connection()
    c = conn.cursor()
    val = None
    try:
        val = int(identifier)
    except (ValueError, TypeError):
        pass

    if val is not None:
        c.execute("""
            SELECT w.*, s.name as shift_name
            FROM workers w
            LEFT JOIN shifts s ON w.shift_id = s.id
            WHERE (w.enroll_number = ? OR w.id = ?) AND w.is_active = 1
        """, (val, val))
    else:
        c.execute("""
            SELECT w.*, s.name as shift_name
            FROM workers w
            LEFT JOIN shifts s ON w.shift_id = s.id
            WHERE lower(w.name) LIKE ? AND w.is_active = 1
        """, (f"%{str(identifier).lower().strip()}%",))

    worker = c.fetchone()
    conn.close()
    if not worker:
        return None
    w_dict = dict(worker)
    balance = get_worker_leave_balance(w_dict['id'], date.today().year)
    w_dict['leave_balance'] = balance
    return w_dict

def apply_leave(worker_id, leave_type_code, start_date, end_date, reason, applied_by='worker', applied_by_user_id=None, document_ref=None, initial_status='PENDING', status=None, reviewer_id=None, admin_notes=None):
    if status:
        initial_status = status
    if not reviewer_id and applied_by_user_id:
        reviewer_id = applied_by_user_id

    try:
        d1 = datetime.strptime(start_date, '%Y-%m-%d').date()
        d2 = datetime.strptime(end_date, '%Y-%m-%d').date()
    except Exception as e:
        return False, f"Invalid date format: {e}"

    if d2 < d1:
        return False, "End date cannot be earlier than start date"

    # Calculate working days (skip Sundays)
    cur = d1
    days_count = 0.0
    while cur <= d2:
        if cur.weekday() != 6: # Not Sunday
            days_count += 1.0
        cur += timedelta(days=1)
    if days_count == 0.0:
        days_count = 1.0

    conn = get_connection()
    c = conn.cursor()

    year = d1.year
    balance = get_worker_leave_balance(worker_id, year)
    type_bal = next((b for b in balance['balances'] if b['code'] == leave_type_code), None)
    if not type_bal:
        conn.close()
        return False, f"Invalid leave type code: {leave_type_code}"

    if initial_status == 'APPROVED':
        c.execute("""
            INSERT INTO leave_applications (
                worker_id, leave_type_code, start_date, end_date, days_count, reason,
                status, applied_by, applied_by_user_id, document_ref, admin_notes,
                reviewed_by, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (worker_id, leave_type_code, start_date, end_date, days_count, reason, applied_by, applied_by_user_id, document_ref, admin_notes, reviewer_id))
        app_id = c.lastrowid
        c.execute("""
            UPDATE worker_leave_balances
            SET used_days = used_days + ?
            WHERE worker_id = ? AND leave_type_code = ? AND year = ?
        """, (days_count, worker_id, leave_type_code, year))
    else:
        c.execute("""
            INSERT INTO leave_applications (
                worker_id, leave_type_code, start_date, end_date, days_count, reason,
                status, applied_by, applied_by_user_id, document_ref, admin_notes
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?)
        """, (worker_id, leave_type_code, start_date, end_date, days_count, reason, applied_by, applied_by_user_id, document_ref, admin_notes))
        app_id = c.lastrowid

    conn.commit()
    conn.close()
    return True, app_id

def review_leave_application(leave_id, status, reviewer_id, admin_notes=None):
    if status not in ('APPROVED', 'REJECTED'):
        return False, "Invalid status. Must be APPROVED or REJECTED"

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM leave_applications WHERE id = ?", (leave_id,))
    app = c.fetchone()
    if not app:
        conn.close()
        return False, "Leave application not found"

    app_dict = dict(app)
    old_status = app_dict['status']
    worker_id = app_dict['worker_id']
    leave_type = app_dict['leave_type_code']
    days_count = float(app_dict['days_count'])
    year = int(app_dict['start_date'][:4])

    if old_status == 'APPROVED' and status == 'REJECTED':
        c.execute("""
            UPDATE worker_leave_balances
            SET used_days = MAX(0, used_days - ?)
            WHERE worker_id = ? AND leave_type_code = ? AND year = ?
        """, (days_count, worker_id, leave_type, year))
    elif old_status != 'APPROVED' and status == 'APPROVED':
        c.execute("""
            UPDATE worker_leave_balances
            SET used_days = used_days + ?
            WHERE worker_id = ? AND leave_type_code = ? AND year = ?
        """, (days_count, worker_id, leave_type, year))

    c.execute("""
        UPDATE leave_applications
        SET status = ?, admin_notes = COALESCE(?, admin_notes), reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, admin_notes, reviewer_id, leave_id))

    conn.commit()
    conn.close()
    return True, "Leave application updated successfully"

def get_leave_applications(worker_id=None, status=None, year=None, month=None):
    conn = get_connection()
    c = conn.cursor()

    query = """
        SELECT la.*, lt.name as leave_type_name, lt.color as leave_color,
               w.enroll_number, w.name as worker_name, w.department,
               u.full_name as reviewer_name
        FROM leave_applications la
        JOIN workers w ON la.worker_id = w.id
        JOIN leave_types lt ON la.leave_type_code = lt.code
        LEFT JOIN users u ON la.reviewed_by = u.id
        WHERE 1=1
    """
    params = []
    if worker_id:
        query += " AND la.worker_id = ?"
        params.append(worker_id)
    if status:
        query += " AND la.status = ?"
        params.append(status)
    if year:
        query += " AND strftime('%Y', la.start_date) = ?"
        params.append(str(year))
    if month:
        query += " AND CAST(strftime('%m', la.start_date) AS INTEGER) = ?"
        params.append(int(month))

    query += " ORDER BY la.id DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_leave_kpis(year=None):
    if not year:
        year = date.today().year
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leave_applications WHERE status = 'PENDING'")
    pending_count = c.fetchone()[0]

    cur_month = f"{date.today().strftime('%Y-%m')}%"
    c.execute("SELECT COUNT(*) FROM leave_applications WHERE status = 'APPROVED' AND start_date LIKE ?", (cur_month,))
    approved_month = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leave_applications WHERE status = 'REJECTED' AND start_date LIKE ?", (cur_month,))
    rejected_month = c.fetchone()[0]

    c.execute("SELECT SUM(used_days), SUM(allocated_days) FROM worker_leave_balances WHERE year = ?", (year,))
    row = c.fetchone()
    total_used = row[0] or 0.0
    total_allocated = row[1] or 0.0

    conn.close()
    return {
        'pending_count': pending_count,
        'approved_month': approved_month,
        'rejected_month': rejected_month,
        'total_used': total_used,
        'total_allocated': total_allocated
    }

def get_approved_leaves_map(start_date, end_date):
    """
    Returns a dict mapping (enroll_number, 'YYYY-MM-DD') -> leave_dict
    for all APPROVED leave applications that overlap [start_date, end_date].
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT la.*, lt.name as leave_type_name, lt.color as leave_color, w.enroll_number
        FROM leave_applications la
        JOIN workers w ON la.worker_id = w.id
        JOIN leave_types lt ON la.leave_type_code = lt.code
        WHERE la.status = 'APPROVED'
          AND la.start_date <= ? AND la.end_date >= ?
    """, (end_date, start_date))
    rows = c.fetchall()
    conn.close()

    leaves_map = {}
    for r in rows:
        enr = r['enroll_number']
        cur_d = datetime.strptime(r['start_date'], '%Y-%m-%d').date()
        end_d = datetime.strptime(r['end_date'], '%Y-%m-%d').date()
        while cur_d <= end_d:
            cur_d_str = cur_d.strftime('%Y-%m-%d')
            leaves_map[(enr, cur_d_str)] = dict(r)
            cur_d += timedelta(days=1)
    return leaves_map

def get_worker_personal_attendance(worker_id, year, month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT w.*, s.name as shift_name, s.start_time, s.end_time, s.grace_period_mins, s.half_day_threshold_mins
        FROM workers w
        LEFT JOIN shifts s ON w.shift_id = s.id
        WHERE w.id = ?
    """, (worker_id,))
    worker = c.fetchone()
    if not worker:
        conn.close()
        return None

    w_dict = dict(worker)
    enr = w_dict['enroll_number']
    shift = {
        'start_time': w_dict['start_time'] or '09:00',
        'end_time': w_dict['end_time'] or '18:00',
        'grace_period_mins': w_dict['grace_period_mins'] or 15,
        'half_day_threshold_mins': w_dict['half_day_threshold_mins'] or 120
    }

    num_days = calendar.monthrange(year, month)[1]
    start_d_str = f"{year:04d}-{month:02d}-01"
    end_d_str = f"{year:04d}-{month:02d}-{num_days:02d}"

    c.execute("""
        SELECT event_timestamp, punch_type, verify_mode, is_manual
        FROM attendance_logs
        WHERE enroll_number = ? AND event_timestamp >= ? AND event_timestamp <= ?
        ORDER BY event_timestamp ASC
    """, (enr, f"{start_d_str} 00:00:00", f"{end_d_str} 23:59:59"))
    punches_rows = c.fetchall()
    conn.close()

    punches_by_day = {}
    for p in punches_rows:
        day_str = p['event_timestamp'].split(' ')[0]
        if day_str not in punches_by_day:
            punches_by_day[day_str] = []
        punches_by_day[day_str].append(p['event_timestamp'])

    leaves_map = get_approved_leaves_map(start_d_str, end_d_str)
    holidays_map = get_holidays_map(start_d_str, end_d_str)

    today = date.today()
    day_records = []
    p_count = 0
    hd_count = 0
    a_count = 0
    lv_count = 0
    hld_count = 0
    off_count = 0
    total_mins = 0

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    co_count = 0

    for day in range(1, num_days + 1):
        cur_dt = date(year, month, day)
        cur_d_str = cur_dt.strftime('%Y-%m-%d')
        day_name = day_names[cur_dt.weekday()]
        punches = punches_by_day.get(cur_d_str, [])
        leave_info = leaves_map.get((enr, cur_d_str))
        holiday_info = holidays_map.get(cur_d_str)

        first_in = '-'
        last_out = '-'
        duration_str = '-'
        is_late = False

        if cur_dt > today:
            if holiday_info:
                status = 'HLD'
                hld_count += 1
                duration_str = holiday_info['name']
            elif cur_dt.weekday() == 6:
                status = 'OFF'
                off_count += 1
                duration_str = 'Weekly Off'
            elif leave_info:
                if leave_info.get('leave_type_code') == 'COMP':
                    status = 'CO'
                    co_count += 1
                    duration_str = 'Compensatory Off'
                else:
                    status = 'LV'
                    lv_count += 1
                    duration_str = leave_info.get('leave_type_name', 'Leave')
            else:
                status = '-'
        elif punches:
            first_in = punches[0].split(' ')[1][:5]
            t1 = datetime.strptime(punches[0], '%Y-%m-%d %H:%M:%S')

            has_out_punch = (len(punches) > 1 and punches[-1] != punches[0])
            if has_out_punch:
                last_out = punches[-1].split(' ')[1][:5]
                t2 = datetime.strptime(punches[-1], '%Y-%m-%d %H:%M:%S')
                diff_m = max(0, int((t2 - t1).total_seconds() / 60))
                duration_str = f"{diff_m // 60}h {diff_m % 60}m"
                is_in_progress = False
            else:
                if cur_dt == today:
                    last_out = 'In Progress'
                    now_dt = datetime.now()
                    diff_m = max(0, int((now_dt - t1).total_seconds() / 60))
                    duration_str = f"{diff_m // 60}h {diff_m % 60}m"
                    is_in_progress = True
                else:
                    last_out = 'No Out'
                    diff_m = 0
                    duration_str = 'Single Punch'
                    is_in_progress = False

            total_mins += diff_m
            is_flex = bool(w_dict.get('is_flexible', 0))

            if cur_dt.weekday() == 6:
                status = 'W-OFF'
                p_count += 1
                duration_str += ' (Comp-Off Earned)'
            elif holiday_info:
                status = 'P'
                p_count += 1
                duration_str += f" ({holiday_info['name']})"
            else:
                status = evaluate_daily_status(first_in, shift, is_flexible=is_flex, duration_mins=diff_m, is_in_progress=is_in_progress)
                if status == 'A' and len(punches) > 0:
                    status = 'P' if is_in_progress else 'HD'

                if not is_flex and shift and parse_time(first_in) > parse_time(shift['start_time']) + (shift['grace_period_mins'] or 15):
                    is_late = True

                if status == 'P':
                    p_count += 1
                elif status == 'HD':
                    hd_count += 1
                else:
                    a_count += 1
        elif leave_info:
            if leave_info.get('leave_type_code') == 'COMP':
                status = 'CO'
                co_count += 1
                duration_str = 'Compensatory Off'
            else:
                status = 'LV'
                lv_count += 1
                duration_str = leave_info.get('leave_type_name', 'Leave')
        elif holiday_info:
            status = 'HLD'
            hld_count += 1
            duration_str = holiday_info.get('name', 'Official Holiday')
        elif cur_dt.weekday() == 6:
            status = 'OFF'
            off_count += 1
            duration_str = 'Weekly Off'
        else:
            status = 'A'
            a_count += 1

        day_records.append({
            'date': cur_d_str,
            'day_num': day,
            'day_name': day_name,
            'first_in': first_in,
            'last_out': last_out,
            'duration': duration_str,
            'status': status,
            'is_late': is_late,
            'punches_count': len(punches),
            'leave_reason': leave_info.get('reason', '') if leave_info else '',
            'leave_code': leave_info.get('leave_type_code', '') if leave_info else '',
            'leave_name': leave_info.get('leave_type_name', '') if leave_info else '',
            'holiday_name': holiday_info.get('name', '') if holiday_info else ''
        })

    leave_balance = get_worker_leave_balance(worker_id, year)
    payable_days = p_count + (hd_count * 0.5) + lv_count + hld_count + co_count

    return {
        'worker': w_dict,
        'year': year,
        'month': month,
        'summary': {
            'present': p_count,
            'half_day': hd_count,
            'absent': a_count,
            'leave': lv_count,
            'holiday': hld_count,
            'comp_off': co_count,
            'off': off_count,
            'total_hours': f"{total_mins // 60}h {total_mins % 60}m",
            'payable_days': payable_days
        },
        'leave_balance': leave_balance,
        'records': day_records
    }

def get_stats():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM workers WHERE is_active = 1")
    total_workers = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM shifts WHERE is_active = 1")
    active_shifts = c.fetchone()[0]

    c.execute("SELECT last_status, ip_address FROM devices WHERE id = 1")
    dev = c.fetchone()
    terminal_status = dev['last_status'] if dev else 'OFFLINE'

    # Today attendance stats
    today_str = date.today().strftime('%Y-%m-%d')
    daily = get_daily_attendance_details(today_str)

    present_today = 0
    half_day_today = 0
    absent_today = 0
    leave_today = 0
    holiday_today = 0

    for d in daily:
        st = d.get('status')
        if st == 'P':
            present_today += 1
        elif st == 'HD':
            half_day_today += 1
        elif st == 'LV':
            leave_today += 1
        elif st == 'HLD':
            holiday_today += 1
        elif st == 'A':
            absent_today += 1

    total_present_today = present_today + half_day_today

    c.execute("SELECT COUNT(*) FROM leave_applications WHERE status = 'PENDING'")
    pending_leaves = c.fetchone()[0]

    # Check if today is official holiday
    holidays_map = get_holidays_map(today_str, today_str)
    today_holiday = holidays_map.get(today_str)

    conn.close()
    return {
        'total_workers': total_workers,
        'active_shifts': active_shifts,
        'present_today': present_today,
        'half_day_today': half_day_today,
        'total_present_today': total_present_today,
        'absent_today': absent_today,
        'leave_today': leave_today,
        'holiday_today': holiday_today,
        'is_holiday_today': bool(today_holiday),
        'holiday_today_name': today_holiday['name'] if today_holiday else '',
        'pending_leaves': pending_leaves,
        'terminal_status': terminal_status,
        'today_date': today_str
    }

def get_daily_attendance_details(date_str):
    conn = get_connection()
    c = conn.cursor()

    workers = get_workers()
    shifts_map = {s['id']: s for s in get_shifts()}
    leaves_map = get_approved_leaves_map(date_str, date_str)
    holidays_map = get_holidays_map(date_str, date_str)
    holiday_info = holidays_map.get(date_str)

    c.execute("""
        SELECT id, enroll_number, event_timestamp, is_manual, verify_mode, punch_type, manual_reason
        FROM attendance_logs
        WHERE event_timestamp LIKE ?
        ORDER BY event_timestamp ASC
    """, (f"{date_str}%",))
    rows = c.fetchall()

    punches_by_worker = {}
    manual_by_worker = {}
    for r in rows:
        enr = r['enroll_number']
        if enr not in punches_by_worker:
            punches_by_worker[enr] = []
            manual_by_worker[enr] = False

        v_mode = r['verify_mode']
        is_man = bool(r['is_manual'])
        method_info = get_verify_method_info(v_mode, is_man)

        punches_by_worker[enr].append({
            'id': r['id'],
            'timestamp': r['event_timestamp'],
            'verify_mode': v_mode,
            'is_manual': is_man,
            'manual_reason': r['manual_reason'] or '',
            'method': method_info
        })
        if is_man:
            manual_by_worker[enr] = True

    results = []
    target_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    is_sunday = target_dt.weekday() == 6
    is_future = target_dt > date.today()
    is_today = (date_str == date.today().strftime('%Y-%m-%d'))

    for w in workers:
        enr = w['enroll_number']
        punches = punches_by_worker.get(enr, [])
        shift = shifts_map.get(w['shift_id'])
        leave_info = leaves_map.get((enr, date_str))

        if punches:
            first_in_raw = punches[0]['timestamp']
            first_in = first_in_raw.split(' ')[1]
            first_in_method = punches[0]['method']
            t1 = datetime.strptime(first_in_raw, '%Y-%m-%d %H:%M:%S')

            if len(punches) > 1:
                last_out_raw = punches[-1]['timestamp']
                last_out = last_out_raw.split(' ')[1]
                last_out_method = punches[-1]['method']
                t2 = datetime.strptime(last_out_raw, '%Y-%m-%d %H:%M:%S')
                diff_mins = max(0, int((t2 - t1).total_seconds() / 60))
                hours = diff_mins // 60
                mins = diff_mins % 60
                duration_str = f"{hours}h {mins}m"
            else:
                if is_today:
                    last_out = 'In Progress'
                    last_out_method = {
                        'code': 'progress',
                        'label': 'Shift In Progress',
                        'short': 'Active',
                        'icon': 'bi-hourglass-split',
                        'badge_class': 'bg-warning text-dark'
                    }
                    now_dt = datetime.now()
                    diff_mins = max(0, int((now_dt - t1).total_seconds() / 60))
                    hours = diff_mins // 60
                    mins = diff_mins % 60
                    duration_str = f"{hours}h {mins}m (Active)"
                else:
                    last_out = 'No Out Punch'
                    last_out_method = {
                        'code': 'none',
                        'label': 'Single Punch',
                        'short': 'Single',
                        'icon': 'bi-dash-circle',
                        'badge_class': 'bg-secondary'
                    }
                    duration_str = 'Single Punch'
                    diff_mins = 0

            is_flex = bool(w.get('is_flexible', 0))
            status = evaluate_daily_status(first_in, shift, is_flexible=is_flex, duration_mins=diff_mins, is_in_progress=(last_out == 'In Progress'))
            is_late = False
            if shift and not is_flex:
                punch_m = parse_time(first_in[:5])
                shift_m = parse_time(shift['start_time'])
                if punch_m > shift_m + (shift['grace_period_mins'] or 15):
                    is_late = True
        else:
            first_in = '-'
            last_out = '-'
            first_in_method = None
            last_out_method = None
            duration_str = '-'
            is_late = False
            is_flex = bool(w.get('is_flexible', 0))
            if is_future:
                status = '-'
            elif is_sunday:
                status = 'OFF'
            elif leave_info:
                status = 'LV'
                duration_str = leave_info.get('leave_type_name', 'Leave')
            elif holiday_info:
                # Official Government / Company Holiday: NOT marked as absent!
                status = 'HLD'
                duration_str = holiday_info.get('name', 'Official Holiday')
            else:
                status = 'A'

        results.append({
            'worker_id': w['id'],
            'enroll_number': enr,
            'name': w['name'],
            'department': w['department'],
            'shift_name': ('Flexible Schedule' if is_flex else (w['shift_name'] or 'Not Assigned')),
            'is_flexible': 1 if is_flex else 0,
            'photo': w.get('photo') or '',
            'email': w.get('email') or '',
            'phone': w.get('phone') or '',
            'joining_date': w.get('joining_date') or '',
            'first_check_in': first_in,
            'last_check_out': last_out,
            'first_check_in_method': first_in_method,
            'last_check_out_method': last_out_method,
            'duration': duration_str,
            'status': status,
            'is_late': is_late,
            'has_manual_punch': manual_by_worker.get(enr, False),
            'punches_count': len(punches),
            'all_punches': punches,
            'is_holiday': bool(holiday_info and not punches),
            'is_holiday_work': bool(holiday_info and punches),
            'holiday_name': holiday_info.get('name', '') if holiday_info else '',
            'holiday_notes': holiday_info.get('notes', '') if holiday_info else '',
            'leave_reason': leave_info.get('reason', '') if leave_info else '',
            'leave_code': leave_info.get('leave_type_code', '') if leave_info else '',
            'leave_color': leave_info.get('leave_color', '') if leave_info else '',
            'leave_name': leave_info.get('leave_type_name', '') if leave_info else ''
        })

    conn.close()
    return results

def get_monthly_attendance_matrix(year, month, department=None):
    conn = get_connection()
    c = conn.cursor()

    all_workers = get_workers()
    shifts_map = {s['id']: s for s in get_shifts()}

    # All available departments in workforce
    all_departments = sorted(list(set([w['department'] for w in all_workers if w.get('department')])))

    # Department filter
    if department and department.strip().upper() != 'ALL':
        workers = [w for w in all_workers if (w.get('department') or '').strip().lower() == department.strip().lower()]
    else:
        workers = all_workers

    num_days = calendar.monthrange(year, month)[1]
    days_list = list(range(1, num_days + 1))

    start_d_str = f"{year:04d}-{month:02d}-01"
    end_d_str = f"{year:04d}-{month:02d}-{num_days:02d}"
    leaves_map = get_approved_leaves_map(start_d_str, end_d_str)
    holidays_map = get_holidays_map(start_d_str, end_d_str)

    prefix = f"{year:04d}-{month:02d}-"
    c.execute("""
        SELECT enroll_number, event_timestamp
        FROM attendance_logs
        WHERE event_timestamp LIKE ?
        ORDER BY event_timestamp ASC
    """, (f"{prefix}%",))
    rows = c.fetchall()

    daily_punches = {}
    for r in rows:
        enr = r['enroll_number']
        dt_str = r['event_timestamp']
        day_part = int(dt_str[8:10])
        key = (enr, day_part)
        if key not in daily_punches:
            daily_punches[key] = []
        daily_punches[key].append(dt_str)

    today = date.today()
    matrix_workers = []

    for w in workers:
        enr = w['enroll_number']
        shift = shifts_map.get(w['shift_id'])
        worker_days = {}

        p_count = 0
        hd_count = 0
        a_count = 0
        lv_count = 0
        hld_count = 0
        co_count = 0
        worked_off_count = 0
        off_count = 0

        for day in days_list:
            cur_date = date(year, month, day)
            cur_d_str = cur_date.strftime('%Y-%m-%d')
            key = (enr, day)
            punches = daily_punches.get(key, [])
            leave_info = leaves_map.get((enr, cur_d_str))
            holiday_info = holidays_map.get(cur_d_str)
            is_sunday = (cur_date.weekday() == 6)

            if cur_date > today:
                if holiday_info:
                    status = 'HLD'
                    hld_count += 1
                    tooltip = f"Official Holiday: {holiday_info['name']}"
                elif is_sunday:
                    status = 'OFF'
                    off_count += 1
                    tooltip = 'Weekly Off (Sunday)'
                elif leave_info:
                    if leave_info.get('leave_type_code') == 'COMP':
                        status = 'CO'
                        co_count += 1
                        tooltip = f"Compensatory Off: {leave_info.get('reason', 'Comp-Off')}"
                    else:
                        status = 'LV'
                        lv_count += 1
                        tooltip = f"Approved Leave: {leave_info.get('leave_type_name', 'Leave')}"
                else:
                    status = '-'
                    tooltip = 'Future date'
            elif punches:
                first_in = punches[0].split(' ')[1][:5]
                t1 = datetime.strptime(punches[0], '%Y-%m-%d %H:%M:%S')
                t2 = datetime.strptime(punches[-1], '%Y-%m-%d %H:%M:%S')
                diff_m = max(0, int((t2 - t1).total_seconds() / 60))
                if len(punches) == 1 and cur_date == today:
                    diff_m = max(0, int((datetime.now() - t1).total_seconds() / 60))
                is_flex = bool(w.get('is_flexible', 0))

                if is_sunday:
                    status = 'W-OFF'
                    p_count += 1
                    worked_off_count += 1
                    tooltip = f"Worked on Weekly Off (Sunday) - Comp-Off Earned! (In: {first_in})"
                elif holiday_info:
                    status = 'P'
                    p_count += 1
                    tooltip = f"Worked on Official Holiday: {holiday_info['name']} - Comp-Off / Overtime Eligible (In: {first_in})"
                else:
                    status = evaluate_daily_status(first_in, shift, is_flexible=is_flex, duration_mins=diff_m, is_in_progress=(len(punches) == 1 and cur_date == today))
                    if status == 'P':
                        p_count += 1
                        tooltip = f"{'Flexible Present' if is_flex else 'Present'} (In: {first_in})"
                    elif status == 'HD':
                        hd_count += 1
                        tooltip = f"Half Day (In: {first_in})"
                    else:
                        a_count += 1
                        tooltip = f"Absent (In: {first_in})"
            elif leave_info:
                if leave_info.get('leave_type_code') == 'COMP':
                    status = 'CO'
                    co_count += 1
                    tooltip = f"Compensatory Off Taken: {leave_info.get('reason', 'Comp-Off')}"
                else:
                    status = 'LV'
                    lv_count += 1
                    tooltip = f"On Leave: {leave_info.get('leave_type_name', 'Leave')} ({leave_info.get('reason', '')})"
            elif holiday_info:
                # Official Government / Company Holiday: NOT marked as absent!
                status = 'HLD'
                hld_count += 1
                h_name = holiday_info['name']
                h_note = f" - {holiday_info['notes']}" if holiday_info.get('notes') else ''
                tooltip = f"Official Holiday: {h_name}{h_note}"
            elif is_sunday:
                status = 'OFF'
                off_count += 1
                tooltip = 'Weekly Off (Sunday)'
            else:
                status = 'A'
                a_count += 1
                tooltip = 'Absent (No Punch)'

            worker_days[str(day)] = {
                'status': status,
                'tooltip': tooltip,
                'is_holiday': bool(holiday_info),
                'holiday_name': holiday_info['name'] if holiday_info else '',
                'is_sunday': is_sunday
            }

        # Payable days includes Worked Days, Half Days (x0.5), Approved Paid Leaves, Official Holidays, and Comp-Offs
        payable_days = p_count + (hd_count * 0.5) + lv_count + hld_count + co_count

        matrix_workers.append({
            'id': w['id'],
            'enroll_number': enr,
            'name': w['name'],
            'department': w['department'],
            'shift_name': w['shift_name'] or 'General',
            'is_flexible': 1 if w.get('is_flexible') else 0,
            'photo': w.get('photo') or '',
            'days': worker_days,
            'summary': {
                'present': p_count,
                'half_day': hd_count,
                'absent': a_count,
                'leave': lv_count,
                'holiday': hld_count,
                'comp_off': co_count,
                'worked_weekoff': worked_off_count,
                'off': off_count,
                'total_days': num_days,
                'payable_days': payable_days
            }
        })

    days_meta = []
    for day in days_list:
        cur_date = date(year, month, day)
        cur_d_str = cur_date.strftime('%Y-%m-%d')
        h_info = holidays_map.get(cur_d_str)
        days_meta.append({
            'day': day,
            'date': cur_d_str,
            'weekday': cur_date.weekday(),
            'is_sunday': (cur_date.weekday() == 6),
            'is_holiday': bool(h_info),
            'holiday_name': h_info['name'] if h_info else ''
        })

    month_holidays = [
        {'date': k, 'name': v['name'], 'notes': v.get('notes', '')}
        for k, v in sorted(holidays_map.items())
    ]

    # Department-wise breakdown
    dept_map = {}
    for w in matrix_workers:
        d_name = w.get('department') or 'General'
        if d_name not in dept_map:
            dept_map[d_name] = {
                'department': d_name,
                'headcount': 0,
                'present': 0,
                'half_day': 0,
                'absent': 0,
                'leave': 0,
                'holiday': 0,
                'comp_off': 0,
                'payable_days': 0.0
            }
        dept_map[d_name]['headcount'] += 1
        dept_map[d_name]['present'] += w['summary']['present']
        dept_map[d_name]['half_day'] += w['summary']['half_day']
        dept_map[d_name]['absent'] += w['summary']['absent']
        dept_map[d_name]['leave'] += w['summary']['leave']
        dept_map[d_name]['holiday'] += w['summary']['holiday']
        dept_map[d_name]['comp_off'] += w['summary']['comp_off']
        dept_map[d_name]['payable_days'] += round(w['summary']['payable_days'], 1)

    conn.close()
    return {
        'year': year,
        'month': month,
        'days': days_list,
        'days_meta': days_meta,
        'holidays': month_holidays,
        'workers': matrix_workers,
        'departments': all_departments,
        'department_summary': list(dept_map.values()),
        'selected_department': department or 'ALL'
    }

def get_weekly_attendance_matrix(date_str=None):
    """
    Computes weekly attendance matrix and statistics for the 7-day period (Monday to Sunday)
    containing target date_str. Official holidays are recognized without absent penalties.
    """
    conn = get_connection()
    c = conn.cursor()

    workers = get_workers()
    shifts_map = {s['id']: s for s in get_shifts()}

    if not date_str:
        date_str = date.today().strftime('%Y-%m-%d')

    target_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
    # Monday of the week
    start_dt = target_dt - timedelta(days=target_dt.weekday())
    end_dt = start_dt + timedelta(days=6)

    leaves_map = get_approved_leaves_map(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))
    holidays_map = get_holidays_map(start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days_info = []
    for i in range(7):
        d = start_dt + timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        h_info = holidays_map.get(d_str)
        days_info.append({
            'date': d_str,
            'day_num': d.day,
            'day_name': day_names[i],
            'display': f"{day_names[i]} {d.strftime('%d/%m')}",
            'is_sunday': (i == 6),
            'is_holiday': bool(h_info),
            'holiday_name': h_info['name'] if h_info else ''
        })

    # Fetch all punches for this 7-day week
    start_ts = f"{start_dt.strftime('%Y-%m-%d')} 00:00:00"
    end_ts = f"{end_dt.strftime('%Y-%m-%d')} 23:59:59"

    c.execute("""
        SELECT enroll_number, event_timestamp, verify_mode, is_manual
        FROM attendance_logs
        WHERE event_timestamp >= ? AND event_timestamp <= ?
        ORDER BY event_timestamp ASC
    """, (start_ts, end_ts))
    rows = c.fetchall()

    daily_punches = {}
    for r in rows:
        enr = r['enroll_number']
        dt_str = r['event_timestamp']
        date_part = dt_str.split(' ')[0]
        key = (enr, date_part)
        if key not in daily_punches:
            daily_punches[key] = []
        daily_punches[key].append(dt_str)

    today = date.today()
    weekly_workers = []

    total_week_present = 0
    total_week_halfday = 0
    total_week_late = 0
    total_week_holiday = 0
    total_week_mins = 0

    for w in workers:
        enr = w['enroll_number']
        shift = shifts_map.get(w['shift_id'])

        worker_days = {}
        p_count = 0
        hd_count = 0
        a_count = 0
        lv_count = 0
        hld_count = 0
        co_count = 0
        off_count = 0
        worker_total_mins = 0

        for d_obj in days_info:
            cur_d_str = d_obj['date']
            cur_dt = datetime.strptime(cur_d_str, '%Y-%m-%d').date()
            key = (enr, cur_d_str)
            punches = daily_punches.get(key, [])
            leave_info = leaves_map.get((enr, cur_d_str))
            holiday_info = holidays_map.get(cur_d_str)

            first_in = '-'
            last_out = '-'
            duration_mins = 0
            duration_str = '-'
            status = '-'
            is_late = False

            if cur_dt > today:
                if holiday_info:
                    status = 'HLD'
                    hld_count += 1
                    total_week_holiday += 1
                    duration_str = holiday_info.get('name', 'Official Holiday')
                elif cur_dt.weekday() == 6:
                    status = 'OFF'
                    off_count += 1
                    duration_str = 'Weekly Off'
                elif leave_info:
                    if leave_info.get('leave_type_code') == 'COMP':
                        status = 'CO'
                        co_count += 1
                        duration_str = 'Compensatory Off'
                    else:
                        status = 'LV'
                        lv_count += 1
                        duration_str = leave_info.get('leave_type_name', 'Leave')
                else:
                    status = '-'
            elif punches:
                first_in = punches[0].split(' ')[1][:5]
                t1 = datetime.strptime(punches[0], '%Y-%m-%d %H:%M:%S')

                has_out_punch = (len(punches) > 1 and punches[-1] != punches[0])
                if has_out_punch:
                    last_out = punches[-1].split(' ')[1][:5]
                    t2 = datetime.strptime(punches[-1], '%Y-%m-%d %H:%M:%S')
                    duration_mins = max(0, int((t2 - t1).total_seconds() / 60))
                    h = duration_mins // 60
                    m = duration_mins % 60
                    duration_str = f"{h}h {m}m"
                    is_in_progress = False
                else:
                    if cur_dt == today:
                        last_out = 'In Progress'
                        now_dt = datetime.now()
                        duration_mins = max(0, int((now_dt - t1).total_seconds() / 60))
                        h = duration_mins // 60
                        m = duration_mins % 60
                        duration_str = f"{h}h {m}m (Active)"
                        is_in_progress = True
                    else:
                        last_out = 'No Out'
                        duration_mins = 0
                        duration_str = 'Single Punch'
                        is_in_progress = False

                worker_total_mins += duration_mins
                total_week_mins += duration_mins

                if cur_dt.weekday() == 6:
                    status = 'W-OFF'
                    p_count += 1
                    total_week_present += 1
                    duration_str += ' (Comp-Off Earned)'
                elif holiday_info:
                    status = 'P'
                    p_count += 1
                    total_week_present += 1
                    duration_str += f" ({holiday_info.get('name', 'Holiday')})"
                else:
                    is_flex = bool(w.get('is_flexible', 0))
                    status = evaluate_daily_status(first_in, shift, is_flexible=is_flex, duration_mins=duration_mins, is_in_progress=is_in_progress)
                    if status == 'A' and len(punches) > 0:
                        status = 'P' if is_in_progress else 'HD'

                    if shift and not is_flex:
                        punch_m = parse_time(first_in)
                        shift_m = parse_time(shift['start_time'])
                        grace = shift.get('grace_period_mins') or 15
                        if punch_m > shift_m + grace:
                            is_late = True
                            total_week_late += 1

                    if status == 'P':
                        p_count += 1
                        total_week_present += 1
                    elif status == 'HD':
                        hd_count += 1
                        total_week_halfday += 1
                    else:
                        a_count += 1
            elif leave_info:
                if leave_info.get('leave_type_code') == 'COMP':
                    status = 'CO'
                    co_count += 1
                    duration_str = 'Compensatory Off'
                else:
                    status = 'LV'
                    lv_count += 1
                    duration_str = leave_info.get('leave_type_name', 'Leave')
            elif holiday_info:
                # Official Government / Company Holiday: NOT marked as absent!
                status = 'HLD'
                hld_count += 1
                total_week_holiday += 1
                duration_str = holiday_info.get('name', 'Official Holiday')
            elif cur_dt.weekday() == 6:
                status = 'OFF'
                off_count += 1
                duration_str = 'Weekly Off'
            else:
                status = 'A'
                a_count += 1

            worker_days[cur_d_str] = {
                'status': status,
                'first_in': first_in,
                'last_out': last_out,
                'duration': duration_str,
                'duration_mins': duration_mins,
                'is_late': is_late,
                'punches_count': len(punches),
                'holiday_name': holiday_info.get('name', '') if holiday_info else '',
                'leave_reason': leave_info.get('reason', '') if leave_info else '',
                'leave_type_code': leave_info.get('leave_type_code', '') if leave_info else '',
                'leave_color': leave_info.get('leave_color', '') if leave_info else '',
                'leave_name': leave_info.get('leave_type_name', '') if leave_info else ''
            }

        w_hours = worker_total_mins // 60
        w_mins = worker_total_mins % 60
        payable_days = p_count + (hd_count * 0.5) + lv_count + hld_count + co_count

        weekly_workers.append({
            'worker_id': w['id'],
            'enroll_number': enr,
            'name': w['name'],
            'department': w['department'],
            'shift_name': ('Flexible Schedule' if w.get('is_flexible') else (w['shift_name'] or 'Not Assigned')),
            'is_flexible': 1 if w.get('is_flexible') else 0,
            'photo': w.get('photo') or '',
            'days': worker_days,
            'total_worked_str': f"{w_hours}h {w_mins}m",
            'total_mins': worker_total_mins,
            'summary': {
                'present': p_count,
                'half_day': hd_count,
                'absent': a_count,
                'leave': lv_count,
                'holiday': hld_count,
                'comp_off': co_count,
                'off': off_count,
                'payable_days': payable_days
            }
        })

    conn.close()

    total_possible_shifts = len(workers) * 6 # 6 work days (excluding Sunday)
    attendance_rate = 0
    if total_possible_shifts > 0:
        effective_present = total_week_present + (total_week_halfday * 0.5) + total_week_holiday
        attendance_rate = round((effective_present / total_possible_shifts) * 100, 1)

    co_hours = total_week_mins // 60
    co_mins = total_week_mins % 60

    return {
        'start_date': start_dt.strftime('%Y-%m-%d'),
        'end_date': end_dt.strftime('%Y-%m-%d'),
        'days': days_info,
        'workers': weekly_workers,
        'stats': {
            'total_present': total_week_present,
            'total_halfday': total_week_halfday,
            'total_late': total_week_late,
            'total_holiday': total_week_holiday,
            'total_company_hours': f"{co_hours}h {co_mins}m",
            'attendance_rate': f"{attendance_rate}%",
            'total_workers': len(workers)
        }
    }
def save_attendance_logs(device_id, logs):
    if not logs:
        return 0
    conn = get_connection()
    c = conn.cursor()
    inserted = 0
    cur_year = date.today().year
    default_pw_hash = generate_password_hash('worker123')

    # Cache existing enroll numbers to optimize batch inserts
    c.execute("SELECT enroll_number FROM workers")
    known_enrolls = {row['enroll_number'] for row in c.fetchall()}

    for l in logs:
        enr = int(l['enroll_number'])
        # If worker is not registered yet, auto-provision
        if enr not in known_enrolls:
            try:
                c.execute("""
                    INSERT INTO workers (enroll_number, name, department, shift_id, joining_date, password_hash, email, is_active)
                    VALUES (?, ?, 'General', 1, ?, ?, ?, 1)
                """, (enr, f"Worker #{enr}", date.today().strftime('%Y-%m-%d'), default_pw_hash, f"worker{enr}@company.local"))
                new_wid = c.lastrowid
                known_enrolls.add(enr)

                # Initialize leave quotas for new worker
                c.execute("SELECT code, default_days FROM leave_types WHERE is_active = 1")
                for lt in c.fetchall():
                    c.execute("""
                        INSERT OR IGNORE INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                        VALUES (?, ?, ?, ?, 0)
                    """, (new_wid, lt['code'], cur_year, lt['default_days']))
            except Exception:
                pass

        try:
            c.execute("""
                INSERT OR IGNORE INTO attendance_logs (device_id, enroll_number, event_timestamp, verify_mode, punch_type)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, enr, l['timestamp'], l.get('verify_mode', 1), l.get('in_out_mode', 0)))
            if c.rowcount > 0:
                inserted += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    return inserted

def sync_enrolled_workers(workers_list):
    """
    Synchronizes workers enrolled on the physical biometric device into the database.
    workers_list is a list of dicts: [{'enroll_number': int, 'name': str, ...}]
    Returns dict: {'added': count, 'updated': count, 'total': len(workers_list)}
    """
    if not workers_list:
        return {'added': 0, 'updated': 0, 'total': 0}

    conn = get_connection()
    c = conn.cursor()
    added_count = 0
    updated_count = 0
    cur_year = date.today().year
    default_pw = generate_password_hash('worker123')

    # Get active leave types
    c.execute("SELECT code, default_days FROM leave_types WHERE is_active = 1")
    active_lts = c.fetchall()

    for w in workers_list:
        enr = int(w['enroll_number'])
        name_from_device = (w.get('name') or '').strip()

        c.execute("SELECT id, name FROM workers WHERE enroll_number = ?", (enr,))
        existing = c.fetchone()

        if existing:
            wid = existing['id']
            curr_name = (existing['name'] or '').strip()
            # If name from device is provided and previous name was generic or empty, update it
            if name_from_device and (curr_name.startswith('Worker #') or not curr_name):
                c.execute("UPDATE workers SET name = ? WHERE id = ?", (name_from_device, wid))
                updated_count += 1
            else:
                updated_count += 1

            # Ensure leave quotas are provisioned for current year
            for lt in active_lts:
                c.execute("""
                    INSERT OR IGNORE INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                    VALUES (?, ?, ?, ?, 0)
                """, (wid, lt['code'], cur_year, lt['default_days']))
        else:
            final_name = name_from_device if name_from_device else f"Worker #{enr}"
            c.execute("""
                INSERT INTO workers (enroll_number, name, department, shift_id, joining_date, password_hash, email, is_active)
                VALUES (?, ?, 'General', 1, ?, ?, ?, 1)
            """, (enr, final_name, date.today().strftime('%Y-%m-%d'), default_pw, f"worker{enr}@company.local"))
            new_wid = c.lastrowid
            added_count += 1

            for lt in active_lts:
                c.execute("""
                    INSERT OR IGNORE INTO worker_leave_balances (worker_id, leave_type_code, year, allocated_days, used_days)
                    VALUES (?, ?, ?, ?, 0)
                """, (new_wid, lt['code'], cur_year, lt['default_days']))

    conn.commit()
    conn.close()
    return {'added': added_count, 'updated': updated_count, 'total': len(workers_list)}

def get_device_config(device_id=1):
    """Retrieves hardware biometric device network and connection settings"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    # Default fallback
    return {
        'id': 1,
        'serial_number': 'SBXPC-DEV-001',
        'device_name': 'Front Counter Biometric Terminal',
        'ip_address': '192.168.1.224',
        'port': 5005,
        'machine_id': 1,
        'sync_interval_mins': 2,
        'last_status': 'READY'
    }

def update_device_config(device_id=1, ip_address=None, port=None, machine_id=None, device_name=None, serial_number=None, sync_interval_mins=None):
    """Updates device hardware connection parameters and sync schedule"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO devices (id, serial_number, device_name, ip_address, port, machine_id, sync_interval_mins, last_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'READY')
        """, (device_id, serial_number or 'SBXPC-DEV-001', device_name or 'Front Counter Biometric Terminal',
              ip_address or '192.168.1.224', int(port or 5005), int(machine_id or 1), int(sync_interval_mins or 2)))
    else:
        updates = []
        params = []
        if ip_address is not None:
            updates.append("ip_address = ?")
            params.append(ip_address.strip())
        if port is not None:
            updates.append("port = ?")
            params.append(int(port))
        if machine_id is not None:
            updates.append("machine_id = ?")
            params.append(int(machine_id))
        if device_name is not None:
            updates.append("device_name = ?")
            params.append(device_name.strip())
        if serial_number is not None:
            updates.append("serial_number = ?")
            params.append(serial_number.strip())
        if sync_interval_mins is not None:
            updates.append("sync_interval_mins = ?")
            params.append(int(sync_interval_mins))
        if updates:
            params.append(device_id)
            c.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return get_device_config(device_id)

def log_sync(records_fetched, status, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sync_history (records_fetched, status, message)
        VALUES (?, ?, ?)
    """, (records_fetched, status, message))
    c.execute("""
        UPDATE devices SET last_sync_time = CURRENT_TIMESTAMP, last_status = ? WHERE id = 1
    """, (status,))
    conn.commit()
    conn.close()

def get_sync_history(limit=15):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, sync_time, records_fetched, status, message
        FROM sync_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- Manual Check-In & Check-Out -----------------

def record_manual_punch(enroll_number, punch_type, event_timestamp=None, recorded_by_user_id=None, reason=None, remarks=None, verify_mode=0):
    """
    Records a manual attendance punch (Check-In or Check-Out) for a worker when biometric terminal is offline/failed.
    punch_type: 0 for Check-In, 1 for Check-Out.
    """
    conn = get_connection()
    c = conn.cursor()

    # Validate worker
    c.execute("SELECT id, enroll_number, name, shift_id FROM workers WHERE enroll_number = ? AND is_active = 1", (enroll_number,))
    worker = c.fetchone()
    if not worker:
        conn.close()
        return False, f"Worker with Enroll ID '{enroll_number}' not found"

    # Default to current time if not provided
    if not event_timestamp:
        event_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        try:
            # Normalize to YYYY-MM-DD HH:MM:SS
            event_timestamp = event_timestamp.strip()
            if len(event_timestamp) == 16: # YYYY-MM-DD HH:MM
                event_timestamp += ":00"
            elif len(event_timestamp) == 10: # YYYY-MM-DD
                event_timestamp += " " + datetime.now().strftime('%H:%M:%S')
            dt = datetime.strptime(event_timestamp, '%Y-%m-%d %H:%M:%S')
            event_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            conn.close()
            return False, f"Invalid punch timestamp format: {e}"

    full_reason = reason or "Manual Biometric Override"
    if remarks and remarks.strip():
        full_reason = f"{full_reason} - {remarks.strip()}"

    p_type = 1 if str(punch_type) in ('1', 'out', 'OUT', 'check_out', 'CHECK_OUT') else 0

    try:
        # Check if identical punch already exists
        c.execute("""
            SELECT id FROM attendance_logs 
            WHERE enroll_number = ? AND event_timestamp = ?
        """, (enroll_number, event_timestamp))
        existing = c.fetchone()
        if existing:
            conn.close()
            return False, f"A punch for Worker #{enroll_number} already exists at {event_timestamp}"

        try:
            vm_int = int(verify_mode) if verify_mode is not None else 0
        except (ValueError, TypeError):
            vm_int = 0

        c.execute("""
            INSERT INTO attendance_logs (
                device_id, enroll_number, event_timestamp, punch_type, verify_mode,
                is_manual, recorded_by_user_id, manual_reason
            ) VALUES (0, ?, ?, ?, ?, 1, ?, ?)
        """, (enroll_number, event_timestamp, p_type, vm_int, recorded_by_user_id, full_reason))
        punch_id = c.lastrowid
        conn.commit()
        conn.close()

        punch_label = "Check-Out" if p_type == 1 else "Check-In"
        return True, {
            'punch_id': punch_id,
            'enroll_number': enroll_number,
            'worker_name': worker['name'],
            'punch_type': p_type,
            'punch_label': punch_label,
            'timestamp': event_timestamp,
            'reason': full_reason,
            'message': f"Manual {punch_label} recorded successfully for {worker['name']} (#{enroll_number}) at {event_timestamp}"
        }
    except Exception as e:
        conn.close()
        return False, f"Failed to record manual punch: {e}"

def get_manual_punches(limit=50, target_date=None):
    """
    Returns recent manual punches with worker and admin details.
    """
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT al.id, al.enroll_number, al.event_timestamp, al.punch_type, al.created_at,
               al.manual_reason, al.recorded_by_user_id,
               w.name as worker_name, w.department,
               s.name as shift_name,
               u.full_name as recorded_by_name, u.username as recorded_by_username
        FROM attendance_logs al
        JOIN workers w ON al.enroll_number = w.enroll_number
        LEFT JOIN shifts s ON w.shift_id = s.id
        LEFT JOIN users u ON al.recorded_by_user_id = u.id
        WHERE al.is_manual = 1
    """
    params = []
    if target_date:
        query += " AND strftime('%Y-%m-%d', al.event_timestamp) = ?"
        params.append(target_date)

    query += " ORDER BY al.event_timestamp DESC, al.id DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def delete_manual_punch(punch_id):
    """
    Deletes a manual punch entry.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, enroll_number, event_timestamp FROM attendance_logs WHERE id = ? AND is_manual = 1", (punch_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Manual punch record not found or not a manual entry"

    c.execute("DELETE FROM attendance_logs WHERE id = ? AND is_manual = 1", (punch_id,))
    conn.commit()
    conn.close()
    return True, f"Manual punch #{punch_id} removed successfully"

def get_worker_today_punch_status(identifier, target_date=None):
    """
    Fetches worker information, today's punches, and current check-in/out status.
    """
    if not target_date:
        target_date = date.today().strftime('%Y-%m-%d')

    worker = get_worker_by_enroll_or_id(identifier)
    if not worker:
        return None

    enroll_number = worker['enroll_number']
    conn = get_connection()
    c = conn.cursor()

    start_ts = f"{target_date} 00:00:00"
    end_ts = f"{target_date} 23:59:59"

    c.execute("""
        SELECT al.id, al.event_timestamp, al.punch_type, al.verify_mode, al.is_manual, al.manual_reason,
               u.full_name as recorded_by_name
        FROM attendance_logs al
        LEFT JOIN users u ON al.recorded_by_user_id = u.id
        WHERE al.enroll_number = ? AND al.event_timestamp >= ? AND al.event_timestamp <= ?
        ORDER BY al.event_timestamp ASC
    """, (enroll_number, start_ts, end_ts))
    punches = [dict(r) for r in c.fetchall()]
    conn.close()

    # Determine status
    if not punches:
        status = 'NOT_CHECKED_IN'
        status_label = 'Not Checked In Today'
        next_action = 'CHECK_IN'
        first_in = None
        last_out = None
    elif len(punches) == 1:
        status = 'CHECKED_IN'
        first_in = punches[0]['event_timestamp'].split(' ')[1][:5]
        last_out = None
        status_label = f"Checked In at {first_in}"
        next_action = 'CHECK_OUT'
    else:
        status = 'CHECKED_OUT'
        first_in = punches[0]['event_timestamp'].split(' ')[1][:5]
        last_out = punches[-1]['event_timestamp'].split(' ')[1][:5]
        status_label = f"Checked Out (In: {first_in}, Out: {last_out})"
        next_action = 'CHECK_IN'

    return {
        'worker': worker,
        'date': target_date,
        'punches': punches,
        'status': status,
        'status_label': status_label,
        'next_action': next_action,
        'first_in': first_in,
        'last_out': last_out,
        'total_punches': len(punches)
    }

