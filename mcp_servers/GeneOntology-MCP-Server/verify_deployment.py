import asyncio
import argparse
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='Cloud Run URL (without /sse suffix)')
    args = parser.parse_args()

    sse_url = f"{args.url}/sse"
    print(f"Connecting to {sse_url}...")

    async with sse_client(sse_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected!")
            
            tools = await session.list_tools()
            print(f"Tools available: {[t.name for t in tools.tools]}")
            
            # Test a tool
            print("Testing search_go_terms...")
            result = await session.call_tool("search_go_terms", arguments={"query": "mitochondria", "size": 1})
            print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
