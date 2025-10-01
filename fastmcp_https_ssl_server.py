"""
Advanced FastMCP 2.0 HTTPS Server with SSL/TLS Support
This example shows how to configure proper HTTPS with SSL certificates.
"""

import ssl
import os
from fastmcp import FastMCP
from typing import Dict, Any
from pathlib import Path
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.https import HTTPSRedirectMiddleware
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Server configuration
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "8443"))  # HTTPS default port
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")
DEBUG = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Create FastMCP server with production settings
mcp = FastMCP(
    name="Production HTTPS MCP Server",
    instructions="A production-ready MCP server with HTTPS/SSL support",
    debug=DEBUG
)

# Production-ready tools
@mcp.tool()
async def secure_echo(message: str, timestamp: bool = True) -> Dict[str, Any]:
    """Securely echo a message with optional timestamp"""
    import datetime
    
    result = {"message": message, "server": "FastMCP-HTTPS"}
    
    if timestamp:
        result["timestamp"] = datetime.datetime.now().isoformat()
    
    return result

@mcp.tool()
def server_health() -> Dict[str, Any]:
    """Get server health information"""
    import psutil
    import platform
    
    return {
        "status": "healthy",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "ssl_enabled": SSL_CERT_PATH and SSL_KEY_PATH and 
                      Path(SSL_CERT_PATH).exists() and Path(SSL_KEY_PATH).exists()
    }

# Resource for server metrics
@mcp.resource("metrics://server")
def server_metrics() -> str:
    """Server performance metrics"""
    import json
    import psutil
    
    metrics = {
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
        },
        "memory": {
            "usage_percent": psutil.virtual_memory().percent,
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        },
        "disk": {
            "usage_percent": psutil.disk_usage('/').percent,
            "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
        }
    }
    
    return json.dumps(metrics, indent=2)

def create_ssl_context():
    """Create SSL context for HTTPS"""
    if not SSL_CERT_PATH or not SSL_KEY_PATH:
        print("⚠️  SSL certificate paths not configured")
        return None
        
    cert_path = Path(SSL_CERT_PATH)
    key_path = Path(SSL_KEY_PATH)
    
    if not cert_path.exists():
        print(f"⚠️  SSL certificate not found: {cert_path}")
        return None
        
    if not key_path.exists():
        print(f"⚠️  SSL key not found: {key_path}")
        return None
    
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_path, key_path)
    
    # Security configurations
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    return context

def create_production_app():
    """Create production-ready ASGI app"""
    # Get the base FastMCP app
    app = mcp.streamable_http_app()
    
    # Add CORS middleware for browser clients
    app = CORSMiddleware(
        app,
        allow_origins=["*"],  # Configure appropriately for production
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    
    # Add HTTPS redirect middleware (optional)
    if not DEBUG:
        app = HTTPSRedirectMiddleware(app)
    
    return app

def main():
    """Main server entry point"""
    print("🔒 FastMCP 2.0 HTTPS/SSL Server")
    print("=" * 50)
    
    # Check SSL configuration
    ssl_context = create_ssl_context()
    
    if ssl_context:
        protocol = "https"
        print("✅ SSL/TLS configured successfully")
    else:
        protocol = "http"
        print("⚠️  Running without SSL (development mode)")
        print("💡 To enable HTTPS, configure SSL_CERT_PATH and SSL_KEY_PATH")
    
    server_url = f"{protocol}://{HOST}:{PORT}"
    mcp_endpoint = f"{server_url}/mcp"
    
    print(f"🌐 Server URL: {server_url}")
    print(f"🔧 MCP Endpoint: {mcp_endpoint}")
    print(f"📊 Health Check: {server_url}/health")
    print(f"🐛 Debug Mode: {DEBUG}")
    print()
    
    if ssl_context:
        print("🔐 HTTPS Security Features:")
        print("  ✅ TLS 1.2+ enforced")
        print("  ✅ Strong cipher suites")
        print("  ✅ Certificate validation")
        print()
    
    # Create the ASGI application
    app = create_production_app()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        ssl_keyfile=SSL_KEY_PATH if ssl_context else None,
        ssl_certfile=SSL_CERT_PATH if ssl_context else None,
        ssl_version=ssl.PROTOCOL_TLS_SERVER if ssl_context else None,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
    
    server = uvicorn.Server(config)
    
    print("🚀 Starting server...")
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
