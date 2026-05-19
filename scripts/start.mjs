// Standalone Next.js server (.next/standalone/server.js) defaults to binding on
// `localhost`. On Railway (and most container hosts) the proxy can only reach
// the app if it listens on 0.0.0.0. PORT is set by Railway automatically;
// fall back to 3000 for local runs.
process.env.HOSTNAME = process.env.HOSTNAME || '0.0.0.0';
process.env.PORT = process.env.PORT || '3000';
await import('../.next/standalone/server.js');
