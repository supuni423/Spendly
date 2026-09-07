import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..", "test-page");
const port = 8765;

const CONTENT_TYPES = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "text/javascript",
  ".json": "application/json",
};

createServer(async (req, res) => {
  const filePath = req.url === "/" ? join(root, "index.html") : join(root, req.url);
  try {
    const body = await readFile(filePath);
    const contentType = CONTENT_TYPES[extname(filePath)] ?? "application/octet-stream";
    res.writeHead(200, { "Content-Type": contentType });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end("Not found");
  }
}).listen(port, () => {
  console.log(`Spendly test page: http://localhost:${port}/`);
});
