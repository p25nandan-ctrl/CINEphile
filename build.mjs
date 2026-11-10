// Build: bundles src/auth/auth.js (with supabase-js) -> dist/auth.js and copies the page.
// SUPABASE_URL / SUPABASE_ANON_KEY are read from the environment (Vercel env vars or a local .env)
// and inlined into the bundle. Only the PUBLIC anon key is ever used here.
import { build } from 'esbuild';
import { readFileSync, existsSync, mkdirSync, copyFileSync, rmSync, cpSync } from 'node:fs';

if (existsSync('.env')) {
  for (const line of readFileSync('.env', 'utf8').split(/\r?\n/)) {
    const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/.exec(line);
    if (m && !line.trim().startsWith('#') && process.env[m[1]] === undefined) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
}
const url = (process.env.SUPABASE_URL || '').trim();
const key = (process.env.SUPABASE_ANON_KEY || '').trim();
const onVercel = !!process.env.VERCEL;
const problems = [];
if (!/^https:\/\/[a-z0-9-]+\.supabase\.(co|in)\/?$/i.test(url) && !(process.env.ALLOW_CUSTOM_SUPABASE_URL && /^https?:\/\//.test(url))) problems.push('SUPABASE_URL is missing or not like https://<project-ref>.supabase.co');
if (!key) problems.push('SUPABASE_ANON_KEY is missing');
// Refuse a service-role key: its JWT payload has role "service_role" (new-style secret keys start with sb_secret_).
try {
  if (key.startsWith('sb_secret_')) problems.push('SUPABASE_ANON_KEY looks like a SECRET key. Use the anon/publishable key only.');
  const p = key.split('.')[1];
  if (p && JSON.parse(Buffer.from(p, 'base64url').toString()).role === 'service_role') problems.push('SUPABASE_ANON_KEY is a service_role key. Use the anon/public key only; never ship service_role to a browser.');
} catch (_) { /* opaque key format: fine */ }
if (problems.length) {
  console.error('\n[build] Supabase configuration problem:\n - ' + problems.join('\n - ') + '\nSet them in Vercel (Project > Settings > Environment Variables) or in a local .env (see .env.example).\n');
  if (onVercel) process.exit(1);
  console.error('[build] Not on Vercel: continuing with auth DISABLED (the site still builds, Log in will say it is not configured).\n');
}
rmSync('dist', { recursive: true, force: true });
mkdirSync('dist', { recursive: true });
await build({
  entryPoints: ['src/auth/auth.js'], bundle: true, minify: true, format: 'iife', target: 'es2019',
  outfile: 'dist/auth.js', legalComments: 'none',
  define: {
    'process.env.SUPABASE_URL': JSON.stringify(problems.length ? '' : url),
    'process.env.SUPABASE_ANON_KEY': JSON.stringify(problems.length ? '' : key),
  },
});
copyFileSync('src/index.html', 'dist/index.html');
if (existsSync('assets')) cpSync('assets', 'dist/assets', { recursive: true });
console.log('[build] done ->', 'dist/', problems.length ? '(auth disabled)' : '(auth configured)');
