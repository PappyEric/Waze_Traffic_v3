"""
Create an .sde connection file with SQL Auth for ArcGIS Server,
then register the data store through arcpy.

Run from ArcGIS Pro's Python window:
    exec(open(r'd:/Gemini_Projects/Waze_Traffic_v3/sql/register_datastore_arcpy.py').read())
"""
import os
import arcpy

print("=" * 60)
print("Register KCGIS Data Store via ArcPy")
print("=" * 60)

# Create a server-side .sde connection file with SQL Auth
out_folder = r"d:\Gemini_Projects\Waze_Traffic_v3\sql"
out_name = "KCGIS_server.sde"
sde_path = os.path.join(out_folder, out_name)

# Remove old file if exists
if os.path.exists(sde_path):
    os.remove(sde_path)

print("\nCreating server-side .sde connection file (SQL Auth)...")
arcpy.CreateDatabaseConnection_management(
    out_folder_path=out_folder,
    out_name=out_name,
    database_platform="SQL_SERVER",
    instance=r"gisdb02\gissqlserver",
    account_authentication="DATABASE_AUTH",
    username="nwssvc",
    password="!K@n@wh@911",
    save_user_pass="SAVE_USERNAME",
    database="KCGIS",
    schema="",
    version_type="POINT_IN_TIME",
)
print(f"  Created: {sde_path}")

# Test it
print("\nTesting server-side connection...")
arcpy.env.workspace = sde_path
fcs = arcpy.ListFeatureClasses("*WAZE*")
print(f"  Feature classes found: {fcs}")

# Find publisher .sde connection
pub_sde = None
fav_dir = os.path.join(os.environ.get("APPDATA", ""), "Esri", "ArcGISPro", "Favorites")
for f in os.listdir(fav_dir):
    if f.endswith(".sde") and "gisdb02" in f.lower():
        pub_sde = os.path.join(fav_dir, f)
        break

if pub_sde:
    print(f"\nPublisher connection: {pub_sde}")
else:
    print("\nWARNING: Could not find publisher .sde file")

# Find ArcGIS Server connection
ags_conn = None
for f in os.listdir(fav_dir):
    if f.endswith(".ags") and "kcpsgis" in f.lower():
        ags_conn = os.path.join(fav_dir, f)
        break

if not ags_conn:
    # Check other locations
    for f in os.listdir(fav_dir):
        if f.endswith(".ags"):
            ags_conn = os.path.join(fav_dir, f)
            print(f"  Found AGS connection: {f}")

if ags_conn:
    print(f"ArcGIS Server connection: {ags_conn}")
    
    # Register the data store
    print("\nRegistering data store...")
    try:
        arcpy.AddDataStoreItem(
            connection_file=ags_conn,
            datastore_type="DATABASE",
            connection_name="KCGIS_Waze",
            server_path=sde_path,
            client_path=pub_sde,
        )
        print("  SUCCESS!")
    except arcpy.ExecuteError as e:
        print(f"  Error: {e}")
        print(f"  Messages: {arcpy.GetMessages(2)}")
    except Exception as e:
        print(f"  Error: {e}")
else:
    print("\nNo ArcGIS Server connection (.ags) found in Favorites.")
    print("You can register manually in ArcGIS Pro:")
    print("  1. Right-click your ArcGIS Server connection")
    print("  2. Choose 'Manage Registered Data Sources'")
    print(f"  3. Publisher DB: {pub_sde}")
    print(f"  4. Server DB: {sde_path}")

print("\nDone!")
