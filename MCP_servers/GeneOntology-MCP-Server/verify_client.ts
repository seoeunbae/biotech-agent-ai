import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const EventSourceModule = require("eventsource");
console.log("EventSourceModule:", EventSourceModule);
const EventSource = EventSourceModule.default || EventSourceModule.EventSource || EventSourceModule;
global.EventSource = EventSource;

async function main() {
  const url = "https://gene-ontology-mcp-server-520634294170.us-central1.run.app/sse";
  console.log(`Connecting to ${url}...`);

  const transport = new SSEClientTransport(new URL(url));
  const client = new Client(
    {
      name: "verification-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    }
  );

  try {
    await client.connect(transport);
    console.log("Connected!");

    const tools = await client.listTools();
    console.log("Tools available:", tools.tools.map((t) => t.name));

    console.log("Searching for 'lung cancer'...");
    const result = await client.callTool({
      name: "search_go_terms",
      arguments: {
        query: "lung cancer",
        size: 5
      }
    });

    console.log("Search Result:");
    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error("Error:", error);
  } finally {
    await client.close();
  }
}

main();
