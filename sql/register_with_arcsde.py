"""
Register Waze tables with ArcSDE Geodatabase
=============================================
This script registers the three Waze traffic tables (WAZE_ALERTS, 
WAZE_JAMS, WAZE_IRREGULARITIES) as feature classes in the enterprise
geodatabase.

Prerequisites:
    - Tables must already exist and contain at least one row of data
    - Must be run on a machine with ArcGIS Pro or ArcGIS Desktop installed
    - Must have arcpy available in the Python environment
    - Connection to the geodatabase must already exist in ArcGIS Pro

Usage:
    Run from the ArcGIS Pro Python environment:
    
    > cd d:\\Gemini_Projects\\Waze_Traffic_v3\\sql
    > "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" register_with_arcsde.py

    Or run interactively from the ArcGIS Pro Python window.
"""

import os
import sys

try:
    import arcpy
except ImportError:
    print("ERROR: arcpy is not available in this Python environment.")
    print("This script must be run from the ArcGIS Pro Python environment.")
    print("")
    print('Example: "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" register_with_arcsde.py')
    sys.exit(1)


# ============================================================================
# CONFIGURATION — Update these to match your environment
# ============================================================================

# Path to your .sde connection file for gisdb02\gissqlserver
# Create this in ArcGIS Pro: Catalog > Databases > New Database Connection
# The file is saved to: %APPDATA%\Esri\ArcGISPro\Favorites\
SDE_CONNECTION = None  # Will be auto-detected or set manually below

# Manual override: uncomment and update if auto-detect doesn't work
# SDE_CONNECTION = r"C:\Users\emeadows\AppData\Roaming\Esri\ArcGISPro\Favorites\gisdb02.sde"

# Tables to register
TABLES = [
    {
        "name": "dbo.WAZE_ALERTS",
        "oid_field": "OBJECTID",
        "shape_field": "Shape",
        "geometry_type": "POINT",
    },
    {
        "name": "dbo.WAZE_JAMS",
        "oid_field": "OBJECTID",
        "shape_field": "Shape",
        "geometry_type": "POLYLINE",
    },
    {
        "name": "dbo.WAZE_IRREGULARITIES",
        "oid_field": "OBJECTID",
        "shape_field": "Shape",
        "geometry_type": "POLYLINE",
    },
]

# Coordinate system
SPATIAL_REFERENCE = arcpy.SpatialReference(4326)  # WGS 1984


# ============================================================================
# AUTO-DETECT SDE CONNECTION FILE
# ============================================================================

def find_sde_connection():
    """Try to find an .sde connection file for our server."""
    global SDE_CONNECTION
    
    if SDE_CONNECTION and os.path.exists(SDE_CONNECTION):
        return SDE_CONNECTION
    
    # Check common locations
    search_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), "Esri", "ArcGISPro", "Favorites"),
        os.path.join(os.environ.get("APPDATA", ""), "Esri", "Desktop10.8", "ArcCatalog"),
        os.path.join(os.environ.get("APPDATA", ""), "Esri", "Desktop10.7", "ArcCatalog"),
    ]
    
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith(".sde") and "gisdb02" in f.lower():
                found = os.path.join(search_dir, f)
                print(f"  Found SDE connection: {found}")
                return found
    
    return None


# ============================================================================
# REGISTRATION
# ============================================================================

def is_registered_with_geodatabase(sde_conn, table_name):
    """
    Check if a table is truly registered in the geodatabase system tables.
    
    arcpy.Describe().dataType returns 'FeatureClass' even for unregistered
    tables that have a geometry column — ArcGIS Pro auto-detects them.
    The real test is whether the table appears in GDB_ITEMS with a 
    relationship type that marks it as a registered dataset.
    """
    try:
        desc = arcpy.Describe(os.path.join(sde_conn, table_name))
        # If it has a 'versionedView' or 'isVersioned' attribute with a 
        # non-empty value, it's truly registered. But the most reliable
        # check is whether it has a proper DSID (dataset ID) in SDE_layers.
        if hasattr(desc, "DSID") and desc.DSID is not None and desc.DSID > 0:
            return True
        # Also check: registered tables show as uppercase schema in the 
        # catalog (DBO vs dbo) — but that's not programmatically reliable.
        # Fall back to checking if 'isRegisteredAsVersioned' attr exists
        if hasattr(desc, "isRegisteredAsVersioned"):
            return True
    except Exception:
        pass
    return False


def register_table(sde_conn, table_info):
    """Register a single table as a feature class in the geodatabase."""
    table_name = table_info["name"]
    fc_path = os.path.join(sde_conn, table_name)
    
    print(f"\n--- Registering: {table_name} ---")
    
    # Check if table exists
    if not arcpy.Exists(fc_path):
        print(f"  WARNING: Table {table_name} not found at {fc_path}")
        print(f"  Make sure the table exists and has data.")
        return False
    
    # Show current state for debugging
    desc = arcpy.Describe(fc_path)
    print(f"  dataType: {desc.dataType}")
    if hasattr(desc, "DSID"):
        print(f"  DSID: {desc.DSID}")
    if hasattr(desc, "isRegisteredAsVersioned"):
        print(f"  isRegisteredAsVersioned: {desc.isRegisteredAsVersioned}")
    else:
        print(f"  isRegisteredAsVersioned: (attribute not present — NOT registered)")
    
    # Register with geodatabase (always attempt — it will error if already done)
    try:
        arcpy.management.RegisterWithGeodatabase(
            in_dataset=fc_path,
            in_object_id_field=table_info["oid_field"],
            in_shape_field=table_info["shape_field"],
            in_geometry_type=table_info["geometry_type"],
            in_spatial_reference=SPATIAL_REFERENCE,
        )
        print(f"  SUCCESS: {table_name} registered as {table_info['geometry_type']}")
        return True
    except arcpy.ExecuteError as e:
        err_msg = str(e)
        # "already registered" is a success condition
        if "already registered" in err_msg.lower() or "already exists" in err_msg.lower():
            print(f"  Already registered (confirmed by geodatabase). OK.")
            return True
        print(f"  FAILED: {e}")
        print(f"  ArcPy Messages: {arcpy.GetMessages(2)}")
        return False
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("Waze Traffic — ArcSDE Feature Class Registration")
    print("=" * 60)
    
    # Find or validate SDE connection
    sde_conn = find_sde_connection()
    
    if not sde_conn:
        print("\nERROR: Could not find an .sde connection file for gisdb02.")
        print("Please create one in ArcGIS Pro:")
        print("  1. Open ArcGIS Pro")
        print("  2. Catalog pane > Databases > New Database Connection")
        print("  3. Platform: SQL Server")
        print(r"  4. Instance: gisdb02\gissqlserver")
        print("  5. Authentication: Operating System")
        print("  6. Database: <your geodatabase name>")
        print("  7. Save")
        print("")
        print("Then update SDE_CONNECTION in this script and re-run.")
        return False
    
    print(f"\nUsing SDE connection: {sde_conn}")
    
    # Register each table
    results = {}
    for table_info in TABLES:
        success = register_table(sde_conn, table_info)
        results[table_info["name"]] = success
    
    # Summary
    print("\n" + "=" * 60)
    print("REGISTRATION SUMMARY")
    print("=" * 60)
    for name, success in results.items():
        status = "✓ Registered" if success else "✗ Failed"
        print(f"  {status}  {name}")
    
    all_ok = all(results.values())
    if all_ok:
        print("\nAll tables registered successfully!")
        print("Next step: Publish as a dynamic Map Service from ArcGIS Pro/ArcMap.")
    else:
        print("\nSome registrations failed. Check the errors above.")
    
    return all_ok


if __name__ == "__main__":
    main()
