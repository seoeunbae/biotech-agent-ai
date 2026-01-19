import requests
import sseclient
import json
import sys
import threading

def run_test(url, test_query):
    print(f"Testing URL: {url}")
    sse_url = f"{url}/sse"
    
    # Start SSE connection
    response = requests.get(sse_url, stream=True)
    client = sseclient.SSEClient(response)
    
    session_id = None
    
    # Listen for events
    for event in client.events():
        print(f"Received event: {event.event}")
        if event.event == 'endpoint':
            print(f"Endpoint data: {event.data}")
            # fastmcp / SSE usually sends the endpoint relative or absolute
            # We assume we just need the session ID from the transport? 
            # Actually, standard MCP SSE:
            # Server sends 'endpoint' event with the URL to post messages to.
            # It might include sessionId param.
            
            # Let's parse the endpoint
            # It normally looks like "/messages?sessionId=..."
            endpoint = event.data
            post_url = url + endpoint if endpoint.startswith("/") else endpoint
            print(f"POST URL: {post_url}")
            
            # Send initialize
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", # Check version
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                }
            }
            res = requests.post(post_url, json=init_msg)
            print(f"Initialize response: {res.status_code}")
            
            # Send tools/list
            list_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            res = requests.post(post_url, json=list_msg)
            print(f"Tools list response: {res.status_code}")

            # Send tool call (db_query or similar based on exploration)
            # We know 'opengenes_db_query' or similar exists.
            # Let's try 'opengenes_get_schema_info' first to be safe
            tool_msg = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "opengenes_get_schema_info",
                    "arguments": {}
                }
            }
            res = requests.post(post_url, json=tool_msg)
            print(f"Tool call response: {res.status_code}")
            
            # We rely on 'message' event to get results
            pass
            
        elif event.event == 'message':
            print(f"Message: {event.data}")
            data = json.loads(event.data)
            if 'result' in data:
                print("Result received!")
                if data.get('id') == 3:
                     print("Test Passed: Received schema info or tool result.")
                     sys.exit(0)
            if 'error' in data:
                print(f"Error received: {data['error']}")
                # We might want to exit on error too, but let's see
                
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_deployment.py <SERVICE_URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
        
    try:
        run_test(url, "test")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
