-- Smart Greenhouse IoT System - Initial Data Seeding
-- Seeds the database with initial configuration and test data

-- Insert default admin user
INSERT INTO greenhouse.users (username, email, password_hash, role) VALUES
('admin', 'admin@greenhouse.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewaxqmSUWdT.5yOa', 'admin'),
('manager', 'manager@greenhouse.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewaxqmSUWdT.5yOa', 'manager'),
('operator', 'operator@greenhouse.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewaxqmSUWdT.5yOa', 'operator'),
('viewer', 'viewer@greenhouse.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewaxqmSUWdT.5yOa', 'viewer');

-- Insert greenhouse nodes according to project context
INSERT INTO greenhouse.nodes (node_id, name, location, node_type, api_key, status, firmware_version, configuration) VALUES
('greenhouse_001', 'Main Controller Node 1', 'Section A-B', 'greenhouse', 'gh001_api_key_abc123', 'active', '1.2.3', 
 '{"max_sensors": 50, "max_actuators": 20, "sampling_interval": 60, "wifi_ssid": "greenhouse_net"}'),
('greenhouse_002', 'Main Controller Node 2', 'Section B-C', 'greenhouse', 'gh002_api_key_def456', 'active', '1.2.3',
 '{"max_sensors": 50, "max_actuators": 20, "sampling_interval": 60, "wifi_ssid": "greenhouse_net"}'),
('greenhouse_003', 'Main Controller Node 3', 'Section C + Utilities', 'greenhouse', 'gh003_api_key_ghi789', 'active', '1.2.3',
 '{"max_sensors": 50, "max_actuators": 20, "sampling_interval": 60, "wifi_ssid": "greenhouse_net"}');

-- Insert 3x3 grid zones according to project context
INSERT INTO greenhouse.zones (zone_id, name, row_number, column_number, plant_type, planting_date, target_temperature, target_humidity, target_soil_moisture, irrigation_schedule, configuration) VALUES
-- Row 1
('A1', 'Tomato Zone A1', 1, 1, 'Tomato', '2025-01-15', 24.0, 70.0, 60.0, '2x daily, 5min', 
 '{"plant_variety": "Roma", "expected_harvest": "2025-04-15", "support_type": "stakes"}'),
('A2', 'Lettuce Zone A2', 1, 2, 'Lettuce', '2025-02-01', 18.0, 65.0, 55.0, '3x daily, 3min',
 '{"plant_variety": "Butterhead", "expected_harvest": "2025-03-15", "growing_method": "hydroponic"}'),
('A3', 'Basil Zone A3', 1, 3, 'Basil', '2025-02-10', 22.0, 60.0, 50.0, '2x daily, 4min',
 '{"plant_variety": "Sweet Basil", "expected_harvest": "2025-04-01", "pruning_schedule": "weekly"}'),

-- Row 2
('B1', 'Pepper Zone B1', 2, 1, 'Pepper', '2025-01-20', 25.0, 65.0, 58.0, '2x daily, 5min',
 '{"plant_variety": "Bell Pepper", "expected_harvest": "2025-05-01", "support_type": "cages"}'),
('B2', 'Cucumber Zone B2', 2, 2, 'Cucumber', '2025-02-05', 23.0, 75.0, 65.0, '3x daily, 6min',
 '{"plant_variety": "English Cucumber", "expected_harvest": "2025-04-20", "trellis_height": "2m"}'),
('B3', 'Spinach Zone B3', 2, 3, 'Spinach', '2025-02-15', 16.0, 60.0, 55.0, '2x daily, 3min',
 '{"plant_variety": "Baby Spinach", "expected_harvest": "2025-03-30", "succession_planting": true}'),

-- Row 3
('C1', 'Carrot Zone C1', 3, 1, 'Carrot', '2025-01-25', 20.0, 55.0, 50.0, '1x daily, 4min',
 '{"plant_variety": "Nantes", "expected_harvest": "2025-04-25", "soil_depth": "30cm"}'),
('C2', 'Radish Zone C2', 3, 2, 'Radish', '2025-02-20', 18.0, 60.0, 45.0, '2x daily, 2min',
 '{"plant_variety": "Cherry Belle", "expected_harvest": "2025-03-20", "quick_growing": true}'),
('C3', 'Microgreens Zone C3', 3, 3, 'Microgreens', '2025-03-01', 20.0, 70.0, 65.0, '3x daily, 2min',
 '{"plant_variety": "Mixed", "expected_harvest": "2025-03-15", "growing_medium": "coconut_coir"}');

-- Insert sensors for each zone (24 total sensors as specified)
-- Node 001 sensors (zones A1, A2, A3)
INSERT INTO greenhouse.sensors (node_id, zone_id, sensor_type, pin_number, unit, calibration_offset, calibration_multiplier) VALUES
-- Zone A1 (Tomato) - 4 sensors
('greenhouse_001', 'A1', 'temperature', 1, '°C', 0.0, 1.0),
('greenhouse_001', 'A1', 'humidity', 2, '%', 0.0, 1.0),
('greenhouse_001', 'A1', 'soil_moisture', 3, '%', 0.0, 1.0),
('greenhouse_001', 'A1', 'light', 4, 'lux', 0.0, 1.0),

-- Zone A2 (Lettuce) - 3 sensors
('greenhouse_001', 'A2', 'temperature', 5, '°C', 0.0, 1.0),
('greenhouse_001', 'A2', 'humidity', 6, '%', 0.0, 1.0),
('greenhouse_001', 'A2', 'soil_moisture', 7, '%', 0.0, 1.0),

-- Zone A3 (Basil) - 3 sensors
('greenhouse_001', 'A3', 'temperature', 8, '°C', 0.0, 1.0),
('greenhouse_001', 'A3', 'humidity', 9, '%', 0.0, 1.0),
('greenhouse_001', 'A3', 'soil_moisture', 10, '%', 0.0, 1.0);

-- Node 002 sensors (zones B1, B2, B3)
INSERT INTO greenhouse.sensors (node_id, zone_id, sensor_type, pin_number, unit, calibration_offset, calibration_multiplier) VALUES
-- Zone B1 (Pepper) - 3 sensors
('greenhouse_002', 'B1', 'temperature', 1, '°C', 0.0, 1.0),
('greenhouse_002', 'B1', 'humidity', 2, '%', 0.0, 1.0),
('greenhouse_002', 'B1', 'soil_moisture', 3, '%', 0.0, 1.0),

-- Zone B2 (Cucumber) - 3 sensors
('greenhouse_002', 'B2', 'temperature', 4, '°C', 0.0, 1.0),
('greenhouse_002', 'B2', 'humidity', 5, '%', 0.0, 1.0),
('greenhouse_002', 'B2', 'soil_moisture', 6, '%', 0.0, 1.0),

-- Zone B3 (Spinach) - 3 sensors
('greenhouse_002', 'B3', 'temperature', 7, '°C', 0.0, 1.0),
('greenhouse_002', 'B3', 'humidity', 8, '%', 0.0, 1.0),
('greenhouse_002', 'B3', 'soil_moisture', 9, '%', 0.0, 1.0);

-- Node 003 sensors (zones C1, C2, C3)
INSERT INTO greenhouse.sensors (node_id, zone_id, sensor_type, pin_number, unit, calibration_offset, calibration_multiplier) VALUES
-- Zone C1 (Carrot) - 2 sensors
('greenhouse_003', 'C1', 'temperature', 1, '°C', 0.0, 1.0),
('greenhouse_003', 'C1', 'soil_moisture', 2, '%', 0.0, 1.0),

-- Zone C2 (Radish) - 2 sensors
('greenhouse_003', 'C2', 'temperature', 3, '°C', 0.0, 1.0),
('greenhouse_003', 'C2', 'humidity', 4, '%', 0.0, 1.0),

-- Zone C3 (Microgreens) - 2 sensors
('greenhouse_003', 'C3', 'light', 5, 'lux', 0.0, 1.0),
('greenhouse_003', 'C3', 'humidity', 6, '%', 0.0, 1.0);

-- Insert actuators (12 total as specified)
INSERT INTO greenhouse.actuators (actuator_id, node_id, zone_id, actuator_type, pin_number, max_runtime_seconds, safety_limits) VALUES
-- Zone irrigation solenoids (8 total)
('solenoid_A1', 'greenhouse_001', 'A1', 'solenoid', 20, 300, '{"max_daily_runtime": 1800, "cooldown_seconds": 600}'),
('solenoid_A2', 'greenhouse_001', 'A2', 'solenoid', 21, 180, '{"max_daily_runtime": 1080, "cooldown_seconds": 300}'),
('solenoid_A3', 'greenhouse_001', 'A3', 'solenoid', 22, 240, '{"max_daily_runtime": 1440, "cooldown_seconds": 400}'),
('solenoid_B1', 'greenhouse_002', 'B1', 'solenoid', 20, 300, '{"max_daily_runtime": 1800, "cooldown_seconds": 600}'),
('solenoid_B2', 'greenhouse_002', 'B2', 'solenoid', 21, 360, '{"max_daily_runtime": 2160, "cooldown_seconds": 500}'),
('solenoid_B3', 'greenhouse_002', 'B3', 'solenoid', 22, 180, '{"max_daily_runtime": 1080, "cooldown_seconds": 300}'),
('solenoid_C1', 'greenhouse_003', 'C1', 'solenoid', 20, 240, '{"max_daily_runtime": 1440, "cooldown_seconds": 400}'),
('solenoid_C2', 'greenhouse_003', 'C2', 'solenoid', 21, 120, '{"max_daily_runtime": 720, "cooldown_seconds": 200}'),

-- Main systems (4 total)
('main_pump', 'greenhouse_003', NULL, 'pump', 25, 1800, '{"max_continuous_runtime": 1800, "pressure_threshold": 50}'),
('exhaust_fan', 'greenhouse_003', NULL, 'fan', 26, 3600, '{"temperature_threshold": 30, "humidity_threshold": 85}'),
('led_lights', 'greenhouse_003', 'C3', 'led', 27, 14400, '{"max_daily_runtime": 43200, "power_limit_watts": 500}'),
('heater', 'greenhouse_003', NULL, 'heater', 28, 7200, '{"temperature_threshold": 10, "safety_cutoff": 40}');

-- Insert default rate limits
INSERT INTO monitoring.rate_limits (node_id, endpoint, requests_per_minute, burst_limit) VALUES
('greenhouse_001', '/api/sensor-data', 60, 10),
('greenhouse_001', '/api/actuators/*/control', 30, 5),
('greenhouse_001', '/api/*', 120, 15),
('greenhouse_002', '/api/sensor-data', 60, 10),
('greenhouse_002', '/api/actuators/*/control', 30, 5),
('greenhouse_002', '/api/*', 120, 15),
('greenhouse_003', '/api/sensor-data', 60, 10),
('greenhouse_003', '/api/actuators/*/control', 30, 5),
('greenhouse_003', '/api/*', 120, 15);

-- Insert system configuration
INSERT INTO greenhouse.system_config (config_key, config_value, description) VALUES
('data_retention_days', '365', 'Number of days to retain raw sensor data'),
('compression_threshold_days', '7', 'Days after which to compress time-series data'),
('alert_temperature_min', '5.0', 'Minimum temperature alert threshold (°C)'),
('alert_temperature_max', '35.0', 'Maximum temperature alert threshold (°C)'),
('alert_humidity_max', '95.0', 'Maximum humidity alert threshold (%)'),
('backup_frequency_hours', '24', 'Database backup frequency in hours'),
('node_heartbeat_timeout_minutes', '5', 'Node offline detection timeout'),
('api_key_rotation_days', '90', 'API key rotation frequency'),
('session_timeout_hours', '24', 'User session timeout'),
('maintenance_window_start', '"02:00"', 'Daily maintenance window start time'),
('maintenance_window_duration_hours', '2', 'Maintenance window duration'),
('enable_auto_irrigation', 'true', 'Enable automatic irrigation based on soil moisture'),
('soil_moisture_threshold', '45.0', 'Soil moisture threshold for auto irrigation (%)'),
('enable_climate_control', 'true', 'Enable automatic climate control'),
('grafana_dashboard_refresh_seconds', '30', 'Grafana dashboard auto-refresh interval');

-- Insert sample sensor data for testing (last 24 hours)
DO $$
DECLARE
    sensor_record RECORD;
    start_time TIMESTAMPTZ;
    temp_base DECIMAL;
    humidity_base DECIMAL;
    soil_base DECIMAL;
    light_base INTEGER;
BEGIN
    start_time := NOW() - INTERVAL '24 hours';
    
    -- Generate sample data for each sensor over the last 24 hours
    FOR sensor_record IN 
        SELECT s.sensor_id, s.node_id, s.zone_id, s.sensor_type, s.unit,
               z.target_temperature, z.target_humidity, z.target_soil_moisture
        FROM greenhouse.sensors s
        LEFT JOIN greenhouse.zones z ON s.zone_id = z.zone_id
        WHERE s.is_active = true
    LOOP
        -- Set base values based on zone targets
        temp_base := COALESCE(sensor_record.target_temperature, 20.0);
        humidity_base := COALESCE(sensor_record.target_humidity, 65.0);
        soil_base := COALESCE(sensor_record.target_soil_moisture, 55.0);
        light_base := 800;
        
        -- Insert hourly data points for the last 24 hours
        FOR i IN 0..23 LOOP
            INSERT INTO timeseries.sensor_readings (time, node_id, zone_id, sensor_id, sensor_type, value, unit, quality)
            VALUES (
                start_time + (i * INTERVAL '1 hour'),
                sensor_record.node_id,
                sensor_record.zone_id,
                sensor_record.sensor_id,
                sensor_record.sensor_type,
                CASE 
                    WHEN sensor_record.sensor_type = 'temperature' THEN 
                        temp_base + (RANDOM() - 0.5) * 4 -- ±2°C variation
                    WHEN sensor_record.sensor_type = 'humidity' THEN 
                        humidity_base + (RANDOM() - 0.5) * 20 -- ±10% variation
                    WHEN sensor_record.sensor_type = 'soil_moisture' THEN 
                        soil_base + (RANDOM() - 0.5) * 20 -- ±10% variation
                    WHEN sensor_record.sensor_type = 'light' THEN 
                        light_base + (RANDOM() - 0.5) * 400 -- ±200 lux variation
                    ELSE 0
                END,
                sensor_record.unit,
                'good'
            );
        END LOOP;
    END LOOP;
END $$;

-- Insert sample node heartbeat data
DO $$
DECLARE
    node_record RECORD;
    start_time TIMESTAMPTZ;
BEGIN
    start_time := NOW() - INTERVAL '24 hours';
    
    FOR node_record IN SELECT node_id FROM greenhouse.nodes WHERE status = 'active' LOOP
        -- Insert heartbeat every 5 minutes for the last 24 hours
        FOR i IN 0..287 LOOP -- 24 hours * 12 (5-minute intervals)
            INSERT INTO timeseries.node_heartbeats (time, node_id, status, uptime_seconds, memory_usage_mb, cpu_usage_percent, signal_strength)
            VALUES (
                start_time + (i * INTERVAL '5 minutes'),
                node_record.node_id,
                'active',
                86400 + i * 300, -- Uptime increases
                512 + FLOOR(RANDOM() * 256)::INTEGER, -- Memory usage 512-768 MB
                5.0 + RANDOM() * 15.0, -- CPU usage 5-20%
                -45 + FLOOR(RANDOM() * 20)::INTEGER -- Signal strength -45 to -25 dBm
            );
        END LOOP;
    END LOOP;
END $$;

-- Insert sample actuator events
INSERT INTO timeseries.actuator_events (time, node_id, zone_id, actuator_id, command, state, duration_seconds, triggered_by, reason) VALUES
(NOW() - INTERVAL '2 hours', 'greenhouse_001', 'A1', 'solenoid_A1', 'irrigation', true, 300, 'auto_scheduler', 'Scheduled irrigation'),
(NOW() - INTERVAL '2 hours' + INTERVAL '5 minutes', 'greenhouse_001', 'A1', 'solenoid_A1', 'irrigation', false, 0, 'auto_scheduler', 'Irrigation complete'),
(NOW() - INTERVAL '1 hour', 'greenhouse_002', 'B2', 'solenoid_B2', 'irrigation', true, 360, 'auto_scheduler', 'Scheduled irrigation'),
(NOW() - INTERVAL '1 hour' + INTERVAL '6 minutes', 'greenhouse_002', 'B2', 'solenoid_B2', 'irrigation', false, 0, 'auto_scheduler', 'Irrigation complete'),
(NOW() - INTERVAL '30 minutes', 'greenhouse_003', NULL, 'exhaust_fan', 'ventilation', true, 1800, 'temperature_control', 'High temperature detected');

-- Update last_seen timestamps for nodes
UPDATE greenhouse.nodes SET last_seen = NOW() - INTERVAL '30 seconds' WHERE status = 'active';

-- Log the seeding completion
INSERT INTO timeseries.system_metrics (time, metric_name, metric_value, metric_unit) VALUES
(NOW(), 'database_seeding_completed', 1, 'boolean'),
(NOW(), 'initial_sensor_data_points', (SELECT COUNT(*) FROM timeseries.sensor_readings), 'count'),
(NOW(), 'initial_heartbeat_data_points', (SELECT COUNT(*) FROM timeseries.node_heartbeats), 'count');

COMMENT ON TABLE greenhouse.users IS 'Initial users: admin/admin, manager/manager, operator/operator, viewer/viewer (all passwords: "password")';
COMMENT ON TABLE greenhouse.nodes IS 'Three greenhouse controller nodes with unique API keys';
COMMENT ON TABLE greenhouse.zones IS '3x3 grid zones with different plant types and configurations';
COMMENT ON TABLE greenhouse.sensors IS '24 sensors distributed across zones for comprehensive monitoring';
COMMENT ON TABLE greenhouse.actuators IS '12 actuators including 8 solenoids and 4 main system components';
