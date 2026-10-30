# ⏱️ Workforce Attendance & Biometric Management System
### *Sai Krishna Enterprises - Enterprise Workforce Operating System*

[![Python](https://img.shields.io/badge/Python-3.10%2B%20(64--bit)-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-lightgrey.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Hardware](https://img.shields.io/badge/Hardware-SBXPC%20%7C%20ZKTeco-orange.svg)](https://www.zkteco.com/)
[![Themes](https://img.shields.io/badge/Themes-6%20Production%20Modes-purple.svg)](#-visual-themes--user-preferences)
[![License](https://img.shields.io/badge/License-Proprietary%20Enterprise-red.svg)](#-enterprise-licensing-client)

---

## 📑 Table of Contents

- [🔍 System Overview](#-system-overview)
- [📦 Requirements & Dependencies (`requirements.txt`)](#-requirements--dependencies-requirementstxt)
  - [Third-Party Package Breakdown](#third-party-package-breakdown)
  - [Python Standard Library Modules Utilized](#python-standard-library-modules-utilized)
  - [⚠️ Why 64-Bit Python is Mandatory](#️-why-64-bit-python-is-mandatory)
- [🚀 How to Run the Code (Step-by-Step)](#-how-to-run-the-code-step-by-step)
  - [Prerequisites Checklist](#prerequisites-checklist)
  - [Option 1: One-Click Automated Setup & Launch (Recommended)](#option-1-one-click-automated-setup--launch-recommended)
  - [Option 2: Fast Daily Startup](#option-2-fast-daily-startup)
  - [Option 3: Manual Terminal / PowerShell Launch](#option-3-manual-terminal--powershell-launch)
  - [Option 4: Running with Python Virtual Environment (`venv`)](#option-4-running-with-python-virtual-environment-venv)
- [🔑 User Roles & Default Login Credentials](#-user-roles--default-login-credentials)
- [📡 Biometric Hardware Terminal Integration](#-biometric-hardware-terminal-integration)
- [🎨 Visual Theme Studio (6 Production Modes)](#-visual-theme-studio-6-production-modes)
- [✨ Core Features & Functional Modules](#-core-features--functional-modules)
  - [1. Executive Overview & Live Workforce Cards](#1-executive-overview--live-workforce-cards)
  - [2. Monthly Attendance Matrix & Timesheet](#2-monthly-attendance-matrix--timesheet)
  - [3. Weekly Timesheet & Attendance Register](#3-weekly-timesheet--attendance-register)
  - [4. Daily Biometric Punch Timelines](#4-daily-biometric-punch-timelines)
  - [5. Manual Punch Override (Hardware Fallback)](#5-manual-punch-override-hardware-fallback)
  - [6. Dynamic Department Studio](#6-dynamic-department-studio)
  - [7. Worker Studio & Biometric Enrollment](#7-worker-studio--biometric-enrollment)
  - [8. Shift Studio & Flexible Working Policy](#8-shift-studio--flexible-working-policy)
  - [9. Official Holidays & Government Calendar](#9-official-holidays--government-calendar)
  - [10. Leaves Management System](#10-leaves-management-system)
  - [11. Sub-Admin RBAC Manager](#11-sub-admin-rbac-manager)
  - [12. Hardware Diagnostics & Automated Sync](#12-hardware-diagnostics--automated-sync)
  - [13. Enterprise Licensing Client](#13-enterprise-licensing-client)
  - [14. Worker Self-Service Portal](#14-worker-self-service-portal)
- [📊 Excel Exporters & Reporting](#-excel-exporters--reporting)
- [🧪 Automated Testing Suite](#-automated-testing-suite)
- [🔌 REST API Endpoints Reference](#-rest-api-endpoints-reference)
- [🗄 Database Architecture (`attendance.db`)](#-database-architecture-attendancedb)
- [📁 Project Directory Structure](#-project-directory-structure)
- [🔧 Troubleshooting & Frequently Asked Questions](#-troubleshooting--frequently-asked-questions)

---

## 🔍 System Overview

The **Workforce Attendance & Biometric Management System** is a standalone, local-first enterprise software solution engineered for **Sai Krishna Enterprises**. It connects directly to hardware biometric attendance terminals (fingerprint, face recognition, RFID card, and PIN) over local TCP/IP networks to deliver real-time attendance tracking, shift policy enforcement, automated timesheet generation, leave workflows, and color-coded payroll Excel exports.

### Key Technical Specs:
- **Server Port**: `5000` (Accessible at [`http://localhost:5000`](http://localhost:5000))
- **Backend Architecture**: Python 3.10+ (64-bit), Flask WSGI framework, SQLite 3 embedded database.
- **Frontend Architecture**: Modern Single-Page Application (SPA) built with Vanilla JavaScript, Bootstrap 5, Bootstrap Icons, and CSS3 custom properties with zero heavy build steps.
- **Biometric SDK**: Native 64-bit Windows dynamic link libraries (`SBXPCDLL64.dll`, `SBPCCOMM64.dll`, `GEN_FONT64.dll`) interfacing directly over TCP/IP socket port `5005`.
- **Database Engine**: Zero-configuration, ACID-compliant local SQLite database (`attendance.db`).

---

## 📦 Requirements & Dependencies (`requirements.txt`)

The application dependencies are pinned in [`requirements.txt`](file:///c:/Users/abhay/Downloads/attendance_app%20%281%29/attendance_app/requirements.txt) to guarantee complete reproducibility and long-term enterprise runtime stability.

```txt
# ==============================================================================
# Workforce Attendance System - Python Dependencies
# ==============================================================================
# Environment Requirement: Python 3.10+ (64-bit required for Windows Biometric SDK DLLs)
# Installation Command:    pip install -r requirements.txt
# ==============================================================================

# Core Web Framework & WSGI HTTP Engine
Flask>=3.0.0
Werkzeug>=3.0.0

# HTTP Client for Licensing Verification & Remote Heartbeat
requests>=2.31.0

# Enterprise Payroll Timesheet & Attendance Matrix Excel (.xlsx) Generation
openpyxl>=3.1.2

# Calendar Calculations, Date Parsing, and Timesheet Period Calculations
python-dateutil>=2.8.2
```

### Third-Party Package Breakdown

| Package | Minimum Version | Category | Critical Purpose in Application |
| :--- | :--- | :--- | :--- |
| **`Flask`** | `3.0.0` | Web Framework | Powers the local HTTP server, dynamic API routes, session management, template rendering, and error handling. |
| **`Werkzeug`** | `3.0.0` | WSGI Utility / Security | Provides PBKDF2-SHA256 password hashing for administrators/workers, secure filename sanitization for profile photos, and HTTP request parsing. |
| **`requests`** | `2.31.0` | Networking | Manages outbound HTTP handshakes with the external licensing server (`license_client.py`) for activation, heartbeats, and token reverification. |
| **`openpyxl`** | `3.1.2` | Excel Generation | Generates multi-tab Excel workbooks (`.xlsx`) with custom corporate headers, font weights, cell fills, borders, and conditional cell highlights for Monthly Matrices and Weekly Timesheets. |
| **`python-dateutil`** | `2.8.2` | DateTime Utilities | Performs date-range parsing, leap year adjustments, weekly shift bounds, and calendar matrix arithmetic. |

### Python Standard Library Modules Utilized
In addition to the third-party dependencies above, the application leverages built-in Python modules:
- **`ctypes` & `ctypes.wintypes`**: Loads and invokes functions from native 64-bit C/C++ biometric DLLs (`SBXPCDLL64.dll`, `SBPCCOMM64.dll`).
- **`sqlite3`**: Manages all local relational data queries, transactions, foreign keys, and migrations.
- **`threading`**: Runs background daemons for periodic biometric machine log polling (every 2 minutes) without blocking UI responses.
- **`socket` & `struct`**: Low-level TCP socket utilities for network device handshakes.
- **`hashlib`**: Machine fingerprint calculation for software licensing.

### ⚠️ Why 64-Bit Python is Mandatory

The biometric terminal hardware driver libraries located in `native/` (`SBXPCDLL64.dll`, `SBPCCOMM64.dll`, and `GEN_FONT64.dll`) are compiled as **native 64-bit PE binaries (x86_64)**.

> [!CAUTION]
> If you run the application with **32-bit Python**, the Windows kernel will reject loading the 64-bit DLLs with:
> `OSError: [WinError 193] %1 is not a valid Win32 application`.
> 
> **Always verify you are using 64-bit Python:**
> ```powershell
> python -c "import sys; print('Architecture:', '64-bit' if sys.maxsize > 2**32 else '32-bit')"
> ```
> *If it returns `32-bit`, download and install the official 64-bit Python installer from [python.org](https://www.python.org/downloads/).*

---

## 🚀 How to Run the Code (Step-by-Step)

### Prerequisites Checklist
1. **Operating System**: Windows 10, Windows 11, or Windows Server (required for native Windows biometric DLL drivers).
2. **Python**: **Python 3.10+ (64-bit)** with `pip` added to system PATH.
3. **Network**: Physical biometric terminal connected via Ethernet to your local switch/router (default terminal IP: `192.168.1.224`). *Note: If no physical terminal is attached, the app automatically runs in offline simulation mode without errors.*

---

### Option 1: One-Click Automated Setup & Launch (Recommended)

The easiest method for any user or administrator is running [`setup.bat`](file:///c:/Users/abhay/Downloads/attendance_app%20%281%29/attendance_app/setup.bat):

1. Open PowerShell, Command Prompt, or File Explorer in the application folder:
   ```powershell
   .\setup.bat
   ```
2. **What `setup.bat` executes automatically:**
   - Verifies Python installation in system PATH.
   - Installs all dependencies via `python -m pip install -r requirements.txt`.
   - Initializes `attendance.db` schema and seeds default admin credentials and shifts.
   - Waits 3 seconds and automatically opens **`http://localhost:5000`** in your default web browser.
   - Starts the Flask server process.

---

### Option 2: Fast Daily Startup

Once `setup.bat` has been run the first time, use [`run.bat`](file:///c:/Users/abhay/Downloads/attendance_app%20%281%29/attendance_app/run.bat) for everyday instant launching:

```powershell
.\run.bat
```
*Launches the server and immediately pops up `http://localhost:5000` in your web browser.*

---

### Option 3: Manual Terminal / PowerShell Launch

If you prefer full control via the command line:

1. **Open PowerShell or CMD** in the project directory:
   ```powershell
   cd "c:\Users\abhay\Downloads\attendance_app (1)\attendance_app"
   ```

2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Initialize the Database (First-Time Only)**:
   ```powershell
   python -c "import database as db; db.init_db(); db.seed_default_data(); print('Database ready.')"
   ```

4. **Start the Web Application**:
   ```powershell
   python app.py
   ```

5. **Open in Web Browser**:
   Navigate to 👉 **[http://localhost:5000](http://localhost:5000)**

---

### Option 4: Running with Python Virtual Environment (`venv`)

For isolated production deployments:

1. Create a 64-bit virtual environment:
   ```powershell
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```powershell
   # In PowerShell:
   .\venv\Scripts\Activate.ps1

   # In Command Prompt (cmd):
   .\venv\Scripts\activate.bat
   ```

3. Install requirements inside the environment:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run the application:
   ```powershell
   python app.py
   ```

---

## 🔑 User Roles & Default Login Credentials

The application features built-in Role-Based Access Control (RBAC):

| Role | Access Level | Default Username | Default Password | Description & Privileges |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | Full Master Access | `admin` | `admin123` | Complete system privileges: department management, shift rules, worker studio, manual punches, RBAC, licensing, themes, and biometric diagnostics. |
| **Sub-Admin** | Granular Privileges | *(Assigned by Admin)* | *(Set by Admin)* | Manager or HR accounts with customizable privileges configured via the Sub-Admin RBAC Manager. |
| **Worker (Self-Service)**| Employee Portal | `1` or `worker_1` | `worker123` | Employee access: personal monthly attendance calendar, leave balance inspection, leave requests, and raw punch history. |

---

## 📡 Biometric Hardware Terminal Integration

The application interfaces directly with **SBXPC / ZKTeco** compatible hardware terminals.

- **Driver DLLs**: Stored in [`native/`](file:///c:/Users/abhay/Downloads/attendance_app%20%281%29/attendance_app/native/):
  - `SBXPCDLL64.dll`: Core biometric algorithm & command dispatch engine.
  - `SBPCCOMM64.dll`: Low-level TCP/IP socket network driver.
  - `GEN_FONT64.dll`: Terminal LCD font rendering library.
- **Factory Default Network Configuration**:
  - **Terminal IP Address**: `192.168.1.224`
  - **TCP Communication Port**: `5005`
  - **Machine ID**: `1`
- **Thread-Safe Architecture**: All SDK socket operations are wrapped in an internal Python mutex (`sdk_lock` in `biometric.py`) to prevent port conflicts or race condition crashes during concurrent web requests.
- **Automated Background Polling**: A dedicated daemon thread periodically queries the terminal (default every 2 minutes, customizable in settings) to automatically download new punches.
- **Intelligent Offline Simulation Fallback**: If the hardware terminal is unplugged, powered off, or on another subnet, the application gracefully continues functioning in offline simulation mode without hanging or throwing unhandled errors.

---

## 🎨 Visual Theme Studio (6 Production Modes)

The system provides 6 tailored, high-contrast visual themes switchable with one click from the persistent top navigation bar or the **Theme Studio** in Admin Settings:

| Theme Name | Key | Background | Accent Color | Design Aesthetics & Contrast Compliance |
| :--- | :--- | :--- | :--- | :--- |
| **Midnight Dark** | `dark` | `#000000` | `#3b82f6` (Blue) | Deep black canvas with neon glowing KPI statistics and crisp white text. |
| **Industrial Slate** | `slate` | `#0b1120` | `#38bdf8` (Sky) | Technical dark blue-slate for engineering environments. |
| **Clean Paper Light** | `light` | `#ffffff` | `#2563eb` (Blue) | Crisp, professional pure-white paper layout with deep slate text. |
| **Warm Executive Cream** | `cream` | `#fbf9f5` | `#b45309` (Amber/Cognac) | Soft ivory card surfaces (`#ffffff`), warm champagne sidebar (`#f5f0e6`), and deep stone text (`#1c1917`). **Exceeds WCAG AAA (≥ 7:1) contrast ratio** across all 15 modals, inputs, and tables. |
| **Cyber Emerald** | `emerald` | `#03140d` | `#10b981` (Emerald) | High-contrast deep forest green with vivid mint highlights. |
| **Royal Violet** | `violet` | `#0c0919` | `#8b5cf6` (Purple) | Midnight amethyst theme with royal lavender accents. |

---

## ✨ Core Features & Functional Modules

### 1. Executive Overview & Live Workforce Cards
- **Live Worker Presence Cards**: High-definition employee cards with real-time status indicators (pulsing green for clocked-in, blue for completed shift, red for absent).
- **Dual-Cell Punch Timelines**: Clear split-cell timestamps showing exact **Check-In** and **Check-Out** times with biometric verification badges:
  - 📸 Face Recognition (`bi-person-bounding-box`)
  - 👆 Fingerprint Scan (`bi-fingerprint`)
  - 💳 RFID Proximity Card (`bi-credit-card-2-front`)
  - ✍️ Manual Admin Override (`bi-pencil-square`)
- **Executive KPI Cards**: Real-time counter cards showing Total Workforce, Present Today, Late/Half-Day, and Absent Today.
- **Worker Detail Drawer**: Slide-out modal detailing all daily punch logs, total shift duration, and active status.

### 2. Monthly Attendance Matrix & Timesheet
- **Sticky Frozen Columns**: Employee ID and Name remain permanently pinned while scrolling horizontally through days 1–31.
- **High-Contrast Status Pills**:
  - `P` (Present - Green)
  - `HD` (Half-Day / Late Arrival - Amber)
  - `A` (Absent - Red)
  - `LV` (Approved Leave - Purple)
  - `HLD` (Official Holiday - Cyan)
  - `OFF` (Sunday / Scheduled Off - Slate)
- **Live Summary Totals**: Total Present, Half-Days, Absent, Leaves, and payable working days.

### 3. Weekly Timesheet & Attendance Register
- Consolidated 7-day Monday-to-Sunday view.
- Tracks daily check-in, check-out, and cumulative hours worked per employee.
- One-click weekly Excel timesheet download.

### 4. Daily Biometric Punch Timelines
- Complete chronological audit log of all punches.
- **Real-Time Instant Search**: Filter instantly by Employee Name or Enroll ID as you type.
- Historical date picker to inspect punches for any past date.

### 5. Manual Punch Override (Hardware Fallback)
- Allows administrators to log manual check-ins/check-outs when workers forget their RFID cards or during hardware maintenance.
- Requires selecting verification mode and logging a mandatory audit reason.

### 6. Dynamic Department Studio
- Create, rename, and manage company departments (e.g. Production, QA, Packing, Management).
- Real-time worker count per department.
- **Safe Deletion & Reassignment**: When deleting a department, the system prompts you to safely reassign all existing employees to an alternate active department, preventing orphaned records.

### 7. Worker Studio & Biometric Enrollment
- Register new employees with Enroll Number, Full Name, Department, Shift, Phone, and Email.
- Upload worker profile photos with automatic thumbnail rendering.
- Toggle individual workers between **Fixed Shift** and **Flexible Working Policy**.

### 8. Shift Studio & Flexible Working Policy
- Define shift schedules with custom Start Time, End Time, Grace Periods (e.g., 15 mins), and Half-Day Thresholds (e.g., 120 mins).
- Company-wide Flexible Working Hours configuration for flex-time staff.

### 9. Official Holidays & Government Calendar
- Configure official national, state, and company holidays.
- **Automatic Penalty Excuse**: On official holidays, employees without punches are automatically marked as `HLD` rather than Absent, preserving their paid status.
- Automatic synchronization with monthly payroll matrices and weekly registers.

### 10. Leaves Management System
- Configure leave categories (`Casual Leave`, `Sick Leave`, `Privilege Leave`).
- Manage annual quotas and real-time balances.
- Review, approve, or reject employee leave applications with admin remarks.
- Apply on behalf of workers directly from the admin panel.

### 11. Sub-Admin RBAC Manager
- Create secondary admin accounts for HR staff, managers, or supervisors.
- Granular permission checkboxes: Dashboard View, Attendance View, Excel Export, Worker Management, Shift Management, Terminal Sync, Manual Punches, and Leave Approvals.

### 12. Hardware Diagnostics & Automated Sync
- Live network connectivity indicator (`ONLINE` / `OFFLINE`).
- Handshake test with physical terminal over port `5005`.
- **Remote Clock Synchronization**: Syncs terminal's internal RTC clock with the server's time in one click.
- Configurable auto-sync frequency (1 min, 2 mins, 5 mins, 10 mins, 15 mins, 30 mins).
- Chronological audit log of sync history and error diagnostic codes.

### 13. Enterprise Licensing Client
- Built-in licensing client verifying machine hardware fingerprint against the enterprise licensing server.
- Real-time countdown badge showing remaining license validity.
- Online license key activation and renewal reverification.

### 14. Worker Self-Service Portal
- Dedicated interface for employees when logging in with their worker credentials.
- View personal monthly attendance matrix, raw punch logs, leave balances, and submit leave requests.

---

## 📊 Excel Exporters & Reporting

The system features high-fidelity Excel generation powered by `openpyxl`:

1. **Monthly Attendance Matrix (`.xlsx`)**: Full 31-day timesheet with employee metadata, daily color-coded status cells, and summary columns.
2. **Weekly Attendance Register (`.xlsx`)**: 7-day consolidated shift timesheet with exact check-in/out timestamps and total payable days.
3. **Multi-Sheet Department Pack (`.xlsx`)**: Comprehensive workbook containing:
   - Sheet 1: Company-wide consolidated attendance overview.
   - Sheets 2+: Individual dedicated sheets for every active department.

---

## 🧪 Automated Testing Suite

The project includes an end-to-end automated test suite ([`test_all_features.py`](file:///c:/Users/abhay/Downloads/attendance_app%20%281%29/attendance_app/test_all_features.py)) that validates **14 functional modules and 30+ endpoints**:

To run the complete test suite:
```powershell
python test_all_features.py
```

**Modules Tested:**
- Authentication & Session Rejection
- Dashboard KPI Metrics & Worker Counts
- Monthly Attendance Matrix & Department Filters
- Weekly Timesheet Calculations
- Daily Punch Timelines & Photos
- Worker Directory CRUD & Policy Toggles
- Manual Punch Overrides & Audit Logs
- Department Configuration CRUD & Workforce Reassignment
- Shift Studio & Flexible Working Policies
- Leaves Management & Application Approvals
- Official Holidays & Comp-Off Synchronization
- Sub-Admin RBAC Accounts & Permissions
- Monthly & Weekly Excel Exporters (Validating generated `.xlsx` binaries)
- All 6 UI Themes in Rendered Frontend

---

## 🔌 REST API Endpoints Reference

### Authentication & Profile
- `POST /login`: Authenticates administrators and workers.
- `GET /logout`: Terminates active session.
- `POST /api/user/profile`: Updates display name, email, phone, and password.

### Attendance & Timesheets
- `GET /api/attendance/daily?date=YYYY-MM-DD`: Daily punch records, verification modes, and timestamps.
- `GET /api/attendance/weekly?date=YYYY-MM-DD`: 7-day consolidated weekly timesheet.
- `GET /api/attendance/matrix?month=M&year=YYYY`: 31-day attendance matrix with status pills.
- `GET /api/attendance/export-excel?month=M&year=YYYY`: Generates Monthly Attendance Matrix Excel workbook.
- `GET /api/attendance/export-weekly-excel?date=YYYY-MM-DD`: Generates Weekly Attendance Register Excel workbook.
- `POST /api/attendance/manual-punch`: Creates manual check-in/out override.
- `DELETE /api/attendance/manual-punch/<id>`: Deletes manual punch entry.

### Workforce & Departments
- `GET /api/workers`: Returns all active workers.
- `POST /api/workers`: Registers a new worker.
- `PUT /api/workers/<id>`: Updates worker profile, department, or shift.
- `DELETE /api/workers/<id>`: Removes worker profile.
- `POST /api/workers/<id>/flexibility`: Toggles flexible schedule policy.
- `POST /api/workers/<id>/photo`: Uploads employee face photo.
- `GET /api/departments`: Returns active departments with worker counts.
- `POST /api/departments`: Creates a new department.
- `PUT /api/departments/<id>`: Updates department name and color.
- `DELETE /api/departments/<id>`: Deletes department and reassigns workforce.

### Shifts & Flexible Policy
- `GET /api/shifts`: Returns configured shifts.
- `POST /api/shifts`: Creates new shift configuration.
- `PUT /api/shifts/<id>`: Updates existing shift.
- `DELETE /api/shifts/<id>`: Deletes shift configuration.
- `GET /api/shifts/flexible-policy`: Returns global flexible schedule parameters.
- `POST /api/shifts/flexible-policy`: Updates flexible schedule parameters.

### Leaves & Holidays
- `GET /api/admin/leave-types`: Returns leave categories.
- `POST /api/admin/leave-types`: Adds new leave category.
- `GET /api/admin/leaves`: Returns all submitted leave requests.
- `POST /api/admin/leaves/on-behalf`: Submits leave application on behalf of a worker.
- `POST /api/admin/leaves/<id>/review`: Approves or rejects leave application.
- `GET /api/holidays`: Returns company/government holiday calendar.
- `POST /api/holidays`: Adds official holiday.
- `DELETE /api/holidays/<id>`: Removes official holiday.
- `POST /api/attendance/sync-compoffs`: Synchronizes holiday attendance comp-offs.

### Biometric Terminal & Diagnostics
- `GET /api/terminal/status`: Device network status (`ONLINE` / `OFFLINE`).
- `GET /api/terminal/config`: Returns device IP, port, machine ID, and sync interval.
- `POST /api/terminal/config`: Saves device connection settings.
- `POST /api/terminal/test`: Tests TCP/IP handshake on port 5005.
- `POST /api/terminal/sync`: Triggers immediate biometric log download.
- `POST /api/terminal/sync-clock`: Synchronizes hardware clock with PC server.
- `GET /api/terminal/history`: Returns sync audit logs.

### Sub-Admin RBAC & Licensing
- `GET /api/admins`: Returns sub-admin accounts.
- `POST /api/admins`: Creates sub-admin account.
- `PUT /api/admins/<id>/permissions`: Updates sub-admin permission flags.
- `DELETE /api/admins/<id>`: Removes sub-admin account.
- `GET /api/license/status`: Returns current enterprise license status and expiry.
- `POST /api/license/activate`: Activates license key against provider portal.
- `POST /api/license/reverify`: Re-checks license validity online.

---

## 🗄 Database Architecture (`attendance.db`)

All application data is maintained in a local, zero-maintenance SQLite database located at `attendance.db`:

| Table Name | Description |
| :--- | :--- |
| **`attendance_logs`** | Raw biometric scans & manual punches (Enroll ID, timestamp, verification mode, punch direction, manual reasons). |
| **`workers`** | Workforce master records (Enroll ID, name, department, phone, email, shift ID, flexibility flag, photo path). |
| **`users`** | Login accounts and credentials (PBKDF2-SHA256 password hashes, roles: `super_admin`, sub-admin, `worker`). |
| **`departments`** | Company departments, descriptions, and color accents. |
| **`shifts`** | Shift schedules (General, Morning, Night, start/end times, grace periods, half-day thresholds). |
| **`official_holidays`** | Gazetted and national holidays where absence penalties are excused. |
| **`devices`** | Hardware terminal configuration (IP `192.168.1.224`, Port `5005`, Machine ID, sync interval). |
| **`sync_history`** | Chronological audit trail of hardware sync events, record counts, and status diagnostics. |
| **`leave_types`** | Configured leave categories (`CL`, `SL`, `PL`), allowance days, and paid flags. |
| **`worker_leave_balances`**| Allocated quotas and remaining balances per worker per year. |
| **`leave_applications`**| Submitted employee leave requests and review decisions (`PENDING`, `APPROVED`, `REJECTED`). |
| **`admin_permissions`** | Granular RBAC toggle flags assigned to sub-admins. |
| **`flexible_shift_policy`**| Workplace-wide flexible schedule rules and threshold hours. |
| **`license_config`** | Cached enterprise client license key, activation token, and validity expiry date. |

### How to Back Up the Database
Because SQLite is stored in a single file, backup is as simple as copying `attendance.db`:
```powershell
copy attendance.db attendance_backup.db
```

---

## 📁 Project Directory Structure

```text
attendance_app/
├── setup.bat                # One-click Windows setup & launcher (installs dependencies & starts app)
├── run.bat                  # Daily fast server launcher
├── requirements.txt         # Production Python dependencies with documented specifications
├── README.md                # Comprehensive system documentation
├── app.py                   # Main Flask server, routes, and REST API controller
├── database.py              # SQLite schema initialization, migrations, and queries
├── biometric.py             # SBXPC native SDK connector and thread-safe driver
├── license_client.py        # Client licensing agent, reverification, and heartbeat
├── excel_exporter.py        # OpenPyXL generator for Monthly and Weekly Timesheets
├── test_all_features.py     # End-to-end automated test suite (14 modules, 30+ tests)
├── attendance.db            # SQLite production database file
│
├── native/                  # 64-bit Windows SDK DLL libraries
│   ├── SBXPCDLL64.dll       # Core biometric SDK functions
│   ├── SBPCCOMM64.dll       # Low-level TCP/IP network protocol driver
│   └── GEN_FONT64.dll       # LCD font generator
│
├── static/                  # Static web assets
│   └── img/
│       ├── logo.jpg         # Corporate brand logo
│       └── logo.png         # Corporate brand logo PNG
│
└── templates/
    └── index.html           # Full Single-Page Application (SPA) frontend interface
```

---

## 🔧 Troubleshooting & Frequently Asked Questions

### 1. The Terminal Shows "OFFLINE" Even When Ping Succeeds
- **Subnet Mismatch**: Make sure your computer's IP is on the same subnet as the biometric machine (e.g. if the terminal is `192.168.1.224`, your PC should be `192.168.1.X` with subnet mask `255.255.255.0`).
- **Firewall Rule**: Ensure Windows Defender Firewall allows incoming/outgoing TCP traffic on **Port 5005**.
- **Socket In Use**: Ensure no other background software or older attendance tool is currently connected to the machine.

### 2. Error Loading 64-bit DLLs (`ctypes.WinError 193`)
- This error occurs if `app.py` is started with **32-bit Python**.
- Check your Python architecture by running:
  ```powershell
  python -c "import sys; print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
  ```
- If it prints `32-bit`, download and install **Python 64-bit** from [python.org](https://www.python.org/downloads/).

### 3. Port 5000 is Already in Use
If port 5000 is occupied by another process, identify and stop it:
```powershell
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### 4. How to Reset the Super Admin Password
If you ever lose the `admin` password, run this one-line command from the project directory to reset it to `admin123`:
```powershell
python -c "import database as db; db.update_user_profile(1, 'Administrator', email='admin@saikrishna.local', new_password='admin123'); print('[OK] Password successfully reset to admin123')"
```

### 5. Text Not Visible in Certain Themes
- If text ever appears low-contrast, open the top navigation bar or go to **Admin Settings > Theme Studio** and select **Warm Executive Cream** (`cream`), **Clean Paper Light** (`light`), or **Midnight Dark** (`dark`). All 6 themes are WCAG contrast verified.

---

## 📄 License & System Info
- **Application**: Workforce Biometric Attendance System
- **Client**: Sai Krishna Enterprises
- **Engineered for**: SBXPC / ZKTeco Biometric Terminals, Flexible Schedule Management, and Automated Payroll Timesheets
