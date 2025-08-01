#!/bin/bash

# ESP32-C6 Plant Node Demo - Quick Start Script
# This script helps set up and run the project

set -e  # Exit on any error

echo "🌱 ESP32-C6 Plant Node Demo - Quick Start"
echo "========================================"

# Check if ESP-IDF is available
if ! command -v idf.py &> /dev/null; then
    echo "❌ ESP-IDF not found in PATH"
    echo "Please install ESP-IDF and source the environment:"
    echo "  cd ~/esp/esp-idf"
    echo "  source export.sh"
    exit 1
fi

echo "✅ ESP-IDF found: $(idf.py --version 2>&1 | head -n1)"

# Check if config_local.h exists
CONFIG_FILE="main/include/common/config_local.h"
CONFIG_TEMPLATE="main/include/common/config_local.h.template"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚙️  Setting up configuration..."
    if [ -f "$CONFIG_TEMPLATE" ]; then
        cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
        echo "✅ Created $CONFIG_FILE from template"
        echo "📝 Please edit $CONFIG_FILE with your WiFi credentials and server settings"
        echo ""
        echo "Required changes:"
        echo "  - WIFI_SSID_LOCAL: Your WiFi network name"
        echo "  - WIFI_PASSWORD_LOCAL: Your WiFi password"
        echo "  - SERVER_URL_LOCAL: CoAP server URL (e.g., coap://192.168.1.100:5683)"
        echo ""
        read -p "Press Enter after you've updated the configuration file..."
    else
        echo "❌ Template file $CONFIG_TEMPLATE not found"
        exit 1
    fi
else
    echo "✅ Configuration file exists: $CONFIG_FILE"
fi

# Function to build the project
build_project() {
    echo "🔨 Building project..."
    idf.py build
    if [ $? -eq 0 ]; then
        echo "✅ Build successful!"
        return 0
    else
        echo "❌ Build failed!"
        return 1
    fi
}

# Function to flash the project
flash_project() {
    echo "📡 Flashing to device..."
    idf.py flash
    if [ $? -eq 0 ]; then
        echo "✅ Flash successful!"
        return 0
    else
        echo "❌ Flash failed!"
        echo "💡 Make sure your ESP32-C6 is connected and in download mode"
        return 1
    fi
}

# Function to monitor output
monitor_project() {
    echo "📊 Starting serial monitor..."
    echo "💡 Press Ctrl+] to exit monitor"
    idf.py monitor
}

# Main menu
while true; do
    echo ""
    echo "What would you like to do?"
    echo "1) Build project"
    echo "2) Flash to device"
    echo "3) Build and flash"
    echo "4) Flash and monitor"
    echo "5) Build, flash, and monitor"
    echo "6) Monitor only"
    echo "7) Clean build"
    echo "8) Exit"
    
    read -p "Enter your choice (1-8): " choice
    
    case $choice in
        1)
            build_project
            ;;
        2)
            flash_project
            ;;
        3)
            if build_project; then
                flash_project
            fi
            ;;
        4)
            if flash_project; then
                monitor_project
            fi
            ;;
        5)
            if build_project && flash_project; then
                monitor_project
            fi
            ;;
        6)
            monitor_project
            ;;
        7)
            echo "🧹 Cleaning build..."
            idf.py fullclean
            echo "✅ Clean complete!"
            ;;
        8)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please enter 1-8."
            ;;
    esac
done
