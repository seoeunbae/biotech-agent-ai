
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { EventSource } from "eventsource";

// Proxy EventSource and fetch to inject Authorization header
const originalEventSource = EventSource;
global.EventSource = class extends originalEventSource {
  constructor(url: string | URL, eventSourceInitDict?: any) {
    super(url, {
      ...eventSourceInitDict,
      headers: {
        Authorization: `Bearer ${process.env.IDENTITY_TOKEN}`,
        ...(eventSourceInitDict?.headers || {})
      }
    });
  }
} as any;

const originalFetch = global.fetch;
global.fetch = async (input, init) => {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${process.env.IDENTITY_TOKEN}`);

  return originalFetch(input, {
    ...init,
    headers
  });
};

async function main() {
  const url = "https://openfda-mcp-server-520634294170.us-central1.run.app/sse";
  const identityToken = process.env.IDENTITY_TOKEN;

  if (!identityToken) {
    console.error("IDENTITY_TOKEN environment variable is required");
    process.exit(1);
  }

  const transport = new SSEClientTransport(new URL(url));

  const client = new Client(
    {
      name: "test-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    }
  );

  console.log("Connecting to MCP server...");
  await client.connect(transport);
  console.log("Connected!");

  console.log("Listing tools...");
  const tools = await client.listTools();
  console.log("Tools:", tools.tools.map(t => t.name));

  console.log("Searching for lung cancer treatments...");
  const result = await client.callTool({
    name: "search_drug_labels",
    arguments: {
      indication: "lung cancer",
      limit: 3
    }
  });

  console.log("Result:", JSON.stringify(result, null, 2));

  await client.close();
}

main().catch(console.error);
