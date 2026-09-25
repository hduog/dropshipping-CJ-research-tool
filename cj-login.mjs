// One-time CJ login for the CJ MCP server (stdio). The session is saved to ~/.cj-mcp-token
// and reused by Claude Code, so the password never has to be typed into chat.
// Usage: node cj-login.mjs
import { spawn } from "node:child_process";
import readline from "node:readline";

const SERVER = new URL("./api-mcp/dist/mcp-server/index.cjs", import.meta.url);

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const write = rl._writeToOutput.bind(rl);
const lines = rl[Symbol.asyncIterator]();

async function ask(question, { hidden = false } = {}) {
  process.stdout.write(question);
  // Mask typed characters for the password prompt.
  rl._writeToOutput = hidden ? () => {} : write;
  const { value = "" } = await lines.next();
  if (hidden) process.stdout.write("\n");
  return value.trim();
}

const loginName = await ask("CJ email / username: ");
const password = await ask("CJ password: ", { hidden: true });
rl.close();

const server = spawn(process.execPath, [SERVER.pathname.replace(/^\/([A-Za-z]:)/, "$1")], {
  env: { ...process.env, CJ_ENV: "production" },
  stdio: ["pipe", "pipe", "ignore"],
});

const send = (msg) => server.stdin.write(JSON.stringify({ jsonrpc: "2.0", ...msg }) + "\n");
let buffer = "";
server.stdout.on("data", (chunk) => {
  buffer += chunk;
  let i;
  while ((i = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, i);
    buffer = buffer.slice(i + 1);
    if (!line.trim()) continue;
    const msg = JSON.parse(line);
    if (msg.id === 1) {
      send({ method: "notifications/initialized" });
      send({ id: 2, method: "tools/call", params: { name: "verify_credentials", arguments: { loginName, password } } });
    } else if (msg.id === 2) {
      console.log(msg.result?.content?.[0]?.text ?? JSON.stringify(msg));
      process.exitCode = msg.result?.isError ? 1 : 0;
      server.kill();
    }
  }
});

send({
  id: 1,
  method: "initialize",
  params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "cj-login", version: "1" } },
});
