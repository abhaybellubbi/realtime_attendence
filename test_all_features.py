import requests
import json
import datetime

BASE_URL = "http://localhost:5000"
session = requests.Session()

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

def print_result(module, test_name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    symbol = "[OK]" if passed else "[FAIL]"
    print(f"[{status}] {symbol} {module} -> {test_name} {details}", flush=True)
    if not passed:
        raise Exception(f"Test failed: {module} -> {test_name}: {details}")

print("=====================================================================")
print("SAI KRISHNA ENTERPRISES - COMPREHENSIVE END-TO-END AUTOMATED TEST SUITE")
print("=====================================================================\n")

# -------------------------------------------------------------
# 1. AUTHENTICATION & SESSION LIFECYCLE
# -------------------------------------------------------------
print("--> Testing Authentication & Sessions...")

# 1.1 Login page loads
r = session.get(f"{BASE_URL}/login")
print_result("Auth", "GET /login renders properly", r.status_code == 200)

# 1.2 Invalid credentials rejected
r = session.post(f"{BASE_URL}/login", data={"username": "admin", "password": "wrongpassword"})
print_result("Auth", "Invalid password rejected", "alert-danger" in r.text or "invalid" in r.text.lower() or r.status_code != 200)

# 1.3 Valid Super Admin login
r = session.post(f"{BASE_URL}/login", data={"username": "admin", "password": "admin123"}, allow_redirects=True)
print_result("Auth", "POST /login with admin credentials succeeds", r.status_code == 200 and ("Sai Krishna" in r.text or "Executive Dashboard" in r.text))

# -------------------------------------------------------------
# 2. DASHBOARD & KPIS
# -------------------------------------------------------------
print("\n--> Testing Dashboard Stats...")
r = session.get(f"{BASE_URL}/api/stats")
print_result("Dashboard", "GET /api/stats returns 200 OK", r.status_code == 200)
stats = r.json()
print_result("Dashboard", "Stats payload has workers and attendance metrics", 
             "total_workers" in stats and "present_today" in stats and "absent_today" in stats and "terminal_status" in stats,
             f"(Total: {stats.get('total_workers')}, Present: {stats.get('present_today')}, Absent: {stats.get('absent_today')})")

# -------------------------------------------------------------
# 3. MONTHLY ATTENDANCE MATRIX
# -------------------------------------------------------------
print("\n--> Testing Monthly Attendance Matrix...")
today = datetime.date.today()
year, month = today.year, today.month
r = session.get(f"{BASE_URL}/api/attendance/matrix?year={year}&month={month}")
print_result("Matrix", "GET /api/attendance/matrix returns 200 OK", r.status_code == 200)
matrix = r.json()
print_result("Matrix", "Matrix data structure contains workers and days", 
             "workers" in matrix and "days" in matrix and "year" in matrix and "month" in matrix,
             f"(Days in month: {len(matrix.get('days', []))}, Workers: {len(matrix.get('workers', []))})")

# Test department filter on matrix
r_dept = session.get(f"{BASE_URL}/api/attendance/matrix?year={year}&month={month}&department=Production%20%26%20CNC%20Machining")
print_result("Matrix", "Matrix department filtering works", r_dept.status_code == 200)

# -------------------------------------------------------------
# 4. WEEKLY ATTENDANCE TIMESHEET
# -------------------------------------------------------------
print("\n--> Testing Weekly Timesheet...")
today_str = today.strftime("%Y-%m-%d")
r = session.get(f"{BASE_URL}/api/attendance/weekly?date={today_str}")
print_result("Weekly", "GET /api/attendance/weekly returns 200 OK", r.status_code == 200)
weekly = r.json()
print_result("Weekly", "Weekly payload contains 7-day calendar and workers list", 
             "days" in weekly and "workers" in weekly,
             f"(Days: {len(weekly.get('days', []))}, Workers: {len(weekly.get('workers', []))})")

# -------------------------------------------------------------
# 5. DAILY PUNCH TIMELINES
# -------------------------------------------------------------
print("\n--> Testing Daily Punch Timelines...")
r = session.get(f"{BASE_URL}/api/attendance/daily?date={today_str}")
print_result("Daily", "GET /api/attendance/daily returns 200 OK", r.status_code == 200)
daily = r.json()
print_result("Daily", "Daily attendance records loaded", "attendance" in daily, f"(Count: {len(daily.get('attendance', []))})")

# -------------------------------------------------------------
# 6. WORKERS & WORKER STUDIO CRUD
# -------------------------------------------------------------
print("\n--> Testing Worker Directory & Worker Studio...")
# List workers
r = session.get(f"{BASE_URL}/api/workers")
print_result("Workers", "GET /api/workers returns 200 OK", r.status_code == 200)
workers_data = r.json().get("workers", [])
print(f"    Current total workers: {len(workers_data)}")

# Create a test worker
import time
test_enroll = 90000 + int(str(int(time.time()))[-4:])
new_worker_payload = {
    "enroll_number": test_enroll,
    "name": "Automated Test Worker",
    "department": "Production & CNC Machining",
    "shift_id": None,
    "joining_date": today_str
}
r_create = session.post(f"{BASE_URL}/api/workers", json=new_worker_payload)
print_result("Workers", "POST /api/workers creates worker", r_create.status_code in [200, 201])
worker_id = r_create.json().get("worker_id")

if not worker_id:
    # Find worker by enroll number
    r_all = session.get(f"{BASE_URL}/api/workers").json().get("workers", [])
    for w in r_all:
        if w.get("enroll_number") == test_enroll:
            worker_id = w.get("id")
            break

print_result("Workers", "Worker ID verified after creation", worker_id is not None, f"(ID: {worker_id})")

# Edit Worker Profile & Shift Assignment (Testing the dropdown department field update)
edit_payload = {
    "name": "Automated Test Worker (Updated)",
    "department": "Quality Assurance & QC",
    "shift_id": None,
    "email": "testworker@saikrishna.com",
    "phone": "9876543211",
    "is_flexible": False
}
r_edit = session.put(f"{BASE_URL}/api/workers/{worker_id}", json=edit_payload)
print_result("Workers", "PUT /api/workers/<id> updates worker profile and department", r_edit.status_code == 200)

# Verify single worker department updated in workers list
r_all_after = session.get(f"{BASE_URL}/api/workers").json().get("workers", [])
updated_worker = next((w for w in r_all_after if w.get("id") == worker_id), None)
print_result("Workers", "Worker list reflects updated department from dropdown", 
             updated_worker is not None and updated_worker.get("department") == "Quality Assurance & QC",
             f"(Department: {updated_worker.get('department') if updated_worker else 'None'})")

# Test Worker Flexibility Toggle (Policy Studio)
r_flex = session.post(f"{BASE_URL}/api/workers/{worker_id}/flexibility", json={"is_flexible": True})
print_result("Workers", "POST /api/workers/<id>/flexibility toggles flexible policy", r_flex.status_code == 200)

# -------------------------------------------------------------
# 7. MANUAL CHECK-IN & CHECK-OUT (BIOMETRIC OVERRIDE)
# -------------------------------------------------------------
print("\n--> Testing Manual Punch Override...")
punch_in_payload = {
    "enroll_number": test_enroll,
    "punch_type": 0,
    "date": today_str,
    "time": "08:30:00",
    "reason": "Official Gate Pass / Automated Test"
}
r_punch_in = session.post(f"{BASE_URL}/api/attendance/manual-punch", json=punch_in_payload)
print_result("ManualPunch", "POST /api/attendance/manual-punch records IN punch", r_punch_in.status_code in [200, 201])

punch_out_payload = {
    "enroll_number": test_enroll,
    "punch_type": 1,
    "date": today_str,
    "time": "17:00:00",
    "reason": "Shift End / Automated Test"
}
r_punch_out = session.post(f"{BASE_URL}/api/attendance/manual-punch", json=punch_out_payload)
print_result("ManualPunch", "POST /api/attendance/manual-punch records OUT punch", r_punch_out.status_code in [200, 201])

# Verify manual punches list
r_mp_list = session.get(f"{BASE_URL}/api/attendance/manual-punches?date={today_str}")
print_result("ManualPunch", "GET /api/attendance/manual-punches returns records", r_mp_list.status_code == 200)

# -------------------------------------------------------------
# 8. DEPARTMENT CONFIGURATION & MASTER REGISTRY CRUD
# -------------------------------------------------------------
print("\n--> Testing Department Configuration CRUD & Reassignment...")
# 8.1 List departments
r_depts = session.get(f"{BASE_URL}/api/departments")
print_result("Departments", "GET /api/departments returns active list with worker counts", r_depts.status_code == 200)

# 8.2 Create new department
dept_test_name = "Robotics & Vision Metrology"
r_add_dept = session.post(f"{BASE_URL}/api/departments", json={
    "name": dept_test_name,
    "code": "RVM",
    "description": "High speed 6-axis pick and place and AI optical inspection"
})
print_result("Departments", "POST /api/departments creates department", r_add_dept.status_code in [200, 201])
new_dept_id = r_add_dept.json().get("id")

# 8.3 Update department
r_upd_dept = session.put(f"{BASE_URL}/api/departments/{new_dept_id}", json={
    "name": f"{dept_test_name} (Updated)",
    "code": "RVM-X",
    "description": "Updated high-precision industrial robotics"
})
print_result("Departments", "PUT /api/departments/<id> updates department", r_upd_dept.status_code == 200)

# 8.4 Delete department with worker reassignment parameter
r_del_dept = session.delete(f"{BASE_URL}/api/departments/{new_dept_id}", json={
    "reassign_to": "Production & CNC Machining"
})
print_result("Departments", "DELETE /api/departments/<id> deletes department and reassigns workforce", r_del_dept.status_code == 200)

# -------------------------------------------------------------
# 9. SHIFTS & FLEXIBLE WORKING POLICY
# -------------------------------------------------------------
print("\n--> Testing Shift Studio & Policies...")
r_shifts = session.get(f"{BASE_URL}/api/shifts")
print_result("Shifts", "GET /api/shifts returns configurations", r_shifts.status_code == 200)

# Create a test shift
test_shift_payload = {
    "name": f"Test Shift {test_enroll}",
    "start_time": "09:00",
    "end_time": "18:00",
    "grace_period_mins": 15,
    "half_day_threshold_mins": 240
}
r_create_shift = session.post(f"{BASE_URL}/api/shifts", json=test_shift_payload)
print_result("Shifts", "POST /api/shifts creates shift", r_create_shift.status_code in [200, 201])
shift_id = r_create_shift.json().get("shift_id")

# Update shift
r_upd_shift = session.put(f"{BASE_URL}/api/shifts/{shift_id}", json={
    "name": f"Test Shift {test_enroll} (Upd)",
    "start_time": "09:15",
    "end_time": "18:15",
    "grace_period_mins": 20,
    "half_day_threshold_mins": 240
})
print_result("Shifts", "PUT /api/shifts/<id> updates shift", r_upd_shift.status_code == 200)

# Flexible policy GET and POST
r_flex_get = session.get(f"{BASE_URL}/api/shifts/flexible-policy")
print_result("Shifts", "GET /api/shifts/flexible-policy returns policy", r_flex_get.status_code == 200)

r_flex_post = session.post(f"{BASE_URL}/api/shifts/flexible-policy", json={
    "full_day_hours": 8.0,
    "half_day_hours": 4.0
})
print_result("Shifts", "POST /api/shifts/flexible-policy saves policy", r_flex_post.status_code == 200)

# Delete test shift
r_del_shift = session.delete(f"{BASE_URL}/api/shifts/{shift_id}")
print_result("Shifts", "DELETE /api/shifts/<id> deletes shift", r_del_shift.status_code == 200)

# -------------------------------------------------------------
# 10. LEAVES MANAGEMENT & APPROVALS
# -------------------------------------------------------------
print("\n--> Testing Leaves Management...")
# Leave categories
r_ltypes = session.get(f"{BASE_URL}/api/admin/leave-types")
print_result("Leaves", "GET /api/admin/leave-types returns categories", r_ltypes.status_code == 200)

# Applications list
r_lapps = session.get(f"{BASE_URL}/api/admin/leaves")
print_result("Leaves", "GET /api/admin/leaves returns applications", r_lapps.status_code == 200)

# Submit test leave application on behalf of our test worker
tomorrow = today + datetime.timedelta(days=1)
tomorrow_str = tomorrow.strftime("%Y-%m-%d")
leave_app_payload = {
    "identifier": str(test_enroll),
    "leave_type_code": "CL",
    "start_date": tomorrow_str,
    "end_date": tomorrow_str,
    "reason": "Automated Leave Approval Test",
    "auto_approve": False
}
r_sub_leave = session.post(f"{BASE_URL}/api/admin/leaves/on-behalf", json=leave_app_payload)
print_result("Leaves", "POST /api/admin/leaves/on-behalf creates request", r_sub_leave.status_code in [200, 201])
leave_app_id = r_sub_leave.json().get("leave_id")

if leave_app_id:
    # Review & Approve leave
    r_review = session.post(f"{BASE_URL}/api/admin/leaves/{leave_app_id}/review", json={
        "status": "APPROVED",
        "admin_notes": "Approved by automated test suite"
    })
    print_result("Leaves", "POST /api/admin/leaves/<id>/review approves application", r_review.status_code == 200)

# -------------------------------------------------------------
# 11. COMPANY HOLIDAYS & COMP-OFF SYNCHRONIZATION
# -------------------------------------------------------------
print("\n--> Testing Holidays & Comp-Off Sync...")
r_hld = session.get(f"{BASE_URL}/api/holidays?year={year}")
print_result("Holidays", "GET /api/holidays returns holidays calendar", r_hld.status_code == 200)

# Create a test holiday
test_hld_date = f"{year}-12-{20 + (int(time.time()) % 8)}"
r_add_hld = session.post(f"{BASE_URL}/api/holidays", json={
    "holiday_date": test_hld_date,
    "name": f"Auto Test Holiday {test_enroll}",
    "is_optional": False
})
print_result("Holidays", "POST /api/holidays creates holiday", r_add_hld.status_code in [200, 201])
hld_id = r_add_hld.json().get("holiday", {}).get("id") or r_add_hld.json().get("id")

# Sync comp-offs
r_compoff = session.post(f"{BASE_URL}/api/attendance/sync-compoffs", json={"year": year, "month": month})
print_result("Holidays", "POST /api/attendance/sync-compoffs executes comp-off sync", r_compoff.status_code == 200)

# Delete test holiday
if hld_id:
    r_del_hld = session.delete(f"{BASE_URL}/api/holidays/{hld_id}")
    print_result("Holidays", "DELETE /api/holidays/<id> deletes holiday", r_del_hld.status_code == 200)

# -------------------------------------------------------------
# 12. RBAC ADMIN ACCOUNTS
# -------------------------------------------------------------
print("\n--> Testing RBAC & Administrator Accounts...")
r_admins = session.get(f"{BASE_URL}/api/admins")
print_result("RBAC", "GET /api/admins returns system administrators", r_admins.status_code == 200)

# -------------------------------------------------------------
# 13. EXCEL EXPORTERS
# -------------------------------------------------------------
print("\n--> Testing Excel Exporters...")
# Monthly matrix export
r_exp_m = session.get(f"{BASE_URL}/api/attendance/export-excel?year={year}&month={month}&mode=single")
print_result("Export", "GET /api/attendance/export-excel generates valid monthly .xlsx", 
             r_exp_m.status_code == 200 and len(r_exp_m.content) > 1000,
             f"(Size: {len(r_exp_m.content)} bytes)")

# Weekly timesheet export
r_exp_w = session.get(f"{BASE_URL}/api/attendance/export-weekly-excel?date={today_str}")
print_result("Export", "GET /api/attendance/export-weekly-excel generates valid weekly .xlsx", 
             r_exp_w.status_code == 200 and len(r_exp_w.content) > 1000,
             f"(Size: {len(r_exp_w.content)} bytes)")

# Department pack export
r_exp_d = session.get(f"{BASE_URL}/api/attendance/export-excel?year={year}&month={month}&mode=department_pack")
print_result("Export", "GET /api/attendance/export-excel generates multi-sheet department pack .xlsx", 
             r_exp_d.status_code == 200 and len(r_exp_d.content) > 1000,
             f"(Size: {len(r_exp_d.content)} bytes)")

# -------------------------------------------------------------
# 14. 5 THEMES VERIFICATION IN APPLICATION
# -------------------------------------------------------------
print("\n--> Testing 5 Themes in Rendered Frontend...")
r_app = session.get(f"{BASE_URL}/")
all_themes_found = all(t in r_app.text for t in [
    'Midnight Dark', 'Industrial Slate', 'Clean Paper Light', 'Cyber Emerald', 'Royal Violet',
    'theme-card-dark', 'theme-card-slate', 'theme-card-light', 'theme-card-emerald', 'theme-card-violet'
])
print_result("Themes", "All 5 Themes configured and present in Admin Settings", all_themes_found)

# -------------------------------------------------------------
# CLEANUP
# -------------------------------------------------------------
print("\n--> Cleaning up test worker...")
if worker_id:
    r_del_worker = session.delete(f"{BASE_URL}/api/workers/{worker_id}")
    print_result("Cleanup", "DELETE /api/workers/<id> removes test worker", r_del_worker.status_code == 200)

print("\n=====================================================================")
print("ALL 14 MODULES AND 30+ TESTS PASSED WITH 100% SUCCESS!")
print("=====================================================================")
