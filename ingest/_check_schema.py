"""Check the actual SQL table structure created by ArcPy."""
import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=gisdb02\gissqlserver;"
    r"DATABASE=KCGIS;"
    r"Trusted_Connection=yes;",
    timeout=10
)
cursor = conn.cursor()

tables = ["WAZE_ALERTS", "WAZE_JAMS", "WAZE_IRREGULARITIES"]

for table in tables:
    print(f"\n{'='*70}")
    print(f"  dbo.{table}")
    print(f"{'='*70}")
    
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
               IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
    """)
    
    print(f"  {'Column':<30s} {'Type':<20s} {'MaxLen':<8s} {'Null':<5s}")
    print(f"  {'-'*30} {'-'*20} {'-'*8} {'-'*5}")
    for row in cursor.fetchall():
        maxlen = str(row.CHARACTER_MAXIMUM_LENGTH) if row.CHARACTER_MAXIMUM_LENGTH else ""
        print(f"  {row.COLUMN_NAME:<30s} {row.DATA_TYPE:<20s} {maxlen:<8s} {row.IS_NULLABLE:<5s}")

# Check if there are any SDE geometry helper tables
print(f"\n{'='*70}")
print("  SDE geometry tables for Waze")
print(f"{'='*70}")
cursor.execute("""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME LIKE 'SDE_GEOMETRY%' OR TABLE_NAME LIKE '%WAZE%'
    ORDER BY TABLE_NAME
""")
for row in cursor.fetchall():
    print(f"  {row.TABLE_NAME}")

# Check the SDE_layers registry
print(f"\n{'='*70}")
print("  SDE_layers entries for Waze")
print(f"{'='*70}")
cursor.execute("""
    SELECT layer_id, table_name, spatial_column, eflags, layer_config
    FROM dbo.SDE_layers
    WHERE table_name LIKE '%WAZE%'
    ORDER BY table_name
""")
for row in cursor.fetchall():
    print(f"  layer_id={row.layer_id} table={row.table_name} "
          f"spatial_col={row.spatial_column} config={row.layer_config}")

conn.close()
