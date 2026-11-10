// DEV-ONLY static server for dist/ + the real api/me.js handler (Vercel-style req/res shim).
import http from 'node:http'; import { readFileSync, existsSync } from 'node:fs'; import { createRequire } from 'node:module';
const require = createRequire(import.meta.url); const me = require('../api/me.js');
const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.webp':'image/webp', '.png':'image/png', '.jpg':'image/jpeg', '.css':'text/css', '.svg':'image/svg+xml' };
http.createServer(async (req, res) => {
  const p = new URL(req.url, 'http://x').pathname;
  if (p === '/api/me') { res.status = c => { res.statusCode = c; return res; }; res.json = o => { res.setHeader('content-type','application/json'); res.end(JSON.stringify(o)); }; return me(req, res); }
  const f = 'dist' + (p === '/' ? '/index.html' : p); if (!existsSync(f)) { res.statusCode = 404; return res.end('nf'); }
  res.setHeader('content-type', types[f.slice(f.lastIndexOf('.'))] || 'application/octet-stream'); res.end(readFileSync(f));
}).listen(3000, () => console.log('dev on 3000'));
