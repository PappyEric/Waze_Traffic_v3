"""Check if OBJECTID has IDENTITY property."""
import pyodbc
conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=gisdb02\gissqlserver;"
    r"DATABASE=KCGIS;"
    r"Trusted_Connection=yes;", timeout=10
)
cursor = conn.cursor()

for table in ['WAZE_ALERTS', 'WAZE_JAMS', 'WAZE_IRREGULARITIES']:
    cursor.execute(f"""
        SELECT COLUMNPROPERTY(OBJECT_ID('dbo.{table}'), 'OBJECTID', 'IsIdentity') as is_identity
    """)
    row = cursor.fetchone()
    print(f"{table}: OBJECTID IsIdentity = {row.is_identity}")

    # Also check for SDE row_id_column_type in SDE_table_registry
    cursor.execute(f"""
        SELECT registration_id, row_id_column_name, row_id_column_type 
        FROM dbo.SDE_table_registry 
        WHERE table_name = '{table}'
    """)
    reg = cursor.fetchone()
    if reg:
        print(f"  SDE reg: id={reg.registration_id} rowid_col={reg.row_id_column_name} type={reg.row_id_column_type}")
    else:
        print(f"  SDE reg: not found")

conn.close()
