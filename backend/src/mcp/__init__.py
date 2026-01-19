"""
MCP (Model Context Protocol) Client Module
Provides interface to MCP tools.
"""

from .mcp_client import MCPClient, get_mcp_client

__all__ = ["MCPClient", "get_mcp_client"]
