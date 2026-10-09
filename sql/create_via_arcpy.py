"""
Create Waze feature classes via ArcPy
======================================
Creates the three Waze feature classes using arcpy.management.CreateFeatureClass
which respects the geodatabase's geometry storage configuration. 

Run from ArcGIS Pro's Python window:
    exec(open(r'd:/Gemini_Projects/Waze_Traffic_v3/sql/create_via_arcpy.py').read())
"""

import os

try:
    import arcpy
except ImportError:
    print("ERROR: Must run from ArcGIS Pro Python environment")
    raise


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SDE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "kcpssqlprod_NWSAegisGISDB_admin.sde"
)
SDE_CONNECTION = DEFAULT_SDE if os.path.exists(DEFAULT_SDE) else None

SPATIAL_REF = arcpy.SpatialReference(4326)  # WGS 1984


def find_sde_connection():
    """Find the .sde connection file for kcpssqlprod."""
    if SDE_CONNECTION and os.path.exists(SDE_CONNECTION):
        return SDE_CONNECTION
    search_dirs = [
        os.path.dirname(os.path.abspath(__file__)),
        os.path.join(os.environ.get("APPDATA", ""), "Esri", "ArcGISPro", "Favorites"),
    ]
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith(".sde") and ("kcpssqlprod" in f.lower() or "nwsaegis" in f.lower()):
                return os.path.join(search_dir, f)
    return None


# ============================================================================
# FIELD DEFINITIONS
# Each tuple: (field_name, field_type, field_length, nullable, alias)
# field_type: TEXT, LONG, SHORT, DOUBLE, FLOAT, DATE, BLOB
# ============================================================================

ALERTS_FIELDS = [
    ("uuid",            "TEXT",   100,  True,  "UUID"),
    ("alert_type",      "TEXT",   50,   True,  "Alert Type"),
    ("sub_type",        "TEXT",   100,  True,  "Sub Type"),
    ("street",          "TEXT",   255,  True,  "Street"),
    ("city",            "TEXT",   100,  True,  "City"),
    ("country",         "TEXT",   10,   True,  "Country"),
    ("description",     "TEXT",   2000, True,  "Description"),
    ("confidence",      "SHORT",  None, True,  "Confidence"),
    ("reliability",     "SHORT",  None, True,  "Reliability"),
    ("report_rating",   "SHORT",  None, True,  "Report Rating"),
    ("road_type",       "SHORT",  None, True,  "Road Type"),
    ("magvar",          "SHORT",  None, True,  "Mag Var"),
    ("from_node_id",    "LONG",   None, True,  "From Node ID"),
    ("to_node_id",      "LONG",   None, True,  "To Node ID"),
    ("pub_millis",      "DOUBLE", None, True,  "Pub Millis"),
    ("pub_date",        "DATE",   None, True,  "Pub Date"),
    ("last_updated",    "DATE",   None, True,  "Last Updated"),
]

JAMS_FIELDS = [
    ("uuid",                "DOUBLE", None, True,  "UUID"),
    ("level",               "SHORT",  None, True,  "Jam Level"),
    ("speed_kmh",           "FLOAT",  None, True,  "Speed (km/h)"),
    ("speed_mph",           "FLOAT",  None, True,  "Speed (mph)"),
    ("length_meters",       "LONG",   None, True,  "Length (m)"),
    ("delay_seconds",       "LONG",   None, True,  "Delay (s)"),
    ("street",              "TEXT",   255,  True,  "Street"),
    ("city",                "TEXT",   100,  True,  "City"),
    ("country",             "TEXT",   10,   True,  "Country"),
    ("road_type",           "SHORT",  None, True,  "Road Type"),
    ("start_node",          "TEXT",   100,  True,  "Start Node"),
    ("end_node",            "TEXT",   100,  True,  "End Node"),
    ("turn_type",           "TEXT",   20,   True,  "Turn Type"),
    ("blocking_alert_uuid", "TEXT",   100,  True,  "Blocking Alert UUID"),
    ("pub_millis",          "DOUBLE", None, True,  "Pub Millis"),
    ("pub_date",            "DATE",   None, True,  "Pub Date"),
    ("traffic_color",       "TEXT",   20,   True,  "Traffic Color"),
    ("last_updated",        "DATE",   None, True,  "Last Updated"),
]

IRREGULARITIES_FIELDS = [
    ("irregularity_id",     "DOUBLE", None, True,  "Irregularity ID"),
    ("detection_date",      "DATE",   None, True,  "Detection Date"),
    ("update_date",         "DATE",   None, True,  "Update Date"),
    ("trend",               "SHORT",  None, True,  "Trend"),
    ("street",              "TEXT",   255,  True,  "Street"),
    ("city",                "TEXT",   100,  True,  "City"),
    ("country",             "TEXT",   10,   True,  "Country"),
    ("speed_kmh",           "FLOAT",  None, True,  "Speed (km/h)"),
    ("speed_mph",           "FLOAT",  None, True,  "Speed (mph)"),
    ("regular_speed_kmh",   "FLOAT",  None, True,  "Regular Speed (km/h)"),
    ("regular_speed_mph",   "FLOAT",  None, True,  "Regular Speed (mph)"),
    ("delay_seconds",       "LONG",   None, True,  "Delay (s)"),
    ("severity",            "SHORT",  None, True,  "Severity"),
    ("jam_level",           "SHORT",  None, True,  "Jam Level"),
    ("drivers_count",       "LONG",   None, True,  "Drivers Count"),
    ("length_meters",       "LONG",   None, True,  "Length (m)"),
    ("highway",             "SHORT",  None, True,  "Highway"),
    ("alerts_count",        "SHORT",  None, True,  "Alerts Count"),
    ("n_thumbs_up",         "SHORT",  None, True,  "Thumbs Up"),
    ("n_comments",          "SHORT",  None, True,  "Comments"),
    ("n_images",            "SHORT",  None, True,  "Images"),
    ("traffic_color",       "TEXT",   20,   True,  "Traffic Color"),
    ("last_updated",        "DATE",   None, True,  "Last Updated"),
]


# ============================================================================
# FEATURE CLASS DEFINITIONS
# ============================================================================

FEATURE_CLASSES = [
    {
        "name": "WAZE_ALERTS",
        "geometry_type": "POINT",
        "fields": ALERTS_FIELDS,
    },
    {
        "name": "WAZE_JAMS",
        "geometry_type": "POLYLINE",
        "fields": JAMS_FIELDS,
    },
    {
        "name": "WAZE_IRREGULARITIES",
        "geometry_type": "POLYLINE",
        "fields": IRREGULARITIES_FIELDS,
    },
]


# ============================================================================
# MAIN
# ============================================================================

def create_feature_class(sde_conn, fc_def):
    """Create a single feature class with all fields."""
    name = fc_def["name"]
    fc_path = os.path.join(sde_conn, f"dbo.{name}")
    
    print(f"\n{'='*60}")
    print(f"Creating: {name} ({fc_def['geometry_type']})")
    print(f"{'='*60}")
    
    # Drop if exists
    if arcpy.Exists(fc_path):
        print(f"  Dropping existing table/FC: {name}")
        arcpy.management.Delete(fc_path)
    
    # Create feature class
    print(f"  Creating feature class...")
    arcpy.CreateFeatureclass_management(
        out_path=sde_conn,
        out_name=name,
        geometry_type=fc_def["geometry_type"],
        spatial_reference=SPATIAL_REF,
    )
    
    # Verify it was created
    if not arcpy.Exists(fc_path):
        print(f"  ERROR: Feature class was not created!")
        return False
    
    # Add fields
    print(f"  Adding {len(fc_def['fields'])} fields...")
    for fname, ftype, flength, nullable, alias in fc_def["fields"]:
        try:
            kwargs = {
                "in_table": fc_path,
                "field_name": fname,
                "field_type": ftype,
                "field_alias": alias,
                "field_is_nullable": "NULLABLE" if nullable else "NON_NULLABLE",
            }
            if ftype == "TEXT" and flength:
                kwargs["field_length"] = flength
            
            arcpy.AddField_management(**kwargs)
        except Exception as e:
            print(f"    WARNING: Failed to add field '{fname}': {e}")
    
    # Verify registration
    desc = arcpy.Describe(fc_path)
    print(f"  dataType:    {desc.dataType}")
    print(f"  shapeType:   {desc.shapeType}")
    if hasattr(desc, "DSID"):
        print(f"  DSID:        {desc.DSID}")
    if hasattr(desc, "isRegisteredAsVersioned"):
        print(f"  Versioned:   {desc.isRegisteredAsVersioned}")
    
    # List the fields
    fields = arcpy.ListFields(fc_path)
    print(f"  Fields ({len(fields)}):")
    for f in fields:
        print(f"    {f.name:30s} {f.type:15s} {f.length}")
    
    print(f"  SUCCESS: {name} created and registered!")
    return True


def main():
    print("=" * 60)
    print("Waze Traffic - Create Feature Classes via ArcPy")
    print("=" * 60)
    
    sde_conn = SDE_CONNECTION or find_sde_connection()
    if not sde_conn:
        print("ERROR: No .sde connection found for kcpssqlprod")
        return False
    
    print(f"\nUsing: {sde_conn}")
    
    # Check geodatabase properties
    desc = arcpy.Describe(sde_conn)
    print(f"Workspace type: {desc.workspaceType}")
    if hasattr(desc, "release"):
        print(f"GDB Release: {desc.release}")
    
    results = {}
    for fc_def in FEATURE_CLASSES:
        try:
            ok = create_feature_class(sde_conn, fc_def)
            results[fc_def["name"]] = ok
        except Exception as e:
            print(f"  FAILED: {e}")
            results[fc_def["name"]] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, ok in results.items():
        status = "[OK] Created " if ok else "[XX] Failed  "
        print(f"  {status} {name}")
    
    if all(results.values()):
        print("\nAll feature classes created!")
        print("Next: Run the ingest script to populate with Waze data.")
        print("Then: Publish as a dynamic Map Service.")
    
    return all(results.values())


main()
