# Gene Ontology MCP Server Deployment Walkthrough

I have successfully deployed the Gene Ontology MCP Server to Cloud Run. The server is now accessible via SSE (Server-Sent Events).

## **Deployment Details**

- **Project**: `biotech-agent-demo`
- **Region**: `us-central1`
- **Image**: `us-central1-docker.pkg.dev/biotech-agent-demo/mcp-servers/gene-ontology-mcp-server`
- **Service URL**: `https://gene-ontology-mcp-server-520634294170.us-central1.run.app`

## **Changes Made**

1.  **Transport Refactoring**:
    - Replaced `StdioServerTransport` with `SSEServerTransport` and `Express`.
    - Added `/sse` endpoint for establishing connections.
    - Added `/messages` endpoint for JSON-RPC messages.
    - Added `express` and `cors` dependencies.

2.  **Containerization**:
    - Created a `Dockerfile` using `node:20-alpine`.
    - Configured multi-stage build for optimized image size.
    - Exposed port 8080.

## **Verification**

Verified the deployment using `curl` to connect to the SSE endpoint:

```bash
curl -v -N https://gene-ontology-mcp-server-520634294170.us-central1.run.app/sse
```

**Result**:
```
< HTTP/2 200 
< content-type: text/event-stream
...
event: endpoint
data: /messages?sessionId=ab1cde9b-1f58-4f5a-93d6-1265edb3429b
```


### **Test Query Results**

Executed a search for "lung cancer" using the `search_go_terms` tool.

**Command**:
```bash
npx tsx verify_client.ts
```

**Output**:
```json
{
  "query": "lung cancer",
  "totalResults": 79,
  "returnedResults": 5,
  "results": [
    {
      "id": "GO:0060424",
      "name": "lung field specification",
      "definition": "The process that results in the delineation of a specific region of the foregut into the area in which the lung will develop.",
      "namespace": "cellular_component"
    },
    {
      "id": "GO:0030324",
      "name": "lung development",
      "definition": "The process whose specific outcome is the progression of the lung over time...",
      "namespace": "cellular_component"
    }
  ]
}
```
