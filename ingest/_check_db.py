"""Quick script to check the KCGIS database for SDE/GDB system tables."""
import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=gisdb02\gissqlserver;"
    r"DATABASE=KCGIS;"
    r"Trusted_Connection=yes;",
    timeout=10
)
cursor = conn.cursor()

# Check for SDE system tables (confirms geodatabase)
cursor.execute(
    "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
    "WHERE TABLE_NAME LIKE 'SDE[_]%' OR TABLE_NAME LIKE 'GDB[_]%' "
    "ORDER BY TABLE_SCHEMA, TABLE_NAME"
)
tables = cursor.fetchall()
print(f"SDE/GDB system tables found in KCGIS: {len(tables)}")
for t in tables[:20]:
    print(f"  [{t.TABLE_SCHEMA}].{t.TABLE_NAME}")
if len(tables) > 20:
    print(f"  ... and {len(tables)-20} more")

print()

# Check for any existing Waze-like tables
cursor.execute(
    "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
    "WHERE TABLE_NAME LIKE '%[Ww]aze%' OR TABLE_NAME LIKE '%traffic%' "
    "ORDER BY TABLE_NAME"
)
waze_tables = cursor.fetchall()
if waze_tables:
    print(f"Existing Waze/traffic tables: {len(waze_tables)}")
    for t in waze_tables:
        print(f"  [{t.TABLE_SCHEMA}].{t.TABLE_NAME}")
else:
    print("No existing Waze/traffic tables found.")

# Check current user info
cursor.execute("SELECT SYSTEM_USER AS login, USER_NAME() AS db_user, DB_NAME() AS db_name")
row = cursor.fetchone()
print(f"\nConnected as: {row.login} / DB user: {row.db_user} / Database: {row.db_name}")

# Check user roles
cursor.execute(
    "SELECT r.name AS role FROM sys.database_role_members rm "
    "JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id "
    "JOIN sys.database_principals u ON rm.member_principal_id = u.principal_id "
    "WHERE u.name = USER_NAME()"
)
roles = cursor.fetchall()
print(f"Database roles: {', '.join(r.role for r in roles) if roles else 'none'}")

conn.close()
