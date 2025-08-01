#ifndef CONFIG_H
#define CONFIG_H

// Try to include local configuration (not committed to git)
#ifdef __has_include
    #if __has_include("config_local.h")
        #include "config_local.h"
        #define HAS_LOCAL_CONFIG 1
    #endif
#endif

// WiFi Configuration
#ifdef HAS_LOCAL_CONFIG
    #define WIFI_SSID WIFI_SSID_LOCAL
    #define WIFI_PASSWORD WIFI_PASSWORD_LOCAL
#else
    #define WIFI_SSID "YOUR_WIFI_SSID"
    #define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#endif
#define WIFI_TIMEOUT_MS 30000  // 30 seconds

// Server Configuration
#ifdef HAS_LOCAL_CONFIG
    #define SERVER_URL SERVER_URL_LOCAL
    #define API_KEY API_KEY_LOCAL
#else
    #define SERVER_URL "http://YOUR_SERVER_IP:8000"
    #define API_KEY "gh001_api_key_abc123"
#endif
#define API_ENDPOINT "/api/sensor-data"

// Node Configuration
#ifdef HAS_LOCAL_CONFIG
    #define NODE_ID NODE_ID_LOCAL
    #define ZONE_ID ZONE_ID_LOCAL
    #define PLANT_TYPE PLANT_TYPE_LOCAL
    #define LOCATION_DESCRIPTION LOCATION_DESCRIPTION_LOCAL
#else
    #define NODE_ID "greenhouse_001"
    #define ZONE_ID "A1"
    #define PLANT_TYPE "tomato"
    #define LOCATION_DESCRIPTION "Greenhouse Section A"
#endif

// Sensor Configuration (GPIO pins for ESP32-C6)
#define SOIL_MOISTURE_PIN 4
#define TEMPERATURE_HUMIDITY_PIN 5
#define LIGHT_SENSOR_PIN 6
#define EC_SENSOR_PIN 7

// Actuator Configuration (GPIO pins for ESP32-C6)
#define WATER_PUMP_PIN 8
#define LED_GROW_LIGHT_PIN 9
#define VALVE_PIN 10

// Timing Configuration (milliseconds)
#define SENSOR_READ_INTERVAL_MS 30000   // 30 seconds for demo
#define DATA_SEND_INTERVAL_MS 60000     // 1 minute for demo
#define STATUS_REPORT_INTERVAL_MS 300000 // 5 minutes

// Task Stack Sizes
#define SENSOR_TASK_STACK 4096
#define COMMUNICATION_TASK_STACK 8192
#define STATUS_TASK_STACK 2048

// Task Priorities
#define SENSOR_TASK_PRIORITY 5
#define COMMUNICATION_TASK_PRIORITY 4
#define STATUS_TASK_PRIORITY 3

// HTTP Configuration
#define HTTP_TIMEOUT_MS 10000
#define HTTP_MAX_RETRIES 3

#endif
