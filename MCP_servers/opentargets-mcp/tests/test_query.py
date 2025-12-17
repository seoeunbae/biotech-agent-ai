
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
import sys
import json

async def main():
    if len(sys.argv) < 3:
        print("Usage: python test_query.py <url> <token> <query>")
        sys.exit(1)

    url = sys.argv[1]
    token = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else "lung cancer"
    
    sse_url = f"{url}/sse"
    print(f"Connecting to {sse_url}...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        async with sse_client(sse_url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected and initialized!")
                
                print(f"Searching for: {query}")
                result = await session.call_tool(
                    "search_entities",
                    arguments={"query_string": query, "entity_names": ["disease"]}
                )
                
                # Check structure of result.content
                # usually it's a list of TextContent or ImageContent
                # We expect TextContent with JSON string or similar
                
                if result.content:
                    for content in result.content:
                        if hasattr(content, "text"):
                            data = json.loads(content.text)
                            hits = data.get("search", {}).get("hits", [])
                            print(f"\nFound {len(hits)} hits:")
                            for hit in hits[:5]: # Show top 5
                                print(f"- [{hit.get('id')}] {hit.get('name')} (Score: {hit.get('score')})")
                                if hit.get('object', {}).get('description'):
                                     print(f"  Description: {hit['object']['description'][:100]}...")
                        else:
                            print(f"Non-text content: {content}")
                else:
                    print("No content returned.")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
