"""MCP server main module."""

import os

# Import configuration
from .config import (
    get_myscale_config,
    get_chdb_config,
    get_pgvector_config,
    get_mcp_config,
    get_text_to_vec_sql_config,
    TransportType,
)

# Import service modules
from . import myscaledb
from . import chdb
from . import pgvector
from . import text2vecsql

# Handle truststore
if os.getenv("MCP_TRUSTSTORE_DISABLE", None) != "1":
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:
        pass


__all__ = [
    "myscaledb",
    "chdb",
    "pgvector",
    "text2vecsql",
    "get_myscale_config",
    "get_chdb_config",
    "get_pgvector_config",
    "get_mcp_config",
    "get_text_to_vec_sql_config",
    "TransportType",
]
