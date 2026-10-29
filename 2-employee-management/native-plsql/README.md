# 👔 Employee Management System — Native Oracle PL/SQL

## How to Run

### Option A: Oracle Live SQL (FREE — No Install Required!)
1. Go to **https://livesql.oracle.com**
2. Create a free Oracle account
3. Click **SQL Worksheet**
4. Paste the entire `employee_management.sql` file
5. Click **Run Script**
6. View output in the Results panel

### Option B: Oracle XE (Local Install)
```bash
# After installing Oracle XE (free):
sqlplus system/your_password@XE
@employee_management.sql
```

### Option C: Oracle SQL Developer
1. Download Oracle SQL Developer (free)
2. Connect to your Oracle database
3. Open `employee_management.sql`
4. Press F5 (Run Script)

## What's Inside (Pure PL/SQL)
- **5 Tables**: departments, employees, attendance, payroll, audit_log
- **4 Sequences**: auto-ID generation
- **5 Triggers**: auto-ID, audit logging, delete protection
- **6 Stored Procedures**:
  - `sp_add_employee` — Add with validation
  - `sp_mark_attendance` — MERGE-based upsert
  - `sp_calculate_salary` — Full payroll: Basic + HRA(40%) + DA(20%) + Conv − PF(12%) − ESI(0.75%) − Prof.Tax − TDS
  - `sp_process_payroll` — Bulk process all employees
  - `sp_attendance_report` — Monthly breakdown
  - `sp_dept_salary_report` — Department analytics
- **8 sample employees** with October 2024 attendance data
- **6 demo queries** that auto-run at the end
