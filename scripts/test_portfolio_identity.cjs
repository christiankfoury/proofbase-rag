// Offline fetch regression: exercise the actual TypeScript module, no browser or API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('../apps/web/node_modules/typescript');
const source = fs.readFileSync(path.join(__dirname, '../apps/web/lib/demoAuth.ts'), 'utf8');
const code = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;

async function main() {
  let calls = [];
  let status = 200;
  const exports = {};
  vm.runInNewContext(code, {exports, require: () => ({API_BASE: 'http://example.invalid'}),
    fetch: async (url, options) => {
      calls.push({url, options});
      await new Promise(resolve => setImmediate(resolve));
      return {ok: status === 200, status, headers: {get: () => '30'},
        json: async () => ({users: [], user: {id: options?.headers?.['X-Demo-User-Id']}})};
    }});
  await Promise.all(Array.from({length: 4}, () => exports.fetchDemoUsers()));
  assert.equal(calls.length, 1, 'concurrent user lists share one request');
  calls = [];
  const users = await Promise.all([exports.fetchCurrentDemoUser('employee'),
    exports.fetchCurrentDemoUser('employee'), exports.fetchCurrentDemoUser('admin')]);
  assert.equal(calls.length, 2, 'different selected identities never share responses');
  assert.deepEqual(users.map(user => user.id), ['employee', 'employee', 'admin']);
  await exports.fetchCurrentDemoUser('employee');
  assert.equal(calls.length, 3, 'completed identity is refreshed, not cached');
  status = 429;
  await assert.rejects(exports.fetchDemoUsers(), /Retry in 30 seconds/);
  status = 200;
  await exports.fetchDemoUsers();
  assert.equal(calls.length, 5, 'failed requests do not poison subsequent lookups');
  console.log('Portfolio identity: 5 regression checks passed.');
}
main().catch(error => {console.error(error); process.exitCode = 1;});
