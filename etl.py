import streamlit as st
import mysql.connector
import pandas as pd

# ========== DATABASE CONNECTION ==========
def get_db_connection():
    """Connect to MySQL Database"""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@Yashi123**",
            database="fraud_detection",
            port=3306,
            auth_plugin='mysql_native_password'
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"❌ Connection Error: {e}")
        return None

# ========== FETCH TABLE DATA ==========
def get_table_data(table_name):
    """Fetch data from MySQL tables"""
    conn = get_db_connection()
    if conn:
        try:
            query = f"SELECT * FROM {table_name};"  
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"❌ Query Error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    else:
        return pd.DataFrame()

# ========== STREAMLIT MAIN FUNCTION ==========
def main():
    st.set_page_config(page_title="ETL Process", layout="wide")

    # Sidebar Navigation
    st.sidebar.title("📌 Navigation")
    menu_options = ["Home", "ETL Process", "Transactions", "Run SQL Query", "Power BI Dashboard"]
    choice = st.sidebar.radio("Go to:", menu_options)

    # ========== Home Page ==========
    if choice == "Home":
        st.title("📊 Fraud Detection Dashboard")
        st.write("Welcome! Select a section from the sidebar.")

    # ========== ETL Process Page ==========
    elif choice == "ETL Process":
        st.title("🔄 ETL Process Overview")

        st.write("✅ ETL Process has been successfully completed.")
        st.write("📌 Below are the tables that were processed:")

        tables = ["transactions", "users", "merchants", "cards", "credit_data", "addresses"]
        for table in tables:
            st.subheader(f"📂 {table.upper()}")
            df = get_table_data(table)
            if not df.empty:
                st.dataframe(df)
                st.write(f"Total Rows in `{table}`: {len(df)}")
            else:
                st.warning(f"No data found in {table}")

    # ========== MySQL Transactions Page ==========
    elif choice == "Transactions":
        st.title("📂 Transactions Data")
        df = get_table_data("transactions")
        if not df.empty:
            st.dataframe(df)
            st.write(f"Total Rows: {len(df)}")

    # ========== Run SQL Queries ==========
    elif choice == "Run SQL Query":
        st.title("📝 Run SQL Query")
        query = st.text_area("Write your SQL Query here", height=100)
        if st.button("Run Query"):
            df = get_table_data(query)
            if not df.empty:
                st.dataframe(df, height=600)
                st.write(f"Total Rows: {len(df)}")
            else:
                st.warning("⚠️ No results found or query failed.")

    # ========== Power BI Dashboard ==========
    elif choice == "Power BI Dashboard":
        st.title("📊 Power BI Fraud Detection Dashboard")
        powerbi_url = "https://app.powerbi.com/view?r=YOUR_REPORT_LINK"
        st.markdown(f"[🔗 Click here to view Power BI Dashboard]({powerbi_url})", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
