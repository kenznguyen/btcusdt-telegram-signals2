import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

let server;
let App;

test('React dashboard renders all five-layer control sections without live trading controls', async () => {
  server = await createServer({
    configFile: false,
    root: new URL('../', import.meta.url).pathname,
    appType: 'custom',
    server: { middlewareMode: true },
  });
  ({ default: App } = await server.ssrLoadModule('/src/App.jsx'));
  const html = renderToStaticMarkup(React.createElement(App));
  for (const section of [
    'Trung tâm điều khiển',
    'Strategy Core và AI Strategy độc lập',
    'Risk Management Center',
    'Equity Curve',
    'Data Quality Monitor',
    'Audit Log',
    'Vị thế &amp; lệnh paper',
  ]) assert.ok(html.includes(section), `Missing dashboard section: ${section}`);
  assert.ok(html.includes('PAPER ONLY'));
  assert.ok(!/LIVE TRADING|Gửi lệnh thật|Đặt lệnh thật/i.test(html));
});

after(async () => { if (server) await server.close(); });
