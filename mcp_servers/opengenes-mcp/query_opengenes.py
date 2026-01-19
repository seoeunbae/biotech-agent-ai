import requests
import json
import sys
import subprocess
import time

def get_token():
    try:
        return subprocess.check_output(["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL).decode().strip()
    except:
        print("Could not get gcloud token")
        return None

def run_query(sql):
    url = "https://opengenes-mcp-520634294170.us-central1.run.app"
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
    
    print(f"Connecting to {url}...")
    
    try:
        response = requests.get(f"{url}/sse", headers=headers, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    post_url = None
    state = "CONNECTING" # CONNECTING, INITIALIZING, LISTING, QUERYING, DONE
    
    for line in response.iter_lines():
        if not line: continue
        line = line.decode('utf-8')
        
        if line.startswith("event: endpoint"):
            continue
            
        if line.startswith("data: "):
            data_str = line[6:].strip()
            
            # Endpoint logic
            if (data_str.startswith("/") or data_str.startswith("http")) and state == "CONNECTING":
                endpoint = data_str
                if endpoint.startswith("/"):
                    post_url = f"{url}{endpoint}"
                else:
                    post_url = endpoint
                
                print(f"Endpoint found: {post_url}")
                
                # Initialize
                print("Sending initialize...")
                init_payload = {
                    "jsonrpc": "2.0", 
                    "method": "initialize", 
                    "id": 1,
                    "params": {
                        "protocolVersion": "2024-11-05", 
                        "capabilities": {}, 
                        "clientInfo": {"name": "test", "version": "1.0"}
                    }
                }
                requests.post(post_url, json=init_payload, headers=headers)
                state = "INITIALIZING"
                continue
            
            # Message logic
            try:
                msg = json.loads(data_str)
                msg_id = msg.get("id")
                
                if state == "INITIALIZING" and msg_id == 1:
                    print("Initialized.")
                    # Send initialized notification (required by protocol sometimes? No, simplified here)
                    # Send notifications/initialized ?
                    requests.post(post_url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers)
                    
                    # List Tools
                    print("Listing tools...")
                    list_payload = {
                        "jsonrpc": "2.0", 
                        "method": "tools/list", 
                        "id": 10,
                        "params": {}
                    }
                    requests.post(post_url, json=list_payload, headers=headers)
                    state = "LISTING"

                elif state == "LISTING" and msg_id == 10:
                    print("Tools received.")
                    if "result" in msg:
                        tools = msg["result"].get("tools", [])
                        print(f"Found {len(tools)} tools.")
                        for t in tools:
                            print(f"- {t['name']}")
                            # Check arguments for opengenes_db_query
                            if t['name'] == 'opengenes_db_query':
                                print("  Args:", json.dumps(t.get('inputSchema'), indent=2))
                    
                    # Send Query
                    print(f"Sending query: {sql}")
                    query_payload = {
                        "jsonrpc": "2.0", 
                        "method": "tools/call", 
                        "id": 2,
                        "params": {
                            "name": "opengenes_db_query",
                            "arguments": {"sql": sql}
                        }
                    }
                    requests.post(post_url, json=query_payload, headers=headers)
                    state = "QUERYING"

                elif state == "QUERYING" and msg_id == 2:
                    if "result" in msg:
                        print("\nQuery Result:")
                        content = msg["result"].get("content", [])
                        for item in content:
                            if item.get("type") == "text":
                                print(item["text"])
                    if "error" in msg:
                        print("\nQuery Error:", json.dumps(msg["error"], indent=2))
                    
                    # Exit after query
                    return

                elif "method" in msg:
                    # Server request/notification
                    print(f"Received server request: {msg['method']}")
                
            except json.JSONDecodeError:
                pass

if __name__ == "__main__":
    sql = """
    SELECT HGNC, model_organism, intervention_improves, intervention_deteriorates 
    FROM lifespan_change 
    WHERE intervention_improves LIKE '%carcinogenesis%' 
       OR intervention_deteriorates LIKE '%carcinogenesis%'
       OR intervention_improves LIKE '%tumor%' 
       OR intervention_deteriorates LIKE '%tumor%'
    LIMIT 5
    """
    
    run_query(sql)
