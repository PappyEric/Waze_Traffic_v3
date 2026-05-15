-- ============================================================================
-- Waze Real-Time Traffic Feed — ArcSDE-Compatible Tables
-- Target: gisdb02\gissqlserver
-- 
-- These tables are designed to be registered with an ArcSDE geodatabase.
-- Requirements met:
--   - OBJECTID: int IDENTITY(1,1) NOT NULL PRIMARY KEY (clustered)
--   - Shape: geometry column with consistent SRID 4326
--   - Uniform geometry type per table (Point or LineString)
--   - Spatial indexes for performance
--
-- Run this script in the target geodatabase on gisdb02\gissqlserver.
-- After creation, register with ArcSDE using register_with_arcsde.py
-- ============================================================================

-- ============================================================================
-- TABLE 1: WAZE_ALERTS (Point geometry)
-- Road closures, hazards, accidents, and other Waze alerts
-- ============================================================================
IF OBJECT_ID('dbo.WAZE_ALERTS', 'U') IS NOT NULL
    DROP TABLE dbo.WAZE_ALERTS;
GO

CREATE TABLE dbo.WAZE_ALERTS (
    OBJECTID        int IDENTITY(1,1) NOT NULL,
    uuid            nvarchar(100)     NULL,
    alert_type      nvarchar(50)      NULL,       -- ROAD_CLOSED, HAZARD, ACCIDENT, etc.
    sub_type        nvarchar(100)     NULL,       -- e.g., HAZARD_ON_ROAD_CONSTRUCTION
    street          nvarchar(255)     NULL,
    city            nvarchar(100)     NULL,
    country         nvarchar(10)      NULL,
    description     nvarchar(MAX)     NULL,       -- reportDescription from Waze
    confidence      int               NULL,       -- 0-10
    reliability     int               NULL,       -- 0-10
    report_rating   int               NULL,       -- 0-5
    road_type       int               NULL,       -- Waze road classification
    magvar          int               NULL,       -- Magnetic variance (direction)
    from_node_id    bigint            NULL,
    to_node_id      bigint            NULL,
    pub_millis      bigint            NULL,       -- Waze publish time (epoch ms)
    pub_date        datetime2         NULL,       -- Converted publish datetime
    last_updated    datetime2         NOT NULL DEFAULT SYSUTCDATETIME(),
    Shape           geometry          NULL,       -- POINT(x y) SRID 4326

    CONSTRAINT PK_WAZE_ALERTS PRIMARY KEY CLUSTERED (OBJECTID)
);
GO

-- Spatial index for fast map draws
CREATE SPATIAL INDEX [SIX_WAZE_ALERTS_Shape] ON dbo.WAZE_ALERTS (Shape)
    USING GEOMETRY_AUTO_GRID
    WITH (BOUNDING_BOX = (-83, 37, -80, 40));  -- West Virginia bounding box
GO

-- Non-spatial indexes for CAD queries
CREATE NONCLUSTERED INDEX [IX_WAZE_ALERTS_type] ON dbo.WAZE_ALERTS (alert_type);
GO

CREATE NONCLUSTERED INDEX [IX_WAZE_ALERTS_uuid] ON dbo.WAZE_ALERTS (uuid);
GO


-- ============================================================================
-- TABLE 2: WAZE_JAMS (Polyline geometry)
-- Traffic congestion segments with speed and delay data
-- ============================================================================
IF OBJECT_ID('dbo.WAZE_JAMS', 'U') IS NOT NULL
    DROP TABLE dbo.WAZE_JAMS;
GO

CREATE TABLE dbo.WAZE_JAMS (
    OBJECTID            int IDENTITY(1,1) NOT NULL,
    uuid                bigint            NULL,       -- Waze jam ID
    level               int               NULL,       -- Jam severity 0-5
    speed_kmh           float             NULL,       -- Current speed km/h
    speed_mph           float             NULL,       -- Converted for dispatchers
    length_meters       int               NULL,       -- Jam length in meters
    delay_seconds       int               NULL,       -- Delay vs freeflow (-1 = road closed)
    street              nvarchar(255)     NULL,
    city                nvarchar(100)     NULL,
    country             nvarchar(10)      NULL,
    road_type           int               NULL,       -- Waze road classification
    start_node          nvarchar(100)     NULL,       -- Start location name
    end_node            nvarchar(100)     NULL,       -- End location name
    turn_type           nvarchar(20)      NULL,       -- NONE, LEFT, RIGHT
    blocking_alert_uuid nvarchar(100)     NULL,       -- Linked blocking alert
    pub_millis          bigint            NULL,       -- Waze publish time (epoch ms)
    pub_date            datetime2         NULL,       -- Converted publish datetime
    traffic_color       nvarchar(20)      NULL,       -- green/yellow/orange/red/darkred
    last_updated        datetime2         NOT NULL DEFAULT SYSUTCDATETIME(),
    Shape               geometry          NULL,       -- LINESTRING(...) SRID 4326

    CONSTRAINT PK_WAZE_JAMS PRIMARY KEY CLUSTERED (OBJECTID)
);
GO

-- Spatial index for fast map draws
CREATE SPATIAL INDEX [SIX_WAZE_JAMS_Shape] ON dbo.WAZE_JAMS (Shape)
    USING GEOMETRY_AUTO_GRID
    WITH (BOUNDING_BOX = (-83, 37, -80, 40));  -- West Virginia bounding box
GO

-- Non-spatial indexes
CREATE NONCLUSTERED INDEX [IX_WAZE_JAMS_level] ON dbo.WAZE_JAMS (level);
GO

CREATE NONCLUSTERED INDEX [IX_WAZE_JAMS_uuid] ON dbo.WAZE_JAMS (uuid);
GO


-- ============================================================================
-- TABLE 3: WAZE_IRREGULARITIES (Polyline geometry)
-- Speed irregularities / anomalies detected by Waze
-- ============================================================================
IF OBJECT_ID('dbo.WAZE_IRREGULARITIES', 'U') IS NOT NULL
    DROP TABLE dbo.WAZE_IRREGULARITIES;
GO

CREATE TABLE dbo.WAZE_IRREGULARITIES (
    OBJECTID            int IDENTITY(1,1) NOT NULL,
    irregularity_id     bigint            NULL,       -- Waze irregularity ID
    detection_date      datetime2         NULL,       -- When first detected
    update_date         datetime2         NULL,       -- Last Waze update
    trend               int               NULL,       -- Trend indicator
    street              nvarchar(255)     NULL,
    city                nvarchar(100)     NULL,
    country             nvarchar(10)      NULL,
    speed_kmh           float             NULL,       -- Current speed
    speed_mph           float             NULL,       -- Converted
    regular_speed_kmh   float             NULL,       -- Normal freeflow speed
    regular_speed_mph   float             NULL,       -- Converted
    delay_seconds       int               NULL,       -- Delay vs freeflow
    severity            int               NULL,       -- Severity level
    jam_level           int               NULL,       -- 0-5
    drivers_count       int               NULL,       -- Number of Waze drivers reporting
    length_meters       int               NULL,       -- Length in meters
    highway             bit               NULL,       -- Is highway segment
    alerts_count        int               NULL,
    n_thumbs_up         int               NULL,
    n_comments          int               NULL,
    n_images            int               NULL,
    traffic_color       nvarchar(20)      NULL,       -- green/yellow/orange/red/darkred
    last_updated        datetime2         NOT NULL DEFAULT SYSUTCDATETIME(),
    Shape               geometry          NULL,       -- LINESTRING(...) SRID 4326

    CONSTRAINT PK_WAZE_IRREGULARITIES PRIMARY KEY CLUSTERED (OBJECTID)
);
GO

-- Spatial index for fast map draws
CREATE SPATIAL INDEX [SIX_WAZE_IRREGULARITIES_Shape] ON dbo.WAZE_IRREGULARITIES (Shape)
    USING GEOMETRY_AUTO_GRID
    WITH (BOUNDING_BOX = (-83, 37, -80, 40));  -- West Virginia bounding box
GO

-- Non-spatial indexes
CREATE NONCLUSTERED INDEX [IX_WAZE_IRREGULARITIES_jam_level] ON dbo.WAZE_IRREGULARITIES (jam_level);
GO

PRINT '=== All Waze tables created successfully ==='
PRINT 'Next step: Run register_with_arcsde.py to register these as geodatabase feature classes'
GO
