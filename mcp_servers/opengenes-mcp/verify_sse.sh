#!/bin/bash
URL="https://opengenes-mcp-520634294170.us-central1.run.app"
TOKEN=$(gcloud auth print-identity-token)

echo "Testing SSE connection..."
# Connect to SSE and read first few lines
curl -N -s -H "Authorization: Bearer $TOKEN" -H "Accept: text/event-stream" "$URL/sse" | head -n 5

echo "Testing Tools List..."
# We need to know the session ID from SSE to post messages, but strictly speaking 
# fastmcp might accept messages without session ID if stateless?
# No, fastmcp typically requires session.
# However, we can just check if /sse returns 200 OK and headers to confirm it's up.
