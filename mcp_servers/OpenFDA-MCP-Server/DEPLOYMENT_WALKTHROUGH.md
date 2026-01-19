# OpenFDA MCP Server Cloud Run Deployment Walkthrough

I have successfully containerized and deployed the OpenFDA MCP Server to Google Cloud Run.

## Changes Made

### 1. Refactoring for Cloud Run
Cloud Run requires an HTTP server, but the original project only supported Stdio transport.
- **Refacted `src/index.ts`**: Extracted `FDAServer` class to `src/fda-server.ts` to make it reusable.
- **Created `src/sse.ts`**: Implemented an Express server with `SSEServerTransport` to handle MCP over SSE (Server-Sent Events).
- **Updated `package.json`**: Added `express` and `cors` dependencies and a `start:sse` script.

### 2. Containerization
- **Created `Dockerfile`**: A multi-stage Dockerfile that builds the TypeScript project and runs the SSE server.
  - Used `node:20-slim` for a small footprint.
  - Added `--ignore-scripts` to `npm ci` to prevent premature build execution during install.

### 3. Deployment
- **Project**: `biotech-agent-demo`
- **Region**: `us-central1`
- **Service Name**: `openfda-mcp-server`
- **Artifact Registry**: Created `mcp-servers` repository.
- **Image**: `us-central1-docker.pkg.dev/biotech-agent-demo/mcp-servers/openfda-mcp-server`
- **Service URL**: `https://openfda-mcp-server-520634294170.us-central1.run.app`

## Verification
I verified the deployment by establishing an SSE connection to the server.
Note: The service is **authenticated-only** due to Organization Policy restrictions. You must include an Identity Token in the `Authorization` header.

```bash
# Verify connection (requires valid identity token)
export IDENTITY_TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $IDENTITY_TOKEN" \
  "https://openfda-mcp-server-520634294170.us-central1.run.app/sse?sessionId=test"
```

### 4. API Key Configuration
The server is configured with a valid FDA API key.
- **Environment Variable**: `FDA_API_KEY` set in Cloud Run.
- **Verification**: `search_drug_labels` tool call confirmed `hasAPIKey: true` and rate limits of 240 req/min (vs 40 req/min without key).

### 5. Test Results
Ran a test query for "lung cancer" (`search_drug_labels`).
- **Result**: Successfully returned drugs like Mekinist, Etoposide, and Lorbrena.
- **Status**: Deployment is fully functional.

## Next Steps
- Configure your MCP client (e.g., Claude Desktop, IDE) to connect to this SSE endpoint.
- Ensure the client sends the Authorization header if accessing from outside GCP.
