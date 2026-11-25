import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { once } from 'node:events';
import { createServer } from 'node:net';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import gateway from './worker.mjs';

const socket = createServer();
socket.listen(0, '127.0.0.1');
await once(socket, 'listening');
const { port } = socket.address();
await new Promise((resolve, reject) => socket.close(error => error ? reject(error) : resolve()));

const clientToken = randomBytes(32).toString('hex');
const originToken = randomBytes(32).toString('hex');
const origin = `http://127.0.0.1:${port}/mcp`;
const bridge = spawn('python3', [fileURLToPath(new URL('./bridge.py', import.meta.url)), '--port', String(port)], {
  env: { ...process.env, COSMOS_ORIGIN_TOKEN: originToken },
  stdio: ['ignore', 'ignore', 'inherit'],
});
const exited = once(bridge, 'exit');
const env = {
  COSMOS_CLIENT_TOKEN: clientToken,
  COSMOS_ORIGIN_TOKEN: originToken,
  COSMOS_VPC: {
    async fetch(request) {
      assert.equal(request.headers.get('Authorization'), 'Bearer ' + originToken);
      assert.equal(new URL(request.url).pathname, '/mcp');
      return fetch(origin, { method: request.method, headers: request.headers,
        body: request.body ? await request.arrayBuffer() : undefined });
    },
  },
};
const endpoint = 'https://cosmos.invalid/mcp';
let session;
let nextId = 1;

async function rpc(method, params, notification = false) {
  const headers = { Authorization: 'Bearer ' + clientToken, 'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream' };
  if (session) headers['Mcp-Session-Id'] = session;
  const body = JSON.stringify({ jsonrpc: '2.0', method, params, ...(notification ? {} : { id: nextId++ }) });
  const response = await gateway.fetch(new Request(endpoint, { method: 'POST', headers, body }), env);
  assert.equal(response.status, notification ? 202 : 200);
  if (notification) return;
  session = response.headers.get('Mcp-Session-Id');
  const { result, error } = await response.json();
  assert.equal(error, undefined);
  assert.ok(!result.isError, result.content?.[0]?.text);
  return result;
}

try {
  let ready = false;
  for (let i = 0; i < 50 && bridge.exitCode === null; i++) {
    try {
      ready = (await fetch(origin)).status === 401;
      if (ready) break;
    } catch {
      await delay(50);
    }
  }
  assert.ok(ready, 'The local bridge did not start.');
  assert.equal((await gateway.fetch(new Request(endpoint), env)).status, 401);
  assert.equal((await gateway.fetch(new Request(endpoint), {})).status, 503);
  const init = await rpc('initialize', { protocolVersion: '2025-11-25', capabilities: {},
    clientInfo: { name: 'cosmos-gateway-test', version: '1' } });
  assert.equal(init.serverInfo.version, '2.5.0');
  assert.ok(session);
  await rpc('notifications/initialized', {}, true);
  assert.equal((await rpc('tools/list', {})).tools.length, 15);
  const result = await rpc('tools/call', { name: 'plan_design', arguments: {
    platform: 'web', stack: 'generic', goal: 'Landing page de documentation pour développeurs',
    audience: 'Développeurs', priority: 'editorial',
  } });
  const plan = result.structuredContent;
  const id = plan.landingResearch.referenceIds[0];
  for (const sectionId of [undefined, 'hero', 'features', 'conversion']) {
    const image = await rpc('tools/call', { name: 'read_pattern', arguments: {
      id, workflowId: plan.workflowId, sectionId,
    } });
    assert.equal(image.content[1].mimeType, 'image/jpeg');
    assert.ok(image.content[1].data.length > 1000);
  }
  const closed = await gateway.fetch(new Request(endpoint, { method: 'DELETE',
    headers: { Authorization: 'Bearer ' + clientToken, 'Mcp-Session-Id': session } }), env);
  assert.equal(closed.status, 204);
  console.log('PASS: protected gateway, MCP 2.5.0, 15 tools, one page and three details in one session.');
} finally {
  bridge.kill();
  await exited;
}
