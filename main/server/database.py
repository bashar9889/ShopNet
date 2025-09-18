import sqlite3

# can just import function
def get_cursor():
    conn = sqlite3.connect('database.db')
    return conn, conn.cursor()  

def CreateDatabase():
    try:       
        conn, cursor = get_cursor()        
        # cursor.execute(
        #     """
        #     CREATE TABLE IF NOT EXISTS users (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         name TEXT NOT NULL,
        #         ipAddress TEXT NOT NULL,
        #         udpSocket INTEGER NOT NULL,
        #         tcpSocket INTEGER NOT NULL, 
        #         itemName TEXT, 
        #         itemDescription TEXT,
        #         maxPrice REAL,
        #         offer REAL
        #     )
        #     """
        # )

        cursor.execute(
           """
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                ipAddress TEXT NOT NULL,
                udpSocket INTEGER NOT NULL,
                tcpSocket INTEGER NOT NULL
            )
            """
        )
                
            #sample data
        sample_data = [
            (1, "Alice", "192.168.0.1", 5001, 6001),
            (2, "Bob", "192.168.0.2", 5002, 6002),
            (3, "Charlie", "192.168.0.3", 5003, 6003),
        ]
        #delete users when re-initalized to keep consistency and reduce redudancy
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM users_new")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users';")
        cursor.executemany(
            """
            INSERT INTO users_new (id, name, ipAddress, udpSocket, tcpSocket)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_data,
        )
        conn.commit()
        print("Database loaded successfully")
        print(showUsers())
    except Exception as e:
        print(f"Error creating users table: {e}")

def showUsers():
    try:
        # Use get_cursor() to get both the connection and cursor
        conn, cursor = get_cursor()
        
        cursor.execute("SELECT * FROM users_new")
        users = cursor.fetchall()
        if users:
            user_list = [f"RQ#: {user[0]}, Name: {user[1]}, IP: {user[2]}" for user in users]
            return "\n".join(user_list)
        else:
            return "No users registered."
    except Exception as e:
        return f"Error fetching users: {str(e)}"



def deleteTable():
    try:
        # Use get_cursor() to get both the connection and cursor
        conn, cursor = get_cursor()
        
        cursor.execute("DROP TABLE users")
        cursor.execute("DROP TABLE users_new")
        conn.commit()
        print("Table deleted")
    except Exception as e:
        print(f"Error deleting table: {e}")

