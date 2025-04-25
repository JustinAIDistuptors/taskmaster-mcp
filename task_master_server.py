#!/usr/bin/env python3
"""
Task Master MCP Server
This file implements a simple MCP server for task management.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import secrets
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("taskmaster-mcp")

# Create FastAPI app
app = FastAPI(title="Task Master MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up HTTP Basic Auth
security = HTTPBasic()

# Authentication credentials
USERNAME = "instabids"
PASSWORD = "secure123password"

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    is_username_correct = secrets.compare_digest(credentials.username, USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, PASSWORD)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

# In-memory task storage
tasks = {
    "task-001": {
        "id": "task-001",
        "title": "Implement MCP server",
        "description": "Create a working MCP server implementation",
        "status": "in_progress",
        "priority": "high",
        "created_at": "2025-04-24T12:00:00Z",
        "due_date": "2025-04-26T12:00:00Z"
    },
    "task-002": {
        "id": "task-002",
        "title": "Test relay proxy",
        "description": "Test the relay proxy with the MCP server",
        "status": "pending",
        "priority": "medium",
        "created_at": "2025-04-24T12:30:00Z",
        "due_date": "2025-04-27T12:00:00Z"
    }
}

# Handler functions
def handle_list_tasks(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """List all tasks"""
    return {"tasks": list(tasks.values())}

def handle_get_task(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Get a specific task by ID"""
    task_id = parameters.get("task_id")
    if not task_id:
        return {"error": "task_id parameter is required"}
    
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Task with ID {task_id} not found"}
    
    return {"task": task}

def handle_create_task(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new task"""
    title = parameters.get("title")
    if not title:
        return {"error": "title parameter is required"}
    
    description = parameters.get("description", "")
    priority = parameters.get("priority", "medium")
    due_date = parameters.get("due_date")
    
    task_id = f"task-{str(uuid.uuid4())[:8]}"
    created_at = datetime.now().isoformat()
    
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "status": "pending",
        "priority": priority,
        "created_at": created_at,
        "due_date": due_date
    }
    
    tasks[task_id] = task
    
    return {"task": task, "task_id": task_id}

def handle_update_task(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing task"""
    task_id = parameters.get("task_id")
    if not task_id:
        return {"error": "task_id parameter is required"}
    
    task = tasks.get(task_id)
    if not task:
        return {"error": f"Task with ID {task_id} not found"}
    
    # Update task fields
    for field in ["title", "description", "status", "priority", "due_date"]:
        if field in parameters:
            task[field] = parameters[field]
    
    return {"task": task}

def handle_delete_task(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a task"""
    task_id = parameters.get("task_id")
    if not task_id:
        return {"error": "task_id parameter is required"}
    
    if task_id not in tasks:
        return {"error": f"Task with ID {task_id} not found"}
    
    deleted_task = tasks.pop(task_id)
    
    return {"success": True, "deleted_task": deleted_task}

# Map of function names to handler functions
handler_map = {
    "list_tasks": handle_list_tasks,
    "get_task": handle_get_task,
    "create_task": handle_create_task,
    "update_task": handle_update_task,
    "delete_task": handle_delete_task
}

@app.post("/mcp/{function_name}")
async def handle_mcp_request(
    function_name: str,
    request: Request,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Handle MCP request"""
    try:
        # Parse request body
        body = await request.body()
        parameters = json.loads(body)
        
        # Log the request
        logger.info(f"Received request for function: {function_name}")
        logger.info(f"Parameters: {parameters}")
        
        # Check if function is supported
        if function_name not in handler_map:
            return {"error": f"Function {function_name} not supported"}
        
        # Call the handler function
        result = handler_map[function_name](parameters)
        logger.info(f"Result: {result}")
        
        return result
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return {"error": "Invalid JSON in request body"}
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return {"error": str(e)}

@app.get("/")
async def root():
    """Root endpoint that returns information about the server"""
    return {
        "name": "Task Master MCP Server",
        "version": "1.0.0",
        "description": "MCP server for task management",
        "functions": list(handler_map.keys())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Master MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--transport", type=str, default="http", help="Transport protocol (http or websocket)")
    
    args = parser.parse_args()
    
    if args.transport == "http":
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        logger.error(f"Transport {args.transport} not supported")
        exit(1)
