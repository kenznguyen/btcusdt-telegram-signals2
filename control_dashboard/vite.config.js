import { defineConfig } from 'vite';

export default defineConfig({
  base: '/control/',
  server: {
    host: '127.0.0.1',
    proxy: { '/v1': { target: 'http://127.0.0.1:8789', changeOrigin: false } },
  },
});
