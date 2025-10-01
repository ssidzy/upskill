"""
FastMCP 2.0 HTTPS Client Implementation Example
This demonstrates how to connect to and interact with a FastMCP server over HTTPS.
"""

import asyncio
import json
from typing import Dict, Any, List
from fastmcp import Client

# Server configuration
SERVER_URL = "http://localhost:8000/mcp"  # Change to https:// for HTTPS
HEADERS = {
    "User-Agent": "FastMCP-Demo-Client/2.0",
    "Accept": "application/json"
}

class MCPClient:
    """FastMCP 2.0 Client wrapper with convenient methods"""
    
    def __init__(self, server_url: str, headers: Dict[str, str] = None):
        self.server_url = server_url
        self.headers = headers or {}
        self.client = Client(server_url, headers=self.headers)
    
    async def connect_and_explore(self):
        """Connect to server and explore its capabilities"""
        async with self.client:
            print(f"🔗 Connected to: {self.server_url}")
            print(f"📡 Connection status: {self.client.is_connected()}")
            
            # List available capabilities
            await self.list_capabilities()
            
            # Demonstrate tool usage
            await self.demo_tools()
            
            # Demonstrate resource access
            await self.demo_resources()
            
            # Demonstrate prompt usage
            await self.demo_prompts()
            
            print(f"🔌 Disconnected from server")
    
    async def list_capabilities(self):
        """List all server capabilities"""
        print("\n" + "="*50)
        print("📋 SERVER CAPABILITIES")
        print("="*50)
        
        # List tools
        tools = await self.client.list_tools()
        print(f"\n🔧 Available Tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name} - {tool.description}")
        
        # List resources
        try:
            resources = await self.client.list_resources()
            print(f"\n📊 Available Resources ({len(resources)}):")
            for i, resource in enumerate(resources, 1):
                print(f"  {i}. {resource.uri} - {resource.description or 'No description'}")
        except Exception as e:
            print(f"\n📊 Resources: Could not list ({e})")
        
        # List prompts
        try:
            prompts = await self.client.list_prompts()
            print(f"\n💬 Available Prompts ({len(prompts)}):")
            for i, prompt in enumerate(prompts, 1):
                print(f"  {i}. {prompt.name} - {prompt.description or 'No description'}")
        except Exception as e:
            print(f"\n💬 Prompts: Could not list ({e})")
    
    async def demo_tools(self):
        """Demonstrate tool usage"""
        print("\n" + "="*50)
        print("🔧 TOOL DEMONSTRATIONS")
        print("="*50)
        
        try:
            # Simple math tool
            print("\n1️⃣ Testing add_numbers tool:")
            result = await self.client.call_tool("add_numbers", {"a": 15, "b": 27})
            print(f"   15 + 27 = {result}")
            
            # List users tool (structured output)
            print("\n2️⃣ Testing list_users tool (structured output):")
            users = await self.client.call_tool("list_users", {})
            print(f"   Retrieved {len(users)} users:")
            for user in users[:2]:  # Show first 2 users
                print(f"     - {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
            
            # Get specific user
            print("\n3️⃣ Testing get_user_by_id tool:")
            user = await self.client.call_tool("get_user_by_id", {"user_id": "1"})
            print(f"   User 1: {user.get('name')} - {user.get('role')}")
            
            # Create new task
            print("\n4️⃣ Testing create_task tool:")
            task = await self.client.call_tool("create_task", {
                "title": "Test MCP Integration",
                "user_id": "2",
                "status": "in_progress"
            })
            print(f"   Created task: {task.get('title')} (ID: {task.get('id')})")
            
            # Get weather (async tool)
            print("\n5️⃣ Testing get_weather_info tool (async):")
            weather = await self.client.call_tool("get_weather_info", {"city": "London"})
            print(f"   Weather in {weather.get('city')}: {weather.get('temperature')}°C, {weather.get('condition')}")
            
            # Calculate Fibonacci
            print("\n6️⃣ Testing calculate_fibonacci tool:")
            fib_result = await self.client.call_tool("calculate_fibonacci", {"n": 10})
            sequence = fib_result.get('sequence', [])
            print(f"   First 10 Fibonacci numbers: {sequence}")
            print(f"   Last number: {fib_result.get('last_number')}")
            
        except Exception as e:
            print(f"❌ Tool error: {e}")
    
    async def demo_resources(self):
        """Demonstrate resource access"""
        print("\n" + "="*50)
        print("📊 RESOURCE DEMONSTRATIONS")
        print("="*50)
        
        try:
            # Get all users resource
            print("\n1️⃣ Reading users://list resource:")
            users_resource = await self.client.read_resource("users://list")
            users_data = json.loads(users_resource)
            print(f"   Found {len(users_data)} users in resource")
            
            # Get specific user resource
            print("\n2️⃣ Reading users://1 resource:")
            user_resource = await self.client.read_resource("users://1")
            user_data = json.loads(user_resource)
            print(f"   User 1: {user_data.get('name')} ({user_data.get('email')})")
            
            # Get tasks resource
            print("\n3️⃣ Reading tasks://list resource:")
            tasks_resource = await self.client.read_resource("tasks://list")
            tasks_data = json.loads(tasks_resource)
            print(f"   Found {len(tasks_data)} tasks in resource")
            
            # Get user-specific tasks
            print("\n4️⃣ Reading tasks://user/1 resource:")
            user_tasks_resource = await self.client.read_resource("tasks://user/1")
            user_tasks_data = json.loads(user_tasks_resource)
            print(f"   User 1 has {len(user_tasks_data)} tasks")
            
            # Get server config
            print("\n5️⃣ Reading config://settings resource:")
            config_resource = await self.client.read_resource("config://settings")
            config_data = json.loads(config_resource)
            print(f"   Server: {config_data.get('server_name')} v{config_data.get('version')}")
            print(f"   Transport: {config_data.get('transport')}")
            
        except Exception as e:
            print(f"❌ Resource error: {e}")
    
    async def demo_prompts(self):
        """Demonstrate prompt usage"""
        print("\n" + "="*50)
        print("💬 PROMPT DEMONSTRATIONS")  
        print("="*50)
        
        try:
            # Get user summary prompt
            print("\n1️⃣ Getting User Summary prompt:")
            prompt_result = await self.client.get_prompt("User Summary", {"user_id": "1"})
            print(f"   Generated prompt length: {len(prompt_result)} characters")
            print(f"   Prompt preview: {prompt_result[:150]}...")
            
            # Get task planning prompt
            print("\n2️⃣ Getting Task Planning prompt:")
            prompt_result = await self.client.get_prompt("Task Planning", {
                "user_id": "2", 
                "project": "FastMCP Integration"
            })
            print(f"   Generated prompt length: {len(prompt_result)} characters")
            print(f"   Prompt preview: {prompt_result[:150]}...")
            
        except Exception as e:
            print(f"❌ Prompt error: {e}")

async def main():
    """Main client demonstration"""
    print("🚀 FastMCP 2.0 HTTPS Client Demo")
    print("="*50)
    
    # Create client instance
    client = MCPClient(SERVER_URL, HEADERS)
    
    try:
        # Connect and demonstrate all features
        await client.connect_and_explore()
        
    except ConnectionError:
        print("❌ Could not connect to server!")
        print("💡 Make sure the FastMCP server is running at:", SERVER_URL)
        print("💡 Start the server with: python fastmcp_https_server.py")
        
    except Exception as e:
        print(f"❌ Client error: {e}")

if __name__ == "__main__":
    # Run the client demo
    asyncio.run(main())
