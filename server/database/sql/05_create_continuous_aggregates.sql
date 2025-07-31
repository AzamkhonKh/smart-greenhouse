-- Smart Greenhouse IoT System - Continuous Aggregates
-- Creates real-time materialized views for dashboard performance

-- Hourly sensor statistics - Real-time aggregation for dashboards
CREATE MATERIALIZED VIEW timeseries.hourly_sensor_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS time_bucket,
    node_id,
    zone_id,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS data_points,
    COUNT(*) FILTER (WHERE quality = 'good') AS good_data_points,
    COUNT(*) FILTER (WHERE quality = 'bad') AS bad_data_points
FROM timeseries.sensor_readings
GROUP BY time_bucket, node_id, zone_id, sensor_type;

-- Daily sensor statistics - Longer term trends
CREATE MATERIALIZED VIEW timeseries.daily_sensor_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS time_bucket,
    node_id,
    zone_id,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS data_points,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value) AS q25,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value) AS q75
FROM timeseries.sensor_readings
GROUP BY time_bucket, node_id, zone_id, sensor_type;

-- 15-minute zone summaries - High-frequency zone monitoring
CREATE MATERIALIZED VIEW timeseries.zone_summary_15min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('15 minutes', time) AS time_bucket,
    zone_id,
    AVG(CASE WHEN sensor_type = 'temperature' THEN value END) AS avg_temperature,
    AVG(CASE WHEN sensor_type = 'humidity' THEN value END) AS avg_humidity,
    AVG(CASE WHEN sensor_type = 'soil_moisture' THEN value END) AS avg_soil_moisture,
    AVG(CASE WHEN sensor_type = 'light' THEN value END) AS avg_light,
    COUNT(*) AS total_readings,
    COUNT(DISTINCT node_id) AS active_nodes
FROM timeseries.sensor_readings
WHERE zone_id IS NOT NULL
GROUP BY time_bucket, zone_id;

-- Hourly zone summaries - Detailed zone analytics
CREATE MATERIALIZED VIEW timeseries.zone_summary_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS time_bucket,
    zone_id,
    AVG(CASE WHEN sensor_type = 'temperature' THEN value END) AS avg_temperature,
    MIN(CASE WHEN sensor_type = 'temperature' THEN value END) AS min_temperature,
    MAX(CASE WHEN sensor_type = 'temperature' THEN value END) AS max_temperature,
    AVG(CASE WHEN sensor_type = 'humidity' THEN value END) AS avg_humidity,
    MIN(CASE WHEN sensor_type = 'humidity' THEN value END) AS min_humidity,
    MAX(CASE WHEN sensor_type = 'humidity' THEN value END) AS max_humidity,
    AVG(CASE WHEN sensor_type = 'soil_moisture' THEN value END) AS avg_soil_moisture,
    MIN(CASE WHEN sensor_type = 'soil_moisture' THEN value END) AS min_soil_moisture,
    MAX(CASE WHEN sensor_type = 'soil_moisture' THEN value END) AS max_soil_moisture,
    AVG(CASE WHEN sensor_type = 'light' THEN value END) AS avg_light,
    COUNT(*) AS total_readings,
    COUNT(DISTINCT sensor_id) AS active_sensors
FROM timeseries.sensor_readings
WHERE zone_id IS NOT NULL
GROUP BY time_bucket, zone_id;

-- Node health summary - Real-time node monitoring
CREATE MATERIALIZED VIEW timeseries.node_health_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS time_bucket,
    node_id,
    AVG(memory_usage_mb) AS avg_memory_usage,
    MAX(memory_usage_mb) AS max_memory_usage,
    AVG(cpu_usage_percent) AS avg_cpu_usage,
    MAX(cpu_usage_percent) AS max_cpu_usage,
    AVG(signal_strength) AS avg_signal_strength,
    COUNT(*) AS heartbeat_count,
    COUNT(*) FILTER (WHERE status = 'active') AS active_count,
    COUNT(*) FILTER (WHERE status = 'error') AS error_count
FROM timeseries.node_heartbeats
GROUP BY time_bucket, node_id;

-- Actuator usage statistics - Control system analytics
CREATE MATERIALIZED VIEW timeseries.actuator_usage_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS time_bucket,
    node_id,
    zone_id,
    actuator_id,
    COUNT(*) AS activation_count,
    SUM(duration_seconds) AS total_runtime_seconds,
    AVG(duration_seconds) AS avg_runtime_seconds,
    COUNT(*) FILTER (WHERE state = true) AS on_count,
    COUNT(*) FILTER (WHERE state = false) AS off_count
FROM timeseries.actuator_events
GROUP BY time_bucket, node_id, zone_id, actuator_id;

-- System performance metrics - Overall system health
CREATE MATERIALIZED VIEW timeseries.system_performance_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS time_bucket,
    metric_name,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    COUNT(*) AS data_points,
    STDDEV(metric_value) AS stddev_value
FROM timeseries.system_metrics
GROUP BY time_bucket, metric_name;

-- Add refresh policies for continuous aggregates (automatic updates)
SELECT add_continuous_aggregate_policy('timeseries.hourly_sensor_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('timeseries.daily_sensor_stats',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

SELECT add_continuous_aggregate_policy('timeseries.zone_summary_15min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes');

SELECT add_continuous_aggregate_policy('timeseries.zone_summary_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('timeseries.node_health_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('timeseries.actuator_usage_daily',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

SELECT add_continuous_aggregate_policy('timeseries.system_performance_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Create additional indexes on continuous aggregates for better performance
CREATE INDEX idx_hourly_sensor_stats_zone_time ON timeseries.hourly_sensor_stats(zone_id, time_bucket DESC);
CREATE INDEX idx_daily_sensor_stats_type_time ON timeseries.daily_sensor_stats(sensor_type, time_bucket DESC);
CREATE INDEX idx_zone_summary_15min_zone_time ON timeseries.zone_summary_15min(zone_id, time_bucket DESC);
CREATE INDEX idx_zone_summary_hourly_zone_time ON timeseries.zone_summary_hourly(zone_id, time_bucket DESC);
CREATE INDEX idx_node_health_hourly_node_time ON timeseries.node_health_hourly(node_id, time_bucket DESC);

-- Add comments for documentation
COMMENT ON MATERIALIZED VIEW timeseries.hourly_sensor_stats IS 'Real-time hourly sensor statistics for dashboard performance';
COMMENT ON MATERIALIZED VIEW timeseries.daily_sensor_stats IS 'Daily sensor statistics with percentiles for trend analysis';
COMMENT ON MATERIALIZED VIEW timeseries.zone_summary_15min IS 'High-frequency zone monitoring for real-time alerts';
COMMENT ON MATERIALIZED VIEW timeseries.zone_summary_hourly IS 'Detailed hourly zone analytics with min/max values';
COMMENT ON MATERIALIZED VIEW timeseries.node_health_hourly IS 'Node health monitoring with error tracking';
COMMENT ON MATERIALIZED VIEW timeseries.actuator_usage_daily IS 'Daily actuator usage statistics for maintenance planning';
