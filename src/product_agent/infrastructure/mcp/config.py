import os

def sequential_mcp_server():
    return {
        "sequential-thinking": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-sequential-thinking"
            ]
        }
    }

def mcp_server_config():
    """Regular MCP Config"""

    MCP_SERVER_CONFIG = {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "@playwright/mcp@latest",
            ],
        },
        "sequential-thinking": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-sequential-thinking"
            ]
        },
    }

    return MCP_SERVER_CONFIG



def mcp_server_config_bright_data(bright_data_key: str):
    """Allow injection keys at run time"""
    if bright_data_key == "":
        raise ValueError("Api key is empty")

    MCP_SERVER_CONFIG = {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
        },
        "sequential-thinking": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-sequential-thinking"
            ]
        },
        "Bright Data": {
            "command": "npx",
            "args": ["@brightdata/mcp"],
            "env": {
                "API_TOKEN": bright_data_key,
                "PRO_MODE": "true",
            }
        }
    }

    return MCP_SERVER_CONFIG

