import {Buffer} from 'node:buffer';
import {timingSafeEqual} from 'node:crypto';

const MAX_REQUEST_BYTES = 2_000_000;

function authenticated(request, token) {
  const actual = Buffer.from(request.headers.get('Authorization') || '');
  const expected = Buffer.from('Bearer ' + token);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

async function readBody(stream) {
  if (!stream) return null;
  const reader = stream.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_REQUEST_BYTES) {
        await reader.cancel();
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  return size ? Buffer.concat(chunks, size) : null;
}

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== '/mcp') return new Response(null, {status:404});
    if (!env.COSMOS_CLIENT_TOKEN || !env.COSMOS_ORIGIN_TOKEN || (!env.COSMOS_VPC && !env.COSMOS_UPSTREAM)) {
      return new Response('MCP gateway is not configured', {status:503});
    }
    if (!authenticated(request, env.COSMOS_CLIENT_TOKEN)) {
      return new Response('Unauthorized', {status:401, headers:{'WWW-Authenticate':'Bearer'}});
    }
    if (!['GET','POST','DELETE'].includes(request.method)) {
      return new Response(null, {status:405,headers:{Allow:'GET, POST, DELETE'}});
    }
    const target = new URL(env.COSMOS_VPC ? 'http://127.0.0.1:8765/mcp' : env.COSMOS_UPSTREAM);
    if (!env.COSMOS_VPC && target.protocol !== 'https:' && !(target.protocol === 'http:' && ['localhost','127.0.0.1'].includes(target.hostname))) {
      return new Response('HTTPS origin required', {status:503});
    }
    const headers = new Headers({Authorization:'Bearer '+env.COSMOS_ORIGIN_TOKEN});
    for (const name of ['Accept','Content-Type','Mcp-Session-Id','MCP-Protocol-Version','Last-Event-ID']) {
      const value=request.headers.get(name);
      if (value) headers.set(name,value);
    }
    try {
      let body;
      if (request.method === 'POST') {
        const declaredLength = request.headers.get('Content-Length');
        if (declaredLength !== null && Number(declaredLength) > MAX_REQUEST_BYTES) {
          return new Response(null, {status:413});
        }
        body = await readBody(request.body);
        if (!body) return new Response(null, {status:413});
      }
      const forwarded = new Request(target,{method:request.method,headers,body,redirect:'manual'});
      const upstream = await (env.COSMOS_VPC ? env.COSMOS_VPC.fetch(forwarded) : fetch(forwarded));
      if (upstream.status >= 300 && upstream.status < 400) return new Response('Unexpected origin redirect',{status:502});
      return upstream;
    } catch {
      return new Response('Cosmos origin unavailable', {status:502});
    }
  }
};
