# ⏱️ Client Workforce Attendance System (`attendance_app`)

The **Client Workforce Attendance System** is a production-grade enterprise web application for employee attendance tracking, hardware biometric device integration, shift management, leave approvals, manual overrides, and automated payroll Excel generation.

---

## 📑 Table of Contents
- [Overview](#-overview)
- [How to Start the Attendance App](#-how-to-start-the-attendance-app)
  - [⚡ Option 1: One-Click Automated Setup & Launch (Recommended)](#-option-1-one-click-automated-setup--launch-recommended)
  - [🚀 Option 2: Daily Quick Start](#-option-2-daily-quick-start)
  - [🛠️ Option 3: Manual Command Line](#️-option-3-manual-command-line)
- [User Roles & Default Login Credentials](#-user-roles--default-login-credentials)
- [Biometric Hardware Integration](#-biometric-hardware-integration)
- [Core Features & Functional Modules](#-core-features--functional-modules)
  - [1. Executive Overview Dashboard](#1-executive-overview-dashboard)
  - [2. Monthly Attendance Matrix & Timesheet](#2-monthly-attendance-matrix--timesheet)
  - [3. Weekly Timesheet & Attendance Register](#3-weekly-timesheet--attendance-register)
  - [4. Daily Biometric Punch Logs](#4-daily-biometric-punch-logs)
  - [5. Manual Check-In & Check-Out (Hardware Override)](#5-manual-check-in--check-out-hardware-override)
  - [6. Workforce Directory & Biometric Enrollment](#6-workforce-directory--biometric-enrollment)
  - [7. Worker Studio & Policy Management](#7-worker-studio--policy-management)
  - [8. Shift Studio & Flexible Working Policy](#8-shift-studio--flexible-working-policy)
  - [9. Sub-Admin RBAC Manager](#9-sub-admin-rbac-manager)
  - [10. Hardware Diagnostics & Automated Sync](#10-hardware-diagnostics--automated-sync)
  - [11. Enterprise Licensing Client](#11-enterprise-licensing-client)
  - [12. Worker Self-Service Portal](#12-worker-self-service-portal)
  - [13. Visual Themes & User Preferences](#13-visual-themes--user-preferences)
  - [14. Official Holidays & Government Calendar](#14-official-holidays--government-calendar)
- [Requirements & Dependencies (`requirements.txt`)](#-requirements--dependencies-requirementstxt)
- [REST API Endpoints Reference](#-rest-api-endpoints-reference)
- [Database Architecture (`attendance.db`)](#-database-architecture-attendancedb)
- [Directory Structure](#-directory-structure)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🔍 Overview

- **Port**: `5000` ([http://localhost:5000](http://localhost:5000))
- **Backend**: Python 3.10+ (Flask, Werkzeug, SQLite3, OpenPyXL, Requests, CTypes)
- **Frontend**: Single-Page Application (SPA) with Bootstrap 5, Bootstrap Icons, and Vanilla JavaScript
- **Hardware Integration**: SBXPC / ZKTeco Biometric Fingerprint & RFID Terminals over TCP/IP (Port 5005) via native 64-bit Windows SDK DLLs
- **Primary Database**: Embedded SQLite3 database (`attendance_app/attendance.db`)

---

## 🚀 How to Start the Attendance App

### Prerequisites
1. **Operating System**: Windows 10 / Windows 11 (required for native 64-bit Windows biometric SDK DLLs).
2. **Python Environment**: **Python 3.10+ (64-bit)**.
   > **Important**: You must use **64-bit Python** so `ctypes` can load the 64-bit native DLLs (`SBXPCDLL64.dll`, `SBPCCOMM64.dll`, `GEN_FONT64.dll`).
3. **Local Network / Hardware**: Connect the biometric machine to your LAN switch or router via an Ethernet cable.

---

### ⚡ Option 1: One-Click Automated Setup & Launch (Recommended)

Simply double-click or run **`setup.bat`** from the project root or inside `attendance_app`:

```powershell
.\setup.bat
```

**What this single file does automatically:**
1. ✅ **Checks Python Environment**: Verifies 64-bit Python 3.10+ is installed and configured.
2. 📦 **Installs Everything**: Runs `pip install -r requirements.txt` to install all dependencies (`Flask`, `Werkzeug`, `requests`, `openpyxl`, `python-dateutil`).
3. 💾 **Database Verification**: Validates and initializes `attendance.db`, schemas, and seeds default admin accounts and shifts.
4. 🔌 **Biometric Hardware DLLs**: Validates native 64-bit DLLs (`SBXPCDLL64.dll`, `SBPCCOMM64.dll`, `GEN_FONT64.dll`).
5. 🌐 **Auto-Launch**: Starts the Flask server and opens **http://localhost:5000** in your default web browser automatically!

---

### 🚀 Option 2: Daily Quick Start

After running `setup.bat` once, you can launch the application instantly without reinstalling packages:

```powershell
.\run.bat
```
*(Starts the server and automatically opens http://localhost:5000 in your browser)*

---

### 🛠️ Option 3: Manual Command Line

If you prefer using the command line manually:

1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
2. **Start the Attendance Server**:
   ```powershell
   cd attendance_app
   python app.py
   ```
3. **Open in Browser**:
   Navigate to 👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 User Roles & Default Login Credentials

| Role | Access URL | Username | Password | Purpose / Privileges |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | `http://localhost:5000` | `admin` | `admin123` | Master administrator: full access to shifts, worker flexibility policies, RBAC management, licensing, official holidays, and terminal diagnostics. |
| **Sub-Admin** | `http://localhost:5000` | *Dynamic* | *Dynamic* | Created by Super Admin with granular permissions (e.g. attendance viewing, manual punches, leave management, worker editing). |
| **Worker (Self-Service)** | `http://localhost:5000` | `1` or `worker_1` | `worker123` | Employee portal: personal monthly matrix, raw punch logs, leave balances, and leave request submission. |

---

## 📡 Biometric Hardware Integration

- **SDK Location**: `attendance_app/native/`
  - `SBXPCDLL64.dll`: Core biometric algorithm and command dispatch library.
  - `SBPCCOMM64.dll`: Low-level network socket and TCP/IP protocol driver.
  - `GEN_FONT64.dll`: Terminal LCD font rendering library.
- **Default Network Settings**:
  - **IP Address**: `192.168.1.224`
  - **TCP Port**: `5005`
  - **Machine ID**: `1`
- **Thread-Safe Architecture**: All SDK calls are wrapped in a thread-safe mutex lock (`sdk_lock` in `biometric.py`) to prevent multi-threaded crashes.
- **Automated Background Polling**: A background daemon thread automatically connects to the biometric machine every **2 minutes** (configurable in user settings) to poll attendance logs and import new check-ins.
- **Offline Simulation Fallback**: When the physical biometric machine is powered off or unplugged from the network, the app seamlessly falls back to offline simulation mode so UI, analytics, manual punch overrides, and timesheet reports continue working without freezing or crashing.

---

## ✨ Core Features & Functional Modules

### 1. Executive Overview Dashboard
- **Modern Workforce Attendance Cards & Dual View**:
  - **Visual Employee Cards**: Enterprise-grade cards featuring high-definition worker face photos with fallback geometric dummy silhouette SVG avatars.
  - **Live Presence Indicator**: Circular status indicator on each avatar (pulsing green when clocked in, blue on completed shift, red on absent).
  - **Status Accent Top Bar**: Color-coded gradient top bar indicating Present, Late, Half Day, Holiday, Leave, Weekly Off, or Absent.
  - **Dual-Cell Punch Timelines**: Separate split-column cells for **Check-In** and **Check-Out** with bold mono timestamps and verification mode badges:
    - 📸 **Face Recognition** (`bi-person-bounding-box`)
    - 👆 **Fingerprint Scan** (`bi-fingerprint`)
    - 💳 **RFID / Proximity Card** (`bi-credit-card-2-front`)
    - ✍️ **Manual Admin Punch** (`bi-pencil-square`)
    - ⏳ **Active Shift in Progress** / **Single Punch**
  - **Centered Today Status Badge**: Positioned neatly at the bottom center of each card showing current daily status (`PRESENT`, `HALF DAY`, `ABSENT`, `HOLIDAY`).
  - **Interactive Detail Drawer**: Clicking any worker card slides open a comprehensive modal displaying all daily punch history, verified biometric modes, and duration.
- **High-Contrast KPI Counter Cards**:
  - **Total Workforce**: Displays total registered active staff with dedicated glowing icon (`.stat-icon-primary`).
  - **Present Today**: Real-time counter of employees clocked in today with glowing green icon (`.stat-icon-success`).
  - **Half Day / Late Arrival**: Employees who clocked in after the shift grace period threshold.
  - **Absent Today**: Dynamic count of employees with zero punches recorded on regular working days.
  - **Real-Time Active Count Badge**: High-contrast blue pill (e.g. `6 of 6 employees`) clearly visible in both light and dark themes.

### 2. Monthly Attendance Matrix & Timesheet
- **Sticky Frozen Columns**: Employee ID and Name remain permanently pinned to the left while scrolling horizontally across all 28–31 days of the month.
- **Status Pills**:
  - `P` (Present - Green)
  - `HD` (Half-Day / Late Arrival - Amber)
  - `A` (Absent - Red)
  - `LV` (Approved Leave - Purple)
  - `HLD` (Official Holiday - Cyan)
  - `OFF` (Sunday / Scheduled Day-Off - Slate)
- **Summary Totals**: Live calculation of total Present days, Half-Days, Absent days, Leaves, and payable working days.
- **Color-Coded Payroll Excel Export**: Generates `.xlsx` timesheets with corporate branding headers and color-filled status cells ready for payroll processing.

### 3. Weekly Timesheet & Attendance Register
- Consolidated 7-day Monday-to-Sunday attendance matrix.
- Daily check-in/out timestamps and active duration per worker.
- Weekly payable days calculation with one-click Excel download (`SAI KRISHNA ENTERPRISES - WEEKLY ATTENDANCE REGISTER.xlsx`).

### 4. Daily Biometric Punch Logs
- Comprehensive chronological audit trail of all check-ins and check-outs.
- **Interactive Search Bar**: Real-time instant filtering by Worker ID (Enroll Number) or Employee Name.
- Date picker to inspect raw terminal logs for any past date.
- Verification method breakdown (Face, Fingerprint, RFID Card, Manual).

### 5. Manual Check-In & Check-Out (Hardware Override)
- Allows administrators to log punches for employees when the biometric terminal is offline or in case of missed punches.
- Dropdown selector for verification mode (Face, Fingerprint, RFID, Manual Override).
- Mandatory audit note logging reason for the manual punch.
- High-contrast **Terminal Fallback Ready** status badge.

### 6. Workforce Directory & Biometric Enrollment
- Complete worker roster with employee ID, name, department, phone, shift, and joining date.
- **Instant Search Filter**: Quickly find workers by typing their name or enroll ID.
- **Shift Schedule Badges**: Solid, high-contrast badges (e.g. `General Shift`, `Morning Shift`) styled for pitch-black and pure-white backgrounds.
- Edit worker profiles, update photos, or assign customized shifts.

### 7. Worker Studio & Policy Management
- Assign employees to standard fixed shifts or enable the **Flexible Schedule Policy**.
- Flexible schedule employees are evaluated based on total hours worked rather than strict start-time grace windows.

### 8. Shift Studio & Flexible Working Policy
- Define shift hours (start time, end time).
- **Configurable Grace Period**: Tolerance window for late arrivals before marking Half-Day (e.g. 15 minutes).
- **Configurable Half-Day Threshold**: High-contrast label and badges displaying threshold minutes (e.g. `120 mins Half-Day Threshold:`).
- Company-wide minimum required working hours for full-day and half-day credits.

### 9. Sub-Admin RBAC Manager
- **Super Admin Exclusive**: Create secondary administrative accounts for managers, HR, and accountants.
- **Granular Permissions Matrix**: Toggle checkboxes for individual privileges:
  - Can View Dashboard
  - Can View Attendance
  - Can Export Excel
  - Can Manage Workers
  - Can Manage Shifts
  - Can Trigger Terminal Sync
  - Can Perform Manual Punch
  - Can Manage Leaves

### 10. Hardware Diagnostics & Automated Sync
- Real-time terminal connection status indicator (`ONLINE` / `OFFLINE`).
- **Configurable Auto-Sync Frequency**: Dropdown to select sync intervals (Every 1 min, 2 mins, 5 mins, 10 mins, 15 mins, 30 mins).
- **Test Connection**: Handshakes with the biometric terminal via TCP/IP port 5005.
- **Sync Device Clock**: Automatically aligns the hardware machine's internal RTC clock with the PC server time.
- **Sync History Audit Log**: Chronological table of past sync attempts, records fetched, and diagnostic error codes.

### 11. Enterprise Licensing Client
- Built-in license verification agent communicating with the Provider Licensing Portal.
- Real-time days remaining countdown pill.
- Remote license key activation and online renewal reverification.
- Security lock screen in case of license expiration.

### 12. Worker Self-Service Portal
- Dedicated employee interface accessible when logging in with worker credentials (e.g. username `1`).
- View personal monthly attendance matrix and hours worked.
- Submit new leave applications and track approval statuses.
- Inspect personal raw punch history.

### 13. Visual Themes & User Preferences
- **Dual Production Themes**:
  - **Pitch-Black Theme**: Deep `#000000` dark mode with neon glowing KPI stat icons, solid high-contrast badges, and high readability.
  - **Legit Pure White Theme**: Strict pure white (`rgb(255, 255, 255)` / `#ffffff`) across **ALL PAGES and tabs** with crisp slate borders and deep black text (`#000000`).
- **Universal Top Bar Switcher**: One-click theme toggle available persistently from the top navigation bar and settings page.
- **Clean Sidebar Layout**: Navigation sidebar focused purely on operational tabs with no redundant buttons.
- **Settings & Profile Security**:
  - Update full name, email, and **phone number**.
  - **Mandatory Current Password Verification**: Password updates require entering the current password before changing credentials.

### 14. Official Holidays & Government Calendar
- **Super Admin Exclusive Management**: Dedicated calendar interface to add national, gazetted, and company holidays (`/api/holidays`).
- **No Absent Penalization**: On official holidays, employees who do not clock in are **never marked as absent** (`HLD` status); their pay and timesheets are credited with holiday entitlement.
- **Holiday Work Recognition**: If an employee clocks in on an official holiday, their attendance is recorded and credited with holiday working hours.
- **Multi-Module Synchronization**: Official holidays automatically reflect on Overview cards, Monthly Matrix, Weekly Timesheets, and Excel exports.

---

## 📦 Requirements & Dependencies (`requirements.txt`)

All dependencies are pinned for enterprise stability:

```txt
Flask>=3.0.0
Werkzeug>=3.0.0
requests>=2.31.0
openpyxl>=3.1.2
python-dateutil>=2.8.2
```

Installed automatically via `setup.bat` or manually with `pip install -r requirements.txt`.

---

## 🔌 REST API Endpoints Reference

### Authentication & Profile
- `POST /login`: Authenticates Super Admins, Sub-Admins, and Workers.
- `GET /logout`: Terminates session and redirects to sign-in page.
- `POST /api/user/profile`: Updates current user display name, email, phone number, and password (requires `current_password`).

### Official Holidays (Super Admin)
- `GET /api/holidays`: Returns list of official government/company holidays.
- `POST /api/holidays`: Adds a new official holiday (`holiday_date`, `holiday_name`, `notes`).
- `PUT /api/holidays/<id>`: Updates an existing official holiday.
- `DELETE /api/holidays/<id>`: Removes an official holiday.

### Attendance & Timesheets
- `GET /api/attendance/daily?date=YYYY-MM-DD`: Returns daily attendance details, verification methods (Face, Fingerprint, RFID, Manual), photo URLs, and status for all workers.
- `GET /api/attendance/weekly?date=YYYY-MM-DD`: Returns 7-day consolidated weekly timesheet matrix.
- `GET /api/attendance/matrix?month=M&year=YYYY`: Returns monthly attendance matrix.
- `GET /api/attendance/export-excel?month=M&year=YYYY`: Downloads Monthly Attendance Matrix as Excel (`.xlsx`).
- `GET /api/attendance/export-weekly-excel?date=YYYY-MM-DD`: Downloads Weekly Timesheet as Excel (`.xlsx`).
- `POST /api/attendance/manual-punch`: Records manual check-in or check-out override punch with verification mode selection.
- `DELETE /api/attendance/manual-punch/<id>`: Deletes manual punch entry.

### Workers Management
- `GET /api/workers`: Returns list of all registered employees.
- `POST /api/workers/sync`: Pulls newly enrolled workers from biometric terminal.
- `PUT /api/workers/<id>`: Updates employee details (name, department, shift, phone, email, photo).
- `POST /api/workers/<id>/photo`: Uploads or updates worker photo.
- `DELETE /api/workers/<id>`: Removes an employee.
- `POST /api/workers/<id>/flexibility`: Toggles worker between Flexible Schedule and Fixed Shift (Super Admin only).
- `POST /api/workers/<id>/change-shift`: Assigns a shift to an employee.

### Shifts & Policy
- `GET /api/shifts`: Returns list of configured shifts.
- `POST /api/shifts`: Creates a new shift schedule.
- `PUT /api/shifts/<id>`: Updates existing shift parameters.
- `DELETE /api/shifts/<id>`: Deletes a shift schedule.
- `GET /api/shifts/flexible-policy`: Returns global flexible shift threshold hours.
- `POST /api/shifts/flexible-policy`: Updates global flexible shift threshold hours.

### Leaves Management
- `GET /api/leaves/types`: Returns list of leave types.
- `POST /api/leaves/types`: Creates a new custom leave category.
- `GET /api/workers/<id>/leaves?year=YYYY`: Returns leave quota and balance for an employee.
- `POST /api/workers/<id>/leaves`: Sets or updates leave quota for an employee.
- `GET /api/admin/leaves/applications?year=YYYY`: Returns all submitted leave applications.
- `POST /api/admin/leaves/<id>/review`: Approves or rejects a submitted leave application.

### Biometric Terminal
- `GET /api/terminal/status`: Checks device network status and returns `ONLINE` or `OFFLINE`.
- `GET /api/terminal/config`: Returns device IP, port, machine ID, and sync interval.
- `POST /api/terminal/config`: Saves device connection settings.
- `POST /api/terminal/test`: Tests handshake with physical biometric device.
- `POST /api/terminal/sync`: Triggers manual biometric punch download.
- `POST /api/terminal/sync-clock`: Synchronizes biometric terminal clock with computer time.
- `GET /api/terminal/history?limit=10`: Returns recent synchronization history logs.

### Sub-Admin RBAC
- `GET /api/admins`: Returns list of sub-admin accounts.
- `POST /api/admins`: Creates a new sub-admin account.
- `PUT /api/admins/<id>/permissions`: Updates permission flags for a sub-admin.
- `DELETE /api/admins/<id>`: Deletes a sub-admin account.

### Licensing
- `GET /api/license/status`: Returns cached license status, expiry date, and days remaining.
- `POST /api/license/activate`: Activates license key against provider server.
- `POST /api/license/reverify`: Triggers immediate online license reverification.

### Worker Self-Service
- `GET /api/worker/profile`: Returns logged-in worker profile and leave balances.
- `GET /api/worker/attendance?month=M&year=YYYY`: Returns personal monthly timesheet.
- `GET /api/worker/leaves?year=YYYY`: Returns leave balances and personal applications.
- `POST /api/worker/leaves`: Submits a new leave application request.
- `GET /api/worker/punches?date=YYYY-MM-DD`: Returns personal raw punches.

---

## 🗄 Database Architecture (`attendance.db`)

All application data is stored locally in an embedded **SQLite 3** database located at `attendance_app/attendance.db`. It contains **14 core tables**:

| Table Name | Description |
| :--- | :--- |
| **`attendance_logs`** | Raw biometric scans & manual punches (Enroll ID, timestamp, verification mode, punch direction, manual reasons). |
| **`workers`** | Workforce master records (Enroll ID, name, department, phone, email, shift ID, flexibility flag, photo path). |
| **`users`** | Application login accounts and credentials (PBKDF2 password hashes, roles: `super_admin`, sub-admin, `worker`). |
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

### Database Backup
Because SQLite is self-contained in a single file, you can create a complete backup at any time:
```powershell
copy attendance_app\attendance.db attendance_app\attendance_backup.db
```

---

## 📁 Directory Structure

```text
project_bio/
├── setup.bat                # One-click Windows setup & launcher (installs dependencies & starts app)
├── run.bat                  # Daily fast server launcher
├── setup.py                 # Cross-platform Python setup & diagnostic engine
├── requirements.txt         # Production Python dependencies
├── README.md                # Project ecosystem documentation
│
└── attendance_app/          # Core Client Attendance Application
    ├── app.py               # Main Flask server, routes, and REST API controller
    ├── database.py          # SQLite schema initialization, migrations, and queries
    ├── biometric.py         # SBXPC native SDK connector and thread-safe driver
    ├── license_client.py    # Client licensing agent, reverification, and heartbeat
    ├── excel_exporter.py    # OpenPyXL generator for Monthly and Weekly Timesheets
    ├── attendance.db        # SQLite production database file
    ├── setup.bat            # Local one-click installer inside app folder
    ├── run.bat              # Local fast launcher
    ├── requirements.txt     # Local requirements copy
    ├── README.md            # Dedicated client application documentation
    │
    ├── native/              # 64-bit Windows SDK DLL libraries
    │   ├── SBXPCDLL64.dll   # Core biometric SDK functions
    │   ├── SBPCCOMM64.dll   # Low-level TCP/IP network protocol driver
    │   └── GEN_FONT64.dll   # LCD font generator
    │
    ├── static/              # Static web assets
    │   └── img/
    │       ├── logo.jpg     # Corporate brand logo
    │       └── logo.png     # Brand logo PNG
    │
    └── templates/
        └── index.html       # Full Single-Page Application (SPA) frontend interface
```

---

## 🔧 Troubleshooting & FAQs

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
If port 5000 is already in use by another program, find the process and stop it:
```powershell
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### 4. How to Reset the Super Admin Password
If you forget the `admin` password, run this one-line command to reset it to `admin123`:
```powershell
python -c "import database as db; db.update_user_profile(1, 'Administrator', email='admin@saikrishna.local', new_password='admin123'); print('Password reset to admin123')"
```

---

## 📄 License & System Info
- **Application**: Workforce Biometric Attendance System
- **Client**: Sai Krishna Enterprises
- **Engineered for**: SBXPC / ZKTeco Biometric Terminals, Flexible Schedule Management, and Automated Payroll Timesheets
