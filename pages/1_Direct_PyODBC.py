import streamlit as st
import pyodbc
import pandas as pd

st.set_page_config(page_title="Direct PyODBC Test", layout="centered")
st.title("Azure SQL — Direct pyodbc Connection")

st.markdown("""
This page demonstrates the **direct pyodbc approach** recommended by Streamlit.
No SQLAlchemy required - just pure pyodbc with the same ODBC connection string.
""")

# --- Check for connection string ---
try:
    ODBC_STRING = st.secrets["AZURE_SQL_ODBC"]
except KeyError:
    st.error("❌ Connection string not found in secrets (key: AZURE_SQL_ODBC)")
    st.info("""
    **Required secret:**
    - `AZURE_SQL_ODBC`: Your full ODBC connection string

    Example format:
    ```
    DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...
    ```
    """)
    st.stop()

with st.expander("Current connection string (read-only)"):
    st.code(ODBC_STRING, language="text")

# --- Initialize connection ---
@st.cache_resource(show_spinner=False)
def init_connection(odbc_str: str):
    """Create direct pyodbc connection"""
    return pyodbc.connect(odbc_str)

conn = init_connection(ODBC_STRING)

# --- Connectivity test ---
st.subheader("1) Connectivity check")
if st.button("Test connection"):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT @@VERSION AS version")
            row = cur.fetchone()
        st.success("✅ Connected successfully!")
        st.code(row[0], language="text")
    except Exception as e:
        st.error("Connection failed.")
        st.exception(e)

# --- Run query ---
st.subheader("2) Run a SQL query")
default_query = "SELECT TOP (10) name, create_date FROM sys.tables ORDER BY create_date DESC;"
query = st.text_area("SQL", value=default_query, height=150)
run = st.button("Execute query")

@st.cache_data(ttl=600, show_spinner=False)
def run_query(q: str):
    """Execute query and return results as DataFrame"""
    with conn.cursor() as cur:
        cur.execute(q)
        columns = [column[0] for column in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame.from_records(rows, columns=columns)

if run:
    try:
        df = run_query(query)
        st.write(f"Rows returned: {len(df)}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("Query failed.")
        st.exception(e)

# --- Configuration instructions ---
with st.expander("📋 How to configure secrets"):
    st.markdown("""
    ### For local development (.streamlit/secrets.toml):
    ```toml
    AZURE_SQL_ODBC = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=..."
    ```

    ### For Streamlit Cloud:
    Go to **App settings → Secrets** and paste the same TOML format.

    **Note:** This uses the exact same connection string as the SQLAlchemy method.
    """)

st.caption("Direct pyodbc approach - simpler and recommended by Streamlit for database connections.")
