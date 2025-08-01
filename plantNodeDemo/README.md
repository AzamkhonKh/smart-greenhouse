# ESP32-C6 Plant Node Demo

ESP32-C6 based plant monitoring node with ESP-IDF and FreeRTOS for smart agriculture applications using CoAP communication.

## Quick Start

1. **Install ESP-IDF**: Follow [ESP-IDF Getting Started Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/get-started/)

2. **Setup**:

   ```bash
   git clone <your-repo-url>
   cd plantNodeDemo
   source ~/esp/esp-idf/export.sh
   ./quick-start.sh
   ```

3. **Configure WiFi** in `main/include/common/config_local.h`
4. **Build and flash** using the quick-start script

## Project Structure

This project follows ESP-IDF best practices with a modular component structure:

```text
plantNodeDemo/
├── CMakeLists.txt              # Main project configuration
├── sdkconfig                   # ESP-IDF configuration
├── main/                       # Main component (organized by modules)
│   ├── src/                    # Source implementations
│   │   ├── main.c             # Application entry point
│   │   ├── network/           # Network functionality
│   │   │   ├── wifi_manager.c # WiFi connection management
│   │   │   ├── coap_client.c  # CoAP protocol implementation
│   │   │   └── http_client.c  # HTTP client functionality
│   │   ├── sensors/           # Sensor management
│   │   │   └── sensor_manager.c
│   │   └── simulation/        # Plant simulation
│   │       └── greenhouse_simulator.c
│   ├── include/               # Header files
│   │   ├── common/            # Common configuration
│   │   │   ├── config.h       # Main configuration
│   │   │   └── config_local.h # Local environment config
│   │   ├── network/           # Network headers
│   │   ├── sensors/           # Sensor headers
│   │   └── simulation/        # Simulation headers
│   └── CMakeLists.txt         # Component build configuration
├── components/                 # External components
│   └── libcoap/               # CoAP library
└── build/                     # Build output (generated)
```

## Features

- Multi-sensor monitoring: Temperature, humidity, soil moisture, and light intensity
- CoAP communication protocol
- WiFi connectivity with auto-reconnection  
- Plant simulation for testing
- FreeRTOS task-based architecture
- Modular design

## Hardware

**Target**: ESP32-C6 development board

**Sensors** (simulated):

- DHT22 temperature/humidity sensor
- Soil moisture sensor
- Light sensor
- EC sensor

## Setup libcoap

This project uses the libcoap library for CoAP communication. Get it from GitHub:

```bash
# Clone libcoap into components directory
cd components/
git clone https://github.com/obgm/libcoap.git
cd libcoap/

# Checkout stable version (recommended)
git checkout v4.3.4

# Or use latest development version
# git checkout develop
```

### Alternative: Using ESP-IDF Component Manager

Add to `main/idf_component.yml`:

```yaml
dependencies:
  libcoap:
    git: https://github.com/obgm/libcoap.git
    version: "v4.3.4"
```

## Configuration

Create local configuration file:

```bash
cp main/include/common/config_local.h.template main/include/common/config_local.h
```

Edit with your WiFi and server settings:

```cpp
#define WIFI_SSID_LOCAL "Your_WiFi_Network"
#define WIFI_PASSWORD_LOCAL "your_wifi_password"
#define SERVER_URL_LOCAL "coap://your-server-ip:5683"
#define NODE_ID_LOCAL "esp32c6_plant_node_01"
```

## Build and Flash

### Using Quick Start Script (Recommended)

```bash
./quick-start.sh
```

### Manual Build

```bash
# Set ESP-IDF environment
source ~/esp/esp-idf/export.sh

# Build and flash
idf.py build
idf.py flash monitor
```

## Expected Output

```text
I (123) MAIN: Starting ESP32-C6 sensor node
I (234) WIFI_MANAGER: WiFi connected successfully  
I (345) SENSOR_MANAGER: Reading sensors...
I (456) GREENHOUSE_SIM: Temperature: 23.5°C, Humidity: 65.2%
I (567) COAP_CLIENT: Sending sensor data via CoAP
```

## CoAP Communication

The node sends sensor data via CoAP protocol:

```json
{
   "node_id": "greenhouse_001",
   "api_key": "greenhouse_001_asd",
   "temperature": 23.5,
   "humidity": 65.2,
   "soil_moisture": 45.8,
   "light_intensity": 1200
}
```

## Troubleshooting

**Build issues**: Source ESP-IDF environment: `source ~/esp/esp-idf/export.sh`

**WiFi connection fails**: Check SSID/password in `config_local.h`

**Flashing issues**: Check USB connection and permissions

## License

Educational and development demonstration project.
