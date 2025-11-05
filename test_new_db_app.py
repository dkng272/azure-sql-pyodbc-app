import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
ODBC_STRING = os.getenv("AZURE_SQL_ODBC")

st.set_page_config(page_title="Azure SQL Connectivity Test", layout="centered")
st.title("Azure SQL — SQLAlchemy + pyodbc test")

if not ODBC_STRING:
    st.error("❌ ODBC connection string not found in .env (key: AZURE_SQL_ODBC)")
    st.stop()

with st.expander("Current connection string (read-only)"):
    st.code(ODBC_STRING, language="text")

# --- Build SQLAlchemy engine ---
@st.cache_resource(show_spinner=False)
def get_engine(odbc_str: str):
    odbc_encoded = quote_plus(odbc_str)
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={odbc_encoded}",
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        fast_executemany=True,
    )
    return engine

engine = get_engine(ODBC_STRING)

# --- Connectivity test ---
st.subheader("1) Connectivity check")
if st.button("Run connectivity test"):
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT @@VERSION AS version")).one()
        st.success("✅ Connected successfully!")
        st.code(row.version, language="text")
    except Exception as e:
        st.error("Connection failed.")
        st.exception(e)

# --- Run test query ---
st.subheader("2) Run a SQL query")
default_query = "SELECT TOP (10) name, create_date FROM sys.tables ORDER BY create_date DESC;"
query = st.text_area("SQL", value=default_query, height=150)
run = st.button("Execute query")

@st.cache_data(ttl=600, show_spinner=False)
def run_query(q: str):
    with engine.connect() as conn:
        df = pd.read_sql(text(q), conn)
    return df

if run:
    try:
        df = run_query(query)
        st.write(f"Rows returned: {len(df)}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error("Query failed.")
        st.exception(e)

st.caption("Tip: Store your credentials safely in the .env file and avoid committing it to Git.")