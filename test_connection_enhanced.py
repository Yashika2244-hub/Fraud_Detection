import mysql.connector
import time

def test_mysql_connection():
    config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "@Yashi123**",
        "database": "fraud_detection",
        "port": 3306,
        "connection_timeout": 5
    }
    
    print("🔹 Starting MySQL connection test...")
    print(f"Attempting to connect with: {config}")
    
    try:
        start_time = time.time()
        conn = mysql.connector.connect(**config)
        end_time = time.time()
        
        if conn.is_connected():
            print(f"✅ Connection successful! (Time: {end_time-start_time:.2f}s)")
            
            cursor = conn.cursor()
            
            # Test 1: Check database
            cursor.execute("SELECT DATABASE();")
            db = cursor.fetchone()[0]
            print(f"Current database: {db}")
            
            # Test 2: List tables
            cursor.execute("SHOW TABLES;")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"Tables found: {tables}")
            
            # Test 3: Sample query
            if tables:
                print(f"\nTesting sample query on {tables[0]}:")
                cursor.execute(f"SELECT * FROM {tables[0]} LIMIT 1;")
                print("Sample row:", cursor.fetchone())
            
            cursor.close()
            conn.close()
            return True
            
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error {err.errno}: {err.msg}")
        print("Common causes:")
        print("- MySQL service not running")
        print("- Wrong credentials")
        print("- Firewall blocking port 3306")
        print("- User lacks privileges")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_mysql_connection()