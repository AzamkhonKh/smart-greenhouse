#!/usr/bin/env python3
"""
Test script to check CoAP endpoint paths
"""

import asyncio
import json
from aiocoap import Context, Message, Code

async def test_coap_paths():
    """Test different CoAP endpoint paths"""
    
    print("🔍 Testing CoAP Endpoint Paths")
    print("=" * 50)
    
    # Test paths
    paths = [
        "/sensor/send-data",
        "/sensor/data", 
        "/data",
        "/sensor",
        "/"
    ]
    
    # Create CoAP context
    context = await Context.create_client_context()
    
    try:
        for path in paths:
            print(f"\n📡 Testing path: {path}")
            
            # Test GET first to see if endpoint exists
            try:
                uri = f"coap://localhost:5683{path}"
                request = Message(code=Code.GET, uri=uri)
                
                response = await context.request(request).response
                print(f"  GET {path}: {response.code}")
                
                if response.payload:
                    try:
                        data = json.loads(response.payload.decode('utf-8'))
                        print(f"  Response: {data.get('service', 'Unknown service')}")
                    except:
                        print(f"  Response: {response.payload.decode('utf-8')[:100]}...")
                        
            except Exception as e:
                print(f"  GET {path}: ERROR - {e}")
            
            # Test POST with ESP32-style data
            try:
                esp32_data = {
                    "temperature": 22.5,
                    "humidity": 65.0,
                    "soil_moisture": 15.8,
                    "light": 13700
                }
                
                uri = f"coap://localhost:5683{path}?api_key=gh001_api_key_abc123&node_id=greenhouse_001"
                request = Message(
                    code=Code.POST,
                    payload=json.dumps(esp32_data).encode('utf-8'),
                    uri=uri
                )
                
                response = await context.request(request).response
                print(f"  POST {path}: {response.code}")
                
                if response.code == Code.CREATED:
                    print(f"  ✅ Success!")
                elif response.code == Code.NOT_FOUND:
                    print(f"  ❌ Not Found")
                else:
                    print(f"  ⚠️ Other response: {response.code}")
                    
            except Exception as e:
                print(f"  POST {path}: ERROR - {e}")
    
    finally:
        await context.shutdown()
    
    print("\n" + "=" * 50)
    print("💡 If ESP32 is getting NotFound errors, check:")
    print("1. The exact path your ESP32 code is using")
    print("2. Use one of the working paths above")
    print("3. Make sure to include query parameters for auth")

if __name__ == "__main__":
    asyncio.run(test_coap_paths())
