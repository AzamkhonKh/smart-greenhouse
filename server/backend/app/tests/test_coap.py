#!/usr/bin/env python3
"""
CoAP Test Client for Smart Greenhouse IoT System
Test script for verifying CoAP sensor data submission
"""

import asyncio
import json
from datetime import datetime
import aiocoap
from aiocoap import Message, Code

async def test_coap_sensor_data():
    """Test CoAP sensor data submission"""
    
    # CoAP server details
    coap_uri = "coap://localhost:5683/sensor/send-data"
    
    # Test data payload
    test_data = {
        "node_id": "greenhouse_001",  # Fixed: matches the config NODE_API_KEYS
        "api_key": "gh001_api_key_abc123",  # Replace with actual API key
        "zone_id": "A1",
        "timestamp": datetime.utcnow().isoformat(),
        "temperature": 22.5,
        "humidity": 65.2,
        "soil_moisture": 45.8,
        "light": 1200,
        "ph": 6.5,
        "ec": 1.2,
        "battery_percentage": 85.0,
        "signal_strength": -45,
        "voltage": 3.3,
        "meta_data": {
            "test": True,
            "version": "1.0"
        }
    }
    
    print(f"Testing CoAP endpoint: {coap_uri}")
    print(f"Sending data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Create CoAP context
        context = await aiocoap.Context.create_client_context()
        
        # Create message
        payload = json.dumps(test_data).encode('utf-8')
        message = Message(
            code=Code.POST,
            uri=coap_uri,
            payload=payload
        )
        
        # Send request
        print("\nSending CoAP POST request...")
        response = await context.request(message).response
        
        # Process response
        print(f"Response Code: {response.code}")
        print(f"Response Payload: {response.payload.decode('utf-8')}")
        
        if response.code.is_successful():
            print("✅ CoAP request successful!")
            response_data = json.loads(response.payload.decode('utf-8'))
            print(f"Processed {response_data.get('readings_count', 0)} sensor readings")
        else:
            print("❌ CoAP request failed!")
            
    except Exception as e:
        print(f"❌ Error testing CoAP endpoint: {e}")
    
    finally:
        if 'context' in locals():
            await context.shutdown()

async def test_coap_minimal_data():
    """Test CoAP with minimal sensor data"""
    
    coap_uri = "coap://localhost:5683/sensor/send-data"
    
    # Minimal test data
    minimal_data = {
        "node_id": "greenhouse_001",  # Fixed: matches the config NODE_API_KEYS
        "api_key": "gh001_api_key_abc123",  # Replace with actual API key
        "temperature": 20.0,
        "humidity": 60.0
    }
    
    print(f"\n--- Testing minimal CoAP data ---")
    print(f"Sending minimal data: {json.dumps(minimal_data, indent=2)}")
    
    try:
        context = await aiocoap.Context.create_client_context()
        
        payload = json.dumps(minimal_data).encode('utf-8')
        message = Message(
            code=Code.POST,
            uri=coap_uri,
            payload=payload
        )
        
        print("Sending minimal CoAP POST request...")
        response = await context.request(message).response
        
        print(f"Response Code: {response.code}")
        print(f"Response Payload: {response.payload.decode('utf-8')}")
        
        if response.code.is_successful():
            print("✅ Minimal CoAP request successful!")
        else:
            print("❌ Minimal CoAP request failed!")
            
    except Exception as e:
        print(f"❌ Error testing minimal CoAP endpoint: {e}")
    
    finally:
        if 'context' in locals():
            await context.shutdown()

async def test_coap_with_query_params():
    """Test CoAP with API key in query parameters"""
    
    # Using query parameters for authentication
    coap_uri = "coap://localhost:5683/sensor/send-data?api_key=gh001_api_key_abc123&node_id=greenhouse_001"
    
    # Data without API key and node_id (in query)
    query_data = {
        "zone_id": "B2",
        "timestamp": datetime.utcnow().isoformat(),
        "temperature": 25.0,
        "soil_moisture": 50.0,
        "light": 800
    }
    
    print(f"\n--- Testing CoAP with query parameters ---")
    print(f"URI: {coap_uri}")
    print(f"Payload: {json.dumps(query_data, indent=2)}")
    
    try:
        context = await aiocoap.Context.create_client_context()
        
        payload = json.dumps(query_data).encode('utf-8')
        message = Message(
            code=Code.POST,
            uri=coap_uri,
            payload=payload
        )
        
        print("Sending CoAP POST request with query params...")
        response = await context.request(message).response
        
        print(f"Response Code: {response.code}")
        print(f"Response Payload: {response.payload.decode('utf-8')}")
        
        if response.code.is_successful():
            print("✅ CoAP request with query params successful!")
        else:
            print("❌ CoAP request with query params failed!")
            
    except Exception as e:
        print(f"❌ Error testing CoAP with query params: {e}")
    
    finally:
        if 'context' in locals():
            await context.shutdown()

async def main():
    """Run all CoAP tests"""
    print("🧪 CoAP Sensor Data Submission Tests")
    print("=" * 50)
    
    # Test full data payload
    await test_coap_sensor_data()
    
    # Test minimal data
    await test_coap_minimal_data()
    
    # Test with query parameters
    await test_coap_with_query_params()
    
    print("\n" + "=" * 50)
    print("🏁 CoAP testing completed")

if __name__ == "__main__":
    print("Make sure your FastAPI server is running before running this test!")
    print("The CoAP server should be listening on port 5683")
    print("Update the API key in this script to match your node's API key")
    print("-" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
