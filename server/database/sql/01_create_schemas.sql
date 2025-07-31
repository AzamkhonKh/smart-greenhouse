-- Smart Greenhouse IoT System - Database Schemas
-- Creates the basic schema structure for the unified PostgreSQL+TimescaleDB architecture

-- Create application schema for business logic tables
CREATE SCHEMA IF NOT EXISTS greenhouse;

-- Create monitoring schema for operational tables
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create timeseries schema for TimescaleDB hypertables
CREATE SCHEMA IF NOT EXISTS timeseries;

-- Set default search path
ALTER DATABASE greenhouse SET search_path TO greenhouse, monitoring, timeseries, public;

-- Create custom types
CREATE TYPE greenhouse.user_role AS ENUM ('admin', 'manager', 'operator', 'viewer');
CREATE TYPE greenhouse.node_status AS ENUM ('active', 'inactive', 'maintenance', 'error');
CREATE TYPE greenhouse.sensor_type AS ENUM ('temperature', 'humidity', 'soil_moisture', 'light', 'ph', 'ec');
CREATE TYPE greenhouse.actuator_type AS ENUM ('solenoid', 'pump', 'fan', 'heater', 'led', 'valve');
CREATE TYPE timeseries.data_quality AS ENUM ('good', 'uncertain', 'bad', 'unknown');

COMMENT ON SCHEMA greenhouse IS 'Main application schema for business logic and configuration';
COMMENT ON SCHEMA monitoring IS 'Operational monitoring, logs, and system health data';
COMMENT ON SCHEMA timeseries IS 'TimescaleDB hypertables for sensor data and time-series analytics';
