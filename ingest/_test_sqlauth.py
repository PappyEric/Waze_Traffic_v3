"""Test SQL auth connection with nwssvc credentials."""
import pyodbc

try:
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=gisdb02\gissqlserver;"
        r"DATABASE=KCGIS;"
        r"UID=nwssvc;"
        r"PWD=!K@n@wh@911;",
        timeout=10
    )
    cursor = conn.cursor()
    cursor.execute("SELECT SYSTEM_USER AS login, USER_NAME() AS db_user, DB_NAME() AS db_name")
    row = cursor.fetchone()
    print(f"SUCCESS: Connected as {row.login} / DB user: {row.db_user} / DB: {row.db_name}")
    
    # Check if nwssvc can read Waze tables
    cursor.execute("SELECT COUNT(*) as cnt FROM dbo.WAZE_JAMS")
    print(f"WAZE_JAMS rows: {cursor.fetchone().cnt}")
    
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")
