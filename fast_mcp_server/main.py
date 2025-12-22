"""
name: Grep Search
title: Grep Search 
author: EntityCS
description: Search the entire project folder recursively with grep (shows file, line numbers and context).
required_open_webui_version: 0.4.0
requirements: fastmcp
icon: https://img.icons8.com/search
version: 0.0.2
licence: MIT
"""
import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType
#, HTTPRoute

# ----------------------------------------------------------------------
# Server definition
# ----------------------------------------------------------------------
# Use the service name from docker-compose as hostname
client = httpx.AsyncClient(base_url="http://doordash-drive:8000")

# Load the OpenAPI spec synchronously once
openapi_spec = httpx.get("http://doordash-drive:8000/openapi.json").json()

# Create the MCP server
server = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    # route_map_fn=custom_route_mapper,
    name="Doordash Drive MCP"
)

if __name__ == "__main__":
    server.run(transport="http", host="0.0.0.0", port=8000)
