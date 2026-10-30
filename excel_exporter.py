import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io
import calendar
from datetime import datetime

def clean_sheet_name(name):
    """Excel sheet name sanitizer: max 31 characters, no invalid symbols."""
    for ch in ['\\', '/', '?', '*', '[', ']', ':']:
        name = name.replace(ch, '_')
    cleaned = name.strip()[:30]
    return cleaned if cleaned else "Sheet"

def _get_styles():
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    double_bottom_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='double', color='0F172A')
    )
    styles = {
        'thin_border': thin_border,
        'double_bottom_border': double_bottom_border,
        'fill_header': PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid"),
        'font_header': Font(name="Calibri", size=10, bold=True, color="FFFFFF"),
        'fill_total': PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid"),
        'font_total': Font(name="Calibri", size=10, bold=True, color="FFFFFF"),
        'fill_p': PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid"),
        'font_p': Font(name="Calibri", size=10, bold=True, color="065F46"),
        'fill_hd': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
        'font_hd': Font(name="Calibri", size=10, bold=True, color="92400E"),
        'fill_a': PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),
        'font_a': Font(name="Calibri", size=10, bold=True, color="991B1B"),
        'fill_off': PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),
        'font_off': Font(name="Calibri", size=10, color="64748B"),
        'fill_lv': PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),
        'font_lv': Font(name="Calibri", size=10, bold=True, color="1E40AF"),
        'fill_hld': PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid"),
        'font_hld': Font(name="Calibri", size=10, bold=True, color="6D28D9"),
        'fill_co': PatternFill(start_color="CFFAFE", end_color="CFFAFE", fill_type="solid"),
        'font_co': Font(name="Calibri", size=10, bold=True, color="0E7490"),
        'fill_woff': PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
        'font_woff': Font(name="Calibri", size=10, bold=True, color="92400E"),
        'fill_hld_header': PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid"),
        'font_hld_header': Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    }
    return styles

def _populate_attendance_worksheet(ws, workers, days_list, days_meta, title_main, subtitle_text, styles, show_dept_col=True):
    """
    Populates an OpenPyXL worksheet with formatted matrix attendance data,
    department summaries, column totals, and executive sign-off blocks.
    """
    ws.views.sheetView[0].showGridLines = True
    thin_border = styles['thin_border']
    double_bottom_border = styles['double_bottom_border']

    # Column header structure
    if show_dept_col:
        headers = ["Emp ID", "Worker Name", "Department", "Shift"]
        fixed_cols = 4
    else:
        headers = ["Emp ID", "Worker Name", "Shift"]
        fixed_cols = 3

    for d in days_list:
        headers.append(f"{d:02d}")
    headers.extend(["Present (P)", "Half Day (HD)", "Absent (A)", "Leave (LV)", "Holiday (HLD)", "Comp-Off (CO)", "Off (W-OFF)", "Payable Days"])

    total_cols = len(headers)
    last_col_letter = get_column_letter(total_cols)

    # Title Banner
    ws.merge_cells(f'A1:{last_col_letter}1')
    ws['A1'] = title_main
    ws['A1'].font = Font(name="Calibri", size=15, bold=True, color="0F172A")
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells(f'A2:{last_col_letter}2')
    ws['A2'] = subtitle_text
    ws['A2'].font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws['A2'].alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[4].height = 28

    # Render Headers
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

        day_num = col_idx - fixed_cols
        if 1 <= day_num <= len(days_list) and days_meta.get(day_num, {}).get('is_holiday'):
            cell.fill = styles['fill_hld_header']
            cell.font = styles['font_hld_header']
        else:
            cell.fill = styles['fill_header']
            cell.font = styles['font_header']

    # Render Worker Rows
    current_row = 5
    tot_p = 0
    tot_hd = 0
    tot_a = 0
    tot_lv = 0
    tot_hld = 0
    tot_co = 0
    tot_off = 0
    tot_payable = 0.0

    for w in workers:
        ws.row_dimensions[current_row].height = 20

        # Fixed Columns
        c1 = ws.cell(row=current_row, column=1, value=w.get('enroll_number', ''))
        c1.alignment = Alignment(horizontal="center", vertical="center")
        c1.font = Font(name="Calibri", size=10, bold=True)
        c1.border = thin_border

        c2 = ws.cell(row=current_row, column=2, value=w.get('name', ''))
        c2.alignment = Alignment(horizontal="left", vertical="center")
        c2.font = Font(name="Calibri", size=10, bold=True)
        c2.border = thin_border

        if show_dept_col:
            c3 = ws.cell(row=current_row, column=3, value=w.get('department', 'General'))
            c3.alignment = Alignment(horizontal="left", vertical="center")
            c3.font = Font(name="Calibri", size=9, color="334155")
            c3.border = thin_border

            c4 = ws.cell(row=current_row, column=4, value=w.get('shift_name', 'General'))
            c4.alignment = Alignment(horizontal="left", vertical="center")
            c4.font = Font(name="Calibri", size=9, color="64748B")
            c4.border = thin_border
        else:
            c3 = ws.cell(row=current_row, column=3, value=w.get('shift_name', 'General'))
            c3.alignment = Alignment(horizontal="left", vertical="center")
            c3.font = Font(name="Calibri", size=9, color="64748B")
            c3.border = thin_border

        # Days cells
        col_offset = fixed_cols + 1
        worker_days = w.get('days', {})
        for day in days_list:
            day_str = str(day)
            day_info = worker_days.get(day_str, {})
            status = day_info.get('status', '-')

            cell = ws.cell(row=current_row, column=col_offset, value=status)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

            if status == 'P':
                cell.fill = styles['fill_p']
                cell.font = styles['font_p']
            elif status == 'HD':
                cell.fill = styles['fill_hd']
                cell.font = styles['font_hd']
            elif status == 'A':
                cell.fill = styles['fill_a']
                cell.font = styles['font_a']
            elif status == 'LV':
                cell.fill = styles['fill_lv']
                cell.font = styles['font_lv']
            elif status == 'HLD':
                cell.fill = styles['fill_hld']
                cell.font = styles['font_hld']
            elif status == 'CO':
                cell.fill = styles['fill_co']
                cell.font = styles['font_co']
            elif status == 'W-OFF':
                cell.fill = styles['fill_woff']
                cell.font = styles['font_woff']
            elif status == 'OFF':
                cell.fill = styles['fill_off']
                cell.font = styles['font_off']
            else:
                cell.font = Font(name="Calibri", size=10, color="94A3B8")

            col_offset += 1

        # Summary columns
        sum_data = w.get('summary', {})
        p_val = sum_data.get('present', 0)
        hd_val = sum_data.get('half_day', 0)
        a_val = sum_data.get('absent', 0)
        lv_val = sum_data.get('leave', 0)
        hld_val = sum_data.get('holiday', 0)
        co_val = sum_data.get('comp_off', 0)
        off_val = sum_data.get('off', 0)
        payable_val = sum_data.get('payable_days', 0.0)

        tot_p += p_val
        tot_hd += hd_val
        tot_a += a_val
        tot_lv += lv_val
        tot_hld += hld_val
        tot_co += co_val
        tot_off += off_val
        tot_payable += payable_val

        sum_vals = [p_val, hd_val, a_val, lv_val, hld_val, co_val, off_val, payable_val]
        for s_idx, val in enumerate(sum_vals):
            c_sum = ws.cell(row=current_row, column=col_offset + s_idx, value=val)
            c_sum.alignment = Alignment(horizontal="center", vertical="center")
            c_sum.font = Font(name="Calibri", size=10, bold=True)
            c_sum.border = thin_border
            if s_idx == 7: # Payable days
                c_sum.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
                c_sum.font = Font(name="Calibri", size=10, bold=True, color="1E40AF")

        current_row += 1

    # Total Summary Row at Bottom
    ws.row_dimensions[current_row].height = 22
    total_label_cell = ws.cell(row=current_row, column=1, value="TOTAL")
    total_label_cell.alignment = Alignment(horizontal="center", vertical="center")
    total_label_cell.fill = styles['fill_total']
    total_label_cell.font = styles['font_total']
    total_label_cell.border = double_bottom_border

    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=fixed_cols)
    for c_i in range(1, fixed_cols + 1):
        ws.cell(row=current_row, column=c_i).fill = styles['fill_total']
        ws.cell(row=current_row, column=c_i).border = double_bottom_border

    # Blank out day cells on total row
    col_offset = fixed_cols + 1
    for d in days_list:
        c_blank = ws.cell(row=current_row, column=col_offset, value="")
        c_blank.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        c_blank.border = double_bottom_border
        col_offset += 1

    # Totals in summary columns
    overall_sums = [tot_p, tot_hd, tot_a, tot_lv, tot_hld, tot_co, tot_off, round(tot_payable, 1)]
    for s_idx, sum_val in enumerate(overall_sums):
        c_tot = ws.cell(row=current_row, column=col_offset + s_idx, value=sum_val)
        c_tot.alignment = Alignment(horizontal="center", vertical="center")
        c_tot.font = Font(name="Calibri", size=10, bold=True, color="0F172A")
        c_tot.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        c_tot.border = double_bottom_border
        if s_idx == 7:
            c_tot.fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
            c_tot.font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")

    # Verification Sign-Off Blocks (3 columns)
    sign_row_start = current_row + 3
    ws.row_dimensions[sign_row_start].height = 20
    ws.row_dimensions[sign_row_start + 1].height = 35
    ws.row_dimensions[sign_row_start + 2].height = 20

    sign_boxes = [
        ("Prepared By:", "Shift Supervisor / Timekeeper", 1, min(fixed_cols + 3, total_cols)),
        ("Verified By:", "HR & Payroll Manager", min(fixed_cols + 5, total_cols), min(fixed_cols + 14, total_cols)),
        ("Authorized & Approved By:", "Plant Head / Managing Director", min(fixed_cols + 16, total_cols), total_cols)
    ]

    for label, role, c_start, c_end in sign_boxes:
        if c_start < c_end:
            ws.merge_cells(start_row=sign_row_start, start_column=c_start, end_row=sign_row_start, end_column=c_end)
            ws.merge_cells(start_row=sign_row_start + 1, start_column=c_start, end_row=sign_row_start + 1, end_column=c_end)
            ws.merge_cells(start_row=sign_row_start + 2, start_column=c_start, end_row=sign_row_start + 2, end_column=c_end)

            c_lbl = ws.cell(row=sign_row_start, column=c_start, value=label)
            c_lbl.font = Font(name="Calibri", size=10, bold=True, color="0F172A")
            c_lbl.alignment = Alignment(horizontal="left", vertical="center")

            c_sig = ws.cell(row=sign_row_start + 1, column=c_start, value="")
            c_sig.border = Border(bottom=Side(style='thin', color='94A3B8'))

            c_role = ws.cell(row=sign_row_start + 2, column=c_start, value=role)
            c_role.font = Font(name="Calibri", size=9, italic=True, color="64748B")
            c_role.alignment = Alignment(horizontal="left", vertical="center")

    # Column Widths
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 24
    if show_dept_col:
        ws.column_dimensions['C'].width = 22
        ws.column_dimensions['D'].width = 18
    else:
        ws.column_dimensions['C'].width = 18

    for d_idx in range(fixed_cols + 1, fixed_cols + 1 + len(days_list)):
        col_letter = get_column_letter(d_idx)
        ws.column_dimensions[col_letter].width = 4.5
    for s_idx in range(fixed_cols + 1 + len(days_list), total_cols + 1):
        col_letter = get_column_letter(s_idx)
        ws.column_dimensions[col_letter].width = 13.5

    # Freeze panes so worker ID & name remain visible when scrolling right
    freeze_col = get_column_letter(fixed_cols + 1)
    ws.freeze_panes = f"{freeze_col}5"


def generate_monthly_excel(matrix_data, company_name="Sai Krishna Enterprises", year=2026, month=10, department=None):
    """
    Generates a single-sheet executive attendance register (.xlsx),
    optionally filtered by department, with holiday purple accents and signature block.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    month_name = calendar.month_name[month]

    dept_target = department or matrix_data.get('selected_department') or 'ALL'
    is_filtered = (dept_target.strip().upper() != 'ALL')

    sheet_title = clean_sheet_name(f"{dept_target[:14]}_{month_name[:3]}_{year}") if is_filtered else f"{month_name[:3]}_{year}_Attendance"
    ws.title = sheet_title
    ws.sheet_properties.tabColor = "0284C7" if is_filtered else "1E293B"

    styles = _get_styles()
    days_list = matrix_data.get('days', list(range(1, 32)))
    days_meta = {d.get('day'): d for d in matrix_data.get('days_meta', [])}
    workers = matrix_data.get('workers', [])

    dept_display = dept_target.upper() if is_filtered else "ALL DEPARTMENTS & PRODUCTION LINES"
    title_main = f"{company_name.upper()} - MONTHLY ATTENDANCE REGISTER ({dept_display})"
    subtitle = f"Period: {month_name} {year} | Active Workforce: {len(workers)} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    _populate_attendance_worksheet(
        ws=ws,
        workers=workers,
        days_list=days_list,
        days_meta=days_meta,
        title_main=title_main,
        subtitle_text=subtitle,
        styles=styles,
        show_dept_col=True
    )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def generate_department_pack_excel(matrix_data_full, company_name="Sai Krishna Enterprises", year=2026, month=10):
    """
    Generates a comprehensive, multi-tab Monthly Department Pack (.xlsx):
    - Tab 1: Consolidated Overview (All workers across all manufacturing lines)
    - Tab 2: Dept Analytics Summary (Executive KPI matrix: headcount, attendance rate %, payable totals)
    - Tab 3..N: Dedicated colored worksheets for each Department with department totals & supervisor sign-offs.
    """
    wb = openpyxl.Workbook()
    month_name = calendar.month_name[month]
    styles = _get_styles()

    days_list = matrix_data_full.get('days', list(range(1, 32)))
    days_meta = {d.get('day'): d for d in matrix_data_full.get('days_meta', [])}
    all_workers = matrix_data_full.get('workers', [])
    departments = matrix_data_full.get('departments', [])
    dept_summaries = matrix_data_full.get('department_summary', [])

    # Color palette for department tabs
    tab_colors = ["059669", "2563EB", "D97706", "7C3AED", "DC2626", "0891B2", "4F46E5", "0D9488"]

    # ---------------- 1. Consolidated Overview Sheet ----------------
    ws_con = wb.active
    ws_con.title = "Consolidated_Overview"
    ws_con.sheet_properties.tabColor = "0F172A"

    title_main = f"{company_name.upper()} - CONSOLIDATED MONTHLY ATTENDANCE REGISTER"
    subtitle = f"Consolidated All Divisions | Period: {month_name} {year} | Total Workforce: {len(all_workers)} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    _populate_attendance_worksheet(
        ws=ws_con,
        workers=all_workers,
        days_list=days_list,
        days_meta=days_meta,
        title_main=title_main,
        subtitle_text=subtitle,
        styles=styles,
        show_dept_col=True
    )

    # ---------------- 2. Department Analytics Summary Sheet ----------------
    ws_ana = wb.create_sheet(title="Dept_Analytics_Summary")
    ws_ana.sheet_properties.tabColor = "4338CA"
    ws_ana.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_ana.merge_cells('A1:K1')
    ws_ana['A1'] = f"{company_name.upper()} - DEPARTMENTAL WORKFORCE ANALYTICS & ATTENDANCE AUDIT"
    ws_ana['A1'].font = Font(name="Calibri", size=15, bold=True, color="0F172A")
    ws_ana['A1'].alignment = Alignment(horizontal="center", vertical="center")

    ws_ana.merge_cells('A2:K2')
    ws_ana['A2'] = f"Manufacturing Divisions & Functional Units | Period: {month_name} {year} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws_ana['A2'].font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws_ana['A2'].alignment = Alignment(horizontal="center", vertical="center")

    ws_ana.row_dimensions[1].height = 26
    ws_ana.row_dimensions[2].height = 18
    ws_ana.row_dimensions[4].height = 26

    ana_headers = [
        "Sl", "Manufacturing Division / Department", "Headcount",
        "Total Present (P)", "Half Days (HD)", "Absent (A)", "Leaves (LV)",
        "Holidays (HLD)", "Comp-Offs (CO)", "Total Payable Days", "Attendance Rate %"
    ]

    for col_idx, h in enumerate(ana_headers, 1):
        cell = ws_ana.cell(row=4, column=col_idx, value=h)
        cell.fill = styles['fill_header']
        cell.font = styles['font_header']
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = styles['thin_border']

    ana_row = 5
    tot_hc = 0
    tot_p = 0
    tot_hd = 0
    tot_a = 0
    tot_lv = 0
    tot_hld = 0
    tot_co = 0
    tot_payable = 0.0

    for sl, d_info in enumerate(dept_summaries, 1):
        ws_ana.row_dimensions[ana_row].height = 22
        hc = d_info.get('headcount', 0)
        p = d_info.get('present', 0)
        hd = d_info.get('half_day', 0)
        a = d_info.get('absent', 0)
        lv = d_info.get('leave', 0)
        hld = d_info.get('holiday', 0)
        co = d_info.get('comp_off', 0)
        payable = d_info.get('payable_days', 0.0)

        tot_hc += hc
        tot_p += p
        tot_hd += hd
        tot_a += a
        tot_lv += lv
        tot_hld += hld
        tot_co += co
        tot_payable += payable

        denom = (p + hd + a)
        rate = round(((p + (hd * 0.5)) / denom * 100.0), 1) if denom > 0 else 100.0

        row_vals = [sl, d_info.get('department', 'General'), hc, p, hd, a, lv, hld, co, payable, f"{rate}%"]

        for c_idx, val in enumerate(row_vals, 1):
            cell = ws_ana.cell(row=ana_row, column=c_idx, value=val)
            cell.border = styles['thin_border']
            if c_idx == 2:
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.font = Font(name="Calibri", size=10, bold=True)
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.font = Font(name="Calibri", size=10)

            if c_idx == 10: # Payable Days
                cell.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
                cell.font = Font(name="Calibri", size=10, bold=True, color="1E40AF")
            elif c_idx == 11: # Rate %
                cell.fill = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
                cell.font = Font(name="Calibri", size=10, bold=True, color="065F46")

        ana_row += 1

    # Total row on Analytics Sheet
    ws_ana.row_dimensions[ana_row].height = 24
    overall_denom = (tot_p + tot_hd + tot_a)
    overall_rate = round(((tot_p + (tot_hd * 0.5)) / overall_denom * 100.0), 1) if overall_denom > 0 else 100.0

    tot_vals = ["", "CONSOLIDATED COMPANY TOTAL", tot_hc, tot_p, tot_hd, tot_a, tot_lv, tot_hld, tot_co, round(tot_payable, 1), f"{overall_rate}%"]
    for c_idx, val in enumerate(tot_vals, 1):
        cell = ws_ana.cell(row=ana_row, column=c_idx, value=val)
        cell.border = styles['double_bottom_border']
        cell.fill = styles['fill_total']
        cell.font = styles['font_total']
        if c_idx == 2:
            cell.alignment = Alignment(horizontal="left", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="center", vertical="center")

    ws_ana.column_dimensions['A'].width = 8
    ws_ana.column_dimensions['B'].width = 32
    ws_ana.column_dimensions['C'].width = 12
    ws_ana.column_dimensions['D'].width = 16
    ws_ana.column_dimensions['E'].width = 14
    ws_ana.column_dimensions['F'].width = 13
    ws_ana.column_dimensions['G'].width = 13
    ws_ana.column_dimensions['H'].width = 14
    ws_ana.column_dimensions['I'].width = 14
    ws_ana.column_dimensions['J'].width = 18
    ws_ana.column_dimensions['K'].width = 18

    # ---------------- 3..N Dedicated Department Sheets ----------------
    for idx, dept in enumerate(departments):
        dept_workers = [w for w in all_workers if (w.get('department') or 'General') == dept]
        if not dept_workers:
            continue

        sheet_name = clean_sheet_name(dept)
        ws_dept = wb.create_sheet(title=sheet_name)
        ws_dept.sheet_properties.tabColor = tab_colors[idx % len(tab_colors)]

        dept_title = f"{company_name.upper()} - {dept.upper()} DIVISION"
        dept_subtitle = f"Monthly Attendance Register | Period: {month_name} {year} | Active Division Workforce: {len(dept_workers)} | In-Charge Audit"

        _populate_attendance_worksheet(
            ws=ws_dept,
            workers=dept_workers,
            days_list=days_list,
            days_meta=days_meta,
            title_main=dept_title,
            subtitle_text=dept_subtitle,
            styles=styles,
            show_dept_col=False # Already dedicated to this department
        )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def generate_weekly_excel(weekly_data, company_name="Sai Krishna Enterprises"):
    """
    Generates an executive weekly attendance timesheet in Excel format (.xlsx).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    week_no = weekly_data.get('week_number', '')
    year = weekly_data.get('year', 2026)
    range_display = weekly_data.get('range_display', '')
    ws.title = f"Week_{week_no}_{year}"

    ws.views.sheetView[0].showGridLines = True

    # Color definitions
    fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")

    fill_p = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    font_p = Font(name="Calibri", size=9, bold=True, color="065F46")

    fill_hd = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    font_hd = Font(name="Calibri", size=9, bold=True, color="92400E")

    fill_a = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    font_a = Font(name="Calibri", size=9, bold=True, color="991B1B")

    fill_off = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    font_off = Font(name="Calibri", size=9, bold=True, color="64748B")

    fill_lv = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    font_lv = Font(name="Calibri", size=9, bold=True, color="1E40AF")

    fill_hld = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid")
    font_hld = Font(name="Calibri", size=9, bold=True, color="6D28D9")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    stats = weekly_data.get('stats', {})
    days = weekly_data.get('days', [])
    workers = weekly_data.get('workers', [])

    total_cols = 4 + len(days) + 7
    last_col_letter = get_column_letter(total_cols)

    # Title Block
    ws.merge_cells(f'A1:{last_col_letter}1')
    ws['A1'] = f"{company_name.upper()} - WEEKLY ATTENDANCE REGISTER"
    ws['A1'].font = Font(name="Calibri", size=15, bold=True, color="0F172A")
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells(f'A2:{last_col_letter}2')
    ws['A2'] = f"Week {week_no} ({range_display}) | Attendance Rate: {stats.get('attendance_rate', '0%')} | Total Clocked: {stats.get('total_company_hours', '0h 0m')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws['A2'].font = Font(name="Calibri", size=10, italic=True, color="64748B")
    ws['A2'].alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[4].height = 28

    # Column Headers
    headers = ["Emp ID", "Worker Name", "Department", "Shift"]
    for d in days:
        headers.append(f"{d['day_name']}\n{d['date'][8:]}/{d['date'][5:7]}")
    headers.extend(["Present (P)", "Half Day (HD)", "Absent (A)", "Leave (LV)", "Holiday (HLD)", "Off (W-OFF)", "Total Clocked", "Payable Days"])

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Data Rows
    current_row = 5
    for w in workers:
        ws.row_dimensions[current_row].height = 38

        # Worker Info
        c1 = ws.cell(row=current_row, column=1, value=w.get('enroll_number', ''))
        c1.alignment = Alignment(horizontal="center", vertical="center")
        c1.font = Font(name="Calibri", size=10, bold=True)
        c1.border = thin_border

        c2 = ws.cell(row=current_row, column=2, value=w.get('name', ''))
        c2.alignment = Alignment(horizontal="left", vertical="center")
        c2.font = Font(name="Calibri", size=10, bold=True)
        c2.border = thin_border

        c3 = ws.cell(row=current_row, column=3, value=w.get('department', 'General'))
        c3.alignment = Alignment(horizontal="left", vertical="center")
        c3.font = Font(name="Calibri", size=9, color="475569")
        c3.border = thin_border

        c4 = ws.cell(row=current_row, column=4, value=w.get('shift_name', 'General'))
        c4.alignment = Alignment(horizontal="left", vertical="center")
        c4.font = Font(name="Calibri", size=9, color="475569")
        c4.border = thin_border

        # Days cells
        col_offset = 5
        worker_days = w.get('days', {})
        for d in days:
            d_str = d['date']
            d_info = worker_days.get(d_str, {})
            st = d_info.get('status', '-')

            if st in ('P', 'HD'):
                in_out = f"{d_info.get('first_in', '-')}-{d_info.get('last_out', '-')}"
                dur = d_info.get('duration', '-')
                late_mark = "*" if d_info.get('is_late') else ""
                val_text = f"{st}{late_mark}\n{in_out}\n{dur}"
            elif st == 'OFF':
                val_text = "OFF\nSunday"
            elif st == 'LV':
                val_text = "LEAVE\nApproved"
            elif st == 'HLD':
                h_name = d_info.get('holiday_name') or d_info.get('duration') or 'Official'
                val_text = f"HOLIDAY\n{h_name[:12]}"
            elif st == 'A':
                val_text = "ABSENT\nNo Punch"
            else:
                val_text = "-"

            cell = ws.cell(row=current_row, column=col_offset, value=val_text)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

            if st == 'P':
                cell.fill = fill_p
                cell.font = font_p
            elif st == 'HD':
                cell.fill = fill_hd
                cell.font = font_hd
            elif st == 'A':
                cell.fill = fill_a
                cell.font = font_a
            elif st == 'LV':
                cell.fill = fill_lv
                cell.font = font_lv
            elif st == 'OFF':
                cell.fill = fill_off
                cell.font = font_off
            else:
                cell.font = Font(name="Calibri", size=9, color="94A3B8")

            col_offset += 1

        # Summary columns
        sum_data = w.get('summary', {})
        sum_vals = [
            sum_data.get('present', 0),
            sum_data.get('half_day', 0),
            sum_data.get('absent', 0),
            sum_data.get('leave', 0),
            sum_data.get('off', 0),
            sum_data.get('total_duration', '0h 0m'),
            sum_data.get('payable_days', 0.0)
        ]

        for s_idx, val in enumerate(sum_vals):
            c_sum = ws.cell(row=current_row, column=col_offset + s_idx, value=val)
            c_sum.alignment = Alignment(horizontal="center", vertical="center")
            c_sum.font = Font(name="Calibri", size=10, bold=True)
            c_sum.border = thin_border
            if s_idx == 5: # Total Duration
                c_sum.font = Font(name="Calibri", size=10, bold=True, color="B45309")
            elif s_idx == 6: # Payable days
                c_sum.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
                c_sum.font = Font(name="Calibri", size=10, bold=True, color="1E40AF")

        current_row += 1

    # Column dimensions
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 16
    for d_idx in range(5, 5 + len(days)):
        col_letter = get_column_letter(d_idx)
        ws.column_dimensions[col_letter].width = 15
    for s_idx in range(5 + len(days), 5 + len(days) + 6):
        col_letter = get_column_letter(s_idx)
        ws.column_dimensions[col_letter].width = 13

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
