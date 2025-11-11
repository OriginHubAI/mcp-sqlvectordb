"""MCP server main entry point."""

import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# Support both relative and absolute imports
try:
    from .config import get_mcp_config, TransportType
except ImportError:
    from mcp_server.config import get_mcp_config, TransportType

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-sqlvectordb")

# Load environment variables
load_dotenv()

# Create MCP instance
MCP_SERVER_NAME = "mcp-sqlvectordb"
mcp = FastMCP(name=MCP_SERVER_NAME)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Health check endpoint for monitoring server status.

    Returns OK if the server is running and can connect to MyScaleDB.
    """
    try:
        # Check if MyScaleDB is enabled by trying to create config
        myscale_enabled = os.getenv("MYSCALE_ENABLED", "true").lower() == "true"
        pgvector_enabled = os.getenv("PGVECTOR_ENABLED", "false").lower() == "true"
        response = "OK - "
        if myscale_enabled:
            # Try to create a client connection to verify MyScaleDB connectivity
            try:
                from .myscaledb import create_myscale_client
            except ImportError:
                from mcp_server.myscaledb import create_myscale_client
            client = create_myscale_client()
            myscaledb_version = client.server_version
            response += f"Connected to MyScaleDB {myscaledb_version}"
        if pgvector_enabled:
            # Try to create a client connection to verify pgvector connectivity
            try:
                from .pgvector import create_pgvector_client
            except ImportError:
                from mcp_server.pgvector import create_pgvector_client
            client = create_pgvector_client()
            pgvector_version = client.server_version
            response += f"Connected to pgvector {pgvector_version}"
        return PlainTextResponse(response)
    except Exception as e:
        # Return 503 Service Unavailable if we can't connect to MyScaleDB or pgvector
        return PlainTextResponse(
            f"ERROR - Cannot connect to MyScaleDB or pgvector: {str(e)}", status_code=503
        )


def register_services():
    """Register all services based on configuration."""
    # Register MyScaleDB service
    if os.getenv("MYSCALE_ENABLED", "true").lower() == "true":
        try:
            from .myscaledb import register_tools as register_myscale_tools
        except ImportError:
            from mcp_server.myscaledb import register_tools as register_myscale_tools
        register_myscale_tools(mcp)
        logger.info("MyScaleDB service registered")

    # Register chDB service
    if os.getenv("CHDB_ENABLED", "false").lower() == "true":
        try:
            from .chdb import register_tools as register_chdb_tools
        except ImportError:
            from mcp_server.chdb import register_tools as register_chdb_tools
        register_chdb_tools(mcp)
        logger.info("chDB service registered")

    # Register pgvector service
    if os.getenv("PGVECTOR_ENABLED", "false").lower() == "true":
        try:
            from .pgvector import register_tools as register_pgvector_tools
        except ImportError:
            from mcp_server.pgvector import register_tools as register_pgvector_tools
        register_pgvector_tools(mcp)
        logger.info("pgvector service registered")
    
    if os.getenv("TEXT2VECSQL_ENABLED", "false").lower() == "true":
        try:
            from .text2vecsql import register_tools as register_text2vecsql_tools
        except ImportError:
            from mcp_server.text2vecsql import register_tools as register_text2vecsql_tools
        register_text2vecsql_tools(mcp)
        logger.info("Text to Vector SQL service registered")


def main():
    """Start the MCP server."""
    # Register all services
    register_services()

    # Get server configuration
    mcp_config = get_mcp_config()
    transport = mcp_config.server_transport

    # For HTTP and SSE transports, we need to specify host and port
    http_transports = [TransportType.HTTP.value, TransportType.SSE.value]
    if transport in http_transports:
        # Use the configured bind host (defaults to 127.0.0.1, can be set to 0.0.0.0)
        # and bind port (defaults to 8000)
        logger.info(
            f"Starting MCP server, transport={transport}, host={mcp_config.bind_host}, port={mcp_config.bind_port}"
        )
        mcp.run(transport=transport, host=mcp_config.bind_host, port=mcp_config.bind_port)
    else:
        # For stdio transport, no host or port is needed
        logger.info(f"Starting MCP server, transport={transport}")
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
