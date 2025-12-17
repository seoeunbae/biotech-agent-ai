
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
import sys


async def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_deployment.py <url> [token]")
        sys.exit(1)

    url = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    sse_url = f"{url}/sse"
    print(f"Connecting to {sse_url}...")
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("Using Bearer token for authentication")

    try:
        async with sse_client(sse_url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected and initialized!")
                
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"- {tool.name}: {tool.description[:50]}...")
                
    except Exception as e:
        print(f"Error: {e}")
        # Print clearer error if it's a 403/401
        if "403" in str(e) or "401" in str(e):
             print("\nRecommendation: Provide a valid OIDC token as the second argument.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
