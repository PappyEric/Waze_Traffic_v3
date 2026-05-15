import pyodbc

try:
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=kcpssqlprod;"
        r"DATABASE=NWSAegisGISDB_KanawhaCo_WV;"
        r"UID=nwssqladmin;"
        r"PWD=E8?#\W43XGfq;",
        timeout=10
    )
    print("SUCCESS: Connected as nwssqladmin to NWSAegisGISDB_KanawhaCo_WV")
    conn.close()
except Exception as e:
    print(f"FAILED nwssqladmin: {e}")

try:
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=kcpssqlprod;"
        r"DATABASE=NWSAegisGISDB_KanawhaCo_WV;"
        r"UID=nwssvc;"
        r"PWD=!K@n@w@h@911;",
        timeout=10
    )
    print("SUCCESS: Connected as nwssvc to NWSAegisGISDB_KanawhaCo_WV")
    conn.close()
except Exception as e:
    print(f"FAILED nwssvc: {e}")
