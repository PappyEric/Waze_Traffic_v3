import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=kcpssqlprod;"
    r"DATABASE=master;"
    r"UID=nwssqladmin;"
    r"PWD=E8?#\W43XGfq;",
    timeout=10
)
conn.autocommit = True
cursor = conn.cursor()

print("Setting up nwssvc login on kcpssqlprod...")

# Create login if not exists
cursor.execute("SELECT name FROM sys.server_principals WHERE name = 'nwssvc' AND type = 'S'")
row = cursor.fetchone()
if not row:
    cursor.execute("CREATE LOGIN [nwssvc] WITH PASSWORD = '!K@n@w@h@911', DEFAULT_DATABASE = [NWSAegisGISDB_KanawhaCo_WV]")
    print("Login 'nwssvc' created.")
else:
    print("Login 'nwssvc' already exists. Updating password...")
    cursor.execute("ALTER LOGIN [nwssvc] WITH PASSWORD = '!K@n@w@h@911'")

# Switch to the database
cursor.execute("USE NWSAegisGISDB_KanawhaCo_WV")

# Create user if not exists
cursor.execute("SELECT name FROM sys.database_principals WHERE name = 'nwssvc'")
row = cursor.fetchone()
if not row:
    cursor.execute("CREATE USER [nwssvc] FOR LOGIN [nwssvc]")
    print("User 'nwssvc' created in NWSAegisGISDB_KanawhaCo_WV.")
else:
    print("User 'nwssvc' already exists.")

# Grant db_owner
cursor.execute("ALTER ROLE db_owner ADD MEMBER [nwssvc]")
print("Granted db_owner to 'nwssvc'.")

conn.close()

# Test the connection with nwssvc
try:
    test_conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=kcpssqlprod;"
        r"DATABASE=NWSAegisGISDB_KanawhaCo_WV;"
        r"UID=nwssvc;"
        r"PWD=!K@n@w@h@911;",
        timeout=10
    )
    print("SUCCESS: nwssvc test connection works.")
    test_conn.close()
except Exception as e:
    print(f"FAILED nwssvc test: {e}")
