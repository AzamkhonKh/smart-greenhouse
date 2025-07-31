#!/bin/bash
# Smart Greenhouse Database Migration and Seeding Script
# Runs after PostgreSQL container is healthy

set -e

echo "=== Smart Greenhouse Database Migration & Seeding ==="
echo "Timestamp: $(date)"
echo "PostgreSQL Host: $POSTGRES_HOST"
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is ready!"

# Function to execute SQL with error handling
execute_sql() {
    local file=$1
    local description=$2
    
    echo "Executing: $description"
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$file"; then
        echo "✅ $description completed successfully"
    else
        echo "❌ $description failed"
        exit 1
    fi
}

# Execute migration scripts in order
echo "Starting database migration..."

execute_sql "/opt/sql/01_create_schemas.sql" "Creating database schemas"
execute_sql "/opt/sql/02_create_tables.sql" "Creating application tables"
execute_sql "/opt/sql/03_create_hypertables.sql" "Creating TimescaleDB hypertables"
execute_sql "/opt/sql/04_create_indexes.sql" "Creating database indexes"
execute_sql "/opt/sql/05_create_continuous_aggregates.sql" "Creating continuous aggregates"
execute_sql "/opt/sql/06_create_policies.sql" "Setting up retention and compression policies"

echo "Database structure created successfully!"

# Seed initial data
echo "Seeding initial data..."
execute_sql "/opt/sql/07_seed_data.sql" "Seeding initial application data"

echo "Initial data seeded successfully!"

# Generate migration report
echo "Generating migration report..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    'Migration Report' as title,
    NOW() as completed_at,
    (SELECT COUNT(*) FROM greenhouse.users) as users_count,
    (SELECT COUNT(*) FROM greenhouse.nodes) as nodes_count,
    (SELECT COUNT(*) FROM greenhouse.zones) as zones_count,
    (SELECT COUNT(*) FROM greenhouse.sensors) as sensors_count,
    (SELECT COUNT(*) FROM greenhouse.actuators) as actuators_count,
    (SELECT COUNT(*) FROM timeseries.sensor_readings) as sample_readings_count,
    (SELECT COUNT(*) FROM timescaledb_information.hypertables WHERE hypertable_schema = 'timeseries') as hypertables_count,
    (SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates) as continuous_aggregates_count;
"

# Test database connectivity and features
echo "Testing database features..."

# Test TimescaleDB extension
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ TimescaleDB extension is working'
        ELSE '❌ TimescaleDB extension not found'
    END as timescaledb_status
FROM pg_extension WHERE extname = 'timescaledb';
"

# Test hypertables
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    hypertable_schema,
    hypertable_name,
    num_dimensions,
    compression_enabled
FROM timescaledb_information.hypertables 
WHERE hypertable_schema = 'timeseries'
ORDER BY hypertable_name;
"

# Test continuous aggregates
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    view_name,
    materialized_only,
    finalized
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;
"

# Test sample data query
echo "Testing sample data queries..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    zone_id,
    sensor_type,
    COUNT(*) as reading_count,
    ROUND(AVG(value), 2) as avg_value,
    unit
FROM timeseries.sensor_readings 
WHERE time > NOW() - INTERVAL '1 hour'
GROUP BY zone_id, sensor_type, unit
ORDER BY zone_id, sensor_type;
"

# Log completion
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
INSERT INTO timeseries.system_metrics (time, metric_name, metric_value, metric_unit) 
VALUES (NOW(), 'database_migration_completed', 1, 'boolean');
"

echo "=== Database Migration & Seeding Completed Successfully ==="
echo "Timestamp: $(date)"
echo ""
echo "Next steps:"
echo "1. Start the API service to connect to the database"
echo "2. Access Grafana at http://localhost:3000 (admin/admin123)"
echo "3. Access pgAdmin at http://localhost:5050 (admin@greenhouse.local/admin123) - Development only"
echo "4. Test API endpoints at http://localhost:8000/docs"
echo ""
echo "Database is ready for the Smart Greenhouse IoT System!"
