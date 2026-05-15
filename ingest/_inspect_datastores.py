"""Inspect existing data stores to find working connection pattern."""
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER = "https://kcpsgis.kcps.org:6443/arcgis"
USER = "siteadmin"
PASS = "d(4a6r2wssG_"

# Get token
resp = requests.post(f"{SERVER}/admin/generateToken", data={
    "username": USER, "password": PASS, "client": "requestip", "f": "json"
}, verify=False, timeout=15)
token = resp.json()["token"]

# Get details of each data store
for path in ["/enterpriseDatabases/KCPSCADPROD", "/enterpriseDatabases/KCGIS_Waze", "/enterpriseDatabases/DataStore"]:
    print(f"\n{'='*60}")
    print(f"  {path}")
    print(f"{'='*60}")
    
    resp = requests.post(f"{SERVER}/admin/data/getDataItem", data={
        "itemPath": path, "token": token, "f": "json"
    }, verify=False, timeout=15)
    result = resp.json()
    
    # Redact passwords but show connection pattern
    item = result.get("item", result)
    info = item.get("info", {})
    conn_str = info.get("dataStoreConnectionString", "")
    
    # Parse and display (redact password)
    parts = conn_str.split(";")
    for part in parts:
        if part.upper().startswith("PASSWORD"):
            print(f"  PASSWORD=****")
        else:
            print(f"  {part}")
    
    print(f"  isManaged: {info.get('isManaged')}")

# Also check what account ArcGIS Server runs as
print(f"\n{'='*60}")
print(f"  ArcGIS Server Machine Info")
print(f"{'='*60}")
resp = requests.post(f"{SERVER}/admin/machines", data={
    "token": token, "f": "json"
}, verify=False, timeout=15)
result = resp.json()
for m in result.get("machines", []):
    print(f"  Machine: {m.get('machineName')}")
    print(f"  Platform: {m.get('platform')}")
    if 'adminURL' in m:
        print(f"  Admin URL: {m.get('adminURL')}")
