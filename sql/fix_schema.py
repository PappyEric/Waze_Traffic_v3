import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=kcpssqlprod;"
    r"DATABASE=NWSAegisGISDB_KanawhaCo_WV;"
    r"UID=nwssqladmin;"
    r"PWD=E8?#\W43XGfq;",
    timeout=10
)
conn.autocommit = True
cursor = conn.cursor()

print("Altering nwssvc user to have default schema dbo...")
cursor.execute("ALTER USER [nwssvc] WITH DEFAULT_SCHEMA = dbo")
print("Done.")

conn.close()
