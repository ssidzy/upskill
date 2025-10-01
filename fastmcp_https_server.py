"""
FastMCP 2.0 HTTPS Server Implementation Example
This demonstrates a complete MCP server with HTTP/HTTPS transport,
tools, resources, and client interaction capabilities.
"""

from fastmcp import FastMCP
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio
import httpx

# Create the FastMCP server instance
mcp = FastMCP(
    name="Demo HTTPS MCP Server 🚀",
    instructions="A comprehensive demo server showcasing FastMCP 2.0 capabilities with HTTPS transport"
)

# Example data store (in production, use a proper database)
users_db = {
    "1": {"id": "1", "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
    "2": {"id": "2", "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
    "3": {"id": "3", "name": "Carol Davis", "email": "carol@example.com", "role": "user"}
}

tasks_db = {
    "1": {"id": "1", "title": "Setup MCP Server", "status": "completed", "user_id": "1"},
    "2": {"id": "2", "title": "Implement HTTPS", "status": "in_progress", "user_id": "1"},
    "3": {"id": "3", "title": "Test Client Connection", "status": "pending", "user_id": "2"}
}

# Pydantic models for structured output
class User(BaseModel):
    """User data model"""
    id: str
    name: str
    email: str
    role: str

class Task(BaseModel):
    """Task data model"""
    id: str
    title: str
    status: str
    user_id: str
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

class WeatherData(BaseModel):
    """Weather information structure"""
    city: str = Field(description="City name")
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str = Field(description="Weather condition")
    wind_speed: float = Field(description="Wind speed in km/h")

# =============================================================================
# TOOLS - Actions that can perform side effects
# =============================================================================

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers together"""
    return a + b

@mcp.tool()
def get_user_by_id(user_id: str) -> User:
    """Get a user by their ID - returns structured data"""
    user_data = users_db.get(user_id)
    if not user_data:
        raise ValueError(f"User with ID {user_id} not found")
    return User(**user_data)

@mcp.tool()
def create_task(title: str, user_id: str, status: str = "pending") -> Task:
    """Create a new task and return structured data"""
    if user_id not in users_db:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Generate new task ID
    new_id = str(max(int(k) for k in tasks_db.keys()) + 1)
    
    task_data = {
        "id": new_id,
        "title": title,
        "status": status,
        "user_id": user_id
    }
    
    tasks_db[new_id] = task_data
    return Task(**task_data)

@mcp.tool()
def list_users() -> List[User]:
    """List all users - returns structured data"""
    return [User(**user_data) for user_data in users_db.values()]

@mcp.tool()
async def get_weather_info(city: str) -> WeatherData:
    """Get weather information for a city (simulated API call)"""
    # Simulate API call delay
    await asyncio.sleep(0.5)
    
    # Simulated weather data (in real implementation, call weather API)
    weather_data = {
        "city": city,
        "temperature": 22.5,
        "humidity": 65.0,
        "condition": "Partly cloudy",
        "wind_speed": 12.3
    }
    
    return WeatherData(**weather_data)

@mcp.tool()
def calculate_fibonacci(n: int) -> Dict[str, Any]:
    """Calculate Fibonacci sequence up to n terms"""
    if n <= 0:
        return {"sequence": [], "count": 0}
    elif n == 1:
        return {"sequence": [0], "count": 1}
    elif n == 2:
        return {"sequence": [0, 1], "count": 2}
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return {
        "sequence": sequence,
        "count": n,
        "last_number": sequence[-1]
    }

# =============================================================================
# RESOURCES - Data endpoints (like GET requests)
# =============================================================================

@mcp.resource("users://list")
def get_users_resource() -> str:
    """Get all users as JSON resource"""
    return json.dumps(list(users_db.values()), indent=2)

@mcp.resource("users://{user_id}")
def get_user_resource(user_id: str) -> str:
    """Get specific user data as JSON resource"""
    user_data = users_db.get(user_id)
    if not user_data:
        return json.dumps({"error": f"User {user_id} not found"})
    return json.dumps(user_data, indent=2)

@mcp.resource("tasks://list")
def get_tasks_resource() -> str:
    """Get all tasks as JSON resource"""
    return json.dumps(list(tasks_db.values()), indent=2)

@mcp.resource("tasks://user/{user_id}")
def get_user_tasks_resource(user_id: str) -> str:
    """Get tasks for a specific user"""
    user_tasks = [task for task in tasks_db.values() if task["user_id"] == user_id]
    return json.dumps(user_tasks, indent=2)

@mcp.resource("config://settings")
def get_server_config() -> str:
    """Get server configuration"""
    config = {
        "server_name": "Demo HTTPS MCP Server",
        "version": "2.0.0",
        "transport": "HTTPS",
        "features": ["tools", "resources", "structured_output"],
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(config, indent=2)

# =============================================================================
# PROMPTS - Reusable templates for LLM interactions
# =============================================================================

@mcp.prompt(title="User Summary")
def user_summary_prompt(user_id: str) -> str:
    """Generate a prompt to summarize user information"""
    user_data = users_db.get(user_id)
    if not user_data:
        return f"No user found with ID: {user_id}"
    
    return f"""Please provide a summary of this user:
    
Name: {user_data['name']}
Email: {user_data['email']}
Role: {user_data['role']}
ID: {user_data['id']}

Include their role responsibilities and contact information in your summary."""

@mcp.prompt(title="Task Planning")
def task_planning_prompt(user_id: str, project: str = "General") -> str:
    """Generate a prompt for task planning"""
    return f"""Help plan tasks for project: {project}
    
Assigned to user ID: {user_id}

Please suggest a list of tasks that would be appropriate for this project, 
considering the user's role and current workload."""

# =============================================================================
# CUSTOM ROUTES (for HTTP transport)
# =============================================================================

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Health check endpoint"""
    return PlainTextResponse("OK", status_code=200)

@mcp.custom_route("/status", methods=["GET"])
async def server_status(request: Request) -> JSONResponse:
    """Server status endpoint"""
    status = {
        "server": "FastMCP 2.0 Demo Server",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(users_db),
        "tasks_count": len(tasks_db),
        "transport": "HTTP/HTTPS"
    }
    return JSONResponse(status)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting FastMCP 2.0 HTTPS Server...")
    print("Server features:")
    print("  ✅ Tools with structured output")
    print("  ✅ Resources for data access")
    print("  ✅ Prompts for LLM interactions") 
    print("  ✅ Custom HTTP routes")
    print("  ✅ HTTPS transport support")
    print()
    print("Available endpoints:")
    print("  🔧 Tools: add_numbers, get_user_by_id, create_task, list_users, get_weather_info, calculate_fibonacci")
    print("  📊 Resources: users://list, users://{id}, tasks://list, tasks://user/{id}, config://settings")
    print("  💬 Prompts: User Summary, Task Planning")
    print("  🌐 HTTP: /health, /status")
    print()
    print("Starting server on http://localhost:8000")
    print("MCP endpoint: http://localhost:8000/mcp")
    print("Health check: http://localhost:8000/health")
    print("Server status: http://localhost:8000/status")
    print()
    
    # Run server with HTTP transport (supports HTTPS with proper SSL certificates)
    mcp.run(transport="http", host="0.0.0.0", port=8000)
