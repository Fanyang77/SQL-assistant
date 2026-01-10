AI SQL Assistant

A web-based SQL Assistant built with Streamlit, OpenAI GPT, and SQLAlchemy.
This app allows users to connect to any SQL database, ask questions in plain English, and instantly receive SQL queries, results, and visualizations.

It is designed for analysts, data scientists, and non-technical users who want to explore databases without writing SQL manually.

🚀 What it does

Connect to any SQL database using a connection URL

Or use a built-in demo SQLite database

Convert natural language → SQL

Automatically explain each generated query

Display results in an interactive table

Generate Vega-Lite charts (bar, line, scatter, etc.)

Enforce read-only safety (only SELECT queries allowed)

🧠 How it works

The user enters a question in natural language

The app sends the database schema and the question to an LLM

The LLM generates safe, validated SQL

The query is executed

Results are shown as:

A data table

An auto-generated chart (when appropriate)

This makes the system both powerful and auditable — users can see exactly what SQL was executed.

📂 Project Structure
AI_SQL_Assistant/
├── app.py               # Main Streamlit application
├── import_sqlite3.py    # Helper script to create demo SQLite DB
├── demo.sqlite          # Built-in demo database
├── README.md            # Documentation
├── requirements.txt    # Python dependencies


.env is used locally for the OpenAI API key but should not be committed to GitHub.

⚙️ Installation (Local)
1) Install Python

Make sure Python 3.9+ is installed:

python --version


Download if needed: https://www.python.org/downloads

2) Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate     # Windows
# or
source venv/bin/activate  # Mac/Linux

3) Install dependencies
pip install -r requirements.txt

4) Set your OpenAI API key

Create a file called .env in the project root:

OPENAI_API_KEY=sk-your-key-here

5) Run the app
streamlit run app.py


Open in your browser:

http://localhost:8501

🧪 Using the App
Option 1 — Built-in Demo Database

Leave the Database URL field empty

Click Connect

The app loads demo.sqlite

Try questions like:

“Show all employees.”

“What is the average salary by city?”

“Show a bar chart of salary by department.”

Option 2 — Connect to Your Own Database

Enter a SQLAlchemy connection string:

Database	Example
SQLite	sqlite:///C:/path/to/db.sqlite
PostgreSQL	postgresql://user:password@host:5432/dbname
MySQL	mysql+pymysql://user:password@host:3306/dbname
DuckDB	duckdb:///mydata.duckdb

Then click Connect and start asking questions.

📊 Example Demo Database

The demo database contains:

departments
department_id	department_name
1	Engineering
2	Marketing
3	Finance
employees
employee_id	name	city	department_id	salary	hire_date
1	Alice	New York	1	95000	2020-03-10
...	...	...	...	...	...
projects
project_id	project_name	department_id	budget	start_date	end_date
101	Product Redesign	1	250000	2022-01-01	2022-06-30
...	...	...	...	...	...
🔮 Future Improvements

Multiple simultaneous database connections

More advanced visualization templates

Export to CSV / Excel

Query history & prompt memory

Integration with LangChain

👤 Author

Fan Yang
Fordham University — Gabelli School of Business
Focus: AI in Business · Data Science · LLM Applications
