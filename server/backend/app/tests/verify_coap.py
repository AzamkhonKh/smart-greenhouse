#!/usr/bin/env python3
"""
CoAP Server Verification Script
Checks if the CoAP server can be imported and initialized properly
"""

import sys
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_coap_import():
    """Test if CoAP modules can be imported"""
    try:
        import aiocoap
        import aiocoap.resource as resource
        from aiocoap import Context, Message, Code
        logger.info("✅ aiocoap library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import aiocoap: {e}")
        return False

async def test_coap_server_import():
    """Test if the CoAP server module can be imported"""
    try:
        # Add the backend directory to Python path
        sys.path.append('/Users/azamkhon/milvus/unipis/server/backend')
        
        from coap_server import SensorDataResource, CoAPServer
        logger.info("✅ CoAP server module imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import CoAP server module: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing CoAP server module: {e}")
        return False

async def test_coap_resource():
    """Test if the sensor data resource can be created"""
    try:
        sys.path.append('/Users/azamkhon/milvus/unipis/server/backend')
        from coap_server import SensorDataResource
        
        resource = SensorDataResource()
        logger.info("✅ SensorDataResource created successfully")
        logger.info(f"   Content format: {resource.content_format}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create SensorDataResource: {e}")
        return False

async def test_coap_server_creation():
    """Test if the CoAP server can be created"""
    try:
        sys.path.append('/Users/azamkhon/milvus/unipis/server/backend')
        from coap_server import CoAPServer
        
        server = CoAPServer(host='127.0.0.1', port=5683)
        logger.info("✅ CoAPServer created successfully")
        logger.info(f"   Host: {server.host}")
        logger.info(f"   Port: {server.port}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create CoAPServer: {e}")
        return False

async def main():
    """Run all verification tests"""
    logger.info("🧪 CoAP Server Verification Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Import aiocoap library", test_coap_import),
        ("Import CoAP server module", test_coap_server_import),
        ("Create sensor data resource", test_coap_resource),
        ("Create CoAP server", test_coap_server_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! CoAP server is ready.")
        logger.info("\nNext steps:")
        logger.info("1. Start your FastAPI server")
        logger.info("2. Run test_coap.py to test the endpoint")
        logger.info("3. Check logs for CoAP server startup messages")
    else:
        logger.warning("⚠️  Some tests failed. Check the errors above.")
        logger.info("\nTroubleshooting:")
        logger.info("1. Make sure aiocoap is installed: pip install aiocoap==0.4.7")
        logger.info("2. Check that all dependencies are available")
        logger.info("3. Verify the backend module path is correct")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        sys.exit(1)
