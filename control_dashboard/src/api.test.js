import assert from 'node:assert/strict';
import { test } from 'node:test';
import { apiBase, candleWindow, displayNumber, readHeaders, requestJson } from './api.js';

test('remote tokens require HTTPS and never enter the URL', () => {
  assert.equal(apiBase('', 'https://trade.example'), 'https://trade.example');
  assert.equal(apiBase('http://localhost:8789', 'https://trade.example'), 'http://localhost:8789');
  for (const url of ['http://trade.example', 'https://user:secret@trade.example', 'https://trade.example?token=secret', 'javascript:alert(1)']) {
    assert.throws(() => apiBase(url, 'https://trade.example'));
  }
  assert.deepEqual(readHeaders('read-token'), { Authorization: 'Bearer read-token', Accept: 'application/json' });
  assert.throws(() => readHeaders('secret\nheader'));
});

test('only closed M15 windows are requested and unknown values stay empty', () => {
  const request = new URL(candleWindow(1_800_000_500_000), 'https://trade.example');
  assert.equal(Number(request.searchParams.get('endMs')) % 900000, 0);
  assert.equal(Number(request.searchParams.get('endMs')) - Number(request.searchParams.get('startMs')), 86400000);
  for (const value of [null, undefined, '', true, 'NaN']) assert.equal(displayNumber(value), '—');
  assert.equal(displayNumber('0'), '0.00');
});

test('HTTP requests use memory bearer headers and bounded JSON error handling', async () => {
  const original = global.fetch;
  let observed;
  global.fetch = async (url, options) => { observed = { url, options }; return new Response('{"mode":"PAPER"}'); };
  try {
    assert.equal((await requestJson('https://trade.example', '/v1/paper', 'read-token')).mode, 'PAPER');
    assert.equal(observed.url, 'https://trade.example/v1/paper');
    assert.equal(observed.options.credentials, 'omit');
    assert.equal(observed.options.redirect, 'error');
    assert.equal(observed.options.headers.Authorization, 'Bearer read-token');
    await requestJson('https://trade.example', '/v1/paper/pause', 'control-token', { body: { paused: true } });
    assert.equal(observed.options.method, 'POST');
    assert.deepEqual(JSON.parse(observed.options.body), { paused: true });
    assert.equal(observed.options.headers.Authorization, 'Bearer control-token');
    assert.equal(observed.options.headers['Content-Type'], 'application/json');
    assert.ok(!observed.url.includes('control-token'));
    global.fetch = async () => new Response('{"error":"UNAUTHORIZED"}', { status: 401 });
    await assert.rejects(requestJson('https://trade.example', '/v1/paper', 'bad-token'), /UNAUTHORIZED/);
    global.fetch = async () => new Response('[]');
    await assert.rejects(requestJson('https://trade.example', '/v1/paper', 'read-token'), /Cấu trúc/);
    global.fetch = async () => new Response('not-json');
    await assert.rejects(requestJson('https://trade.example', '/v1/paper', 'read-token'), /JSON/);
    global.fetch = async () => new Response('x'.repeat(2 * 1024 * 1024 + 1));
    await assert.rejects(requestJson('https://trade.example', '/v1/paper', 'read-token'), /giới hạn/);
  } finally { global.fetch = original; }
});


test('risk snapshot marks long and short positions at the latest closed price', async () => {
  const { deriveRiskSnapshot } = await import('./riskMetrics.js');
  const long = deriveRiskSnapshot({ positionBase: '0.01', averageEntryPrice: '100',
    realizedPnlQuote: '2', feesQuote: '0.1' }, '110');
  assert.equal(long.unrealizedPnl, 0.1);
  assert.equal(long.equity, 102);
  assert.equal(long.exposure, 1.1);
  const short = deriveRiskSnapshot({ positionBase: '-0.01', averageEntryPrice: '100',
    realizedPnlQuote: '0', feesQuote: '0' }, '110');
  assert.equal(short.unrealizedPnl, -0.1);
  assert.equal(short.equity, 99.9);
});

test('risk snapshot refuses to invent equity when a required mark is missing', async () => {
  const { deriveRiskSnapshot } = await import('./riskMetrics.js');
  const result = deriveRiskSnapshot({ positionBase: '0.01', averageEntryPrice: '100',
    realizedPnlQuote: '0', feesQuote: '0' }, null);
  assert.equal(result.available, false);
  assert.equal(result.equity, null);
  assert.equal(result.maxDrawdown, null);
  assert.equal(result.dailyLoss, null);
});
