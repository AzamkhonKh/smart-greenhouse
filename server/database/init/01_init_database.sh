#!/bin/bash
# Database Initialization Script for Smart Greenhouse IoT System
# This script sets up PostgreSQL with TimescaleDB extension and creates the initial schema

set -e

echo "Starting Smart Greenhouse Database Initialization..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER" -d "greenhouse"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Enable TimescaleDB extension only in greenhouse database
echo "Enabling TimescaleDB extension in greenhouse database..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" <<-EOSQL
    \echo 'Creating TimescaleDB extension...'
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    \echo 'Creating UUID extension...'
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    \echo 'Creating pgcrypto extension...'
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    \echo 'Extensions created successfully!'
EOSQL

echo "TimescaleDB extension enabled successfully!"

# Verify extensions are installed
echo "Verifying extensions..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -c "\dx"

# Create schemas
echo "Creating database schemas..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/01_create_schemas.sql

# Create tables
echo "Creating tables..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/02_create_tables.sql

# Create hypertables for time-series data
echo "Creating TimescaleDB hypertables..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/03_create_hypertables.sql

# Create indexes and constraints
echo "Creating indexes and constraints..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/04_create_indexes.sql

# Create continuous aggregates
echo "Creating continuous aggregates..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/05_create_continuous_aggregates.sql

# Set up retention and compression policies
echo "Setting up retention and compression policies..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/06_create_policies.sql

# Seed initial data
echo "Seeding initial data..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "greenhouse" -f /opt/sql/07_seed_data.sql

echo "Database initialization completed successfully!"
