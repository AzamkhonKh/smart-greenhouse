-- Smart Greenhouse IoT System - TimescaleDB Hypertables
-- Creates time-series optimized tables for sensor data and monitoring

-- Sensor readings hypertable - Main time-series data storage
CREATE TABLE timeseries.sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(10),
    sensor_id UUID,
    sensor_type greenhouse.sensor_type NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    quality timeseries.data_quality DEFAULT 'good',
    metadata JSONB DEFAULT '{}'
);

-- Create hypertable for sensor readings (partitioned by time)
SELECT create_hypertable('timeseries.sensor_readings', 'time', chunk_time_interval => INTERVAL '1 day');

-- Actuator events hypertable - Control commands and state changes
CREATE TABLE timeseries.actuator_events (
    time TIMESTAMPTZ NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(10),
    actuator_id VARCHAR(50) NOT NULL,
    command VARCHAR(50) NOT NULL,
    state BOOLEAN NOT NULL,
    duration_seconds INTEGER,
    triggered_by VARCHAR(100),
    reason TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create hypertable for actuator events
SELECT create_hypertable('timeseries.actuator_events', 'time', chunk_time_interval => INTERVAL '1 day');

-- Node heartbeats hypertable - Node connectivity and health monitoring
CREATE TABLE timeseries.node_heartbeats (
    time TIMESTAMPTZ NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    status greenhouse.node_status NOT NULL,
    uptime_seconds BIGINT,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    signal_strength INTEGER,
    temperature DECIMAL(4,2),
    free_storage_mb INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Create hypertable for node heartbeats
SELECT create_hypertable('timeseries.node_heartbeats', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Zone aggregates hypertable - Pre-computed zone-level statistics
CREATE TABLE timeseries.zone_aggregates (
    time TIMESTAMPTZ NOT NULL,
    zone_id VARCHAR(10) NOT NULL,
    time_bucket_minutes INTEGER NOT NULL,
    avg_temperature DECIMAL(4,2),
    min_temperature DECIMAL(4,2),
    max_temperature DECIMAL(4,2),
    avg_humidity DECIMAL(5,2),
    min_humidity DECIMAL(5,2),
    max_humidity DECIMAL(5,2),
    avg_soil_moisture DECIMAL(5,2),
    min_soil_moisture DECIMAL(5,2),
    max_soil_moisture DECIMAL(5,2),
    avg_light INTEGER,
    plant_health_score DECIMAL(3,2),
    data_points_count INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Create hypertable for zone aggregates
SELECT create_hypertable('timeseries.zone_aggregates', 'time', chunk_time_interval => INTERVAL '1 day');

-- System metrics hypertable - Overall system performance monitoring
CREATE TABLE timeseries.system_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    node_id VARCHAR(50),
    tags JSONB DEFAULT '{}'
);

-- Create hypertable for system metrics
SELECT create_hypertable('timeseries.system_metrics', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Add foreign key constraints where appropriate
ALTER TABLE timeseries.sensor_readings 
    ADD CONSTRAINT fk_sensor_readings_node 
    FOREIGN KEY (node_id) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE;

ALTER TABLE timeseries.sensor_readings 
    ADD CONSTRAINT fk_sensor_readings_zone 
    FOREIGN KEY (zone_id) REFERENCES greenhouse.zones(zone_id) ON DELETE SET NULL;

ALTER TABLE timeseries.actuator_events 
    ADD CONSTRAINT fk_actuator_events_node 
    FOREIGN KEY (node_id) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE;

ALTER TABLE timeseries.actuator_events 
    ADD CONSTRAINT fk_actuator_events_zone 
    FOREIGN KEY (zone_id) REFERENCES greenhouse.zones(zone_id) ON DELETE SET NULL;

ALTER TABLE timeseries.node_heartbeats 
    ADD CONSTRAINT fk_node_heartbeats_node 
    FOREIGN KEY (node_id) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE;

ALTER TABLE timeseries.zone_aggregates 
    ADD CONSTRAINT fk_zone_aggregates_zone 
    FOREIGN KEY (zone_id) REFERENCES greenhouse.zones(zone_id) ON DELETE CASCADE;

-- Add comments for documentation
COMMENT ON TABLE timeseries.sensor_readings IS 'Time-series sensor measurements with automatic partitioning';
COMMENT ON TABLE timeseries.actuator_events IS 'Actuator control commands and state change history';
COMMENT ON TABLE timeseries.node_heartbeats IS 'Node connectivity and health monitoring data';
COMMENT ON TABLE timeseries.zone_aggregates IS 'Pre-computed zone-level statistics for dashboard performance';
COMMENT ON TABLE timeseries.system_metrics IS 'System-wide performance and operational metrics';
