"""Validate the KCGIS_Waze data store after granting access."""
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

conn_win = (
    "SERVER=gisdb02\\gissqlserver;"
    "INSTANCE=sde:sqlserver:gisdb02\\gissqlserver;"
    "DBCLIENT=sqlserver;"
    "DB_CONNECTION_PROPERTIES=gisdb02\\gissqlserver;"
    "DATABASE=KCGIS;"
    "VERSION=sde.DEFAULT;"
    "AUTHENTICATION_MODE=OSA"
)

item = {
    "type": "egdb",
    "info": {"dataStoreConnectionString": conn_win, "isManaged": False},
    "path": "/enterpriseDatabases/KCGIS_Waze",
}

print("Validating KCGIS_Waze data store...")
resp = requests.post(f"{SERVER}/admin/data/validateDataItem", data={
    "item": json.dumps(item), "token": token, "f": "json",
}, verify=False, timeout=30)
result = resp.json()

for m in result.get("machines", []):
    print(f"  Machine: {m.get('machine')}")
    print(f"  Status: {m.get('status')}")
    for di in m.get("dataItems", []):
        print(f"  Validation: {di.get('validationState')}")
        if di.get("message"):
            print(f"  Message: {di.get('message')}")

print("\nDone.")
