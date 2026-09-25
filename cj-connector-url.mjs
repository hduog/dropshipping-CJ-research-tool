// Exchange a CJ API Key for an access token and print the claude.ai connector URL.
// Usage: node cj-connector-url.mjs   (the API key is read from a hidden prompt)
import readline from "node:readline";

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
process.stdout.write("CJ API Key: ");
rl._writeToOutput = () => {}; // hide the key while typing
const [apiKey = ""] = await rl[Symbol.asyncIterator]().next().then(({ value }) => [value?.trim()]);
rl.close();
process.stdout.write("\n");

const res = await fetch("https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ apiKey }),
});
const json = await res.json().catch(() => ({}));

if (!json.result || !json.data?.accessToken) {
  console.error(`Failed (code ${json.code ?? res.status}): ${json.message ?? "unknown error"}`);
  process.exit(1);
}

const { accessToken, accessTokenExpiryDate } = json.data;
console.log(`Access token expires: ${accessTokenExpiryDate}\n`);
console.log("Connector URL (keep it secret):");
console.log(`https://developers.cjdropshipping.com/mcp/${accessToken}`);
