import os
import arcpy

out_folder = r"d:\Gemini_Projects\Waze_Traffic_v3\sql"
out_name = "kcpssqlprod_NWSAegisGISDB.sde"
sde_path = os.path.join(out_folder, out_name)

if os.path.exists(sde_path):
    os.remove(sde_path)

print(f"Creating .sde connection to kcpssqlprod / NWSAegisGISDB_KanawhaCo_WV...")
arcpy.CreateDatabaseConnection_management(
    out_folder_path=out_folder,
    out_name=out_name,
    database_platform="SQL_SERVER",
    instance="kcpssqlprod",
    account_authentication="DATABASE_AUTH",
    username="nwssvc",
    password="!K@n@w@h@911",
    save_user_pass="SAVE_USERNAME",
    database="NWSAegisGISDB_KanawhaCo_WV"
)
print(f"SDE Connection created: {sde_path}")

# Modify create_via_arcpy.py to use this connection
with open(r"d:\Gemini_Projects\Waze_Traffic_v3\sql\create_via_arcpy.py", "r") as f:
    content = f.read()

content = content.replace('SDE_CONNECTION = None  # Auto-detect', f'SDE_CONNECTION = r"{sde_path}"')

with open(r"d:\Gemini_Projects\Waze_Traffic_v3\sql\create_via_arcpy_new.py", "w") as f:
    f.write(content)

print("Created create_via_arcpy_new.py")
