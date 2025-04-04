import streamlit as st
import os
import mysql.connector
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from mysql.connector import Error


# ✅ Page Config Set
st.set_page_config(page_title="Fraud Detection", layout="wide")

# ========== Custom CSS ==========
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #0E1117 !important; 
        color: white !important;
    }

    [data-testid="stSidebar"] * {
        color: #D3D3D3 !important;  
        font-size: 16px !important;
    }

    .st-emotion-cache-1d391kg {
        color: white !important;
        font-weight: bold;
    }

    [data-testid="stAppViewContainer"], .main, .block-container {
        background-color: #FFFFFF !important;
    }

    h1, h2, h3, h4 {
        color: #222222 !important;
    }

    p, span {
        color: #333333 !important;
        font-size: 16px !important;
    }

    .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ========== DATABASE CONNECTION ==========
def get_db():
    """Connect to MySQL Database"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=int(os.environ.get("MYSQLPORT", 3306)),
            auth_plugin='mysql_native_password',
            connect_timeout=5,
            use_pure=True
        )
        return conn
    except Error as e:
        st.error(f"❌ Connection failed: {e}")
    return None

# ========== FETCH DATA FUNCTIONS ==========
def get_data(query):
    """Execute SQL query and return DataFrame"""
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            data = cursor.fetchall()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"❌ Query failed: {e}")
            return pd.DataFrame()
        finally:
            if conn.is_connected():
                conn.close()
    else:
        st.warning("⚠️ No database connection.")
        return pd.DataFrame()

def get_table_names():
    """Fetch all MySQL table names"""
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            return tables
        except Exception as e:
            st.error(f"❌ Could not fetch table names: {e}")
            return []
        finally:
            if conn.is_connected():
                conn.close()
    return []

def get_merged_data():
    """Fetch and merge transactions, users, merchants, and cards"""
    transactions = get_data("SELECT * FROM transaction")
    users = get_data("SELECT id, gender, AgeGroup FROM user")
    merchants = get_data("SELECT merchant_id, merchant_state FROM merchants")
    cards = get_data("SELECT id AS card_id, card_brand FROM cards")

    if transactions.empty or users.empty or merchants.empty or cards.empty:
        st.error("❌ Some tables are empty. Merging failed!")
        return pd.DataFrame()

    # ✅ Data Cleaning (Fixing Amount Column in transactions BEFORE merging)
    if "amount" in transactions.columns:
        transactions["amount"] = transactions["amount"].astype(str)  # पहले string में convert करो
        transactions["amount"] = transactions["amount"].replace('[\$,]', '', regex=True).astype(float)  # `$` और special characters हटाओ
        transactions = transactions.dropna(subset=["amount"])  # NaN values drop करो

    # ✅ Merging tables
    merged_df = transactions.merge(users, left_on="client_id", right_on="id", how="left")
    merged_df = merged_df.merge(merchants, on="merchant_id", how="left")
    merged_df = merged_df.merge(cards, on="card_id", how="left")

    # ✅ Fixing Date Column & Extracting Hour
    if "date" in merged_df.columns:
        merged_df["date"] = pd.to_datetime(merged_df["date"], errors="coerce")
        merged_df["hour"] = merged_df["date"].dt.hour  # Extract hour
    else:
        merged_df["hour"] = None

    return merged_df

def get_total_amount():
    """Fetch total transaction amount with rounding"""
    query = "SELECT ROUND(SUM(amount), 2) AS total_amount FROM transaction;"
    df = get_data(query)
    return df["total_amount"][0] if not df.empty else 0.00

def get_total_fraud_amount():
    """Fetch total fraud transaction amount with rounding"""
    query = "SELECT ROUND(SUM(amount), 2) AS total_fraud_amount FROM transaction WHERE fraud_classification = 'Fraud';"
    df = get_data(query)
    return df["total_fraud_amount"][0] if not df.empty else 0.00

# ========== STREAMLIT MAIN FUNCTION ==========
def main():
    # Sidebar Navigation
    st.sidebar.title("📌 Navigation")
    menu_options = ["🏠 Home", "🗂️ Datasets", "📜 SQL Query", "🐍 Python", "📊 Power BI", "⬇️ Download"]
    choice = st.sidebar.radio("Go to:", menu_options)
    
    # ========== Home Page ==========
    if choice == "🏠 Home":
        st.title("📊 Fraud Detection Dashboard")
        st.write("🔍 **Analyze fraudulent transactions and financial risks.**")

        merged_df = get_merged_data()

        if merged_df.empty:
            st.warning("⚠ No data available!")
        else:
            # ✅ Filters (Inside Dashboard, NOT Sidebar)
            years = ["All"] + sorted(merged_df["date"].dt.year.dropna().unique().tolist())
            months = ["All"] + sorted(merged_df["date"].dt.month.dropna().unique().tolist())
            genders = ["All"] + sorted(merged_df["gender"].dropna().unique().tolist())

            col1, col2, col3 = st.columns([1, 1, 1])
            selected_year = col1.selectbox("📅 Year", years, index=0)
            selected_month = col2.selectbox("📆 Month", months, index=0)
            selected_gender = col3.selectbox("👤 Gender", genders, index=0)

            # ✅ Apply Filters
            filtered_df = merged_df.copy()
            if selected_year != "All":
                filtered_df = filtered_df[filtered_df["date"].dt.year == selected_year]
            if selected_month != "All":
                filtered_df = filtered_df[filtered_df["date"].dt.month == selected_month]
            if selected_gender != "All":
                filtered_df = filtered_df[filtered_df["gender"] == selected_gender]

            # ✅ KPIs (Top Section)
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            total_transactions = len(filtered_df)
            total_amount = round(float(filtered_df["amount"].sum()), 2) 
            total_fraud_transactions = len(filtered_df[filtered_df["fraud_classification"] == "Fraud"])
            total_fraud_amount = round(float(filtered_df[filtered_df["fraud_classification"] == "Fraud"]["amount"].sum()), 2) 
     
            # ✅ Formatting Properly
            formatted_total_amount = f"${total_amount:,.2f}"  # 🔹 Ensures proper formatting
            formatted_fraud_amount = f"${total_fraud_amount:,.2f}"  # 🔹 Ensures proper formatting

            kpi_col1.metric("📑 Total Transactions", f"{total_transactions:,}")
            kpi_col2.metric("💰 Total Amount", formatted_total_amount) 
            kpi_col3.metric("🚨 Fraud Transactions", f"{total_fraud_transactions:,}")
            kpi_col4.metric("🔥 Fraud Amount", formatted_fraud_amount) 

            # ✅ Layout for GIF & Filters (Below KPIs)
            gif_col, slicer_col = st.columns([2, 1])

            # ✅ Display Fraud Detection GIF (Left Side)
            gif_path = "C:/Users/Dell/Downloads/Fraud Hoax GIF.gif"
            gif_col.markdown("### 🔍 Fraud Detection in Action")
            gif_col.image(gif_path, width=350)

            # ✅ Show Selected Filters Again (Right Side)
            slicer_col.markdown("### 🎛️ Selected Filters")
            slicer_col.write(f"📅 **Year:** {selected_year}")
            slicer_col.write(f"📆 **Month:** {selected_month}")
            slicer_col.write(f"👤 **Gender:** {selected_gender}")

    # ========== Transactions Page ==========  
    elif choice == "Transactions":
        st.title("📂 Transactions Data")
        df = get_data("SELECT * FROM transaction")  # ✅ LIMIT हटाया गया
        if not df.empty:
            st.dataframe(df, height=800)  # ✅ अब पूरा Data Show होगा
            st.write(f"🔹 Total Rows: {len(df)}")

    # ========== MySQL Tables ==========
    elif choice == "🗂️ Datasets":
        st.title("🗂️ Datasets Overview")
        tables = get_table_names()

        if tables:
            selected_table = st.selectbox("Select a table", tables)

            if st.button("📥 Load Table Data"):
                df = get_data(f"SELECT * FROM {selected_table}")
                if not df.empty:
                    st.dataframe(df, height=600)
                    st.write(f"Total Rows: {len(df)}")
                else:
                    st.warning(f"⚠ No data found in {selected_table}")
        else:
            st.warning("⚠ No tables found in the database.")
   
    # ========== Run SQL Queries ==========
    elif choice == "📜 SQL Query":
        st.title("📜 SQL Query")

        # Predefined Queries
        predefined_queries = {
            "Show all transactions": "SELECT * FROM transaction LIMIT 100",
            "Fraud Transactions": "SELECT * FROM transaction WHERE fraud_classification = 'Fraud' LIMIT 100",
            "Fraud Amount (Merchant-State Wise)": """
                SELECT m.merchant_state, SUM(t.amount) AS fraud_cases
                FROM transaction t
                JOIN merchants m ON t.merchant_id = m.merchant_id
                WHERE t.fraud_classification = 'Fraud'
                GROUP BY m.merchant_state
                ORDER BY fraud_cases DESC
                LIMIT 10;
            """,
            "Fraud Amount by Merchant ID": """
                SELECT m.merchant_id, SUM(t.amount) AS total
                FROM merchants m
                JOIN transaction t ON m.merchant_id = t.merchant_id
                WHERE fraud_classification = 'Fraud'
                GROUP BY m.merchant_id
                ORDER BY total DESC
                LIMIT 10;
            """,
            "Fraud Amount (Gender-wise)": """
                SELECT u.gender, COUNT(t.id) AS fraud_cases
                FROM transaction t
                JOIN user u ON t.client_id = u.id
                WHERE t.fraud_classification = 'Fraud'
                GROUP BY u.gender;
            """,
            "Monthly Fraud Trend": """
                SELECT DATE_FORMAT(date, '%M') AS month, SUM(amount) AS fraud_amount
                FROM transaction
                WHERE fraud_classification = 'Fraud' AND DATE_FORMAT(date, '%M') IS NOT NULL
                GROUP BY month
                ORDER BY fraud_amount DESC;
            """,
            "Fraud Transactions by Age Group": """
                SELECT u.AgeGroup, SUM(t.amount) AS fraud_amount
                FROM transaction t
                JOIN user u ON u.id = t.client_id
                WHERE t.fraud_classification = 'Fraud'
                GROUP BY u.AgeGroup
                ORDER BY fraud_amount DESC;
            """,
            "Top Clients by Fraud Amount (Ranking)": """
                SELECT client_id, SUM(amount) AS total_fraud, 
                RANK() OVER (ORDER BY SUM(amount) DESC) AS ranking
                FROM transaction 
                WHERE fraud_classification = 'Fraud'
                GROUP BY client_id;
            """,
            "Moving Average of Fraud Transactions": """
                SELECT id, client_id, amount, fraud_classification,
                AVG(amount) OVER (PARTITION BY client_id ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg
                FROM transaction;
            """,
            "Fraud Detection by Transaction Time": """
                SELECT id, client_id, amount, DATE_FORMAT(date, '%H:%i:%s') AS transaction_time,
                CASE 
                    WHEN HOUR(date) BETWEEN 0 AND 6 THEN 'Late Night'
                    WHEN HOUR(date) BETWEEN 7 AND 12 THEN 'Morning'
                    WHEN HOUR(date) BETWEEN 13 AND 18 THEN 'Afternoon'
                    ELSE 'Evening'
                END AS time_category
                FROM transaction;
            """,
            "Card Brand with Most Fraud Transactions": """
                SELECT card_brand FROM cards 
                WHERE id = (
                    SELECT card_id FROM transaction 
                    WHERE fraud_classification = 'Fraud'
                    GROUP BY card_id 
                    ORDER BY COUNT(id) DESC 
                    LIMIT 1
                );
            """,
            "Top Users with Most Transaction Errors": """
                SELECT u.id AS user_id, u.creditscorecategory, COUNT(t.errors) AS total_errors
                FROM transaction t
                JOIN user u ON t.client_id = u.id
                WHERE t.errors IS NOT NULL
                GROUP BY u.id, u.creditscorecategory
                ORDER BY total_errors DESC
                LIMIT 10;
            """
        }

        query_type = st.selectbox("Choose a predefined query", ["Custom Query"] + list(predefined_queries.keys()))

        if query_type == "Custom Query":
            query = st.text_area("Write your SQL Query here", height=100)
        else:
            query = predefined_queries[query_type]

        if st.button("🔍 Run Query"):
            df = get_data(query)
            if not df.empty:
                st.dataframe(df, height=600)
                st.write(f"Total Rows: {len(df)}")
            else:
                st.warning("⚠️ No results found or query failed.")

    # ========== Python Work (Data Cleaning, EDA, Statistics, Anomaly Detection) ==========
    elif choice == "🐍 Python":
        st.title("🐍 Python: Select an Analysis Type")
        analysis_type = st.selectbox("Choose an analysis type", ["Data Cleaning", "EDA", "Statistical Analysis", "Anomaly Detection"])

        merged_df = get_merged_data()
        if merged_df.empty:
            st.warning("⚠ Merged data not available.")
        else:
            # ========== Data Cleaning Section ==========
            if analysis_type == "Data Cleaning":
                st.subheader("🛠 Data Cleaning Process")

                # 🔹 Show Raw Data
                st.write("### 🔹 Raw Data Before Cleaning")
                raw_data = {
                    "amount": ["$200", "$5000", "$1500", "$700", "$1200"],
                    "date": ["11-03-2025", "12-03-2025", "13-03-2025", "14-03-2025", "15-03-2025"]
                }
                st.dataframe(pd.DataFrame(raw_data))

                # 🔹 Cleaning Steps
                st.write("### 🧹 Cleaning Steps Applied:")
                st.code("""
# Remove '$' sign and convert to float
df["amount"] = df["amount"].replace('[\$,]', '', regex=True).astype(float)

# Convert 'date' to correct format (Fixing Date Issue)
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors='coerce', dayfirst=True)

# Extract hour from date
df["hour"] = df["date"].dt.hour
                """, language="python")

                # 🔹 Show Cleaned Data
                st.write("### ✅ Cleaned Data After Processing")
                st.dataframe(merged_df[["amount", "date", "hour"]])

            # ========== Exploratory Data Analysis (EDA) ==========
            elif analysis_type == "EDA":
                st.subheader("🔍 Fraud vs Non-Fraud Transactions")
                fraud_counts = merged_df["fraud_classification"].value_counts()
                fig, ax = plt.subplots()
                sns.barplot(x=fraud_counts.index, y=fraud_counts.values, ax=ax, palette="coolwarm")
                ax.set_title("Fraud vs Non-Fraud Transactions")
                st.pyplot(fig)

                # 📌 Fraud Cases by Gender (Pie Chart)
                if "gender" in merged_df.columns:
                    st.subheader("📌 Fraud Cases Distribution by Gender")
                    fraud_by_gender = merged_df[merged_df["fraud_classification"] == "Fraud"].groupby("gender").size()
                    fig, ax = plt.subplots(figsize=(8, 8))
                    ax.pie(fraud_by_gender, labels=fraud_by_gender.index, autopct="%1.1f%%", colors=['#ff9999', '#66b3ff','#99ff99'], startangle=140)
                    ax.set_title("Fraud Cases Distribution by Gender")
                    st.pyplot(fig)

                # 📌 Fraud Cases by Card Brand (Bar Chart)
                if "card_brand" in merged_df.columns:
                    st.subheader("📌 Fraud Cases by Card Brand")
                    fraud_by_card_brand = merged_df[merged_df["fraud_classification"] == "Fraud"].groupby("card_brand").size()
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.barplot(x=fraud_by_card_brand.index, y=fraud_by_card_brand.values, ax=ax, palette="coolwarm")
                    ax.set_xlabel("Card Brand")
                    ax.set_ylabel("Fraud Cases")
                    ax.set_title("Fraud Cases by Card Brand")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                # 📌 Fraud Cases by Card Type
                if "card_type" in merged_df.columns:
                    st.subheader("📌 Fraud Cases by Card Type")
                    fig, ax = plt.subplots(figsize=(8, 5))
                    sns.countplot(data=merged_df, x='card_type', hue='fraud_classification', palette='viridis', order=merged_df['card_type'].value_counts().index)
                    ax.set_xlabel("Card Type")
                    ax.set_ylabel("Count")
                    ax.set_title("Fraud Cases by Card Type")
                    st.pyplot(fig)

                # 📌 Top 10 Merchants with Most Fraud Cases
                if "merchant_id" in merged_df.columns:
                    st.subheader("📌 Top 10 Merchants with Most Fraud Cases")
                    fraud_by_mcc = merged_df[merged_df['fraud_classification']=='Fraud'].groupby('merchant_id').size().nlargest(10)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.barplot(x=fraud_by_mcc.index, y=fraud_by_mcc.values, palette='viridis', ax=ax)
                    ax.set_title("Top 10 Merchants with Most Fraud Cases")
                    ax.set_xlabel("Merchant ID")
                    ax.set_ylabel("Fraud Count")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                # 📌 Fraud by Payment Method (Chip Used or Not)
                if "use_chip" in merged_df.columns:
                    st.subheader("📌 Fraud by Payment Method")
                    fraud_payment = merged_df[merged_df['fraud_classification']=='Fraud']['use_chip'].value_counts()
                    fig, ax = plt.subplots(figsize=(6, 6))
                    ax.pie(fraud_payment, labels=fraud_payment.index, autopct="%1.1f%%", colors=['blue', 'red', 'green'], startangle=90)
                    ax.set_title("Fraud by Payment Method")
                    st.pyplot(fig)

                # 📌 Top 10 High-Risk Merchants by Fraud Amount
                if "merchant_id" in merged_df.columns and "amount" in merged_df.columns:
                    st.subheader("📌 Top 10 High-Risk Merchants by Fraud Amount")
                    high_risk_merchants = merged_df[merged_df['fraud_classification']=='Fraud'].groupby('merchant_id')['amount'].sum().nlargest(10)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.barplot(x=high_risk_merchants.index, y=high_risk_merchants.values, palette='coolwarm', ax=ax)
                    ax.set_title("Top 10 High-Risk Merchants by Fraud Amount")
                    ax.set_xlabel("Merchant ID")
                    ax.set_ylabel("Total Fraud Amount")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                # 📌 Fraud Cases by Age Group
                if "AgeGroup" in merged_df.columns:
                    st.subheader("📌 Fraud Cases by Age Group")
                    fraud_cases = merged_df[merged_df["fraud_classification"] == "Fraud"].groupby("AgeGroup").size()
                    fig, ax = plt.subplots(figsize=(8, 5))
                    sns.barplot(x=fraud_cases.index, y=fraud_cases.values, palette="coolwarm", ax=ax)
                    ax.set_title("Fraud Cases Count by Age Group")
                    ax.set_xlabel("Age Group")
                    ax.set_ylabel("Number of Fraud Cases")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                # 📌 Fraud Cases by Transaction Hour
                if "date" in merged_df.columns:
                    st.subheader("📌 Fraud Cases by Hour of Transaction")
                    merged_df["hour"] = pd.to_datetime(merged_df["date"]).dt.hour  # Extract hour
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.countplot(data=merged_df[merged_df['fraud_classification'] == 'Fraud'], x='hour', palette='flare', ax=ax)
                    ax.set_xlabel("Hour of the Day")
                    ax.set_ylabel("Fraud Cases")
                    ax.set_title("Fraud Cases by Hour of Transaction")
                    st.pyplot(fig)

            # ========== Statistical Analysis ==========
            elif analysis_type == "Statistical Analysis":
                st.subheader("📊 Statistical Analysis of Fraud Patterns")
                
                if "fraud_classification" in merged_df.columns and "amount" in merged_df.columns:
                    # Clean data
                    merged_df["amount"] = pd.to_numeric(merged_df["amount"], errors="coerce")
                    merged_df = merged_df.dropna(subset=["amount", "fraud_classification"])
                    
                    # Separate fraud and non-fraud transactions
                    fraud_amounts = merged_df[merged_df['fraud_classification'] == 'Fraud']['amount']
                    non_fraud_amounts = merged_df[merged_df['fraud_classification'] == 'Non-Fraud']['amount']
                    
                    # Create two columns for metrics
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Mean Fraud Amount", f"${fraud_amounts.mean():.2f}")
                        st.metric("Median Fraud Amount", f"${fraud_amounts.median():.2f}")
                        
                    with col2:
                        st.metric("Mean Non-Fraud Amount", f"${non_fraud_amounts.mean():.2f}")
                        st.metric("Median Non-Fraud Amount", f"${non_fraud_amounts.median():.2f}")
                    
                    # T-Test
                    st.markdown("### Hypothesis Testing (T-Test)")
                    t_stat, p_value = stats.ttest_ind(fraud_amounts, non_fraud_amounts, equal_var=False)
                    
                    st.write(f"**T-Statistic:** {t_stat:.4f}")
                    st.write(f"**P-Value:** {p_value:.4f}")
                    
                    if p_value < 0.05:
                        st.success("✅ Statistically significant difference between fraud and non-fraud amounts (p < 0.05)")
                    else:
                        st.warning("⚠ No statistically significant difference between fraud and non-fraud amounts")
                    
                    # Fraud Rate
                    fraud_rate = len(fraud_amounts) / len(merged_df) * 100
                    st.metric("Overall Fraud Rate", f"{fraud_rate:.2f}%")
                    
                    # Visualization
                    st.markdown("### Amount Distribution Comparison")
                    plt.figure(figsize=(10,6))
                    sns.histplot(fraud_amounts, bins=50, color='red', label="Fraud", kde=True, alpha=0.6)
                    sns.histplot(non_fraud_amounts, bins=50, color='blue', label="Non-Fraud", kde=True, alpha=0.6)
                    plt.legend()
                    plt.title('Fraud vs Non-Fraud Amount Distribution')
                    plt.xlabel('Transaction Amount')
                    plt.ylabel('Frequency')
                    st.pyplot(plt)
                    
                    # Boxplot for comparison
                    st.markdown("### Amount Distribution (Boxplot)")
                    plt.figure(figsize=(10,6))
                    sns.boxplot(x='fraud_classification', y='amount', data=merged_df, 
                               palette={"Fraud": "red", "Non-Fraud": "blue"})
                    plt.title('Transaction Amount by Fraud Classification')
                    plt.xlabel('Fraud Classification')
                    plt.ylabel('Amount ($)')
                    st.pyplot(plt)
                    
                else:
                    st.error("Required columns ('amount' or 'fraud_classification') missing in the dataset!")

            # ========== Anomaly Detection ==========
            elif analysis_type == "Anomaly Detection":
                st.subheader("🚨 Detecting Anomalous Transactions")

                if "amount" in merged_df.columns:
                    # Clean amount column
                    merged_df["amount"] = pd.to_numeric(merged_df["amount"], errors="coerce")
                    merged_df = merged_df.dropna(subset=["amount"])

                    # Method selection
                    method = st.radio("Choose an anomaly detection method", ["Z-Score", "IQR"], horizontal=True)

                    # Z-Score Method
                    if method == "Z-Score":
                        st.markdown("### Z-Score Method")
                        st.info("Transactions with Z-Score > 3 are considered anomalies")
                        
                        # Calculate Z-Score
                        merged_df["z_score"] = np.abs(stats.zscore(merged_df["amount"]))
                        
                        # Allow threshold adjustment
                        z_threshold = st.slider("Select Z-Score threshold", 
                                               min_value=2.0, 
                                               max_value=5.0, 
                                               value=3.0, 
                                               step=0.1,
                                               help="Standard threshold is 3.0")
                        
                        # Find outliers
                        outliers = merged_df[merged_df["z_score"] > z_threshold]
                        
                        # Display results
                        st.metric("Total Anomalies Detected", len(outliers))
                        st.dataframe(outliers[["client_id", "amount", "fraud_classification", "z_score"]].sort_values("z_score", ascending=False))
                        
                        # Fraud-specific anomalies
                        if "fraud_classification" in merged_df.columns:
                            fraud_outliers = outliers[outliers["fraud_classification"] == "Fraud"]
                            st.metric("Fraud Anomalies", len(fraud_outliers))
                            st.dataframe(fraud_outliers[["client_id", "amount", "z_score"]])

                    # IQR Method
                    elif method == "IQR":
                        st.markdown("### IQR Method")
                        st.info("Transactions outside 1.5*IQR range are considered anomalies")
                        
                        # Calculate IQR bounds
                        Q1 = merged_df["amount"].quantile(0.25)
                        Q3 = merged_df["amount"].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        # Allow multiplier adjustment
                        iqr_multiplier = st.slider("Select IQR multiplier", 
                                                 min_value=1.0, 
                                                 max_value=3.0, 
                                                 value=1.5, 
                                                 step=0.1,
                                                 help="Standard multiplier is 1.5")
                        
                        lower_bound = Q1 - iqr_multiplier * IQR
                        upper_bound = Q3 + iqr_multiplier * IQR
                        
                        # Find anomalies
                        anomalies_iqr = merged_df[(merged_df["amount"] < lower_bound) | (merged_df["amount"] > upper_bound)]
                        
                        # Display results
                        st.metric("Total Anomalies Detected", len(anomalies_iqr))
                        st.dataframe(anomalies_iqr[["client_id", "amount", "fraud_classification"]].sort_values("amount", ascending=False))
                        
                        # Fraud-specific anomalies
                        if "fraud_classification" in merged_df.columns:
                            fraud_outliers_iqr = anomalies_iqr[anomalies_iqr["fraud_classification"] == "Fraud"]
                            st.metric("Fraud Anomalies", len(fraud_outliers_iqr))
                            st.dataframe(fraud_outliers_iqr[["client_id", "amount"]])

    # ========== Power BI without Power BI Service ==========
    elif choice == "📊 Power BI":
        st.title("📊 Power BI Fraud Detection Report")
        st.write("### 🔹Download Power BI Report as PDF")
        
        # ✅ Correct File Path
        pdf_path = "C:/Users/Dell/Downloads/fin.pdf"  # Or use "C:\\Users\\Dell\\Downloads\\fin.pdf"
        
        try:
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(label="📥 Download Power BI Report", data=pdf_file, file_name="PowerBI_Report.pdf", mime="application/pdf")
        except FileNotFoundError:
            st.error("⚠️ PDF File Not Found! Please check the file path.")

    # ========== Download Section ==========
    elif choice == "⬇️ Download":
        st.title("⬇️ Download Reports & Data")
        
        # ✅ MySQL SQL File Download
        st.subheader("🗄️ Download MySQL SQL File")
        sql_file_path = "C:/Users/Dell/Downloads/Financial_fraud_detection.sql"
        
        try:
            with open(sql_file_path, "r", encoding="utf-8") as sql_file:
                sql_code = sql_file.read()
                st.download_button(label="📥 Download MySQL Script", data=sql_code, file_name="fraud_detection_analysis.sql", mime="text/plain")
        except FileNotFoundError:
            st.error("⚠ SQL File not found! Please check the file path.")

        # ✅ Power BI Report Download
        st.subheader("📊 Download Power BI Report")
        pdf_path = "C:/Users/Dell/Downloads/fin.pdf"
        
        try:
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(label="📥 Download Power BI Report", data=pdf_file, file_name="PowerBI_Report.pdf", mime="application/pdf")
        except FileNotFoundError:
            st.error("⚠ Power BI Report not found! Please check the file path.")

        # ✅ Python Script Download
        st.subheader("🐍 Download Python Jupyter Notebook")
        python_script_path = "C:/Users/Dell/Downloads/fraud_detection2.ipynb"
        
        try:
            with open(python_script_path, "r", encoding="utf-8") as py_file:
                python_code = py_file.read()
                st.download_button(label="📥 Download Python Notebook", data=python_code, file_name="fraud_detection.ipynb", mime="application/json")
        except FileNotFoundError:
            st.error("⚠ Python Notebook not found! Please check the file path.")

if __name__ == "__main__":
    main()
