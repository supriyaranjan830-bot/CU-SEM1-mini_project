-- ============================================================================
--  EMPLOYEE MANAGEMENT SYSTEM
--  Language: Oracle PL/SQL
--
--  Features:
--    - Employee table with full HR fields
--    - Department reference table
--    - Attendance tracking table with daily records
--    - Automated salary calculation stored procedure
--      (Basic + HRA + DA + Conveyance - PF - ESI - Prof.Tax - TDS)
--    - Attendance-based salary proration
--    - Payroll processing procedure (bulk for all employees)
--    - Employee reporting views & procedures
--    - Triggers for audit logging and auto-ID generation
--
--  How to Run:
--    Option A: Oracle Live SQL (FREE, no install)
--      1. Go to https://livesql.oracle.com
--      2. Sign in with Oracle account (free registration)
--      3. Paste this entire script into SQL Worksheet
--      4. Click "Run Script"
--
--    Option B: Oracle XE (Local)
--      1. Install Oracle Database XE (free) from oracle.com
--      2. Connect via SQLPlus: sqlplus system/password@XE
--      3. Run: @employee_management.sql
--
--    Option C: Oracle SQL Developer
--      1. Open SQL Developer (free download from oracle.com)
--      2. Connect to your Oracle DB
--      3. Open this file → Run Script (F5)
-- ============================================================================


-- ======================== CLEANUP (if re-running) ========================
BEGIN
    FOR rec IN (SELECT table_name FROM user_tables WHERE table_name IN
        ('DEPARTMENTS','EMPLOYEES','ATTENDANCE','PAYROLL','AUDIT_LOG')) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || rec.table_name || ' CASCADE CONSTRAINTS';
    END LOOP;
    FOR rec IN (SELECT sequence_name FROM user_sequences WHERE sequence_name IN
        ('EMP_SEQ','ATT_SEQ','PAY_SEQ','AUDIT_SEQ')) LOOP
        EXECUTE IMMEDIATE 'DROP SEQUENCE ' || rec.sequence_name;
    END LOOP;
END;
/


-- ======================== SEQUENCES ========================

CREATE SEQUENCE emp_seq   START WITH 1001 INCREMENT BY 1;
CREATE SEQUENCE att_seq   START WITH 1    INCREMENT BY 1;
CREATE SEQUENCE pay_seq   START WITH 1    INCREMENT BY 1;
CREATE SEQUENCE audit_seq START WITH 1    INCREMENT BY 1;


-- ======================== TABLES ========================

-- Department Master Table
CREATE TABLE departments (
    dept_id     NUMBER(5)    PRIMARY KEY,
    dept_name   VARCHAR2(50) NOT NULL UNIQUE,
    location    VARCHAR2(50),
    created_at  DATE DEFAULT SYSDATE
);

-- Employee Table
CREATE TABLE employees (
    emp_id        NUMBER(10)    PRIMARY KEY,
    emp_name      VARCHAR2(100) NOT NULL,
    email         VARCHAR2(100) UNIQUE,
    phone         VARCHAR2(15),
    dept_id       NUMBER(5)     REFERENCES departments(dept_id),
    designation   VARCHAR2(50)  NOT NULL,
    basic_salary  NUMBER(10,2)  NOT NULL CHECK (basic_salary > 0),
    join_date     DATE          DEFAULT SYSDATE,
    status        VARCHAR2(20)  DEFAULT 'Active'
                  CHECK (status IN ('Active','On Leave','Probation','Resigned')),
    created_at    DATE          DEFAULT SYSDATE,
    updated_at    DATE          DEFAULT SYSDATE
);

-- Attendance Table
CREATE TABLE attendance (
    att_id      NUMBER(10)    PRIMARY KEY,
    emp_id      NUMBER(10)    REFERENCES employees(emp_id),
    att_date    DATE          NOT NULL,
    status      VARCHAR2(20)  NOT NULL
                CHECK (status IN ('Present','Absent','Half Day','Leave')),
    remarks     VARCHAR2(200),
    CONSTRAINT  att_unique UNIQUE (emp_id, att_date)
);

-- Payroll Table
CREATE TABLE payroll (
    pay_id          NUMBER(10)    PRIMARY KEY,
    emp_id          NUMBER(10)    REFERENCES employees(emp_id),
    pay_month       NUMBER(2)     NOT NULL,
    pay_year        NUMBER(4)     NOT NULL,
    basic_salary    NUMBER(10,2),
    hra             NUMBER(10,2),
    da              NUMBER(10,2),
    conveyance      NUMBER(10,2),
    gross_salary    NUMBER(10,2),
    pf_deduction    NUMBER(10,2),
    esi_deduction   NUMBER(10,2),
    prof_tax        NUMBER(10,2),
    tds             NUMBER(10,2),
    total_deduction NUMBER(10,2),
    net_salary      NUMBER(10,2),
    days_present    NUMBER(5,1),
    total_days      NUMBER(5),
    processed_date  DATE DEFAULT SYSDATE,
    CONSTRAINT pay_unique UNIQUE (emp_id, pay_month, pay_year)
);

-- Audit Log Table
CREATE TABLE audit_log (
    log_id      NUMBER(10)    PRIMARY KEY,
    table_name  VARCHAR2(50),
    action      VARCHAR2(20),
    emp_id      NUMBER(10),
    old_value   VARCHAR2(500),
    new_value   VARCHAR2(500),
    changed_by  VARCHAR2(50)  DEFAULT USER,
    changed_at  DATE          DEFAULT SYSDATE
);


-- ======================== TRIGGERS ========================

-- Auto-generate Employee ID
CREATE OR REPLACE TRIGGER trg_emp_id
BEFORE INSERT ON employees
FOR EACH ROW
BEGIN
    IF :NEW.emp_id IS NULL THEN
        :NEW.emp_id := emp_seq.NEXTVAL;
    END IF;
END;
/

-- Auto-generate Attendance ID
CREATE OR REPLACE TRIGGER trg_att_id
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    IF :NEW.att_id IS NULL THEN
        :NEW.att_id := att_seq.NEXTVAL;
    END IF;
END;
/

-- Auto-generate Payroll ID
CREATE OR REPLACE TRIGGER trg_pay_id
BEFORE INSERT ON payroll
FOR EACH ROW
BEGIN
    IF :NEW.pay_id IS NULL THEN
        :NEW.pay_id := pay_seq.NEXTVAL;
    END IF;
END;
/

-- Audit Trail: Log employee updates
CREATE OR REPLACE TRIGGER trg_emp_audit
AFTER UPDATE ON employees
FOR EACH ROW
BEGIN
    IF :OLD.basic_salary != :NEW.basic_salary THEN
        INSERT INTO audit_log (log_id, table_name, action, emp_id, old_value, new_value)
        VALUES (audit_seq.NEXTVAL, 'EMPLOYEES', 'SALARY_CHANGE', :NEW.emp_id,
                'Salary: ' || :OLD.basic_salary, 'Salary: ' || :NEW.basic_salary);
    END IF;
    IF :OLD.status != :NEW.status THEN
        INSERT INTO audit_log (log_id, table_name, action, emp_id, old_value, new_value)
        VALUES (audit_seq.NEXTVAL, 'EMPLOYEES', 'STATUS_CHANGE', :NEW.emp_id,
                'Status: ' || :OLD.status, 'Status: ' || :NEW.status);
    END IF;
    -- Update timestamp
    -- (Note: cannot modify :NEW in AFTER trigger; handled via procedure)
END;
/

-- Trigger: Prevent deleting active employees
CREATE OR REPLACE TRIGGER trg_emp_delete_check
BEFORE DELETE ON employees
FOR EACH ROW
BEGIN
    IF :OLD.status = 'Active' THEN
        RAISE_APPLICATION_ERROR(-20001,
            'Cannot delete active employee ' || :OLD.emp_name ||
            '. Change status to Resigned first.');
    END IF;
END;
/


-- ======================== STORED PROCEDURES ========================

-- ---------------------------------------------------------------------------
-- Procedure: Add New Employee
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_add_employee (
    p_name       IN VARCHAR2,
    p_email      IN VARCHAR2,
    p_phone      IN VARCHAR2,
    p_dept_id    IN NUMBER,
    p_designation IN VARCHAR2,
    p_salary     IN NUMBER,
    p_join_date  IN DATE DEFAULT SYSDATE
) AS
BEGIN
    INSERT INTO employees (emp_name, email, phone, dept_id, designation,
                           basic_salary, join_date)
    VALUES (p_name, p_email, p_phone, p_dept_id, p_designation,
            p_salary, p_join_date);

    DBMS_OUTPUT.PUT_LINE('Employee ' || p_name || ' added successfully.');
    COMMIT;
EXCEPTION
    WHEN DUP_VAL_ON_INDEX THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: Email ' || p_email || ' already exists.');
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: ' || SQLERRM);
        ROLLBACK;
END;
/

-- ---------------------------------------------------------------------------
-- Procedure: Mark Attendance
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_mark_attendance (
    p_emp_id   IN NUMBER,
    p_date     IN DATE,
    p_status   IN VARCHAR2,
    p_remarks  IN VARCHAR2 DEFAULT NULL
) AS
BEGIN
    MERGE INTO attendance a
    USING (SELECT p_emp_id AS emp_id, p_date AS att_date FROM dual) d
    ON (a.emp_id = d.emp_id AND a.att_date = d.att_date)
    WHEN MATCHED THEN
        UPDATE SET status = p_status, remarks = p_remarks
    WHEN NOT MATCHED THEN
        INSERT (emp_id, att_date, status, remarks)
        VALUES (p_emp_id, p_date, p_status, p_remarks);

    DBMS_OUTPUT.PUT_LINE('Attendance marked: EMP ' || p_emp_id ||
                         ' | ' || p_date || ' | ' || p_status);
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: ' || SQLERRM);
        ROLLBACK;
END;
/

-- ---------------------------------------------------------------------------
-- Procedure: Calculate Salary for One Employee (PL/SQL Payroll Engine)
--   Earnings:
--     HRA        = 40% of Basic
--     DA         = 20% of Basic
--     Conveyance = Rs. 1600 fixed
--     Gross      = Basic + HRA + DA + Conveyance
--   Deductions:
--     PF         = 12% of Basic
--     ESI        = 0.75% of Gross (if Gross < 21000)
--     Prof. Tax  = Rs. 200 (if Gross > 15000)
--     TDS        = 5% of (Gross - 50000) if Gross > 50000
--   Attendance Proration:
--     Adjusted Basic = (Basic / Total Days) * Days Present
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_calculate_salary (
    p_emp_id    IN NUMBER,
    p_month     IN NUMBER,
    p_year      IN NUMBER
) AS
    v_basic       NUMBER(10,2);
    v_hra         NUMBER(10,2);
    v_da          NUMBER(10,2);
    v_conv        NUMBER(10,2) := 1600;
    v_gross       NUMBER(10,2);
    v_pf          NUMBER(10,2);
    v_esi         NUMBER(10,2);
    v_pt          NUMBER(10,2);
    v_tds         NUMBER(10,2);
    v_total_ded   NUMBER(10,2);
    v_net         NUMBER(10,2);
    v_days_present NUMBER(5,1) := 0;
    v_total_days  NUMBER(5);
    v_day_rate    NUMBER(10,2);
    v_emp_name    VARCHAR2(100);
    v_emp_basic   NUMBER(10,2);

    CURSOR c_attendance IS
        SELECT status FROM attendance
        WHERE emp_id = p_emp_id
          AND EXTRACT(MONTH FROM att_date) = p_month
          AND EXTRACT(YEAR FROM att_date) = p_year;
BEGIN
    -- Get employee details
    SELECT emp_name, basic_salary INTO v_emp_name, v_emp_basic
    FROM employees WHERE emp_id = p_emp_id;

    -- Calculate total working days in month (excluding Sundays)
    v_total_days := 0;
    FOR d IN 1..TO_NUMBER(TO_CHAR(LAST_DAY(TO_DATE(p_year||'-'||LPAD(p_month,2,'0')||'-01','YYYY-MM-DD')),'DD')) LOOP
        IF TO_CHAR(TO_DATE(p_year||'-'||LPAD(p_month,2,'0')||'-'||LPAD(d,2,'0'),'YYYY-MM-DD'),'DY','NLS_DATE_LANGUAGE=ENGLISH') != 'SUN' THEN
            v_total_days := v_total_days + 1;
        END IF;
    END LOOP;

    -- Count present days from attendance records
    v_days_present := v_total_days; -- Default: assume all present if no record
    FOR rec IN c_attendance LOOP
        IF rec.status = 'Absent' THEN
            v_days_present := v_days_present - 1;
        ELSIF rec.status = 'Half Day' THEN
            v_days_present := v_days_present - 0.5;
        ELSIF rec.status = 'Leave' THEN
            v_days_present := v_days_present - 1;
        END IF;
    END LOOP;

    IF v_days_present < 0 THEN v_days_present := 0; END IF;

    -- Prorate basic salary based on attendance
    v_day_rate := v_emp_basic / v_total_days;
    v_basic    := ROUND(v_day_rate * v_days_present, 2);

    -- Calculate earnings
    v_hra   := ROUND(v_basic * 0.40, 2);
    v_da    := ROUND(v_basic * 0.20, 2);
    v_gross := v_basic + v_hra + v_da + v_conv;

    -- Calculate deductions
    v_pf  := ROUND(v_basic * 0.12, 2);
    v_esi := CASE WHEN v_gross < 21000 THEN ROUND(v_gross * 0.0075, 2) ELSE 0 END;
    v_pt  := CASE WHEN v_gross > 15000 THEN 200 ELSE 0 END;
    v_tds := CASE WHEN v_gross > 50000 THEN ROUND((v_gross - 50000) * 0.05, 2) ELSE 0 END;
    v_total_ded := v_pf + v_esi + v_pt + v_tds;

    -- Net salary
    v_net := v_gross - v_total_ded;

    -- Insert/update payroll record
    MERGE INTO payroll p
    USING (SELECT p_emp_id AS emp_id, p_month AS pay_month, p_year AS pay_year FROM dual) d
    ON (p.emp_id = d.emp_id AND p.pay_month = d.pay_month AND p.pay_year = d.pay_year)
    WHEN MATCHED THEN
        UPDATE SET basic_salary = v_basic, hra = v_hra, da = v_da, conveyance = v_conv,
                   gross_salary = v_gross, pf_deduction = v_pf, esi_deduction = v_esi,
                   prof_tax = v_pt, tds = v_tds, total_deduction = v_total_ded,
                   net_salary = v_net, days_present = v_days_present,
                   total_days = v_total_days, processed_date = SYSDATE
    WHEN NOT MATCHED THEN
        INSERT (emp_id, pay_month, pay_year, basic_salary, hra, da, conveyance,
                gross_salary, pf_deduction, esi_deduction, prof_tax, tds,
                total_deduction, net_salary, days_present, total_days)
        VALUES (p_emp_id, p_month, p_year, v_basic, v_hra, v_da, v_conv,
                v_gross, v_pf, v_esi, v_pt, v_tds,
                v_total_ded, v_net, v_days_present, v_total_days);

    DBMS_OUTPUT.PUT_LINE('-----------------------------------------------');
    DBMS_OUTPUT.PUT_LINE('PAYSLIP: ' || v_emp_name || ' (EMP-' || p_emp_id || ')');
    DBMS_OUTPUT.PUT_LINE('Period : ' || TO_CHAR(TO_DATE(p_month,'MM'),'Month') || ' ' || p_year);
    DBMS_OUTPUT.PUT_LINE('-----------------------------------------------');
    DBMS_OUTPUT.PUT_LINE('Attendance : ' || v_days_present || '/' || v_total_days || ' days');
    DBMS_OUTPUT.PUT_LINE('Basic      : Rs. ' || TO_CHAR(v_basic,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('HRA (40%)  : Rs. ' || TO_CHAR(v_hra,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('DA  (20%)  : Rs. ' || TO_CHAR(v_da,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('Conveyance : Rs. ' || TO_CHAR(v_conv,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('GROSS      : Rs. ' || TO_CHAR(v_gross,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('-----------------------------------------------');
    DBMS_OUTPUT.PUT_LINE('PF  (12%)  : Rs. ' || TO_CHAR(v_pf,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('ESI (0.75%): Rs. ' || TO_CHAR(v_esi,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('Prof. Tax  : Rs. ' || TO_CHAR(v_pt,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('TDS        : Rs. ' || TO_CHAR(v_tds,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('DEDUCTIONS : Rs. ' || TO_CHAR(v_total_ded,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('===============================================');
    DBMS_OUTPUT.PUT_LINE('NET SALARY : Rs. ' || TO_CHAR(v_net,'99,99,999.99'));
    DBMS_OUTPUT.PUT_LINE('===============================================');

    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: Employee ' || p_emp_id || ' not found.');
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: ' || SQLERRM);
        ROLLBACK;
END;
/

-- ---------------------------------------------------------------------------
-- Procedure: Process Payroll for ALL Active Employees
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_process_payroll (
    p_month IN NUMBER,
    p_year  IN NUMBER
) AS
    v_count NUMBER := 0;
    CURSOR c_emp IS
        SELECT emp_id, emp_name FROM employees WHERE status = 'Active';
BEGIN
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('================================================');
    DBMS_OUTPUT.PUT_LINE('  BULK PAYROLL PROCESSING');
    DBMS_OUTPUT.PUT_LINE('  Period: ' || TO_CHAR(TO_DATE(p_month,'MM'),'Month') || ' ' || p_year);
    DBMS_OUTPUT.PUT_LINE('================================================');
    DBMS_OUTPUT.PUT_LINE('');

    FOR emp IN c_emp LOOP
        sp_calculate_salary(emp.emp_id, p_month, p_year);
        v_count := v_count + 1;
        DBMS_OUTPUT.PUT_LINE('');
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('================================================');
    DBMS_OUTPUT.PUT_LINE('  Payroll processed for ' || v_count || ' employees.');
    DBMS_OUTPUT.PUT_LINE('================================================');
END;
/

-- ---------------------------------------------------------------------------
-- Procedure: Employee Attendance Report
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_attendance_report (
    p_month IN NUMBER,
    p_year  IN NUMBER
) AS
    v_present  NUMBER;
    v_absent   NUMBER;
    v_halfday  NUMBER;
    v_leave    NUMBER;
    v_total    NUMBER;
    v_pct      NUMBER(5,1);

    CURSOR c_emp IS
        SELECT emp_id, emp_name, dept_id FROM employees WHERE status = 'Active';
BEGIN
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('================================================================');
    DBMS_OUTPUT.PUT_LINE('  MONTHLY ATTENDANCE REPORT');
    DBMS_OUTPUT.PUT_LINE('  Period: ' || TO_CHAR(TO_DATE(p_month,'MM'),'Month') || ' ' || p_year);
    DBMS_OUTPUT.PUT_LINE('================================================================');
    DBMS_OUTPUT.PUT_LINE(RPAD('Employee',20) || RPAD('Present',10) || RPAD('Absent',10) ||
                         RPAD('Half Day',10) || RPAD('Leave',10) || 'Att %');
    DBMS_OUTPUT.PUT_LINE('----------------------------------------------------------------');

    FOR emp IN c_emp LOOP
        SELECT NVL(SUM(CASE WHEN status='Present'  THEN 1 ELSE 0 END),0),
               NVL(SUM(CASE WHEN status='Absent'   THEN 1 ELSE 0 END),0),
               NVL(SUM(CASE WHEN status='Half Day' THEN 1 ELSE 0 END),0),
               NVL(SUM(CASE WHEN status='Leave'    THEN 1 ELSE 0 END),0),
               COUNT(*)
        INTO   v_present, v_absent, v_halfday, v_leave, v_total
        FROM   attendance
        WHERE  emp_id = emp.emp_id
          AND  EXTRACT(MONTH FROM att_date) = p_month
          AND  EXTRACT(YEAR FROM att_date)  = p_year;

        IF v_total > 0 THEN
            v_pct := ROUND((v_present + v_halfday * 0.5) / v_total * 100, 1);
        ELSE
            v_pct := 0;
        END IF;

        DBMS_OUTPUT.PUT_LINE(RPAD(emp.emp_name,20) ||
                             RPAD(v_present,10) || RPAD(v_absent,10) ||
                             RPAD(v_halfday,10) || RPAD(v_leave,10) ||
                             v_pct || '%');
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('================================================================');
END;
/

-- ---------------------------------------------------------------------------
-- Procedure: Department-wise Salary Report
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_dept_salary_report AS
    CURSOR c_dept IS
        SELECT d.dept_name,
               COUNT(e.emp_id)       AS emp_count,
               SUM(e.basic_salary)   AS total_basic,
               AVG(e.basic_salary)   AS avg_basic,
               MIN(e.basic_salary)   AS min_basic,
               MAX(e.basic_salary)   AS max_basic
        FROM   departments d
        LEFT JOIN employees e ON d.dept_id = e.dept_id AND e.status = 'Active'
        GROUP BY d.dept_name
        ORDER BY total_basic DESC;
BEGIN
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('================================================================');
    DBMS_OUTPUT.PUT_LINE('  DEPARTMENT-WISE SALARY REPORT');
    DBMS_OUTPUT.PUT_LINE('================================================================');
    DBMS_OUTPUT.PUT_LINE(RPAD('Department',15) || RPAD('Emp#',6) ||
                         RPAD('Total Basic',14) || RPAD('Avg Basic',12) ||
                         RPAD('Min',10) || 'Max');
    DBMS_OUTPUT.PUT_LINE('----------------------------------------------------------------');

    FOR dept IN c_dept LOOP
        DBMS_OUTPUT.PUT_LINE(
            RPAD(dept.dept_name,15) ||
            RPAD(dept.emp_count,6) ||
            RPAD('Rs.' || TO_CHAR(NVL(dept.total_basic,0),'99,99,999'),14) ||
            RPAD('Rs.' || TO_CHAR(NVL(dept.avg_basic,0),'99,999'),12) ||
            RPAD('Rs.' || TO_CHAR(NVL(dept.min_basic,0),'99,999'),10) ||
            'Rs.' || TO_CHAR(NVL(dept.max_basic,0),'99,999')
        );
    END LOOP;
    DBMS_OUTPUT.PUT_LINE('================================================================');
END;
/


-- ======================== INSERT SAMPLE DATA ========================

-- Departments
INSERT INTO departments VALUES (10, 'IT',         'Bangalore', SYSDATE);
INSERT INTO departments VALUES (20, 'HR',         'Mumbai',    SYSDATE);
INSERT INTO departments VALUES (30, 'Finance',    'Delhi',     SYSDATE);
INSERT INTO departments VALUES (40, 'Marketing',  'Hyderabad', SYSDATE);
INSERT INTO departments VALUES (50, 'Operations', 'Pune',      SYSDATE);

-- Employees
BEGIN
    sp_add_employee('Aarav Mehta',   'aarav@company.com',  '9876543210', 10, 'Senior Developer',    75000, TO_DATE('2022-03-15','YYYY-MM-DD'));
    sp_add_employee('Priya Sharma',  'priya@company.com',  '9876543211', 20, 'HR Manager',          65000, TO_DATE('2021-06-01','YYYY-MM-DD'));
    sp_add_employee('Rohit Gupta',   'rohit@company.com',  '9876543212', 30, 'Finance Analyst',     58000, TO_DATE('2023-01-10','YYYY-MM-DD'));
    sp_add_employee('Sneha Patel',   'sneha@company.com',  '9876543213', 40, 'Marketing Executive', 48000, TO_DATE('2023-07-20','YYYY-MM-DD'));
    sp_add_employee('Vikram Singh',  'vikram@company.com', '9876543214', 50, 'Ops Lead',            62000, TO_DATE('2022-11-05','YYYY-MM-DD'));
    sp_add_employee('Deepa Nair',    'deepa@company.com',  '9876543215', 10, 'QA Engineer',         52000, TO_DATE('2023-04-12','YYYY-MM-DD'));
    sp_add_employee('Arjun Rao',     'arjun@company.com',  '9876543216', 30, 'Accountant',          45000, TO_DATE('2022-08-30','YYYY-MM-DD'));
    sp_add_employee('Kavya Joshi',   'kavya@company.com',  '9876543217', 40, 'Content Strategist',  42000, TO_DATE('2024-02-14','YYYY-MM-DD'));
END;
/

-- Sample Attendance for October 2024
DECLARE
    TYPE emp_ids_t IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
    v_emps emp_ids_t;
    v_status VARCHAR2(20);
    v_day DATE;
    v_rand NUMBER;
BEGIN
    SELECT emp_id BULK COLLECT INTO v_emps FROM employees WHERE status = 'Active';

    FOR i IN 1..v_emps.COUNT LOOP
        FOR d IN 1..31 LOOP
            v_day := TO_DATE('2024-10-' || LPAD(d, 2, '0'), 'YYYY-MM-DD');
            -- Skip Sundays
            IF TO_CHAR(v_day, 'DY', 'NLS_DATE_LANGUAGE=ENGLISH') != 'SUN' THEN
                v_rand := DBMS_RANDOM.VALUE(1, 100);
                IF v_rand <= 75 THEN
                    v_status := 'Present';
                ELSIF v_rand <= 85 THEN
                    v_status := 'Absent';
                ELSIF v_rand <= 92 THEN
                    v_status := 'Half Day';
                ELSE
                    v_status := 'Leave';
                END IF;
                sp_mark_attendance(v_emps(i), v_day, v_status);
            END IF;
        END LOOP;
    END LOOP;
END;
/


-- ======================== RUN DEMONSTRATIONS ========================

SET SERVEROUTPUT ON SIZE UNLIMITED;

PROMPT
PROMPT ================================================================
PROMPT   DEMO 1: EMPLOYEE LISTING
PROMPT ================================================================

SELECT emp_id, emp_name, designation,
       (SELECT dept_name FROM departments WHERE dept_id = e.dept_id) AS department,
       basic_salary, status
FROM employees e
ORDER BY emp_id;


PROMPT
PROMPT ================================================================
PROMPT   DEMO 2: PROCESS PAYROLL FOR OCTOBER 2024
PROMPT ================================================================

BEGIN
    sp_process_payroll(10, 2024);
END;
/


PROMPT
PROMPT ================================================================
PROMPT   DEMO 3: PAYROLL SUMMARY TABLE
PROMPT ================================================================

SELECT p.emp_id,
       e.emp_name,
       p.days_present || '/' || p.total_days AS attendance,
       p.gross_salary,
       p.total_deduction,
       p.net_salary
FROM payroll p
JOIN employees e ON p.emp_id = e.emp_id
WHERE p.pay_month = 10 AND p.pay_year = 2024
ORDER BY p.net_salary DESC;


PROMPT
PROMPT ================================================================
PROMPT   DEMO 4: ATTENDANCE REPORT
PROMPT ================================================================

BEGIN
    sp_attendance_report(10, 2024);
END;
/


PROMPT
PROMPT ================================================================
PROMPT   DEMO 5: DEPARTMENT SALARY REPORT
PROMPT ================================================================

BEGIN
    sp_dept_salary_report;
END;
/


PROMPT
PROMPT ================================================================
PROMPT   DEMO 6: AUDIT LOG
PROMPT ================================================================

-- Trigger a salary change to test audit
UPDATE employees SET basic_salary = 80000 WHERE emp_id = 1001;
COMMIT;

SELECT * FROM audit_log ORDER BY log_id;


PROMPT
PROMPT ================================================================
PROMPT   ALL DEMOS COMPLETE. Employee Management System is operational!
PROMPT ================================================================
