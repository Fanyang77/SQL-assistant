 SQL Assistant (Streamlit + LLM)

A web-based SQL Assistant built with Streamlit, OpenAI GPT, and SQLAlchemy.
This app allows users to connect to any SQL database, query it using natural language, view the results, and even generate charts automatically via Vega-Lite.


1.Features

 Connect to any SQL database using a connection URL
 Or use the built-in demo SQLite database (auto-created on first launch)
 Ask questions in plain English — the LLM converts them into SQL
 Automatically explains each query in natural language
 Displays results in an interactive data table
 Generates Vega-Lite charts automatically (bar, line, scatter, etc.)
 Safely restricts queries to SELECT-only (no modifications or deletions)






2.Project Structure
SQL-assistant/
│
├── app.py                 # Streamlit web app
├── .env                   # Contains your OpenAI API key
├── mytest.db              # Sample SQLite database (3 tables, 10+ rows)
├── demo.sqlite            # Auto-generated demo DB
├── import_sqlite3.py      # Optional helper script to test SQLite manually
├── Command.txt            # (optional) Notes or terminal commands
└── README.md              # This documentation






3. Installation
Install Python

a. Make sure you have Python 3.9+ installed.
Check with:
py --version
If not installed, download it from python.org/downloads

 Remember to check the box “Add Python to PATH” during installation.

b.  Create a Virtual Environment (optional but recommended)
python -m venv venv
venv\Scripts\activate      # Windows
# or
source venv/bin/activate   # Mac/Linux

c.  Install Dependencies
py -m pip install streamlit sqlalchemy pandas openai sqlparse python-dotenv duckdb altair

d.  Create .env File

In the project folder, create a file named .env with your API key:
OPENAI_API_KEY=sk-your-real-openai-api-key
Get your key from https://platform.openai.com/api-keys

f. Running the App
From your terminal (inside the project folder):
py -m streamlit run app.py

It will open automatically in your browser at
http://localhost:8501






4. How to Use

🧩 Option 1 — Demo Database

Leave the “Database URL” box empty

Click Connect

A demo SQLite database (demo.sqlite) will be created automatically

Try queries like:

“Show all employees.”

“What is the average salary by city?”

“Show a bar chart of salary by department.”

🧩 Option 2 — Connect to Your Own Database

You can use any SQL database by entering its connection URL in the “Database URL” box:

Database Type	Example URL
SQLite	sqlite:///C:/Users/potat/OneDrive/Desktop/SQL-assistant/mytest.db
PostgreSQL	postgresql://user:password@hostname:5432/dbname
MySQL	mysql+pymysql://user:password@hostname:3306/dbname
DuckDB	duckdb:///mydata.duckdb



5. Example Database Schema (mytest.db)

departments

department_id	department_name
1	Engineering
2	Marketing
3	Finance

employees

employee_id	name	city	department_id	salary	hire_date
1	Alice	New York	1	95000	2020-03-10
…	…	…	…	…	…

projects

project_id	project_name	department_id	budget	start_date	end_date
101	Product Redesign	1	250000	2022-01-01	2022-06-30
…	…	…	…	…	…





6. Future Improvements

Support for multiple simultaneous connections

More advanced data visualization templates

Export results to CSV or Excel

Integration with LangChain for prompt history




Author

Fan Yang (potat)
Fordham University, Gabelli School of Business
AI in Business | Data Science | Streamlit Developer

