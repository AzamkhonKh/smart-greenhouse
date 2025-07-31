# Smart Greenhouse Database Setup

This directory contains the complete database initialization and seeding configuration for the Smart Greenhouse IoT System using PostgreSQL with TimescaleDB extension.

## Architecture

- **PostgreSQL 15** with **TimescaleDB** extension for unified relational and time-series data
- **Redis 7** for high-performance caching and session management
- **Grafana** for monitoring dashboards with PostgreSQL data sources

## Directory Structure

```shell
database/
├── init/                           # PostgreSQL initialization scripts
│   └── 01_init_database.sh        # Main initialization script
├── sql/                           # SQL migration files
│   ├── 01_create_schemas.sql      # Database schemas and types
│   ├── 02_create_tables.sql       # Application tables
│   ├── 03_create_hypertables.sql  # TimescaleDB hypertables
│   ├── 04_create_indexes.sql      # Performance indexes
│   ├── 05_create_continuous_aggregates.sql  # Real-time views
│   ├── 06_create_policies.sql     # Retention and compression
│   └── 07_seed_data.sql          # Initial data seeding
├── scripts/                       # Migration utilities
│   └── migrate_and_seed.sh       # Migration orchestration
└── Dockerfile.migrator           # Migration container
```

## Database Schema

### Main Tables (PostgreSQL)

- `greenhouse.users` - User authentication and roles
- `greenhouse.nodes` - Greenhouse controller registry
- `greenhouse.zones` - 3x3 grid zone definitions
- `greenhouse.sensors` - Sensor configuration
- `greenhouse.actuators` - Actuator configuration
- `greenhouse.permissions` - Access control
- `monitoring.api_logs` - Audit trail
- `monitoring.rate_limits` - API throttling

### Time-Series Tables (TimescaleDB)

- `timeseries.sensor_readings` - All sensor measurements
- `timeseries.actuator_events` - Control commands history
- `timeseries.node_heartbeats` - Node health monitoring
- `timeseries.zone_aggregates` - Pre-computed zone statistics
- `timeseries.system_metrics` - System performance data

## Initial Data

The database is seeded with:

- **4 users**: admin, manager, operator, viewer (all with password: "password")
- **3 nodes**: greenhouse_001, greenhouse_002, greenhouse_003
- **9 zones**: 3x3 grid (A1-A3, B1-B3, C1-C3) with different plants
- **24 sensors**: Distributed across zones for comprehensive monitoring
- **12 actuators**: 8 solenoid valves + 4 main system components
- **Sample data**: 24 hours of synthetic sensor readings and heartbeats

## API Keys

Each node has a unique API key for authentication:

- `greenhouse_001`: `gh001_api_key_abc123`
- `greenhouse_002`: `gh002_api_key_def456`
- `greenhouse_003`: `gh003_api_key_ghi789`

## TimescaleDB Features

### Continuous Aggregates (Real-time Views)

- `hourly_sensor_stats` - Hourly sensor statistics
- `daily_sensor_stats` - Daily trends with percentiles
- `zone_summary_15min` - High-frequency zone monitoring
- `zone_summary_hourly` - Detailed zone analytics
- `node_health_hourly` - Node performance tracking
- `actuator_usage_daily` - Control system analytics

### Data Retention Policies

- **Sensor readings**: 1 year (as per project spec)
- **Actuator events**: 6 months
- **Node heartbeats**: 3 months
- **Continuous aggregates**: 2-5 years (compressed summaries)

### Compression

- **Automatic compression**: Applied after 7 days for raw data
- **90%+ space savings** on historical data
- **Segmented by**: node_id, sensor_type for optimal query performance

## Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check database migration logs
docker-compose logs db_migrator

# Access services
# - API: http://localhost:8000
# - Grafana: http://localhost:3000 (admin/admin123)
# - pgAdmin: http://localhost:5050 (admin@greenhouse.local/admin123)
```

### Development Profile

```bash
# Start with development tools
docker-compose --profile development up -d

# Additional services:
# - Redis Commander: http://localhost:8081
# - pgAdmin: http://localhost:5050
```

## Health Checks

All services include health checks:

- PostgreSQL: `pg_isready` command
- Redis: `redis-cli ping`
- API: `/api/health` endpoint
- Grafana: `/api/health` endpoint

## Performance Monitoring

Use these queries to monitor database performance:

```sql
-- Compression statistics
SELECT * FROM timeseries.get_compression_stats();

-- Data age and volume
SELECT * FROM timeseries.get_data_age_stats();

-- Complete maintenance report
SELECT generate_maintenance_report();
```

## Backup Strategy

- **Automated daily backups** at 2:00 AM
- **Point-in-time recovery** with WAL archiving
- **Compressed storage** for historical data
- **Retention policies** for automatic cleanup

## Security

- **API key authentication** for nodes
- **Session-based authentication** for users
- **Role-based access control** (admin/manager/operator/viewer)
- **Rate limiting** per node and endpoint
- **Complete audit trail** for all API operations

This setup provides a production-ready database infrastructure for the Smart Greenhouse IoT System with enterprise-grade performance, security, and monitoring capabilities.
