# Open Genes MCP Server Deployment Walkthrough

I have successfully deployed the **Open Genes MCP Server** to Google Cloud Run.

## Deployment Details

- **Service Name**: `opengenes-mcp`
- **Region**: `us-central1`
- **Project**: `biotech-agent-demo`
- **URL**: `https://opengenes-mcp-520634294170.us-central1.run.app`
- **Mode**: SSE (Server-Sent Events)

## Verification

I verified the deployment by connecting to the `/sse` endpoint using an authenticated request and executing a SQL query.

### 1. Connection Verification

```bash
# Command used for verification
curl -N -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H "Accept: text/event-stream" "https://opengenes-mcp-520634294170.us-central1.run.app/sse" | head -n 2
```

**Output:**
```
event: endpoint
data: /messages/?session_id=...
```

### 2. Functional Verification (Query)

I executed a test query searching for genes related to **carcinogenesis** (broadening the search from "lung cancer" which yielded no specific results in this dataset).

**Query:**
```sql
SELECT HGNC, model_organism, intervention_improves, intervention_deteriorates 
FROM lifespan_change 
WHERE intervention_improves LIKE '%carcinogenesis%' 
   OR intervention_deteriorates LIKE '%carcinogenesis%'
LIMIT 5
```

**Result:**
The server returned **TP53** (a well-known tumor suppressor gene) entries for mice, confirming the database is accessible and queries are working.

```json
[
  {
    "HGNC": "TP53",
    "model_organism": "mouse",
    "intervention_deteriorates": "carcinogenesis,apoptosis,blood"
  },
  ...
]
```

## Setup for MCP Clients

To use this server with an MCP client (like Claude Desktop or an Agent), configure it to use the SSE transport:

```json
{
  "mcpServers": {
    "opengenes-mcp": {
      "url": "https://opengenes-mcp-520634294170.us-central1.run.app/sse",
      "transport": "sse"
    }
  }
}
```

> [!NOTE]
> The service requires authentication (`Authorization: Bearer ...`). If your client does not support adding headers, you may need to use a proxy or update the IAM policy to allow unauthenticated access (if permitted by organization policy).
