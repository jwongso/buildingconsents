"""MCP server entry point for NZ Building Consents.

Run via stdio (for Claude Desktop / Claude Code):
    python -m mcp_server

Claude Desktop config (~/.claude_desktop_config.json):
    {
      "mcpServers": {
        "nz-building": {
          "command": "python3",
          "args": ["-m", "mcp_server"],
          "cwd": "/path/to/buildingconsents"
        }
      }
    }

Tools exposed:
    lookup_building_zone  - geocode an address and return its district plan zone
    legal_search          - search NZ building legislation
    legal_ask             - full RAG answer with citations
    legal_get_source      - fetch a legislation section by ID
    legal_get_legislation - fetch a legislation section by ID (e.g. NZLEG/BA2004/s41)

Typical agent workflow:
    1. lookup_building_zone('123 Main St, Nelson') -> zone context
    2. legal_ask('[Zone context: Nelson Inner City - Centre]\n\nDo I need a consent for a deck?')
"""

from core.mcp import create_mcp_server
from app.jurisdiction import NZBuildingJurisdiction

server = create_mcp_server(NZBuildingJurisdiction())

if __name__ == "__main__":
    server.run("stdio")
