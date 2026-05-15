"""Grant full SDE permissions to KCPS\\NWSSVC."""
import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=gisdb02\gissqlserver;"
    r"DATABASE=KCGIS;"
    r"Trusted_Connection=yes;",
    timeout=10
)
conn.autocommit = True
cursor = conn.cursor()

# Grant db_owner so ArcGIS Server can fully interact with the geodatabase
print("Granting db_owner role to KCPS\\NWSSVC...")
try:
    cursor.execute("ALTER ROLE db_owner ADD MEMBER [KCPS\\NWSSVC]")
    print("  Done.")
except Exception as e:
    print(f"  {e}")

# Verify all roles
cursor.execute("""
    SELECT r.name AS role FROM sys.database_role_members rm
    JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
    JOIN sys.database_principals u ON rm.member_principal_id = u.principal_id
    WHERE u.name = 'KCPS\\NWSSVC'
""")
roles = [row.role for row in cursor.fetchall()]
print(f"KCPS\\NWSSVC roles: {', '.join(roles)}")

conn.close()
