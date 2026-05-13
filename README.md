# MCP Server

This repository contains a local MCP server (`mcp_server.py`) with file organization tools and Gmail API support.

## Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Place `credentials.json` in the same directory as `mcp_server.py`.
3. Run the Gmail tool once to authenticate and generate `token.json`.

## Notes

- `credentials.json` must be downloaded from Google Cloud Console.
- `token.json` is created automatically after the first successful Gmail OAuth login.
