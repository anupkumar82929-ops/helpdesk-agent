CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE employees (
  employee_id TEXT PRIMARY KEY,
  full_name   TEXT NOT NULL,
  email       TEXT NOT NULL,
  phone       TEXT,            -- sensitive: not readable by the MCP role
  salary_inr  INTEGER,         -- sensitive: not readable by the MCP role
  department  TEXT,
  job_title   TEXT,
  manager_id  TEXT REFERENCES employees(employee_id),
  location    TEXT,
  hire_date   DATE
);

CREATE TABLE leave_balances (
  employee_id TEXT REFERENCES employees(employee_id),
  leave_type  TEXT,
  total_days  NUMERIC(4,1) NOT NULL,
  used_days   NUMERIC(4,1) NOT NULL,
  PRIMARY KEY (employee_id, leave_type)
);

CREATE TABLE it_assets (
  asset_id        TEXT PRIMARY KEY,
  employee_id     TEXT REFERENCES employees(employee_id),
  asset_type      TEXT,
  model           TEXT,
  serial_number   TEXT,
  assigned_on     DATE,
  warranty_expiry DATE,
  status          TEXT
);

CREATE TABLE tickets (
  id          SERIAL PRIMARY KEY,
  ticket_ref  TEXT,
  employee_id TEXT,
  category    TEXT,
  summary     TEXT NOT NULL,
  status      TEXT DEFAULT 'open',
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE doc_chunks (
  id          SERIAL PRIMARY KEY,
  source      TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content     TEXT NOT NULL,
  embedding   vector(768)
);

INSERT INTO employees (employee_id, full_name, email, phone, salary_inr, department, job_title, manager_id, location, hire_date) VALUES
('E101','Priya Sharma','priya.sharma@acme.example','+91 98765 43210',1800000,'Engineering','Engineering Manager',NULL,'Bengaluru','2019-03-11'),
('E105','Meera Nair','meera.nair@acme.example','+91 98111 22233',2200000,'HR','HR Head',NULL,'Mumbai','2018-05-02'),
('E106','Arjun Rao','arjun.rao@acme.example','+91 97777 88899',2400000,'Finance','Finance Controller',NULL,'Delhi','2017-11-13'),
('E102','Rahul Verma','rahul.verma@acme.example','+91 91234 56789',1200000,'Engineering','Software Engineer','E101','Bengaluru','2021-07-05'),
('E103','Anita Desai','anita.desai@acme.example','+91 99887 76655',1000000,'HR','HR Executive','E105','Mumbai','2022-01-17'),
('E104','Vikram Singh','vikram.singh@acme.example','+91 90000 11122',1500000,'Finance','Senior Analyst','E106','Delhi','2020-09-21');

INSERT INTO leave_balances VALUES
('E101','annual',18,4),('E101','casual',8,2),('E101','sick',10,0),
('E102','annual',18,7.5),('E102','casual',8,5),('E102','sick',10,3),
('E103','annual',18,12),('E103','casual',8,1),('E103','sick',10,6),
('E104','annual',18,2),('E104','casual',8,0),('E104','sick',10,1),
('E105','annual',18,9),('E105','casual',8,3),('E105','sick',10,0),
('E106','annual',18,16),('E106','casual',8,8),('E106','sick',10,2);

INSERT INTO it_assets VALUES
('A-1001','E101','Laptop','MacBook Pro 14 M3','C02XK1ABJG5H','2023-04-01','2026-04-01','active'),
('A-1002','E102','Laptop','Dell Latitude 7440','DL7440-83KQ21','2022-08-10','2025-08-10','active'),
('A-1003','E102','Monitor','Dell U2723QE','MN-77123','2022-08-10','2025-08-10','active'),
('A-1004','E103','Laptop','Lenovo ThinkPad T14','PF3QW8XZ','2022-02-01','2025-02-01','repair'),
('A-1005','E104','Laptop','HP EliteBook 840 G10','5CG3412XYZ','2023-10-15','2026-10-15','active'),
('A-1006','E104','Mobile','iPhone 14','F2LXQ0AAPQ','2023-10-15','2025-10-15','active'),
('A-1007','E105','Laptop','MacBook Air M2','FVFH22ABC1','2022-06-20','2025-06-20','active');

-- Read-only role for the MCP server (least privilege).
-- Column-level grant: salary and phone are NOT readable through MCP.
CREATE ROLE mcp_reader LOGIN PASSWORD 'mcp_reader';
GRANT USAGE ON SCHEMA public TO mcp_reader;
GRANT SELECT (employee_id, full_name, email, department, job_title, manager_id, location, hire_date) ON employees TO mcp_reader;
GRANT SELECT ON leave_balances, it_assets TO mcp_reader;
