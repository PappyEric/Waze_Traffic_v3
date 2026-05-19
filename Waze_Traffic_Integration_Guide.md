# Real-Time Waze Traffic Integration for 911 CAD

**A Guide for GIS Administrators**

This document outlines how to integrate a Waze Partner Hub traffic feed into an ArcGIS Enterprise environment for use in Tyler Technologies CAD (or any dynamic mapping client).

## 1. Architecture Overview

The integration follows a "Truncate and Reload" pattern to keep GIS data perfectly synchronized with the real-time feed without building up historical bloat.

1.  **Python Ingest Script**: Fetches JSON from Waze every 90 seconds.
2.  **MSSQL (ArcSDE)**: Stores three feature classes (Alerts, Jams, Irregularities).
3.  **ArcGIS Server**: Hosts a dynamic Map Service referencing the registered SQL data.
4.  **CAD Client**: Consumes the Map Service REST endpoint.

---

## 2. Database Preparation

Creating the tables manually in SQL often causes "Geometry Type Mismatch" errors in ArcSDE. Use ArcPy to ensure the Geodatabase handles the geometry storage correctly.

### Script: `create_waze_fc.py`

Run this in the ArcGIS Pro Python window to create natively registered feature classes.

```python
import arcpy, os

# Configuration
sde_conn = r"C:\Path\To\Your\Connection.sde"
spatial_ref = arcpy.SpatialReference(4326) # WGS 1984

# Define tables
tables = [
    ("WAZE_ALERTS", "POINT"),
    ("WAZE_JAMS", "POLYLINE"),
    ("WAZE_IRREGULARITIES", "POLYLINE")
]

for name, geo_type in tables:
    path = os.path.join(sde_conn, name)
    if arcpy.Exists(path): arcpy.Delete_management(path)

    arcpy.CreateFeatureclass_management(sde_conn, name, geo_type, spatial_reference=spatial_ref)
    # Add your fields here (TEXT, LONG, SHORT, DATE, etc.)
    arcpy.AddField_management(path, "uuid", "TEXT", field_length=100)
    # ... add other fields as needed
```

---

## 3. SQL Permissions

For the ingest script and ArcGIS Server to communicate, a service account is required. In this example, we use `nwssvc`.

1.  **Create SQL Login**: Enable SQL Authentication.
2.  **Grant Permissions**: The ingest script requires `db_owner` on the specific GIS database to perform `DELETE` and `INSERT` operations.
3.  **Default Schema**: Set the default schema for the user to `dbo`.

```sql
ALTER USER [nwssvc] WITH DEFAULT_SCHEMA = dbo;
ALTER ROLE db_owner ADD MEMBER [nwssvc];
```

---

## 4. The Ingest Service (`waze_ingest.py`)

The heart of the system is a Python script that uses `pyodbc` for database operations and `requests` for the API. It runs continuously, pulling new data every 90 seconds.

### Key Logic:

- **Coordinate Transformation**: Waze provides coordinates in a list. The script converts these into **WKT (Well-Known Text)** format.
- **SQL Insertion**: Uses the native SQL `geometry::STGeomFromText()` function for high performance.
- **Symbology Mapping**: The script calculates a `traffic_color` field (Green/Yellow/Orange/Red) based on jam severity, making map styling effortless.

```python
# Example SQL Insert for Alerts
insert_sql = """
    INSERT INTO dbo.WAZE_ALERTS (OBJECTID, uuid, Shape, ...)
    VALUES (?, ?, geometry::STGeomFromText(?, 4326), ...)
"""
```

---

## 5. ArcGIS Server Configuration

To keep the data "live," ArcGIS Server must reference the database directly.

1.  **Register Data Store**: In ArcGIS Server Manager, register your MSSQL database. Use the `nwssvc` SQL credentials so the server doesn't rely on Windows permissions.
2.  **Publishing**:
    - **Cashing**: MUST be set to "Draw this map service dynamically from the data."
    - **Refresh**: Ensure "Reference registered data" is selected in the publishing wizard.

---

## 6. Automating the Service

To ensure the script runs 24/7 and restarts if the computer reboots, it is installed as a Windows Service.

### Operational Architecture (Local Environment)

Due to internet connectivity restrictions on the database server (`kcpssqlprod`), the ingest polling service is installed on the local workstation acting as the gateway (with both internet access to the Waze API and database network access to SQL server).

- **Ingest Host (Workstation)**: `ADMIN8854` (Running as a Windows Service)
- **Database Server**: `kcpssqlprod` (Receiving SQL inserts over the network)
- **Service Name**: `WazeTrafficIngest`
- **Refresh Rate**: 90 Seconds
- **Database**: `NWSAegisGISDB_KanawhaCo_WV`
- **Service Account**: `nwssvc`

---

## 7. Service Management & Operations

### Service Status and Control

To manage the service on **ADMIN8854**, open **PowerShell as Administrator** and use the standard Windows Service cmdlets:

```powershell
# Check status
Get-Service WazeTrafficIngest

# Start
Start-Service WazeTrafficIngest

# Stop
Stop-Service WazeTrafficIngest

# Restart
Restart-Service WazeTrafficIngest
```

### 💡 Frequently Asked Operational Questions

#### Does it run when I log out of `emeadows`?

**Yes.** The service runs in the background under the System context. Once installed, it is completely independent of user logon sessions. You can safely log off, and it will keep polling.

#### Will the computer sleeping stop the script?

**No, sleep is disabled.** Workstation `ADMIN8854` has its power scheme configured to **"Never Sleep"** when plugged into AC power. As long as it has power, the script will stay active.

#### Where are the logs located?

Logs are output to standard output (`stdout`) to prevent disk write overhead. If running as a Windows Service, runtime errors are captured and written to the Windows Application Event Log under the `WazeTrafficIngest` source.

---
