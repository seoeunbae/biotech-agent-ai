
import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { FDAServer } from "./fda-server.js";

const app = express();

const sessions = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  console.log(`New SSE connection from ${req.ip}`);
  const transport = new SSEServerTransport("/messages", res);
  const server = new FDAServer();

  await server.connect(transport);

  sessions.set(transport.sessionId, transport);

  // Clean up on close
  transport.onclose = () => {
    console.log(`Session closed: ${transport.sessionId}`);
    sessions.delete(transport.sessionId);
  };

  // Transport is started by server.connect()
  // await transport.start();
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;
  if (!sessionId) {
    res.status(400).send("Missing sessionId parameter");
    return;
  }

  const transport = sessions.get(sessionId);
  if (!transport) {
    res.status(404).send("Session not found");
    return;
  }

  await transport.handlePostMessage(req, res);
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`FDA MCP Server (SSE) listening on port ${PORT}`);
});
