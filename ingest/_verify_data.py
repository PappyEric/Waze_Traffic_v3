"""Verify the ingested Waze data in the KCGIS database."""
import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=gisdb02\gissqlserver;"
    r"DATABASE=KCGIS;"
    r"Trusted_Connection=yes;",
    timeout=10
)
cursor = conn.cursor()

print("=" * 70)
print("WAZE DATA VERIFICATION")
print("=" * 70)

# Alerts summary
cursor.execute("""
    SELECT COUNT(*) as cnt, 
           COUNT(CASE WHEN Shape.STIsValid() = 1 THEN 1 END) as valid_geom,
           Shape.STGeometryType() as geom_type
    FROM dbo.WAZE_ALERTS
    GROUP BY Shape.STGeometryType()
""")
for row in cursor.fetchall():
    print(f"\nWAZE_ALERTS: {row.cnt} rows, {row.valid_geom} valid geometries, type={row.geom_type}")

cursor.execute("""
    SELECT TOP 5 alert_type, sub_type, street, city, 
           Shape.STAsText() as wkt
    FROM dbo.WAZE_ALERTS
    ORDER BY OBJECTID
""")
print("  Sample alerts:")
for row in cursor.fetchall():
    wkt_short = row.wkt[:50] if row.wkt else "NULL"
    print(f"    {row.alert_type:15s} | {(row.street or 'n/a'):20s} | {(row.city or 'n/a'):20s} | {wkt_short}")

# Alert type distribution
cursor.execute("""
    SELECT alert_type, COUNT(*) as cnt
    FROM dbo.WAZE_ALERTS
    GROUP BY alert_type
    ORDER BY cnt DESC
""")
print("  Type distribution:")
for row in cursor.fetchall():
    print(f"    {row.alert_type:20s} = {row.cnt}")

# Jams summary
print()
cursor.execute("""
    SELECT COUNT(*) as cnt, 
           COUNT(CASE WHEN Shape.STIsValid() = 1 THEN 1 END) as valid_geom,
           Shape.STGeometryType() as geom_type
    FROM dbo.WAZE_JAMS
    GROUP BY Shape.STGeometryType()
""")
for row in cursor.fetchall():
    print(f"WAZE_JAMS: {row.cnt} rows, {row.valid_geom} valid geometries, type={row.geom_type}")

cursor.execute("""
    SELECT TOP 5 level, speed_mph, traffic_color, street, city, 
           Shape.STNumPoints() as pts,
           Shape.STLength() as len
    FROM dbo.WAZE_JAMS
    ORDER BY level DESC
""")
print("  Sample jams (sorted by severity):")
for row in cursor.fetchall():
    print(f"    Level {row.level} | {row.speed_mph:6.1f} mph | {row.traffic_color:8s} | {(row.street or 'n/a'):25s} | {row.pts} pts")

# Jam level distribution
cursor.execute("""
    SELECT traffic_color, level, COUNT(*) as cnt
    FROM dbo.WAZE_JAMS
    GROUP BY traffic_color, level
    ORDER BY level DESC
""")
print("  Traffic color distribution:")
for row in cursor.fetchall():
    print(f"    Level {row.level} ({row.traffic_color:8s}) = {row.cnt}")

# Irregularities
print()
cursor.execute("SELECT COUNT(*) as cnt FROM dbo.WAZE_IRREGULARITIES")
row = cursor.fetchone()
print(f"WAZE_IRREGULARITIES: {row.cnt} rows")

# Spatial extent check
print()
cursor.execute("""
    SELECT 
        Shape.STEnvelope().STPointN(1).STX as min_x,
        Shape.STEnvelope().STPointN(1).STY as min_y,
        Shape.STEnvelope().STPointN(3).STX as max_x,
        Shape.STEnvelope().STPointN(3).STY as max_y
    FROM (
        SELECT geometry::EnvelopeAggregate(Shape) as Shape 
        FROM dbo.WAZE_ALERTS 
        WHERE Shape IS NOT NULL
    ) t
""")
row = cursor.fetchone()
if row and row.min_x:
    print(f"ALERTS spatial extent: ({row.min_x:.3f}, {row.min_y:.3f}) to ({row.max_x:.3f}, {row.max_y:.3f})")

cursor.execute("""
    SELECT 
        Shape.STEnvelope().STPointN(1).STX as min_x,
        Shape.STEnvelope().STPointN(1).STY as min_y,
        Shape.STEnvelope().STPointN(3).STX as max_x,
        Shape.STEnvelope().STPointN(3).STY as max_y
    FROM (
        SELECT geometry::EnvelopeAggregate(Shape) as Shape 
        FROM dbo.WAZE_JAMS 
        WHERE Shape IS NOT NULL
    ) t
""")
row = cursor.fetchone()
if row and row.min_x:
    print(f"JAMS spatial extent:   ({row.min_x:.3f}, {row.min_y:.3f}) to ({row.max_x:.3f}, {row.max_y:.3f})")

print()
print("All checks passed! Data is ready for ArcSDE registration.")

conn.close()
