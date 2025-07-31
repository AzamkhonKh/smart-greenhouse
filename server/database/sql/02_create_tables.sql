-- Smart Greenhouse IoT System - Core Tables
-- Creates all application tables according to the project context architecture

-- Users table for authentication and authorization
CREATE TABLE greenhouse.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role greenhouse.user_role NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Nodes table for greenhouse controller registry
CREATE TABLE greenhouse.nodes (
    node_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    node_type VARCHAR(50) NOT NULL DEFAULT 'greenhouse',
    api_key VARCHAR(255) UNIQUE NOT NULL,
    status greenhouse.node_status DEFAULT 'active',
    firmware_version VARCHAR(20),
    configuration JSONB DEFAULT '{}',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Zones table for 3x3 grid zone definitions
CREATE TABLE greenhouse.zones (
    zone_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    row_number INTEGER NOT NULL CHECK (row_number BETWEEN 1 AND 3),
    column_number INTEGER NOT NULL CHECK (column_number BETWEEN 1 AND 3),
    plant_type VARCHAR(50),
    planting_date DATE,
    configuration JSONB DEFAULT '{}',
    target_temperature DECIMAL(4,2),
    target_humidity DECIMAL(5,2),
    target_soil_moisture DECIMAL(5,2),
    irrigation_schedule VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(row_number, column_number)
);

-- Sensors table for sensor registry and configuration
CREATE TABLE greenhouse.sensors (
    sensor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(50) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE,
    zone_id VARCHAR(10) REFERENCES greenhouse.zones(zone_id) ON DELETE SET NULL,
    sensor_type greenhouse.sensor_type NOT NULL,
    pin_number INTEGER,
    calibration_offset DECIMAL(10,4) DEFAULT 0,
    calibration_multiplier DECIMAL(10,4) DEFAULT 1,
    unit VARCHAR(20) NOT NULL,
    min_value DECIMAL(10,4),
    max_value DECIMAL(10,4),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(node_id, pin_number)
);

-- Actuators table for actuator configuration and safety limits
CREATE TABLE greenhouse.actuators (
    actuator_id VARCHAR(50) PRIMARY KEY,
    node_id VARCHAR(50) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE,
    zone_id VARCHAR(10) REFERENCES greenhouse.zones(zone_id) ON DELETE SET NULL,
    actuator_type greenhouse.actuator_type NOT NULL,
    pin_number INTEGER,
    max_runtime_seconds INTEGER DEFAULT 300,
    safety_limits JSONB DEFAULT '{}',
    current_state BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(node_id, pin_number)
);

-- Permissions table for fine-grained access control
CREATE TABLE greenhouse.permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES greenhouse.users(user_id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    actions TEXT[] NOT NULL,
    granted_by UUID REFERENCES greenhouse.users(user_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE(user_id, resource_type, resource_id)
);

-- API logs table for complete audit trail
CREATE TABLE monitoring.api_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    node_id VARCHAR(50),
    user_id UUID,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    ip_address INET,
    user_agent TEXT,
    error_message TEXT
);

-- Rate limits table for per-node endpoint throttling
CREATE TABLE monitoring.rate_limits (
    limit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(50) REFERENCES greenhouse.nodes(node_id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    requests_per_minute INTEGER NOT NULL DEFAULT 60,
    burst_limit INTEGER NOT NULL DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(node_id, endpoint)
);

-- System configuration table
CREATE TABLE greenhouse.system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_by UUID REFERENCES greenhouse.users(user_id),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE greenhouse.users IS 'User accounts with role-based access control';
COMMENT ON TABLE greenhouse.nodes IS 'Greenhouse controller nodes registry with API keys';
COMMENT ON TABLE greenhouse.zones IS '3x3 grid zone definitions with plant-specific settings';
COMMENT ON TABLE greenhouse.sensors IS 'Sensor registry with calibration and pin mapping';
COMMENT ON TABLE greenhouse.actuators IS 'Actuator configuration with safety limits';
COMMENT ON TABLE greenhouse.permissions IS 'Fine-grained access control matrix';
COMMENT ON TABLE monitoring.api_logs IS 'Complete audit trail for security and analytics';
COMMENT ON TABLE monitoring.rate_limits IS 'Per-node endpoint throttling configuration';
