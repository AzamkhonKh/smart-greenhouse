#!/usr/bin/env python3
"""
Test script for ESP32-style CoAP sensor data submission
Simulates the exact payload format your ESP32 device is sending
"""

import asyncio
import json
from datetime import datetime
from aiocoap import Context, Message, Code

async def test_esp32_coap():
    """Test CoAP endpoint with ESP32-style payload"""
    
    print("🔧 ESP32-Style CoAP Sensor Data Test")
    print("=" * 50)
    print("Testing CoAP endpoint: coap://localhost:5683/sensor/send-data")
    
    # ESP32 payload format - clean sensor data only
    esp32_payload = {
        "temperature": 22.5,
        "humidity": 65.0,
        "soil_moisture": 15.8,
        "light": 13700
    }
    
    print(f"Sending ESP32-style data: {json.dumps(esp32_payload, indent=2)}")
    print()
    
    # Create CoAP context
    context = await Context.create_client_context()
    
    try:
        # Test with query parameters (recommended for ESP32)
        # Use the actual IP that ESP32 is trying to reach
        uri = "coap://192.168.1.52:5683/sensor/send-data?api_key=gh001_api_key_abc123&node_id=greenhouse_001"
        print(f"🔗 URI: {uri}")
        
        # Create CoAP request
        request = Message(
            code=Code.POST,
            payload=json.dumps(esp32_payload).encode('utf-8'),
            uri=uri
        )
        
        print("📡 Sending ESP32-style CoAP POST request...")
        
        # Send request
        response = await context.request(request).response
        
        print(f"📨 Response Code: {response.code}")
        if response.payload:
            try:
                response_data = json.loads(response.payload.decode('utf-8'))
                print(f"📦 Response Payload: {json.dumps(response_data, indent=2)}")
            except:
                print(f"📦 Response Payload: {response.payload.decode('utf-8')}")
        
        if response.code == Code.CREATED:
            print("✅ ESP32-style CoAP request successful!")
        else:
            print(f"❌ ESP32-style CoAP request failed with code: {response.code}")
    
    except Exception as e:
        print(f"💥 Error: {e}")
    
    finally:
        await context.shutdown()
    
    print()
    print("=" * 50)
    print("🔧 ESP32 Implementation Tip:")
    print("In your ESP32 code, use this CoAP URI format:")
    print("coap://your-server:5683/sensor/send-data?api_key=YOUR_KEY&node_id=YOUR_NODE")
    print("With clean JSON payload containing only sensor values.")

async def test_multiple_formats():
    """Test both old and new payload formats"""
    print("\n🧪 Testing Multiple Payload Formats")
    print("=" * 50)
    
    # Test 1: ESP32 style (auth in query params)
    print("Test 1: ESP32 Style (Clean payload + Query auth)")
    await test_esp32_coap()
    
    print("\n" + "-" * 30 + "\n")
    
    # Test 2: Original style (auth in payload) 
    print("Test 2: Original Style (Auth in payload)")
    context = await Context.create_client_context()
    
    try:
        original_payload = {
            "node_id": "greenhouse_001",
            "api_key": "gh001_api_key_abc123",
            "temperature": 22.5,
            "humidity": 65.0,
            "soil_moisture": 15.8,
            "light": 13700
        }
        
        uri = "coap://192.168.1.52:5683/sensor/send-data"
        request = Message(
            code=Code.POST,
            payload=json.dumps(original_payload).encode('utf-8'),
            uri=uri
        )
        
        print(f"📡 Sending original-style request to: {uri}")
        response = await context.request(request).response
        
        print(f"📨 Response Code: {response.code}")
        if response.payload:
            try:
                response_data = json.loads(response.payload.decode('utf-8'))
                print(f"📦 Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"📦 Response: {response.payload.decode('utf-8')}")
        
        if response.code == Code.CREATED:
            print("✅ Original-style CoAP request successful!")
        else:
            print(f"❌ Original-style CoAP request failed")
            
    except Exception as e:
        print(f"💥 Error: {e}")
    
    finally:
        await context.shutdown()

if __name__ == "__main__":
    print("Make sure your CoAP server is running before running this test!")
    print("The CoAP server should be listening on port 5683")
    print("-" * 60)
    
    # Run the tests
    asyncio.run(test_multiple_formats())
    
    print("\n🏁 Testing completed")
    print("\n💡 For your ESP32, use the query parameter method for cleaner code!")
