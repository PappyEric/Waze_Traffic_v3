"""
Register the KCGIS database as a Data Store on ArcGIS Server.
This allows ArcGIS Server to access the Waze feature classes
for dynamic Map Service publishing.
"""

import requests
import json
import urllib3

# Suppress SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

ARCGIS_SERVER_URL = "https://kcpsgis.kcps.org:6443/arcgis"
ADMIN_USER = "siteadmin"
ADMIN_PASSWORD = "d(4a6r2wssG_"

# Database connection for ArcGIS Server to use
DB_SERVER = r"gisdb02\gissqlserver"
DB_NAME = "KCGIS"
DB_USER = "nwssvc"
DB_PASSWORD = "!K@n@wh@911"

# Data store path (must start with /enterpriseDatabases/)
DATA_STORE_PATH = "/enterpriseDatabases/KCGIS_Waze"


def get_token(server_url, username, password):
    """Get an admin token from ArcGIS Server."""
    token_url = f"{server_url}/admin/generateToken"
    params = {
        "username": username,
        "password": password,
        "client": "requestip",
        "f": "json",
    }
    resp = requests.post(token_url, data=params, verify=False, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    
    if "token" not in result:
        raise Exception(f"Failed to get token: {result.get('messages', result)}")
    
    return result["token"]


def register_data_store(server_url, token):
    """Register the KCGIS database as a data store."""
    
    # Build the connection string in ArcGIS Server format
    # This is the ESRI enterprise geodatabase connection string format
    conn_string = (
        f"SERVER={DB_SERVER};"
        f"INSTANCE=sde:sqlserver:{DB_SERVER};"
        f"DBCLIENT=sqlserver;"
        f"DB_CONNECTION_PROPERTIES={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"USER={DB_USER};"
        f"PASSWORD={DB_PASSWORD};"
        f"VERSION=sde.DEFAULT;"
        f"AUTHENTICATION_MODE=DBMS"
    )
    
    item = {
        "type": "egdb",
        "info": {
            "dataStoreConnectionString": conn_string,
            "isManaged": False,
        },
        "path": DATA_STORE_PATH,
    }
    
    register_url = f"{server_url}/admin/data/registerItem"
    params = {
        "item": json.dumps(item),
        "token": token,
        "f": "json",
    }
    
    print(f"Registering data store: {DATA_STORE_PATH}")
    print(f"  Database: {DB_SERVER} / {DB_NAME}")
    print(f"  User: {DB_USER}")
    
    resp = requests.post(register_url, data=params, verify=False, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    if result.get("status") == "success":
        print(f"  SUCCESS: Data store registered!")
        return True
    else:
        print(f"  Response: {json.dumps(result, indent=2)}")
        return False


def validate_data_store(server_url, token):
    """Validate the registered data store."""
    validate_url = f"{server_url}/admin/data/validateDataItem"
    
    item = {
        "type": "egdb",
        "info": {
            "dataStoreConnectionString": (
                f"SERVER={DB_SERVER};"
                f"INSTANCE=sde:sqlserver:{DB_SERVER};"
                f"DBCLIENT=sqlserver;"
                f"DB_CONNECTION_PROPERTIES={DB_SERVER};"
                f"DATABASE={DB_NAME};"
                f"USER={DB_USER};"
                f"PASSWORD={DB_PASSWORD};"
                f"VERSION=sde.DEFAULT;"
                f"AUTHENTICATION_MODE=DBMS"
            ),
            "isManaged": False,
        },
        "path": DATA_STORE_PATH,
    }
    
    params = {
        "item": json.dumps(item),
        "token": token,
        "f": "json",
    }
    
    print(f"\nValidating data store connection...")
    resp = requests.post(validate_url, data=params, verify=False, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    
    if result.get("status") == "success":
        print(f"  VALID: ArcGIS Server can connect to {DB_SERVER}/{DB_NAME}")
    else:
        print(f"  Validation result: {json.dumps(result, indent=2)}")
    
    return result


def list_data_stores(server_url, token):
    """List existing data stores."""
    list_url = f"{server_url}/admin/data/findItems"
    params = {
        "parentPath": "/enterpriseDatabases",
        "ancestorPath": "/",
        "types": "egdb",
        "token": token,
        "f": "json",
    }
    
    resp = requests.post(list_url, data=params, verify=False, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    
    items = result.get("items", [])
    print(f"\nExisting enterprise database data stores ({len(items)}):")
    for item in items:
        print(f"  - {item.get('path', 'unknown')}")
    
    return items


def main():
    print("=" * 60)
    print("ArcGIS Server — Register KCGIS Data Store")
    print("=" * 60)
    
    # Get admin password
    admin_pw = ADMIN_PASSWORD
    
    # Get token
    print(f"\nConnecting to {ARCGIS_SERVER_URL}...")
    try:
        token = get_token(ARCGIS_SERVER_URL, ADMIN_USER, admin_pw)
        print("  Authenticated successfully.")
    except Exception as e:
        print(f"  FAILED to authenticate: {e}")
        return
    
    # List existing data stores
    list_data_stores(ARCGIS_SERVER_URL, token)
    
    # Validate first
    validate_data_store(ARCGIS_SERVER_URL, token)
    
    # Register
    register_data_store(ARCGIS_SERVER_URL, token)
    
    # List again to confirm
    list_data_stores(ARCGIS_SERVER_URL, token)
    
    print("\nDone! Now retry publishing the Waze_Traffic Map Service from ArcGIS Pro.")


if __name__ == "__main__":
    main()
