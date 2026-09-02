import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..", "test-page");
const port = 8765;

createServer(async (req, res) => {
  const filePath = req.url === "/" ? join(root, "index.html") : join(root, req.url);
  try {
    const body = await readFile(filePath);
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end("Not found");
  }
}).listen(port, () => {
  console.log(`Spendly test page: http://localhost:${port}/`);
});
