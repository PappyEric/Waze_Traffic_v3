"""Just unregister KCGIS_Waze so we can re-register cleanly."""
import requests, json, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SERVER = "https://kcpsgis.kcps.org:6443/arcgis"
resp = requests.post(f"{SERVER}/admin/generateToken", data={
    "username": "siteadmin", "password": "d(4a6r2wssG_",
    "client": "requestip", "f": "json"
}, verify=False, timeout=15)
token = resp.json()["token"]
resp = requests.post(f"{SERVER}/admin/data/unregisterItem", data={
    "itemPath": "/enterpriseDatabases/KCGIS_Waze",
    "force": "true", "token": token, "f": "json",
}, verify=False, timeout=15)
print(f"Unregister: {resp.json()}")
