# Backend Structure - Smart Greenhouse IoT System

This document outlines the restructured backend architecture following FastAPI best practices.

## 📁 Directory Structure

```
backend/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .env.example               # Environment variables template
├── app/                       # Main application package
│   ├── __init__.py
│   ├── api/                   # API layer
│   │   ├── __init__.py
│   │   └── v1/                # API version 1
│   │       ├── __init__.py
│   │       ├── api_router.py  # Main API router
│   │       ├── auth_router.py # Authentication endpoints
│   │       ├── nodes_router.py # Node management
│   │       ├── sensors_router.py # Sensor data
│   │       ├── actuators_router.py # Actuator control
│   │       ├── analytics_router.py # Analytics endpoints
│   │       ├── users_router.py # User management
│   │       ├── zones_router.py # Zone management
│   │       └── health_router.py # Health checks
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   ├── auth.py            # Authentication logic
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   └── exceptions.py      # Custom exceptions
│   ├── db/                    # Database layer
│   │   ├── __init__.py
│   │   └── database.py        # Database connections
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy models
│   │   └── tortoise_models.py # Tortoise ORM models
│   ├── schemas/               # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py         # Request/Response schemas
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── base_service.py    # Base service class
│   │   └── coap_server.py     # CoAP server service
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   ├── redis_utils.py     # Redis utilities
│   │   └── helpers.py         # Common helpers
│   └── tests/                 # Test files
│       ├── __init__.py
│       ├── test_coap.py
│       ├── test_coap_paths.py
│       ├── test_esp32_coap.py
│       └── verify_coap.py
├── admin/                     # Admin utilities (legacy)
│   ├── admin_config.py
│   └── create_admin.py
├── logs/                      # Log files
├── templates/                 # Jinja2 templates
└── docs/                      # Documentation
    ├── COAP_README.md         # CoAP API documentation
    └── STRUCTURE.md           # This file
```

## 🏗️ Architecture Principles

### 1. **Separation of Concerns**

- **API Layer**: Handles HTTP requests, validation, and responses
- **Core Layer**: Authentication, configuration, dependencies
- **Service Layer**: Business logic and external service integrations
- **Data Layer**: Database models and data access
- **Utils Layer**: Common utilities and helpers

### 2. **Dependency Injection**

- FastAPI's dependency injection system is used throughout
- Dependencies are defined in `app/core/dependencies.py`
- Database sessions, Redis clients, and auth are injected as needed

### 3. **Error Handling**

- Custom exceptions in `app/core/exceptions.py`
- Global exception handlers for consistent error responses
- Proper HTTP status codes and error messages

### 4. **Configuration Management**

- Environment-based configuration using Pydantic Settings
- Centralized in `app/core/config.py`
- Type validation and default values

### 5. **Service Layer Pattern**

- Business logic encapsulated in service classes
- Base service class provides common functionality
- Services are injectable and testable

## 🔧 Key Components

### **Main Application (`main.py`)**

- FastAPI application factory
- Middleware configuration
- Exception handler registration
- Lifespan management for startup/shutdown

### **API Router (`app/api/v1/api_router.py`)**

- Centralized routing configuration
- Version-specific API endpoints
- Organized by feature modules

### **Configuration (`app/core/config.py`)**

- Pydantic Settings for type-safe configuration
- Environment variable support
- Database, Redis, and security settings

### **Dependencies (`app/core/dependencies.py`)**

- Database session management
- Authentication dependencies
- Redis client injection
- Admin user validation

### **Services (`app/services/`)**

- **CoAP Server**: Handles IoT device communication
- **Base Service**: Common service functionality
- Extensible for additional services

### **Models (`app/models/`)**

- **SQLAlchemy Models**: For PostgreSQL/TimescaleDB
- **Tortoise Models**: For async ORM operations
- Clear separation of data access patterns

### **Schemas (`app/schemas/`)**

- Pydantic models for request/response validation
- Type safety and automatic documentation
- Input validation and serialization

## 🚀 Benefits of This Structure

### **Maintainability**

- Clear separation of concerns
- Easy to locate and modify code
- Consistent patterns throughout

### **Scalability**

- Modular architecture allows for easy extension
- Service layer can be scaled independently
- Database and caching layers are abstracted

### **Testability**

- Dependency injection makes mocking easy
- Service layer can be tested in isolation
- Clear interfaces between components

### **Developer Experience**

- IDE autocomplete and type checking
- Clear import paths
- Consistent error handling

### **Production Ready**

- Proper logging and monitoring
- Configuration management
- Health checks and graceful shutdown

## 📝 Usage Examples

### **Adding a New Endpoint**

1. Create the endpoint in the appropriate router (e.g., `sensors_router.py`)
2. Add business logic to a service class
3. Define request/response schemas in `schemas.py`
4. Update the main router in `api_router.py`

### **Adding a New Service**

1. Create a new service class inheriting from `BaseService`
2. Implement `start()` and `stop()` methods
3. Add dependency injection if needed
4. Register in the main application lifespan

### **Environment Configuration**

1. Add new settings to `Settings` class in `config.py`
2. Set environment variables or use `.env` file
3. Access via `get_settings()` dependency

## 🔐 Security Features

- JWT token authentication
- API key validation for IoT devices
- Rate limiting per endpoint
- Input validation and sanitization
- CORS and trusted host middleware
- Secure password hashing

## 📊 Monitoring and Observability

- Structured logging throughout the application
- Health check endpoints
- Exception tracking and error reporting
- Performance monitoring capabilities
- Redis-based caching and session management

## 🧪 Testing Strategy

- Unit tests for service layer
- Integration tests for API endpoints
- CoAP protocol testing
- Database testing with test fixtures
- Async test support with pytest-asyncio

This structure provides a solid foundation for a maintainable, scalable, and production-ready FastAPI application.
