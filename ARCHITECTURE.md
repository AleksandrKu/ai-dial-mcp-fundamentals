# Architecture

## System Overview

```mermaid
graph TB
    User[👤 User] -->|Input| Agent[🤖 Agent]
    Agent -->|Chat API| DIAL[DIAL/OpenAI]
    Agent -->|MCP Protocol| MCP[MCP Server]
    MCP -->|Tool Results| Agent
    DIAL -->|Response + Tool Calls| Agent
    Agent -->|Output| User
```

**Agent** (`agent/`): Console app that orchestrates DIAL and MCP.  
**MCP Server** (`mcp_server/`): User management tools, flow diagram resource, and guidance prompts.

---

## Initialization Flow

```mermaid
sequenceDiagram
    participant App
    participant MCP as MCPClient
    participant Server as MCP Server
    participant DIAL as DialClient

    App->>MCP: streamable_http_client(url)
    MCP->>Server: initialize()
    Server-->>MCP: ServerCapabilities

    App->>MCP: get_resources() / get_tools() / get_prompts()
    MCP->>Server: list_resources, list_tools, list_prompts
    Server-->>MCP: Resources, Tools, Prompts

    App->>DIAL: DialClient(api_key, endpoint, tools, mcp_client)
    App->>MCP: get_prompt() for each prompt
    App->>App: Build message history (system + prompts)
```

---

## Chat Loop (with Tool Calling)

```mermaid
sequenceDiagram
    participant User
    participant App
    participant DIAL as DialClient
    participant MCP as MCPClient
    participant Server as MCP Server

    User->>App: Message
    App->>DIAL: get_completion(messages)

    alt AI returns tool calls
        DIAL->>MCP: call_tool(name, args)
        MCP->>Server: call_tool
        Server-->>MCP: Result
        MCP-->>DIAL: Result
        DIAL->>DIAL: get_completion(messages) [recursive]
    end

    DIAL-->>App: Message
    App-->>User: Response
```

---

## Components

| Component | Responsibility |
|-----------|----------------|
| **app.py** | Entry point, MCP setup, message history, chat loop |
| **MCPClient** | MCP connection via `streamable_http_client`, tools/resources/prompts |
| **DialClient** | DIAL/OpenAI chat, streaming, tool-call handling, delegates execution to MCPClient |
| **Message** | Chat message model (role, content, tool_calls, tool_call_id) |

---

## MCP Server Capabilities

| Type | Name | Description |
|------|------|--------------|
| **Tools** | get_user_by_id, search_user, add_user, update_user, delete_user | User CRUD and search |
| **Resource** | users-management://flow-diagram | Flow diagram (image/png) |
| **Prompts** | search_guidance, user_creation_guidance | Search and creation guidance |

---

## Tech Stack

- **Agent**: Python, asyncio
- **MCP**: `mcp` SDK, `streamable_http_client`
- **AI**: Azure OpenAI (`AsyncAzureOpenAI`)
- **MCP Server**: FastMCP, streamable HTTP transport
