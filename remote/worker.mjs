import {timingSafeEqual} from 'node:crypto';

function authenticated(request, token) {
  const actual = Buffer.from(request.headers.get('Authorization') || '');
  const expected = Buffer.from('Bearer ' + token);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== '/mcp') return new Response(null, {status:404});
    if (!env.COSMOS_CLIENT_TOKEN || !env.COSMOS_ORIGIN_TOKEN || !env.COSMOS_UPSTREAM) {
      return new Response('MCP gateway is not configured', {status:503});
    }
    if (!authenticated(request, env.COSMOS_CLIENT_TOKEN)) {
      return new Response('Unauthorized', {status:401, headers:{'WWW-Authenticate':'Bearer'}});
    }
    if (!['GET','POST','DELETE'].includes(request.method)) {
      return new Response(null, {status:405,headers:{Allow:'GET, POST, DELETE'}});
    }
    const target = new URL(env.COSMOS_UPSTREAM);
    if (target.protocol !== 'https:' && !(target.protocol === 'http:' && ['localhost','127.0.0.1'].includes(target.hostname))) {
      return new Response('HTTPS origin required', {status:503});
    }
    const headers = new Headers({Authorization:'Bearer '+env.COSMOS_ORIGIN_TOKEN});
    for (const name of ['Accept','Content-Type','Mcp-Session-Id','MCP-Protocol-Version','Last-Event-ID']) {
      const value=request.headers.get(name);
      if (value) headers.set(name,value);
    }
    try {
      const upstream=await fetch(target,{method:request.method,headers,body:request.body,redirect:'manual'});
      if (upstream.status >= 300 && upstream.status < 400) return new Response('Unexpected origin redirect',{status:502});
      return upstream;
    } catch {
      return new Response('Cosmos origin unavailable', {status:502});
    }
  }
};
