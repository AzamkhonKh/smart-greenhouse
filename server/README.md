# Smart Greenhouse IoT System - Server

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab.svg)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.0+-orange.svg)](https://www.timescale.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed.svg)](https://docs.docker.com/compose)
[![CoAP](https://img.shields.io/badge/CoAP-RFC7252-green.svg)](https://tools.ietf.org/html/rfc7252)

A production-ready, containerized Smart Greenhouse IoT system featuring **dual-protocol communication** (HTTP REST + CoAP), real-time analytics, and enterprise-grade architecture.

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (Recommended)
- **Python 3.11+** (For local development)

### 🐳 Docker Deployment (Recommended)

```bash
# Clone and navigate
git clone https://github.com/AzamkhonKh/smart-greenhouse.git
cd smart-greenhouse/server

# Start all services
docker-compose up -d

# Verify deployment
curl http://localhost:8000/health
```

**That's it!** The system will be available at:

- **API**: <http://localhost:8000>
- **Documentation**: <http://localhost:8000/docs>
- **CoAP**: `coap://localhost:5683`
- **Grafana**: <http://localhost:3000>

### 🛠️ Local Development

```bash
cd backend

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start application
python main.py
```

## 🏗️ Architecture

### System Overview

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Devices   │    │   Web Clients   │    │  Grafana Dash   │
│    (CoAP)       │    │    (HTTP)       │    │   (HTTP)        │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
      ┌───▼──────────────────────▼──────────────────────▼───┐
      │              FastAPI Backend                       │
      │        HTTP REST (8000) + CoAP (5683)             │
      └─────────────────┬─────────┬─────────────────────────┘
                        │         │
          ┌─────────────▼───┐   ┌─▼─────┐
          │ PostgreSQL +    │   │ Redis │
          │ TimescaleDB     │   │       │
          └─────────────────┘   └───────┘
```

### Multi-Protocol Communication

#### HTTP REST API (Port 8000)

- **Full-featured**: Complete CRUD operations, authentication, file uploads
- **Standards**: OpenAPI 3.0, JSON:API, HTTP/2
- **Security**: JWT tokens, API keys, rate limiting, CORS
- **Documentation**: Interactive Swagger UI and ReDoc

#### CoAP Server (UDP Port 5683)

- **Lightweight**: Optimized for constrained IoT devices
- **Standards**: RFC 7252 compliant with observe patterns
- **Authentication**: Query parameter and header-based auth
- **Efficiency**: Binary protocol, minimal overhead

### Database Architecture

#### PostgreSQL + TimescaleDB

- **Unified Storage**: Single database for all data types
- **Time-Series**: Automatic partitioning and compression
- **Analytics**: Continuous aggregates and real-time computations
- **Scalability**: Horizontal scaling with distributed hypertables

#### Redis

- **Caching**: API response caching and session storage
- **Real-time**: Pub/sub for live notifications
- **Rate Limiting**: Token bucket algorithm implementation
- **Performance**: Sub-millisecond response times

## 📁 Project Structure

```text
server/
├── 🐳 docker-compose.yml           # Multi-service orchestration
├── 📖 README.md                    # This file
├── backend/                        # FastAPI application
│   ├── 🚀 main.py                  # Unified application entry point
│   ├── 📦 requirements.txt         # Python dependencies
│   ├── 🐳 Dockerfile               # Container build instructions
│   ├── ⚙️ .env.example             # Environment template
│   └── app/                        # Application package
│       ├── api/v1/                 # 🌐 Versioned API endpoints
│       │   ├── auth.py             # Authentication routes
│       │   ├── sensors.py          # Sensor data endpoints
│       │   ├── nodes.py            # Node management
│       │   ├── analytics.py        # Data analytics
│       │   └── actuators.py        # Device control
│       ├── core/                   # 🔐 Core functionality
│       │   ├── config.py           # Configuration management
│       │   ├── auth.py             # Authentication logic
│       │   └── exceptions.py       # Custom exceptions
│       ├── db/                     # 🗄️ Database layer
│       │   ├── database.py         # Connection management
│       │   └── migrations/         # Schema migrations
│       ├── models/                 # 📊 Data models
│       │   ├── user.py             # User entities
│       │   ├── sensor.py           # Sensor definitions
│       │   └── node.py             # Node management
│       ├── schemas/                # 🔍 Request/Response validation
│       ├── services/               # 🔧 Business logic
│       │   ├── coap_server.py      # CoAP protocol handler
│       │   ├── analytics.py        # Data processing
│       │   └── notifications.py    # Alert system
│       └── utils/                  # 🛠️ Utility functions
├── database/                       # 🗄️ Database setup
│   ├── init/                       # Database initialization
│   └── scripts/                    # Migration and backup scripts
└── grafana/                        # 📊 Monitoring dashboards
    ├── dashboards/                 # Pre-built dashboards
    └── datasources/                # Data source configurations
```

## 🔌 API Reference

### Core Endpoints

| Method | Endpoint | Description | Protocol |
|--------|----------|-------------|----------|
| `GET` | `/` | System status and information | HTTP |
| `GET` | `/health` | Health check for load balancers | HTTP |
| `GET` | `/docs` | Interactive API documentation | HTTP |
| `GET` | `/redoc` | Alternative API documentation | HTTP |

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | User authentication |
| `POST` | `/auth/refresh` | Token refresh |
| `POST` | `/auth/logout` | Session termination |
| `GET` | `/auth/me` | Current user profile |

### IoT Management (`/api/v1`)

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| **Nodes** | `/nodes/*` | IoT device registration and management |
| **Sensors** | `/sensors/*` | Sensor configuration and data retrieval |
| **Actuators** | `/actuators/*` | Device control and automation |
| **Analytics** | `/analytics/*` | Data aggregation and insights |
| **Zones** | `/zones/*` | Greenhouse zone management |

### CoAP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sensor/send-data` | Endpoint discovery |
| `POST` | `/sensor/send-data` | Sensor data submission |

**Example CoAP Request:**

```bash
# Discovery
coap-client -m GET coap://localhost:5683/sensor/send-data

# Data submission
echo '{"temperature":22.5,"humidity":65}' | \
  coap-client -m POST coap://localhost:5683/sensor/send-data?api_key=KEY&node_id=NODE -f -
```

## ⚙️ Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=greenhouse
POSTGRES_USER=greenhouse_user
POSTGRES_PASSWORD=secure_password
POSTGRES_PORT=5432

# TimescaleDB
TIMESCALEDB_ENABLED=true
TIMESCALE_CHUNK_TIME_INTERVAL=1d
TIMESCALE_COMPRESSION_ENABLED=true

# Redis
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=your-super-secure-secret
API_KEY_CACHE_TTL=300

# Features
RATE_LIMIT_ENABLED=true
COAP_SERVER_ENABLED=true
```

## 🧪 Testing

### Quick Verification

```bash
# Test all endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/sensors
curl http://localhost:8000/api/v1/nodes

# CoAP testing with command line
coap-client -m GET coap://localhost:5683/sensor/send-data
```

### CoAP Testing Scripts

For comprehensive CoAP testing, use the provided test scripts in `backend/app/tests/`:

```bash
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run CoAP tests
cd app/tests

# Verify CoAP server and imports
python verify_coap.py

# Test basic CoAP functionality
python test_coap.py

# Test ESP32-style CoAP communication
python test_esp32_coap.py

# Test different endpoint paths
python test_coap_paths.py
```

**Available Test Scripts:**

| Script | Purpose | Description |
|--------|---------|-------------|
| `verify_coap.py` | Import verification | Check if CoAP libraries and server can be imported |
| `test_coap.py` | Full CoAP test | Complete sensor data submission with authentication |
| `test_esp32_coap.py` | ESP32 simulation | Simulate ESP32 device communication patterns |
| `test_coap_paths.py` | Endpoint testing | Test different CoAP endpoint paths and methods |

**Note**: Make sure the CoAP server is running (`docker-compose up -d`) before running the test scripts.

### Health Checks

| Endpoint | Service | Description |
|----------|---------|-------------|
| `/health` | System | Overall health status |
| `/api/v1/health` | Detailed | All services status |

## 📊 Monitoring

- **API Documentation**: <http://localhost:8000/docs> (Swagger UI)
- **Grafana Dashboards**: <http://localhost:3000>
- **Logs**: `docker-compose logs api`

## 🔍 Troubleshooting

### Common Issues

**Container won't start:**

```bash
# Check logs
docker-compose logs api

# Rebuild
docker-compose down && docker-compose up --build
```

**Database connection errors:**

```bash
# Test connection
docker exec -it greenhouse_postgres psql -U greenhouse_user -d greenhouse
```

**CoAP not responding:**

```bash
# Test UDP port
nc -u localhost 5683
```

## 🚀 Current Status

### ✅ Working Features

- **Multi-Protocol API**: HTTP REST + CoAP support ✓
- **Containerized Deployment**: Docker Compose ready ✓
- **Database Integration**: PostgreSQL + TimescaleDB + Redis ✓
- **Real-time Data**: Live sensor readings ✓
- **API Documentation**: Interactive Swagger UI ✓
- **Health Monitoring**: System status endpoints ✓

### 📊 Live Services

When running with `docker-compose up -d`:

- **FastAPI Backend**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>
- **CoAP Server**: `coap://localhost:5683`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Grafana**: <http://localhost:3000>

### 🎯 Architecture Benefits

- **Single Entry Point**: Unified `main.py` handles all scenarios
- **Adaptive System**: Works with or without full database stack
- **Production Ready**: Enterprise-grade logging, monitoring, error handling
- **Developer Friendly**: Hot reload, comprehensive docs, easy debugging
- **Scalable**: Service-based architecture, horizontal scaling support

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

## 📄 License

This project is licensed under the MIT License.

---

**Smart Greenhouse IoT System** - Production-ready, scalable, and developer-friendly! 🌱🚀
