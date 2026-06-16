import duckdb
import streamlit as st


def get_connection():
    token = st.secrets["MOTHERDUCK_TOKEN"]

    if not token:
        raise ValueError("Chưa cấu hình MOTHERDUCK_TOKEN trong .streamlit/secrets.toml")

    conn = duckdb.connect(f"md:shopping_db?token={token}")
    return conn


if __name__ == "__main__":
    conn = get_connection()

    result = conn.execute("""
        SELECT COUNT(*) 
        FROM main.fact_sessions
    """).fetchone()[0]

    print("Kết nối thành công!")
    print("Số dòng trong fact_sessions:", result)