import sqlite3

# Create or open a database file
conn = sqlite3.connect("mytest.db")
cur = conn.cursor()

# Drop old tables (optional, for repeat testing)
cur.executescript("""
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS projects;
""")

# --- Create tables ---
cur.executescript("""
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT,
    department_id INTEGER,
    salary REAL,
    hire_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT,
    department_id INTEGER,
    budget REAL,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);
""")

# --- Insert data ---
cur.executescript("""
INSERT INTO departments VALUES
    (1, 'Engineering'),
    (2, 'Marketing'),
    (3, 'Finance');

INSERT INTO employees VALUES
    (1, 'Alice', 'New York', 1, 95000, '2020-03-10'),
    (2, 'Bob', 'Chicago', 2, 72000, '2019-06-21'),
    (3, 'Charlie', 'San Francisco', 1, 105000, '2018-11-01'),
    (4, 'Diana', 'Boston', 3, 88000, '2021-01-15'),
    (5, 'Evan', 'Chicago', 2, 97000, '2022-04-05'),
    (6, 'Fiona', 'New York', 1, 110000, '2017-09-09'),
    (7, 'George', 'Austin', 3, 66000, '2020-12-01'),
    (8, 'Hannah', 'New York', 1, 99000, '2023-02-10'),
    (9, 'Ian', 'Chicago', 2, 78000, '2021-07-18'),
    (10, 'Julia', 'San Francisco', 3, 87000, '2022-12-12');

INSERT INTO projects VALUES
    (101, 'Product Redesign', 1, 250000, '2022-01-01', '2022-06-30'),
    (102, 'Mobile App', 1, 400000, '2023-03-01', '2023-12-31'),
    (103, 'Ad Campaign', 2, 150000, '2022-04-01', '2022-08-01'),
    (104, 'Rebranding', 2, 90000, '2023-01-15', '2023-05-15'),
    (105, 'Budget Audit', 3, 50000, '2021-09-01', '2021-12-01');
""")

conn.commit()
conn.close()
print("✅ Database 'mytest.db' created successfully with 3 tables and 10+ rows!")
