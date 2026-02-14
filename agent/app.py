import asyncio
import json
import os

from mcp import Resource
from mcp.types import Prompt

from agent.mcp_client import MCPClient
from agent.dial_client import DialClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('DIAL_API_KEY', '')
DIAL_URL = os.getenv('DIAL_URL', '')
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', '')

if not API_KEY or not DIAL_URL or not MCP_SERVER_URL:
    raise ValueError("Missing required environment variables")

# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

async def main():
    # 1. Create MCP client and connect to MCP server
    async with MCPClient(mcp_server_url=MCP_SERVER_URL) as mcp_client:

        # 2. Get available MCP resources
        resources: list[Resource] = await mcp_client.get_resources()
        print(f"\n📦 Available Resources: {len(resources)}")
        for resource in resources:
            print(f"  - {resource.name}: {resource.uri}")

        # 3. Get available MCP tools
        tools = await mcp_client.get_tools()
        print(f"\n🔧 Available Tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['function']['name']}: {tool['function']['description']}")

        # 4. Create DialClient
        dial_client = DialClient(
            api_key=os.getenv("DIAL_API_KEY"),
            endpoint=os.getenv("DIAL_URL"),
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            tools=tools,
            mcp_client=mcp_client,
        )

        # 5. Create messages list with system prompt
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)
        ]

        # 6. Add prompts from MCP server as system-level guidance
        prompts: list[Prompt] = await mcp_client.get_prompts()
        print(f"\n💡 Available Prompts: {len(prompts)}")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
            prompt_content = await mcp_client.get_prompt(prompt.name)
            messages.append(Message(role=Role.SYSTEM, content=prompt_content))

        # 7. Create console chat
        print("\n" + "="*60)
        print("🤖 User Management Agent")
        print("Type 'exit' or 'quit' to end the conversation")
        print("="*60 + "\n")

        while True:
            # Get user input
            user_input = input("👤 You: ").strip()

            # Check for exit commands
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Goodbye!")
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Add user message to history
            messages.append(Message(role=Role.USER, content=user_input))

            # Get AI response
            ai_response = await dial_client.get_completion(messages)

            # Add AI response to message history
            messages.append(ai_response)

            print()  # Empty line for readability


if __name__ == "__main__":
    asyncio.run(main())
