-- Smart Greenhouse IoT System - Database Indexes
-- Creates optimized indexes for query performance

-- Indexes for users table
CREATE INDEX idx_users_username ON greenhouse.users(username);
CREATE INDEX idx_users_email ON greenhouse.users(email);
CREATE INDEX idx_users_role ON greenhouse.users(role);
CREATE INDEX idx_users_active ON greenhouse.users(is_active);

-- Indexes for nodes table
CREATE INDEX idx_nodes_status ON greenhouse.nodes(status);
CREATE INDEX idx_nodes_last_seen ON greenhouse.nodes(last_seen);
CREATE INDEX idx_nodes_type ON greenhouse.nodes(node_type);

-- Indexes for zones table
CREATE INDEX idx_zones_plant_type ON greenhouse.zones(plant_type);
CREATE INDEX idx_zones_status ON greenhouse.zones(status);
CREATE INDEX idx_zones_grid_position ON greenhouse.zones(row_number, column_number);

-- Indexes for sensors table
CREATE INDEX idx_sensors_node_id ON greenhouse.sensors(node_id);
CREATE INDEX idx_sensors_zone_id ON greenhouse.sensors(zone_id);
CREATE INDEX idx_sensors_type ON greenhouse.sensors(sensor_type);
CREATE INDEX idx_sensors_active ON greenhouse.sensors(is_active);

-- Indexes for actuators table
CREATE INDEX idx_actuators_node_id ON greenhouse.actuators(node_id);
CREATE INDEX idx_actuators_zone_id ON greenhouse.actuators(zone_id);
CREATE INDEX idx_actuators_type ON greenhouse.actuators(actuator_type);
CREATE INDEX idx_actuators_active ON greenhouse.actuators(is_active);

-- Indexes for permissions table
CREATE INDEX idx_permissions_user_id ON greenhouse.permissions(user_id);
CREATE INDEX idx_permissions_resource ON greenhouse.permissions(resource_type, resource_id);
CREATE INDEX idx_permissions_expires ON greenhouse.permissions(expires_at);

-- Indexes for API logs table
CREATE INDEX idx_api_logs_timestamp ON monitoring.api_logs(timestamp);
CREATE INDEX idx_api_logs_node_id ON monitoring.api_logs(node_id);
CREATE INDEX idx_api_logs_user_id ON monitoring.api_logs(user_id);
CREATE INDEX idx_api_logs_endpoint ON monitoring.api_logs(endpoint);
CREATE INDEX idx_api_logs_status ON monitoring.api_logs(status_code);

-- Indexes for rate limits table
CREATE INDEX idx_rate_limits_node ON monitoring.rate_limits(node_id);
CREATE INDEX idx_rate_limits_endpoint ON monitoring.rate_limits(endpoint);
CREATE INDEX idx_rate_limits_active ON monitoring.rate_limits(is_active);

-- TimescaleDB-specific indexes for hypertables

-- Sensor readings indexes
CREATE INDEX idx_sensor_readings_node_time ON timeseries.sensor_readings(node_id, time DESC);
CREATE INDEX idx_sensor_readings_zone_time ON timeseries.sensor_readings(zone_id, time DESC);
CREATE INDEX idx_sensor_readings_type_time ON timeseries.sensor_readings(sensor_type, time DESC);
CREATE INDEX idx_sensor_readings_quality ON timeseries.sensor_readings(quality);

-- Actuator events indexes
CREATE INDEX idx_actuator_events_actuator_time ON timeseries.actuator_events(actuator_id, time DESC);
CREATE INDEX idx_actuator_events_node_time ON timeseries.actuator_events(node_id, time DESC);
CREATE INDEX idx_actuator_events_command ON timeseries.actuator_events(command);

-- Node heartbeats indexes
CREATE INDEX idx_node_heartbeats_node_time ON timeseries.node_heartbeats(node_id, time DESC);
CREATE INDEX idx_node_heartbeats_status ON timeseries.node_heartbeats(status);

-- Zone aggregates indexes
CREATE INDEX idx_zone_aggregates_zone_time ON timeseries.zone_aggregates(zone_id, time DESC);
CREATE INDEX idx_zone_aggregates_bucket ON timeseries.zone_aggregates(time_bucket_minutes);

-- System metrics indexes
CREATE INDEX idx_system_metrics_name_time ON timeseries.system_metrics(metric_name, time DESC);
CREATE INDEX idx_system_metrics_node_time ON timeseries.system_metrics(node_id, time DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_sensor_readings_composite ON timeseries.sensor_readings(node_id, sensor_type, time DESC);
CREATE INDEX idx_actuator_events_composite ON timeseries.actuator_events(node_id, actuator_id, time DESC);

-- Partial indexes for active records only
CREATE INDEX idx_sensors_active_node ON greenhouse.sensors(node_id) WHERE is_active = true;
CREATE INDEX idx_actuators_active_node ON greenhouse.actuators(node_id) WHERE is_active = true;
CREATE INDEX idx_nodes_active ON greenhouse.nodes(node_id) WHERE status = 'active';

-- GIN indexes for JSONB fields
CREATE INDEX idx_nodes_configuration ON greenhouse.nodes USING GIN(configuration);
CREATE INDEX idx_zones_configuration ON greenhouse.zones USING GIN(configuration);
CREATE INDEX idx_sensor_readings_metadata ON timeseries.sensor_readings USING GIN(metadata);
CREATE INDEX idx_actuator_events_metadata ON timeseries.actuator_events USING GIN(metadata);
CREATE INDEX idx_system_metrics_tags ON timeseries.system_metrics USING GIN(tags);

-- Update statistics for better query planning
ANALYZE greenhouse.users;
ANALYZE greenhouse.nodes;
ANALYZE greenhouse.zones;
ANALYZE greenhouse.sensors;
ANALYZE greenhouse.actuators;
ANALYZE monitoring.api_logs;
ANALYZE timeseries.sensor_readings;
ANALYZE timeseries.actuator_events;
ANALYZE timeseries.node_heartbeats;
