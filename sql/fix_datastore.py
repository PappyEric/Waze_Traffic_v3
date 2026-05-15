"""Re-register with corrected connection string matching publisher format."""
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER = "https://kcpsgis.kcps.org:6443/arcgis"

resp = requests.post(f"{SERVER}/admin/generateToken", data={
    "username": "siteadmin", "password": "d(4a6r2wssG_",
    "client": "requestip", "f": "json"
}, verify=False, timeout=15)
token = resp.json()["token"]
print("Authenticated.\n")

# Force unregister old
print("Unregistering old KCGIS_Waze...")
resp = requests.post(f"{SERVER}/admin/data/unregisterItem", data={
    "itemPath": "/enterpriseDatabases/KCGIS_Waze",
    "force": "true",
    "token": token, "f": "json",
}, verify=False, timeout=15)
print(f"  {resp.json()}\n")

# Match the exact format from the publisher connection string
# but with SQL auth credentials for the server side
conn_str = (
    "SERVER=gisdb02;"
    "INSTANCE=sde:sqlserver:gisdb02\\gissqlserver;"
    "DBCLIENT=sqlserver;"
    "DB_CONNECTION_PROPERTIES=gisdb02\\gissqlserver;"
    "DATABASE=KCGIS;"
    "USER=nwssvc;"
    "PASSWORD=!K@n@wh@911;"
    "VERSION=dbo.DEFAULT;"
    "AUTHENTICATION_MODE=DBMS"
)

item = {
    "type": "egdb",
    "info": {
        "dataStoreConnectionString": conn_str,
        "isManaged": False,
    },
    "path": "/enterpriseDatabases/KCGIS_Waze",
}

print("Registering with corrected connection string (SQL Auth)...")
print(f"  SERVER=gisdb02")
print(f"  INSTANCE=sde:sqlserver:gisdb02\\gissqlserver")
print(f"  VERSION=dbo.DEFAULT")
print(f"  AUTH=DBMS (user=nwssvc)")
resp = requests.post(f"{SERVER}/admin/data/registerItem", data={
    "item": json.dumps(item), "token": token, "f": "json",
}, verify=False, timeout=30)
print(f"  Register: {resp.json()}\n")

# Validate
print("Validating...")
resp = requests.post(f"{SERVER}/admin/data/validateDataItem", data={
    "item": json.dumps(item), "token": token, "f": "json",
}, verify=False, timeout=30)
result = resp.json()
for m in result.get("machines", []):
    for di in m.get("dataItems", []):
        state = di.get("validationState")
        msg = di.get("message", "")
        print(f"  Result: {state}")
        if msg:
            print(f"  Message: {msg}")

# If SQL auth fails, try OSA with corrected format
if any(m.get("status") == "error" for m in result.get("machines", [])):
    print("\nSQL Auth failed. Trying OSA with corrected format...")
    
    requests.post(f"{SERVER}/admin/data/unregisterItem", data={
        "itemPath": "/enterpriseDatabases/KCGIS_Waze",
        "force": "true", "token": token, "f": "json",
    }, verify=False, timeout=15)
    
    conn_osa = (
        "SERVER=gisdb02;"
        "INSTANCE=sde:sqlserver:gisdb02\\gissqlserver;"
        "DBCLIENT=sqlserver;"
        "DB_CONNECTION_PROPERTIES=gisdb02\\gissqlserver;"
        "DATABASE=KCGIS;"
        "VERSION=dbo.DEFAULT;"
        "AUTHENTICATION_MODE=OSA"
    )
    
    item_osa = {
        "type": "egdb",
        "info": {"dataStoreConnectionString": conn_osa, "isManaged": False},
        "path": "/enterpriseDatabases/KCGIS_Waze",
    }
    
    resp = requests.post(f"{SERVER}/admin/data/registerItem", data={
        "item": json.dumps(item_osa), "token": token, "f": "json",
    }, verify=False, timeout=30)
    print(f"  Register (OSA): {resp.json()}")
    
    resp = requests.post(f"{SERVER}/admin/data/validateDataItem", data={
        "item": json.dumps(item_osa), "token": token, "f": "json",
    }, verify=False, timeout=30)
    result = resp.json()
    for m in result.get("machines", []):
        for di in m.get("dataItems", []):
            print(f"  Validate (OSA): {di.get('validationState')}")
            if di.get("message"):
                print(f"  Message: {di.get('message')}")

print("\nDone!")
