from pathlib import Path
from typing import Optional, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt
from pydantic import AnyUrl


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, server_params: Optional[StdioServerParameters] = None) -> None:
        server_script = Path(__file__).resolve().parents[1] / "mcp_server" / "server.py"
        self.server_params = server_params or StdioServerParameters(
            command="python3",
            args=[str(server_script)],
        )
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None

    async def __aenter__(self):
        # Establish connection to MCP server using stdio transport
        self._stdio_context = stdio_client(self.server_params)
        read_stream, write_stream = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()

        init_result = await self.session.initialize()
        print(f"MCP Server initialized: {init_result}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Shutdown MCP client connections
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)

        if self._stdio_context:
            await self._stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        # Get available tools from MCP server and convert to DIAL/OpenAI format
        # 1. Call `await self.session.list_tools()` and assign to `tools`
        tools = await self.session.list_tools()

        # 2. Convert MCP tool schema to DIAL/OpenAI format
        # Return list with dicts in OpenAI function calling format
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        # Call tool on MCP server and return result
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)

        # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        content = tool_result.content[0]

        # 3. print(f"    ⚙️: {content}\n")
        print(f"    ⚙️: {content}\n")

        # 4. If `isinstance(content, TextContent)` -> return content.text, else -> return content
        if isinstance(content, TextContent):
            return content.text
        else:
            return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        # Get available resources from MCP server
        # Wrap into try/except (not all MCP servers have resources), get `list_resources` (it is async) and resources
        # from it. In case of error print error and return an empty array
        try:
            resources_result = await self.session.list_resources()
            return resources_result.resources
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        # Get available prompts from MCP server
        # Wrap into try/except (not all MCP servers have prompts), get `list_prompts` (it is async) and prompts
        # from it. In case of error print error and return an empty array
        try:
            prompts_result = await self.session.list_prompts()
            return prompts_result.prompts
        except Exception as e:
            print(f"Error getting prompts: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        # Get resource content by URI
        # 1. Get resource by uri (uri is that we provided on the Server side "users-management://flow-diagram")
        resource_result: ReadResourceResult = await self.session.read_resource(uri)

        # 2. Get contents of [0] resource
        content = resource_result.contents[0]

        # 3. ResourceContents has 2 types TextResourceContents and BlobResourceContents, in case if content is instance
        #    of TextResourceContents return its `text`, in case of BlobResourceContents return its `blob`
        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob
        else:
            return content

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        # Get prompt content by name
        # 1. Get prompt by name
        prompt_result: GetPromptResult = await self.session.get_prompt(name)

        # 2. Create variable `combined_content` with empty string
        combined_content = ""

        # 3. Iterate through prompt result `messages` and:
        #       - if `message` has attribute 'content' and is instance of TextContent then concat `combined_content`
        #          with `message.content.text + "\n"`
        #       - if `message` has attribute 'content' and is instance of `str` then concat `combined_content` with
        #          with `message.content + "\n"`
        for message in prompt_result.messages:
            if hasattr(message, 'content'):
                if isinstance(message.content, TextContent):
                    combined_content += message.content.text + "\n"
                elif isinstance(message.content, str):
                    combined_content += message.content + "\n"

        return combined_content
