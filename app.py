import os
import json
import pandas as pd
import sqlparse
import streamlit as st
import re
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from sqlparse.sql import Identifier, IdentifierList
from sqlparse.tokens import Keyword, DML

# --- Page config (do this first) ---
st.set_page_config(
    page_title="SQL Assistant • Natural Language to SQL",
    page_icon="🤖",
    layout="wide",
)

# --- Custom CSS to make it feel more like a website ---
st.markdown(
    """
    <style>
    /* Global styles */
    body {
        background-color: #0f172a;
    }
    .main {
        background: radial-gradient(circle at top left, #1e293b 0, #020617 50%);
        color: #e5e7eb;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(148, 163, 184, 0.12);
        color: #e5e7eb;
        border-radius: 999px;
        padding: 0.3rem 0.75rem;
        font-size: 0.8rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }
    .pill span {
        font-size: 0.9rem;
    }
    .feature-card {
        background: radial-gradient(circle at top left, #1f2937 0, #020617 60%);
        border-radius: 1rem;
        padding: 1rem 1.2rem;
        border: 1px solid rgba(148, 163, 184, 0.3);
        height: 100%;
    }
    .feature-title {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .feature-body {
        font-size: 0.85rem;
        color: #9ca3af;
    }
    .footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(148, 163, 184, 0.2);
        font-size: 0.8rem;
        color: #6b7280;
    }
    /* Make Streamlit standard widgets blend in a bit more */
    .stTextArea textarea, .stTextInput input {
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(148, 163, 184, 0.4) !important;
    }
    .stDataFrame {
        border-radius: 0.75rem;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Load API key ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Please set your OPENAI_API_KEY in a .env file or system environment variable.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Helper functions ---
def is_select_only(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    stmt = parsed[0]
    forbidden = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
        "REPLACE", "GRANT", "REVOKE", "MERGE", "CALL", "EXEC", "BEGIN", "COMMIT"
    }
    tokens = [t for t in stmt.flatten() if not t.is_whitespace]
    for t in tokens:
        if t.value.upper() in forbidden:
            return False
    return sql.strip().upper().startswith(("SELECT", "WITH"))

def add_limit(sql: str, max_rows: int = 200) -> str:
    upper = sql.upper()
    if " LIMIT " in upper or " FETCH " in upper or " TOP " in upper:
        return sql
    return f"{sql.rstrip()} LIMIT {max_rows}"

def reflect_schema(engine) -> dict:
    insp = inspect(engine)
    schema = {}
    for table in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns(table)]
        schema[table] = cols
    return schema

def schema_markdown(schema: dict) -> str:
    return "\n".join([f"- {t}({', '.join(cols)})" for t, cols in schema.items()])

def normalize_table_names(sql: str, schema: dict) -> str:
    """
    Normalize table names in the SQL to match the actual schema keys,
    ignoring case. Only unquoted identifiers are adjusted.
    """
    if not schema:
        return sql

    # Map lowercase -> canonical table name from schema
    table_map = {t.lower(): t for t in schema.keys()}

    parsed = sqlparse.parse(sql)
    if not parsed:
        return sql

    stmt = parsed[0]

    def _fix_identifier(token: Identifier):
        name = token.get_real_name()
        if not name:
            return

        key = name.lower()
        if key in table_map:
            canonical = table_map[key]
            alias = token.get_alias()

            # Preserve alias, if any
            if alias and alias != canonical:
                token.value = f"{canonical} AS {alias}"
            else:
                token.value = canonical

    def _recurse(tokens):
        for token in tokens:
            if isinstance(token, Identifier):
                _fix_identifier(token)
            elif isinstance(token, IdentifierList):
                for id_token in token.get_identifiers():
                    if isinstance(id_token, Identifier):
                        _fix_identifier(id_token)
            elif token.is_group:
                _recurse(token.tokens)

    _recurse(stmt.tokens)
    return str(stmt)

def ask_llm(question: str, schema: dict) -> dict:
    sys_prompt = f"""You are a data analyst that writes safe SQL and summaries.

SCHEMA:
{schema_markdown(schema)}

RULES:
- Return valid JSON with keys: sql, summary, chart
- sql: SELECT-only statement (CTEs ok, no INSERT/UPDATE/DELETE)
- Always LIMIT results if user doesn’t
- Use table and column names EXACTLY as they appear in the SCHEMA above.
- Never invent new tables or columns.
- summary: short English explanation
- chart: Vega-Lite JSON spec or null
- Do not include comments or text outside the JSON object.
"""
    resp = client.chat.completions.create(
        model="gpt-4.1-nano",
        temperature=0.2,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question}
        ]
    )

    content = resp.choices[0].message.content.strip()

    # --- SAFER JSON PARSING ---
    try:
        return json.loads(content)
    except Exception:
        # Extract potential JSON body
        start, end = content.find("{"), content.rfind("}")
        fragment = content[start:end+1]

        # Clean up bad formatting:
        fragment = fragment.replace("'", '"')                # single → double quotes
        fragment = re.sub(r"//.*?\n", "", fragment)          # remove JS-style comments
        fragment = re.sub(r"/\*.*?\*/", "", fragment)        # remove block comments
        fragment = re.sub(r",\s*}", "}", fragment)           # remove trailing commas
        fragment = re.sub(r",\s*]", "]", fragment)

        try:
            return json.loads(fragment)
        except Exception as e:
            st.warning("⚠️ LLM returned invalid JSON. Showing raw output below:")
            st.text(content)
            raise e

# --- Session state for DB ---
if "engine" not in st.session_state:
    st.session_state.engine = None
    st.session_state.schema = None
    st.session_state.connected = False

# --- SIDEBAR: Connection panel ---
with st.sidebar:
    st.markdown("### 🔌 Connection")
    st.caption("Connect your own database or use the built-in demo.")

    db_url = st.text_input(
        "Database URL",
        value="",
        placeholder="e.g. postgresql+psycopg2://user:pass@host:5432/dbname"
    )
    reset_demo = st.checkbox("Reset demo SQLite (when URL is empty)", value=False)

    if st.button("Connect"):
        try:
            if not db_url:
                db_path = Path("demo.sqlite")
                if reset_demo and db_path.exists():
                    db_path.unlink()  # delete old demo DB

                db_url = f"sqlite:///{db_path}"
                engine = create_engine(db_url)

                with engine.begin() as conn:
                    # --- Ensure tables exist ---
                    conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS employees(
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        city TEXT,
                        department_id INTEGER,
                        salary REAL
                    )
                    """)

                    conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS departments(
                        department_id INTEGER PRIMARY KEY,
                        department_name TEXT
                    )
                    """)

                    conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS projects(
                        project_id INTEGER PRIMARY KEY,
                        project_name TEXT,
                        department_id INTEGER,
                        budget REAL
                    )
                    """)

                    # --- Auto-fix employees schema if department_id is missing (from older runs) ---
                    cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(employees)").fetchall()]
                    if "department_id" not in cols:
                        # Drop and recreate employees with correct schema, then reseed
                        conn.exec_driver_sql("DROP TABLE employees")
                        conn.exec_driver_sql("""
                        CREATE TABLE employees(
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            city TEXT,
                            department_id INTEGER,
                            salary REAL
                        )
                        """)

                    # --- Seed each table independently if empty ---
                    dep_count = conn.exec_driver_sql("SELECT COUNT(*) FROM departments").scalar()
                    if dep_count == 0:
                        conn.exec_driver_sql("""
                        INSERT INTO departments(department_id, department_name) VALUES
                            (1, 'Engineering'),
                            (2, 'Marketing'),
                            (3, 'Finance');
                        """)

                    emp_count = conn.exec_driver_sql("SELECT COUNT(*) FROM employees").scalar()
                    if emp_count == 0:
                        conn.exec_driver_sql("""
                        INSERT INTO employees(id, name, city, department_id, salary) VALUES
                            (1, 'Alice', 'New York', 1, 90000),
                            (2, 'Bob', 'Chicago', 2, 75000),
                            (3, 'Charlie', 'New York', 1, 80000),
                            (4, 'David', 'San Francisco', 1, 120000),
                            (5, 'Eva', 'Chicago', 2, 95000);
                        """)

                    proj_count = conn.exec_driver_sql("SELECT COUNT(*) FROM projects").scalar()
                    if proj_count == 0:
                        conn.exec_driver_sql("""
                        INSERT INTO projects(project_id, project_name, department_id, budget) VALUES
                            (101, 'Product Redesign', 1, 250000),
                            (102, 'Ad Campaign', 2, 100000),
                            (103, 'Budget Review', 3, 50000);
                        """)
            else:
                engine = create_engine(db_url)

            st.session_state.engine = engine
            st.session_state.schema = reflect_schema(engine)
            st.session_state.connected = True
            st.success("Connected ✅")
            st.caption(f"Tables: {', '.join(st.session_state.schema.keys()) or 'None'}")
        except Exception as e:
            st.session_state.connected = False
            st.error(f"❌ Connection failed:\n{e}")

    # Connection status
    if st.session_state.connected:
        st.markdown("✅ **Status:** Connected")
    else:
        st.markdown("🟥 **Status:** Not connected")

    st.markdown("---")
    st.caption("Tip: Leave URL empty to use the demo SQLite database with sample HR data.")

# --- MAIN: Hero section ---
st.markdown(
    """
    <div class="pill">
        <span>🤖</span>
        <span>LLM-powered SQL assistant · Safe, read-only queries</span>
    </div>
    <div class="hero-title">Natural Language SQL Assistant</div>
    <div class="hero-subtitle">
        Ask questions in plain English. Get executable SQL, a data preview, and an auto-generated chart.
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Feature cards ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-title">🔒 Safe by design</div>
            <div class="feature-body">
                Only <code>SELECT</code> and CTE queries are allowed. 
                Mutating statements are automatically blocked.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-title">📊 Built-in visualization</div>
            <div class="feature-body">
                The assistant returns a Vega-Lite spec so you get 
                charts alongside your query results.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-title">🧠 Schema-aware</div>
            <div class="feature-body">
                The model sees your live schema and never invents 
                tables or columns that don't exist.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# --- Tabs for interaction ---
if st.session_state.engine:
    tab_query, tab_schema = st.tabs(["💬 Ask a question", "📚 Schema & examples"])

    with tab_query:
        q_col1, q_col2 = st.columns([3, 1])

        with q_col1:
            question = st.text_area(
                "Ask a question about your data",
                placeholder="Examples: \"What is the average salary by department?\" or \"Top 5 cities by headcount.\"",
                height=140,
            )

        with q_col2:
            st.markdown("**Run query**")
            st.markdown(
                "Use natural language. The assistant will:\n\n"
                "1. Generate a safe SQL query\n"
                "2. Explain it in plain English\n"
                "3. Render the result and a chart"
            )
            run_clicked = st.button("🚀 Run", use_container_width=True)

        if run_clicked and question.strip():
            try:
                llm_out = ask_llm(question, st.session_state.schema)
                sql = llm_out.get("sql")
                summary = llm_out.get("summary", "")

                st.markdown("#### Generated SQL")
                if not sql:
                    st.info("ℹ️ No SQL query was generated for this question.")
                    st.write("### Current Database Schema")
                    st.json(st.session_state.schema)
                else:
                    sql = sql.strip()
                    sql = normalize_table_names(sql, st.session_state.schema)

                    if not is_select_only(sql):
                        st.error("❌ LLM generated unsafe SQL. Query blocked.")
                    else:
                        sql = add_limit(sql)
                        st.code(sql, language="sql")

                        if summary:
                            st.markdown("#### Explanation")
                            st.write(summary)

                        st.markdown("#### Result preview")
                        df = pd.read_sql_query(sql, st.session_state.engine)
                        st.dataframe(df, use_container_width=True)

                        chart_spec = llm_out.get("chart")
                        if chart_spec:
                            try:
                                if isinstance(chart_spec, str):
                                    chart_spec = json.loads(chart_spec)
                                # Remove external data reference if present
                                if "data" in chart_spec:
                                    del chart_spec["data"]
                                st.subheader("📊 Visualization")
                                st.vega_lite_chart(df, chart_spec, use_container_width=True)
                            except Exception as e:
                                st.warning(f"Chart rendering failed: {e}")
            except Exception as e:
                st.error(f"Error: {e}")
        elif run_clicked and not question.strip():
            st.warning("Please type a question before running.")

    with tab_schema:
        st.markdown("### Current database schema")
        if st.session_state.schema:
            st.json(st.session_state.schema)
        else:
            st.info("No schema available yet. Connect a database first.")

        with st.expander("Need inspiration? Try these prompts:"):
            st.markdown(
                """
                - "Show me the number of employees in each department."
                - "Average salary by city, sorted from highest to lowest."
                - "Total project budget per department."
                """
            )
else:
    st.info("Connect to a database from the left sidebar to start asking questions.")

# --- Footer ---
st.markdown(
    """
    <div class="footer">
        Built with ❤️ in Streamlit · LLM-powered SQL assistant<br/>
        Safe read-only access · Add it to your data stack as an internal analytics tool.
    </div>
    """,
    unsafe_allow_html=True,
)
