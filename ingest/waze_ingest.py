"""
Waze Real-Time Traffic Feed Ingest Service
============================================
Fetches data from the Waze Partner Hub API every 30 seconds and writes
alerts, jams, and irregularities into ArcSDE-compatible MSSQL tables.

Usage:
    Manual run:     python waze_ingest.py
    One-shot test:  python waze_ingest.py --once
    Install service: python install_service.py install
    
Connection: Windows Authentication to gisdb02\\gissqlserver
"""

import sys
import os
import time
import json
import logging
import argparse
from datetime import datetime, timezone

import requests
import pyodbc

# ============================================================================
# CONFIGURATION
# ============================================================================

# Waze Partner Hub API
WAZE_FEED_URL = (
    "https://www.waze.com/partnerhub-api/partners/11564347598/"
    "waze-feeds/67b4a799-aac0-4584-8253-3b396b4bdf08?format=1"
)

# MSSQL Connection (Windows Authentication)
# Update DB_NAME to your actual geodatabase name
DB_SERVER = r"kcpssqlprod"
DB_NAME = "NWSAegisGISDB_KanawhaCo_WV"

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID=nwssvc;"
    f"PWD=!K@n@w@h@911;"
)

# Polling interval in seconds
POLL_INTERVAL = 90

# Request timeout in seconds
REQUEST_TIMEOUT = 25

# ============================================================================
# LOGGING
# ============================================================================

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(LOG_DIR, "waze_ingest.log"),
            encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("WazeIngest")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def epoch_ms_to_datetime(millis):
    """Convert epoch milliseconds to datetime string for SQL Server."""
    if millis is None:
        return None
    try:
        dt = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return None


def jam_level_to_color(level):
    """Map Waze jam level (0-5) to a traffic color for symbology."""
    mapping = {
        0: "green",       # Free flow
        1: "green",       # Free flow
        2: "yellow",      # Light traffic
        3: "orange",      # Moderate traffic
        4: "red",         # Heavy traffic
        5: "darkred",     # Standstill / road closed
    }
    return mapping.get(level, "green")


def build_point_wkt(location):
    """Build a WKT POINT from a Waze location dict {x, y}."""
    if not location or "x" not in location or "y" not in location:
        return None
    x = location["x"]
    y = location["y"]
    if x is None or y is None:
        return None
    return f"POINT({x} {y})"


def build_linestring_wkt(line_array):
    """Build a WKT LINESTRING from a Waze line array [{x, y}, ...]."""
    if not line_array or len(line_array) < 2:
        return None
    coords = []
    for pt in line_array:
        if "x" in pt and "y" in pt and pt["x"] is not None and pt["y"] is not None:
            coords.append(f"{pt['x']} {pt['y']}")
    if len(coords) < 2:
        return None
    return f"LINESTRING({', '.join(coords)})"


def safe_str(value, max_len=None):
    """Safely convert a value to string, with optional truncation."""
    if value is None:
        return None
    s = str(value)
    if max_len and len(s) > max_len:
        s = s[:max_len]
    return s


def safe_float(value):
    """Safely convert to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """Safely convert to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def kmh_to_mph(kmh):
    """Convert km/h to mph."""
    if kmh is None:
        return None
    try:
        return round(float(kmh) * 0.621371, 2)
    except (ValueError, TypeError):
        return None


# ============================================================================
# FETCH WAZE DATA
# ============================================================================

def fetch_waze_feed():
    """Fetch the Waze Partner Hub JSON feed."""
    logger.info("Fetching Waze feed...")
    try:
        response = requests.get(WAZE_FEED_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        alerts = data.get("alerts", [])
        jams = data.get("jams", [])
        irregularities = data.get("irregularities", [])
        
        logger.info(
            f"Received: {len(alerts)} alerts, {len(jams)} jams, "
            f"{len(irregularities)} irregularities"
        )
        return alerts, jams, irregularities
    except requests.exceptions.Timeout:
        logger.error("Waze API request timed out")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Waze feed: {e}")
        raise


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_connection():
    """Get a pyodbc connection using Windows Authentication."""
    return pyodbc.connect(CONNECTION_STRING, timeout=10)


def ingest_alerts(cursor, alerts):
    """Truncate and reload the WAZE_ALERTS table."""
    cursor.execute("DELETE FROM dbo.WAZE_ALERTS")
    
    if not alerts:
        logger.info("No alerts to insert")
        return 0

    insert_sql = """
        INSERT INTO dbo.WAZE_ALERTS (
            OBJECTID,
            uuid, alert_type, sub_type, street, city, country,
            description, confidence, reliability, report_rating,
            road_type, magvar, from_node_id, to_node_id,
            pub_millis, pub_date, Shape
        ) VALUES (
            ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, 
            geometry::STGeomFromText(?, 4326)
        )
    """

    count = 0
    for alert in alerts:
        wkt = build_point_wkt(alert.get("location"))
        if wkt is None:
            continue  # Skip alerts without valid location

        pub_millis = safe_int(alert.get("pubMillis"))

        count += 1  # OBJECTID starts at 1
        params = (
            count,
            safe_str(alert.get("uuid"), 100),
            safe_str(alert.get("type"), 50),
            safe_str(alert.get("subtype"), 100),
            safe_str(alert.get("street"), 255),
            safe_str(alert.get("city"), 100),
            safe_str(alert.get("country"), 10),
            safe_str(alert.get("reportDescription"), 2000),
            safe_int(alert.get("confidence")),
            safe_int(alert.get("reliability")),
            safe_int(alert.get("reportRating")),
            safe_int(alert.get("roadType")),
            safe_int(alert.get("magvar")),
            safe_int(alert.get("fromNodeId")),
            safe_int(alert.get("toNodeId")),
            pub_millis,
            epoch_ms_to_datetime(pub_millis),
            wkt,
        )

        try:
            cursor.execute(insert_sql, params)
        except pyodbc.Error as e:
            count -= 1  # Roll back the counter on failure
            logger.warning(f"Failed to insert alert {alert.get('uuid')}: {e}")

    logger.info(f"Inserted {count} alerts")
    return count


def ingest_jams(cursor, jams):
    """Truncate and reload the WAZE_JAMS table."""
    cursor.execute("DELETE FROM dbo.WAZE_JAMS")
    
    if not jams:
        logger.info("No jams to insert")
        return 0

    insert_sql = """
        INSERT INTO dbo.WAZE_JAMS (
            OBJECTID,
            uuid, level_, speed_kmh, speed_mph, length_meters,
            delay_seconds, street, city, country, road_type,
            start_node, end_node, turn_type, blocking_alert_uuid,
            pub_millis, pub_date, traffic_color, Shape
        ) VALUES (
            ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            geometry::STGeomFromText(?, 4326)
        )
    """

    count = 0
    for jam in jams:
        wkt = build_linestring_wkt(jam.get("line"))
        if wkt is None:
            continue  # Skip jams without valid geometry

        level = safe_int(jam.get("level"))
        speed_kmh = safe_float(jam.get("speedKMH"))
        pub_millis = safe_int(jam.get("pubMillis"))

        count += 1  # OBJECTID starts at 1
        params = (
            count,
            safe_int(jam.get("uuid")),
            level,
            speed_kmh,
            kmh_to_mph(speed_kmh),
            safe_int(jam.get("length")),
            safe_int(jam.get("delay")),
            safe_str(jam.get("street"), 255),
            safe_str(jam.get("city"), 100),
            safe_str(jam.get("country"), 10),
            safe_int(jam.get("roadType")),
            safe_str(jam.get("startNode"), 100),
            safe_str(jam.get("endNode"), 100),
            safe_str(jam.get("turnType"), 20),
            safe_str(jam.get("blockingAlertUuid"), 100),
            pub_millis,
            epoch_ms_to_datetime(pub_millis),
            jam_level_to_color(level),
            wkt,
        )

        try:
            cursor.execute(insert_sql, params)
        except pyodbc.Error as e:
            count -= 1
            logger.warning(f"Failed to insert jam {jam.get('uuid')}: {e}")

    logger.info(f"Inserted {count} jams")
    return count


def ingest_irregularities(cursor, irregularities):
    """Truncate and reload the WAZE_IRREGULARITIES table."""
    cursor.execute("DELETE FROM dbo.WAZE_IRREGULARITIES")
    
    if not irregularities:
        logger.info("No irregularities to insert")
        return 0

    insert_sql = """
        INSERT INTO dbo.WAZE_IRREGULARITIES (
            OBJECTID,
            irregularity_id, detection_date, update_date, trend,
            street, city, country,
            speed_kmh, speed_mph, regular_speed_kmh, regular_speed_mph,
            delay_seconds, severity, jam_level, drivers_count,
            length_meters, highway, alerts_count,
            n_thumbs_up, n_comments, n_images,
            traffic_color, Shape
        ) VALUES (
            ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?,
            geometry::STGeomFromText(?, 4326)
        )
    """

    count = 0
    for irr in irregularities:
        wkt = build_linestring_wkt(irr.get("line"))
        if wkt is None:
            continue

        speed_kmh = safe_float(irr.get("speed"))
        regular_speed = safe_float(irr.get("regularSpeed"))
        jam_level = safe_int(irr.get("jamLevel"))
        detection_ms = safe_int(irr.get("detectionDateMillis"))
        update_ms = safe_int(irr.get("updateDateMillis"))

        count += 1  # OBJECTID starts at 1
        params = (
            count,
            safe_int(irr.get("id")),
            epoch_ms_to_datetime(detection_ms),
            epoch_ms_to_datetime(update_ms),
            safe_int(irr.get("trend")),
            safe_str(irr.get("street"), 255),
            safe_str(irr.get("city"), 100),
            safe_str(irr.get("country"), 10),
            speed_kmh,
            kmh_to_mph(speed_kmh),
            regular_speed,
            kmh_to_mph(regular_speed),
            safe_int(irr.get("delaySeconds")),
            safe_int(irr.get("severity")),
            jam_level,
            safe_int(irr.get("driversCount")),
            safe_int(irr.get("length")),
            1 if irr.get("highway") else 0,
            safe_int(irr.get("alertsCount")),
            safe_int(irr.get("nThumbsUp")),
            safe_int(irr.get("nComments")),
            safe_int(irr.get("nImages")),
            jam_level_to_color(jam_level),
            wkt,
        )

        try:
            cursor.execute(insert_sql, params)
        except pyodbc.Error as e:
            count -= 1
            logger.warning(f"Failed to insert irregularity {irr.get('id')}: {e}")

    logger.info(f"Inserted {count} irregularities")
    return count


# ============================================================================
# MAIN INGEST CYCLE
# ============================================================================

def run_ingest_cycle():
    """Execute a single fetch-and-load cycle."""
    start_time = time.time()
    
    try:
        # Fetch data from Waze
        alerts, jams, irregularities = fetch_waze_feed()
        
        # Connect to MSSQL and load
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # All three tables are refreshed atomically
            alert_count = ingest_alerts(cursor, alerts)
            jam_count = ingest_jams(cursor, jams)
            irr_count = ingest_irregularities(cursor, irregularities)
            
            conn.commit()
            
            elapsed = round(time.time() - start_time, 2)
            logger.info(
                f"Cycle complete in {elapsed}s — "
                f"{alert_count} alerts, {jam_count} jams, "
                f"{irr_count} irregularities"
            )
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error, rolled back: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Ingest cycle failed: {e}")
        return False


def run_continuous():
    """Run the ingest loop continuously every POLL_INTERVAL seconds."""
    logger.info("=" * 60)
    logger.info("Waze Traffic Ingest Service Starting")
    logger.info(f"  Server:   {DB_SERVER}")
    logger.info(f"  Database: {DB_NAME}")
    logger.info(f"  Interval: {POLL_INTERVAL}s")
    logger.info(f"  Feed URL: {WAZE_FEED_URL[:80]}...")
    logger.info("=" * 60)
    
    consecutive_failures = 0
    max_failures = 10  # After 10 consecutive failures, increase wait time
    
    while True:
        success = run_ingest_cycle()
        
        if success:
            consecutive_failures = 0
            time.sleep(POLL_INTERVAL)
        else:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                wait_time = min(300, POLL_INTERVAL * consecutive_failures)
                logger.warning(
                    f"{consecutive_failures} consecutive failures. "
                    f"Backing off to {wait_time}s"
                )
                time.sleep(wait_time)
            else:
                time.sleep(POLL_INTERVAL)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Waze Real-Time Traffic Feed Ingest Service"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ingest cycle and exit"
    )
    parser.add_argument(
        "--server",
        type=str,
        default=None,
        help=f"Override SQL Server instance (default: {DB_SERVER})"
    )
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help=f"Override database name (default: {DB_NAME})"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help=f"Override poll interval in seconds (default: {POLL_INTERVAL})"
    )
    
    args = parser.parse_args()
    
    # Apply overrides
    if args.server:
        DB_SERVER = args.server
        CONNECTION_STRING = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID=nwssvc;"
            f"PWD=!K@n@w@h@911;"
        )
    if args.database:
        DB_NAME = args.database
        CONNECTION_STRING = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID=nwssvc;"
            f"PWD=!K@n@w@h@911;"
        )
    if args.interval:
        POLL_INTERVAL = args.interval
    
    if args.once:
        logger.info("Running single ingest cycle...")
        success = run_ingest_cycle()
        sys.exit(0 if success else 1)
    else:
        try:
            run_continuous()
        except KeyboardInterrupt:
            logger.info("Shutting down (Ctrl+C)")
            sys.exit(0)
