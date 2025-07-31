-- Migration: Convert sensor_type enum to VARCHAR and add new sensor types
-- This migration allows for more flexible sensor types including IoT node metrics

BEGIN;

-- Step 1: Add new enum values to existing enum type
ALTER TYPE greenhouse.sensor_type ADD VALUE 'battery_percentage';
ALTER TYPE greenhouse.sensor_type ADD VALUE 'signal_strength';
ALTER TYPE greenhouse.sensor_type ADD VALUE 'voltage';

-- Step 2: Alternative approach - convert to VARCHAR for maximum flexibility
-- Note: This is commented out, use if enum approach doesn't work well

-- Add new VARCHAR column
-- ALTER TABLE greenhouse.sensors ADD COLUMN sensor_type_new VARCHAR(50);

-- Copy existing enum values to new column
-- UPDATE greenhouse.sensors SET sensor_type_new = sensor_type::TEXT;

-- Drop the old enum column
-- ALTER TABLE greenhouse.sensors DROP COLUMN sensor_type;

-- Rename new column to original name
-- ALTER TABLE greenhouse.sensors RENAME COLUMN sensor_type_new TO sensor_type;

-- Add NOT NULL constraint
-- ALTER TABLE greenhouse.sensors ALTER COLUMN sensor_type SET NOT NULL;

-- Same for timeseries.sensor_readings table
-- ALTER TABLE timeseries.sensor_readings ADD COLUMN sensor_type_new VARCHAR(50);
-- UPDATE timeseries.sensor_readings SET sensor_type_new = sensor_type::TEXT;
-- ALTER TABLE timeseries.sensor_readings DROP COLUMN sensor_type;
-- ALTER TABLE timeseries.sensor_readings RENAME COLUMN sensor_type_new TO sensor_type;
-- ALTER TABLE timeseries.sensor_readings ALTER COLUMN sensor_type SET NOT NULL;

COMMIT;
