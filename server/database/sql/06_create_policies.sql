-- Smart Greenhouse IoT System - Data Retention and Compression Policies
-- Configures automatic data lifecycle management for optimal storage and performance

-- Compression policies for hypertables (90%+ space savings)

-- Compress sensor readings older than 7 days
SELECT add_compression_policy('timeseries.sensor_readings', INTERVAL '7 days');

-- Compress actuator events older than 3 days
SELECT add_compression_policy('timeseries.actuator_events', INTERVAL '3 days');

-- Compress node heartbeats older than 1 day
SELECT add_compression_policy('timeseries.node_heartbeats', INTERVAL '1 day');

-- Compress zone aggregates older than 7 days
SELECT add_compression_policy('timeseries.zone_aggregates', INTERVAL '7 days');

-- Compress system metrics older than 1 day
SELECT add_compression_policy('timeseries.system_metrics', INTERVAL '1 day');

-- Data retention policies (automatic deletion of old data)

-- Keep sensor readings for 1 year (as specified in project context)
SELECT add_retention_policy('timeseries.sensor_readings', INTERVAL '1 year');

-- Keep actuator events for 6 months
SELECT add_retention_policy('timeseries.actuator_events', INTERVAL '6 months');

-- Keep node heartbeats for 3 months
SELECT add_retention_policy('timeseries.node_heartbeats', INTERVAL '3 months');

-- Keep zone aggregates for 2 years (aggregated data is smaller and valuable for trends)
SELECT add_retention_policy('timeseries.zone_aggregates', INTERVAL '2 years');

-- Keep system metrics for 6 months
SELECT add_retention_policy('timeseries.system_metrics', INTERVAL '6 months');

-- Retention policies for continuous aggregates (keep longer since they're compressed summaries)

-- Keep hourly stats for 2 years
SELECT add_retention_policy('timeseries.hourly_sensor_stats', INTERVAL '2 years');

-- Keep daily stats for 5 years
SELECT add_retention_policy('timeseries.daily_sensor_stats', INTERVAL '5 years');

-- Keep 15-minute zone summaries for 6 months
SELECT add_retention_policy('timeseries.zone_summary_15min', INTERVAL '6 months');

-- Keep hourly zone summaries for 2 years
SELECT add_retention_policy('timeseries.zone_summary_hourly', INTERVAL '2 years');

-- Keep node health data for 1 year
SELECT add_retention_policy('timeseries.node_health_hourly', INTERVAL '1 year');

-- Keep actuator usage data for 3 years
SELECT add_retention_policy('timeseries.actuator_usage_daily', INTERVAL '3 years');

-- Keep system performance data for 1 year
SELECT add_retention_policy('timeseries.system_performance_hourly', INTERVAL '1 year');

-- Operational data retention policies

-- Keep API logs for 90 days (security and debugging)
CREATE OR REPLACE FUNCTION monitoring.cleanup_api_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM monitoring.api_logs 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Log the cleanup operation
    INSERT INTO timeseries.system_metrics (time, metric_name, metric_value, metric_unit)
    VALUES (NOW(), 'api_logs_cleanup_rows', ROW_COUNT(), 'count');
END;
$$ LANGUAGE plpgsql;

-- Schedule API logs cleanup to run daily
SELECT cron.schedule('api_logs_cleanup', '0 2 * * *', 'SELECT monitoring.cleanup_api_logs();');

-- Configure chunk time intervals for optimal performance
SELECT set_chunk_time_interval('timeseries.sensor_readings', INTERVAL '1 day');
SELECT set_chunk_time_interval('timeseries.actuator_events', INTERVAL '1 day');
SELECT set_chunk_time_interval('timeseries.node_heartbeats', INTERVAL '1 hour');
SELECT set_chunk_time_interval('timeseries.zone_aggregates', INTERVAL '1 day');
SELECT set_chunk_time_interval('timeseries.system_metrics', INTERVAL '1 hour');

-- Enable automatic compression for better performance
ALTER TABLE timeseries.sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'node_id, sensor_type',
    timescaledb.compress_orderby = 'time DESC'
);

ALTER TABLE timeseries.actuator_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'node_id, actuator_id',
    timescaledb.compress_orderby = 'time DESC'
);

ALTER TABLE timeseries.node_heartbeats SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'node_id',
    timescaledb.compress_orderby = 'time DESC'
);

ALTER TABLE timeseries.zone_aggregates SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'zone_id',
    timescaledb.compress_orderby = 'time DESC'
);

ALTER TABLE timeseries.system_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'metric_name, node_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- Create a maintenance function to optimize hypertables
CREATE OR REPLACE FUNCTION timeseries.optimize_hypertables()
RETURNS void AS $$
DECLARE
    table_name text;
BEGIN
    -- List of hypertables to optimize
    FOR table_name IN 
        SELECT hypertable_name FROM timescaledb_information.hypertables 
        WHERE hypertable_schema = 'timeseries'
    LOOP
        -- Recompress chunks that might not be optimally compressed
        EXECUTE format('SELECT compress_chunk(i) FROM show_chunks(%L) i 
                       WHERE NOT is_compressed', 'timeseries.' || table_name);
        
        -- Update statistics for better query planning
        EXECUTE format('ANALYZE timeseries.%I', table_name);
    END LOOP;
    
    -- Log the maintenance operation
    INSERT INTO timeseries.system_metrics (time, metric_name, metric_value, metric_unit)
    VALUES (NOW(), 'hypertable_maintenance_completed', 1, 'count');
END;
$$ LANGUAGE plpgsql;

-- Schedule hypertable optimization to run weekly
SELECT cron.schedule('hypertable_optimization', '0 3 * * 0', 'SELECT timeseries.optimize_hypertables();');

-- Create monitoring function for storage efficiency
CREATE OR REPLACE FUNCTION timeseries.get_compression_stats()
RETURNS TABLE (
    table_name text,
    total_size_mb numeric,
    compressed_size_mb numeric,
    compression_ratio numeric,
    total_chunks bigint,
    compressed_chunks bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.hypertable_name::text,
        ROUND((cs.total_bytes / 1024.0 / 1024.0)::numeric, 2) as total_size_mb,
        ROUND((cs.compressed_total_bytes / 1024.0 / 1024.0)::numeric, 2) as compressed_size_mb,
        ROUND((100.0 * cs.compressed_total_bytes / NULLIF(cs.total_bytes, 0))::numeric, 1) as compression_ratio,
        cs.total_chunks,
        cs.number_compressed_chunks as compressed_chunks
    FROM timescaledb_information.hypertables h
    JOIN timescaledb_information.compression_settings cs ON h.hypertable_name = cs.hypertable_name
    WHERE h.hypertable_schema = 'timeseries'
    ORDER BY total_size_mb DESC;
END;
$$ LANGUAGE plpgsql;

-- Add helpful utility functions for data management
CREATE OR REPLACE FUNCTION timeseries.get_data_age_stats()
RETURNS TABLE (
    table_name text,
    oldest_data timestamp with time zone,
    newest_data timestamp with time zone,
    data_span interval,
    total_rows bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'sensor_readings'::text,
        MIN(time),
        MAX(time),
        MAX(time) - MIN(time),
        COUNT(*)
    FROM timeseries.sensor_readings
    UNION ALL
    SELECT 
        'actuator_events'::text,
        MIN(time),
        MAX(time),
        MAX(time) - MIN(time),
        COUNT(*)
    FROM timeseries.actuator_events
    UNION ALL
    SELECT 
        'node_heartbeats'::text,
        MIN(time),
        MAX(time),
        MAX(time) - MIN(time),
        COUNT(*)
    FROM timeseries.node_heartbeats;
END;
$$ LANGUAGE plpgsql;

-- Create database maintenance report function
CREATE OR REPLACE FUNCTION generate_maintenance_report()
RETURNS json AS $$
DECLARE
    result json;
BEGIN
    SELECT json_build_object(
        'timestamp', NOW(),
        'compression_stats', (SELECT json_agg(row_to_json(t)) FROM timeseries.get_compression_stats() t),
        'data_age_stats', (SELECT json_agg(row_to_json(t)) FROM timeseries.get_data_age_stats() t),
        'database_size_mb', (SELECT ROUND((pg_database_size('greenhouse') / 1024.0 / 1024.0)::numeric, 2))
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION timeseries.get_compression_stats() IS 'Returns compression statistics for all hypertables';
COMMENT ON FUNCTION timeseries.get_data_age_stats() IS 'Returns data age and volume statistics';
COMMENT ON FUNCTION generate_maintenance_report() IS 'Generates comprehensive database maintenance report';
