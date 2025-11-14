# How To Run

1. Configuare local service env:
```bash
cp .env.example .env
```

Modify ref env config


2. Run Mcp Server

```bash
# init runtime env
uv sync --all-extras --dev

# run mcp server
uv run python -m mcp_server.main
```

3. Regist Mcp Tools in Dify
