# MyScaleDB MCP Server

An MCP server for MyScaleDB, PgVector - combining analytical database power with vector search capabilities.

## Features

### MyScaleDB Tools

* `run_select_query`
  * Execute standard SQL SELECT queries on your MyScaleDB cluster.
  * Input: `query` (string): The SQL SELECT query to execute.
  * Best for regular data analysis and aggregation queries.
  * All MyScaleDB queries are run with `readonly = 1` to ensure they are safe.

* `run_similarity_select_query`
  * Execute SELECT queries with vector search and full-text search capabilities.
  * Input: `query` (string): The SQL query with distance(), TextSearch(), or HybridSearch() functions.
  * Best for similarity search, semantic search, and hybrid search queries.
  * Supports: distance(), TextSearch(), HybridSearch() functions.

* `list_databases`
  * List all databases on your MyScaleDB cluster.

* `list_tables`
  * List all tables in a database.
  * Input: `database` (string): The name of the database.

### chDB Tools

* `run_chdb_select_query`
  * Execute SQL queries using [chDB](https://github.com/chdb-io/chdb)'s embedded ClickHouse engine.
  * Input: `sql` (string): The SQL query to execute.
  * Query data directly from various sources (files, URLs, databases) without ETL processes.

### pgvector Tools

* `run_pgvector_select_query`
  * Execute SELECT queries on PostgreSQL with pgvector extension
* `list_pgvector_tables`
  * List all tables in the PostgreSQL database
* `list_pgvector_vectors`
  * List all vector columns and their dimensions
* `search_similar_vectors`
  * Perform similarity search using vector embeddings

### Health Check Endpoint

When running with HTTP or SSE transport, a health check endpoint is available at `/health`. This endpoint:
- Returns `200 OK` with the MyScaleDB version if the server is healthy and can connect to MyScaleDB
- Returns `503 Service Unavailable` if the server cannot connect to MyScaleDB

Example:
```bash
curl http://localhost:8000/health
# Response: OK - Connected to MyScaleDB 24.3.1
```

## Configuration

