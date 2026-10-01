import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { gzipSync } from 'node:zlib';
import { resolve, extname, sep } from 'node:path';
const root = resolve('out');
const port = Number(process.env.PORT || 3000);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.txt': 'text/plain', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };
createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let file = resolve(root, '.' + decodeURIComponent(url.pathname));
    if (file !== root && !file.startsWith(root + sep)) { res.writeHead(403).end(); return; }
    if ((await stat(file)).isDirectory()) file = resolve(file, 'index.html');
    const bytes = await readFile(file);
    const compress = /gzip/.test(req.headers['accept-encoding'] || '') && /\.(html|css|js|json|txt|svg)$/.test(file);
    const body = compress ? gzipSync(bytes) : bytes;
    res.writeHead(200, { 'Content-Type': types[extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache', 'Vary': 'Accept-Encoding', 'Content-Length': body.length, ...(compress ? { 'Content-Encoding': 'gzip' } : {}) }).end(body);
  } catch { res.writeHead(404, { 'Content-Type': 'text/plain' }).end('Not found'); }
}).listen(port, '127.0.0.1', () => console.log(`Static preview: http://localhost:${port}`));
