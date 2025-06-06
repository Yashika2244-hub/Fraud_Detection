# test_connection.py
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Yashi123**",
        database="fraud_detection"
    )
    print("✅ MySQL Connection Successful!")
    conn.close()
except Exception as e:
    print(f"❌ error: {e}")
