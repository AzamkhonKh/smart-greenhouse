"""
Smart Greenhouse IoT System - CoAP Server
Handles CoAP requests for sensor data submission
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
import aiocoap.resource as resource
import aiocoap
from aiocoap import Context, Message, Code

from app.db.database import get_db_session
from app.core.auth import verify_api_key_sync
from app.models.models import Node, Sensor, SensorReading, DataQuality
from app.services.base_service import BaseService
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Rate limiting for protocol error warnings
class RateLimitedLogger:
    def __init__(self, interval=60):  # Log at most once per 60 seconds
        self.interval = interval
        self.last_logged = {}
    
    def log_if_allowed(self, key, log_func, message):
        current_time = time.time()
        if key not in self.last_logged or current_time - self.last_logged[key] >= self.interval:
            log_func(message)
            self.last_logged[key] = current_time
            return True
        return False

rate_limiter = RateLimitedLogger()

class CatchAllResource(resource.Resource):
    """Catch-all resource to log unmatched requests before they become NotFound"""
    
    def _log_request_details(self, request, method="UNKNOWN"):
        """Log comprehensive request details"""
        try:
            client_addr = getattr(request, 'remote', 'unknown')
            logger.warning(f"🔍 === {method} REQUEST DETAILS (UNMATCHED) ===")
            logger.warning(f"🔍 Client Address: {client_addr}")
            
            # Log URI path
            if hasattr(request, 'opt') and hasattr(request.opt, 'uri_path') and request.opt.uri_path:
                path_segments = '/'.join(request.opt.uri_path)
                logger.warning(f"🔍 Requested Path: /{path_segments}")
            else:
                logger.warning(f"🔍 Requested Path: / (root)")
            
            # Log query parameters
            if hasattr(request, 'opt') and hasattr(request.opt, 'uri_query') and request.opt.uri_query:
                query_params = '&'.join(request.opt.uri_query)
                logger.warning(f"🔍 Query Parameters: {query_params}")
            else:
                logger.warning(f"🔍 Query Parameters: None")
            
            # Log payload details
            if hasattr(request, 'payload') and request.payload:
                logger.warning(f"🔍 Payload Size: {len(request.payload)} bytes")
                try:
                    payload_str = request.payload.decode('utf-8')
                    logger.warning(f"🔍 Payload Content: {payload_str[:200]}...")
                except:
                    logger.warning(f"🔍 Payload Content: <binary data>")
            else:
                logger.warning(f"🔍 Payload: None")
            
            # Log headers/options
            if hasattr(request, 'opt'):
                logger.warning(f"🔍 Content Format: {getattr(request.opt, 'content_format', 'None')}")
                logger.warning(f"🔍 Accept: {getattr(request.opt, 'accept', 'None')}")
            
            logger.warning(f"🔍 === END REQUEST DETAILS ===")
            
        except Exception as e:
            logger.warning(f"🔍 Error logging request details: {e}")
    
    async def render_get(self, request):
        """Log GET requests to unmatched paths"""
        self._log_request_details(request, "GET")
        return Message(code=Code.NOT_FOUND, payload=b"Path not found")
    
    async def render_post(self, request):
        """Log POST requests to unmatched paths"""
        self._log_request_details(request, "POST")
        return Message(code=Code.NOT_FOUND, payload=b"Path not found")

class SensorDataResource(resource.Resource):
    """CoAP resource for handling sensor data submissions"""
    
    def __init__(self):
        super().__init__()
        self.content_format = 50  # application/json
    
    def _log_request_details(self, request, method="UNKNOWN"):
        """Log comprehensive request details for matched requests"""
        try:
            client_addr = getattr(request, 'remote', 'unknown')
            logger.info(f"📋 === {method} REQUEST DETAILS (MATCHED) ===")
            logger.info(f"📋 Client Address: {client_addr}")
            
            # Log URI path
            if hasattr(request, 'opt') and hasattr(request.opt, 'uri_path') and request.opt.uri_path:
                path_segments = '/'.join(request.opt.uri_path)
                logger.info(f"📋 Requested Path: /{path_segments}")
            else:
                logger.info(f"📋 Requested Path: / (root)")
            
            # Log query parameters in detail
            if hasattr(request, 'opt') and hasattr(request.opt, 'uri_query') and request.opt.uri_query:
                query_params = '&'.join(request.opt.uri_query)
                logger.info(f"📋 Query Parameters: {query_params}")
                # Parse and log individual parameters
                for param in request.opt.uri_query:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # Mask sensitive data
                        if key.lower() in ['api_key', 'key', 'token']:
                            masked_value = value[:8] + '...' if len(value) > 8 else value
                            logger.info(f"📋   {key}: {masked_value}")
                        else:
                            logger.info(f"📋   {key}: {value}")
            else:
                logger.info(f"📋 Query Parameters: None")
            
            # Log payload details
            if hasattr(request, 'payload') and request.payload:
                logger.info(f"📋 Payload Size: {len(request.payload)} bytes")
                try:
                    payload_str = request.payload.decode('utf-8')
                    logger.info(f"📋 Payload Preview: {payload_str[:300]}...")
                except:
                    logger.info(f"📋 Payload Content: <binary data - first 50 bytes: {request.payload[:50]}>")
            else:
                logger.info(f"📋 Payload: None")
            
            # Log CoAP headers/options
            if hasattr(request, 'opt'):
                logger.info(f"📋 Content Format: {getattr(request.opt, 'content_format', 'None')}")
                logger.info(f"📋 Accept: {getattr(request.opt, 'accept', 'None')}")
                
            # Log CoAP message details
            if hasattr(request, 'code'):
                logger.info(f"📋 CoAP Code: {request.code}")
            if hasattr(request, 'mtype'):
                logger.info(f"📋 Message Type: {request.mtype}")
            if hasattr(request, 'mid'):
                logger.info(f"📋 Message ID: {request.mid}")
            if hasattr(request, 'token'):
                logger.info(f"📋 Token: {request.token.hex() if request.token else 'None'}")
            
            logger.info(f"📋 === END REQUEST DETAILS ===")
            
        except Exception as e:
            logger.warning(f"📋 Error logging request details: {e}")
    
    async def render_get(self, request):
        """Handle GET requests for endpoint discovery"""
        self._log_request_details(request, "GET")
        
        try:
            client_addr = getattr(request, 'remote', 'unknown')
            logger.info(f"📋 CoAP GET request from {client_addr} - providing endpoint info")
            
            info = {
                "service": "Smart Greenhouse CoAP Server",
                "version": "1.0",
                "endpoints": {
                    "POST /sensor/send-data": "Send sensor data with auth in query params",
                    "POST /sensor/data": "Alternative sensor data endpoint", 
                    "POST /data": "Simple data endpoint",
                    "POST /sensor": "Sensor endpoint",
                    "POST /": "Root endpoint"
                },
                "auth": "Use query parameters: ?api_key=KEY&node_id=NODE_ID",
                "payload": "JSON with sensor values: {\"temperature\":22.5,\"humidity\":65.0}"
            }
            
            response_payload = json.dumps(info, indent=2).encode('utf-8')
            logger.info(f"📋 GET Response: {len(response_payload)} bytes")
            return Message(code=Code.CONTENT, payload=response_payload)
            
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=b"Server error")
    
    async def render_post(self, request):
        """Handle POST requests to /sensor/send-data"""
        # Log comprehensive request details
        self._log_request_details(request, "POST")
        
        # Log incoming request with detailed path information
        try:
            client_addr = getattr(request, 'remote', 'unknown')
            # Get the actual URI path that was requested
            try:
                if hasattr(request, 'opt') and hasattr(request.opt, 'uri_path'):
                    path_segments = '/'.join(request.opt.uri_path) if request.opt.uri_path else '/'
                    logger.info(f"🎯 CoAP POST matched! Client: {client_addr}, Path: /{path_segments}")
                else:
                    logger.info(f"🎯 CoAP POST matched! Client: {client_addr}, Path: <root>")
            except Exception as path_error:
                logger.warning(f"⚠️ Could not determine requested path: {path_error}")
                logger.info(f"🎯 CoAP POST matched! Client: {client_addr}, Path: unknown")
        except Exception as addr_error:
            logger.warning(f"⚠️ Could not determine client address: {addr_error}")
            client_addr = 'unknown'
        
        try:
            # Extract API key from query parameters or payload
            api_key = None
            node_id = None
            
            # Try to get API key from query parameters with error handling
            query_params = {}
            try:
                if request.opt.uri_query:
                    for param in request.opt.uri_query:
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = value
                    api_key = query_params.get('api_key')
                    node_id = query_params.get('node_id')
            except (AttributeError, UnicodeDecodeError, ValueError) as query_error:
                logger.warning(f"⚠️ Error parsing query parameters: {query_error}")
                # Continue without query params
            
            # Parse JSON payload with enhanced error handling
            try:
                if not request.payload:
                    logger.warning(f"⚠️ Empty payload received from {client_addr}")
                    return Message(code=Code.BAD_REQUEST, payload=b"Empty payload")
                
                # Attempt to decode payload as UTF-8
                try:
                    payload_str = request.payload.decode('utf-8')
                except UnicodeDecodeError as unicode_error:
                    logger.error(f"❌ Invalid UTF-8 payload from {client_addr}: {unicode_error}")
                    logger.error(f"🔍 Raw payload bytes: {request.payload[:50]}...")  # Log first 50 bytes
                    return Message(code=Code.BAD_REQUEST, payload=b"Invalid UTF-8 encoding in payload")
                
                # Parse JSON
                payload = json.loads(payload_str)
                logger.info(f"📦 CoAP payload received: {json.dumps(payload, indent=2)}")
                
            except json.JSONDecodeError as json_error:
                logger.error(f"❌ Invalid JSON payload from {client_addr}: {json_error}")
                logger.error(f"🔍 Payload content: {request.payload.decode('utf-8', errors='replace')[:200]}...")
                return Message(code=Code.BAD_REQUEST, payload=b"Invalid JSON payload")
            except Exception as payload_error:
                logger.error(f"❌ Unexpected payload error from {client_addr}: {payload_error}")
                return Message(code=Code.BAD_REQUEST, payload=b"Payload processing error")
            
            # Get API key and node_id from payload if not in query
            if not api_key:
                api_key = payload.get('api_key')
            if not node_id:
                node_id = payload.get('node_id')
            
            # For IoT devices that send clean sensor data, require auth via query params
            if not api_key or not node_id:
                logger.warning(f"🚫 Missing API key or node ID in CoAP request from {client_addr}")
                logger.info(f"💡 Hint: For clean sensor payloads, use query parameters: /sensor/send-data?api_key=KEY&node_id=NODE")
                return Message(code=Code.UNAUTHORIZED, payload=b"Missing API key or node ID. Use query parameters: ?api_key=KEY&node_id=NODE")
            
            # Verify API key and get node
            async with get_db_session() as db:
                logger.info(f"🔐 Authenticating node: {node_id} with API key: {api_key[:8]}...")
                node = await self.verify_node_auth(db, api_key, node_id)
                if not node:
                    logger.warning(f"❌ Authentication failed for node: {node_id}")
                    return Message(code=Code.UNAUTHORIZED, payload=b"Invalid API key or node ID")
                
                # Process sensor data
                logger.info(f"🔄 Processing sensor data for node: {node_id}")
                result = await self.process_sensor_data(db, node, payload)
                
                if result['success']:
                    response_payload = json.dumps({
                        "status": "success",
                        "message": f"Processed {result['readings_count']} sensor readings",
                        "timestamp": datetime.utcnow().isoformat()
                    }).encode('utf-8')
                    
                    logger.info(f"✅ CoAP SUCCESS: Processed {result['readings_count']} readings from node {node_id}")
                    logger.info(f"📤 Response Size: {len(response_payload)} bytes")
                    logger.info(f"📤 Response Code: 2.01 Created")
                    logger.info(f"📤 Response Content: {response_payload.decode('utf-8')}")
                    return Message(code=Code.CREATED, payload=response_payload)
                else:
                    logger.error(f"❌ CoAP ERROR: {result['message']} for node {node_id}")
                    error_payload = json.dumps({
                        "status": "error",
                        "message": result['message']
                    }).encode('utf-8')
                    logger.info(f"📤 Error Response Size: {len(error_payload)} bytes")
                    logger.info(f"📤 Error Response Code: 5.00 Internal Server Error")
                    logger.info(f"📤 Error Response Content: {error_payload.decode('utf-8')}")
                    return Message(code=Code.INTERNAL_SERVER_ERROR, payload=error_payload)
                    
        except Exception as e:
            logger.error(f"💥 CoAP EXCEPTION: {str(e)} from {client_addr}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            logger.error(f"🔍 Exception details: {repr(e)}")
            
            # Log stack trace for debugging
            import traceback
            logger.error(f"🔍 Stack trace: {traceback.format_exc()}")
            
            error_payload = json.dumps({
                "status": "error",
                "message": "Internal server error"
            }).encode('utf-8')
            
            logger.info(f"📤 Exception Response Size: {len(error_payload)} bytes")
            logger.info(f"📤 Exception Response Code: 5.00 Internal Server Error")
            logger.info(f"📤 Exception Response Content: {error_payload.decode('utf-8')}")
            return Message(code=Code.INTERNAL_SERVER_ERROR, payload=error_payload)
    
    async def verify_node_auth(self, db: AsyncSession, api_key: str, node_id: str) -> Optional[Node]:
        """Verify API key and return node if valid"""
        try:
            query = select(Node).where(
                and_(
                    Node.api_key == api_key,
                    Node.node_id == node_id
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error during node auth: {e}")
            return None
    
    async def process_sensor_data(self, db: AsyncSession, node: Node, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data and create readings"""
        # Count actual sensor values (exclude metadata)
        sensor_values = [k for k, v in data.items() if v is not None and k not in ['node_id', 'api_key', 'timestamp', 'zone_id', 'meta_data']]
        logger.info(f"📊 Processing sensor data for node {node.node_id} with {len(sensor_values)} sensor values: {sensor_values}")
        
        try:
            readings_created = 0
            # Use provided timestamp or current time for ESP32 devices
            reading_time = datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
            zone_id = data.get('zone_id')  # Optional for ESP32 devices
            
            # Sensor type mappings
            sensor_mappings = {
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "soil_moisture": data.get("soil_moisture"),
                "light": data.get("light"),
                "ph": data.get("ph"),
                "ec": data.get("ec"),
                "battery_percentage": data.get("battery_percentage"),
                "signal_strength": data.get("signal_strength"),
                "voltage": data.get("voltage")
            }
            
            for sensor_type, value in sensor_mappings.items():
                if value is not None:
                    # Find active sensor of this type for the node
                    sensor_query = select(Sensor).where(
                        and_(
                            Sensor.node_id == node.node_id,
                            Sensor.sensor_type == sensor_type,
                            Sensor.is_active == True
                        )
                    ).limit(1)
                    
                    sensor_result = await db.execute(sensor_query)
                    sensor = sensor_result.scalar_one_or_none()
                    
                    if sensor:
                        # Apply calibration
                        calibrated_value = (float(value) * float(sensor.calibration_multiplier)) + float(sensor.calibration_offset)
                        logger.debug(f"📈 {sensor_type}: {value} → {calibrated_value} (calibrated)")
                        
                        # Determine unit based on sensor type
                        unit_map = {
                            "temperature": "°C",
                            "humidity": "%",
                            "soil_moisture": "%",
                            "light": "lux",
                            "ph": "pH",
                            "ec": "μS/cm",
                            "battery_percentage": "%",
                            "signal_strength": "dBm",
                            "voltage": "V"
                        }
                        
                        # Create sensor reading
                        reading = SensorReading(
                            time=reading_time,
                            node_id=node.node_id,
                            zone_id=zone_id or sensor.zone_id,
                            sensor_id=sensor.sensor_id,
                            sensor_type=sensor_type,
                            value=calibrated_value,
                            unit=unit_map.get(sensor_type, ""),
                            quality=DataQuality.good,
                            meta_data=data.get('meta_data', {})
                        )
                        
                        db.add(reading)
                        readings_created += 1
                        logger.debug(f"💾 Created reading: {sensor_type} = {calibrated_value} {unit_map.get(sensor_type, '')}")
                    else:
                        logger.warning(f"⚠️ No active sensor found for type {sensor_type} on node {node.node_id}")
            
            if readings_created > 0:
                # Update node last_seen timestamp
                node.last_seen = reading_time
                await db.commit()
                logger.info(f"💿 Database commit successful: {readings_created} readings saved for node {node.node_id}")
                
                return {
                    "success": True,
                    "readings_count": readings_created,
                    "message": f"Successfully processed {readings_created} sensor readings"
                }
            else:
                logger.warning(f"⚠️ No valid sensor data found to process for node {node.node_id}")
                return {
                    "success": False,
                    "readings_count": 0,
                    "message": "No valid sensor data found to process"
                }
                
        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Database error processing sensor data for node {node.node_id}: {str(e)}")
            return {
                "success": False,
                "readings_count": 0,
                "message": f"Error processing sensor data: {str(e)}"
            }

class CoAPServerService(BaseService):
    """CoAP Server for IoT device communication"""
    
    def __init__(self, host='0.0.0.0', port=5683, log_protocol_errors=True):
        super().__init__()
        self.host = host
        self.port = port
        self.context = None
        self.server_task = None
        self.log_protocol_errors = log_protocol_errors
    
    async def start(self):
        """Start the CoAP server"""
        try:
            # Create CoAP context
            root = resource.Site()
            
            # Add sensor data resource - support multiple common paths
            sensor_resource = SensorDataResource()
            
            # Primary endpoint
            root.add_resource(['sensor', 'send-data'], sensor_resource)
            
            # Alternative endpoints that ESP32 devices might use
            root.add_resource(['sensor', 'data'], sensor_resource)
            root.add_resource(['data'], sensor_resource)
            root.add_resource(['sensor'], sensor_resource)
            root.add_resource([''], sensor_resource)  # Root endpoint
            
            # Add catch-all resource to log unmatched requests (this helps debug NotFound errors)
            catch_all = CatchAllResource()
            # Common paths that might be requested but not handled
            root.add_resource(['api'], catch_all)
            root.add_resource(['coap'], catch_all) 
            root.add_resource(['sensors'], catch_all)  # plural form
            root.add_resource(['device'], catch_all)
            root.add_resource(['submit'], catch_all)
            
            # Create and bind context with error handling
            self.context = await Context.create_server_context(
                root, 
                bind=(self.host, self.port)
            )
            
            # Set up exception handling for the context
            if hasattr(self.context, 'loop'):
                self.context.loop.set_exception_handler(self._handle_exception)
            
            logger.info(f"🚀 CoAP server started on {self.host}:{self.port}")
            logger.info(f"� Log protocol errors: {self.log_protocol_errors}")
            logger.info("�📋 Available endpoints:")
            logger.info(f"  📨 POST coap://{self.host}:{self.port}/sensor/send-data")
            logger.info(f"  📨 POST coap://{self.host}:{self.port}/sensor/data")
            logger.info(f"  📨 POST coap://{self.host}:{self.port}/data")
            logger.info(f"  📨 POST coap://{self.host}:{self.port}/sensor")
            logger.info(f"  📨 POST coap://{self.host}:{self.port}/")
            logger.info("📋 Catch-all endpoints for debugging:")
            logger.info(f"  🔍 /api, /coap, /sensors, /device, /submit")
            logger.info("📋 All requests will be logged in detail!")
            
            # Return immediately - server will run in background
            return self.context
            
        except Exception as e:
            logger.error(f"💥 Failed to start CoAP server: {e}")
            raise
    
    def _handle_exception(self, loop, context):
        """Handle uncaught exceptions in the CoAP server"""
        exception = context.get('exception')
        if exception:
            if isinstance(exception, UnicodeDecodeError):
                # Only log protocol errors if enabled
                if self.log_protocol_errors:
                    # Rate-limited logging for UTF-8 errors to reduce log noise
                    rate_limiter.log_if_allowed(
                        'unicode_error',
                        lambda msg: logger.warning(msg),
                        f"🔍 CoAP Protocol Error: Invalid UTF-8 data received - {exception}"
                    )
                    rate_limiter.log_if_allowed(
                        'unicode_tip',
                        lambda msg: logger.info(msg),
                        "💡 This often happens when non-CoAP clients connect to the CoAP port (logged once per minute)"
                    )
                # Always log at debug level for troubleshooting
                logger.debug(f"🔍 CoAP Protocol Error (debug): Invalid UTF-8 data - {exception}")
            elif isinstance(exception, (ConnectionError, OSError)):
                if self.log_protocol_errors:
                    rate_limiter.log_if_allowed(
                        'network_error',
                        lambda msg: logger.warning(msg),
                        f"🌐 CoAP Network Error: {exception}"
                    )
                logger.debug(f"🌐 CoAP Network Error (debug): {exception}")
            else:
                logger.error(f"💥 CoAP Server Exception: {exception}")
                logger.error(f"🔍 Context: {context}")
        else:
            logger.error(f"💥 CoAP Server Error: {context}")
    
    async def stop(self):
        """Stop the CoAP server"""
        if self.context:
            await self.context.shutdown()
            logger.info("🛑 CoAP server stopped")

# Global CoAP server instance
# Set log_protocol_errors=False to suppress common protocol warnings
import os
suppress_protocol_warnings = os.getenv('COAP_SUPPRESS_PROTOCOL_WARNINGS', 'false').lower() == 'true'
coap_server = CoAPServerService(log_protocol_errors=not suppress_protocol_warnings)

async def start_coap_server():
    """Start the CoAP server (for use with FastAPI lifespan)"""
    await coap_server.start()

async def stop_coap_server():
    """Stop the CoAP server (for use with FastAPI lifespan)"""
    await coap_server.stop()
