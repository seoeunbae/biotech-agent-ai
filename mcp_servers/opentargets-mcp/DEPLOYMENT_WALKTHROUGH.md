# Deployment Walkthrough: OpenTargets MCP Server

I have successfully deployed the OpenTargets MCP Server to Google Cloud Run.

## Changes
- **Dockerfile**: Updated to support Cloud Run's `$PORT` environment variable and use `sse` transport.
- **Verification Script**: Created `tests/verify_deployment.py` to verify the deployment using `mcp` client and OIDC authentication.

## Verification Results
### Automated Verification
I ran the verification script against the deployed service URL:
`https://opentargets-mcp-520634294170.us-central1.run.app`

The script successfully connected and listed the available tools:
- `get_client`: Return the active OpenTargetsClient...
- `get_disease_by_id`: Retrieve information about a specific disease...
- `get_drug_by_id`: Retrieve information about a specific drug...
- ...and many others.

### Manual Verification Steps
To verify manually, you can run the following command (requires `mcp` package installed):

```bash
uv run python tests/verify_deployment.py https://opentargets-mcp-520634294170.us-central1.run.app $(gcloud auth print-identity-token)
```

## Service Details
- **URL**: `https://opentargets-mcp-520634294170.us-central1.run.app`
- **Region**: `us-central1`
- **Authentication**: Requires OIDC token (Org Policy restricts unauthenticated access).

## Test Query Results
**Query**: "lung cancer" (standard medical term for "폐암")
**Result**: `[EFO_0001071] lung carcinoma`
**Description**: *A carcinoma that arises from epithelial cells of the lung...*
