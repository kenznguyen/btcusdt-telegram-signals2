const MAX_RESPONSE_BYTES = 2 * 1024 * 1024;

export function apiBase(raw, origin) {
  const url = new URL(raw.trim() || origin);
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((url.protocol !== 'https:' && !(local && url.protocol === 'http:')) ||
      url.username || url.password || url.search || url.hash) {
    throw new Error('Cần URL HTTPS không chứa token; HTTP chỉ dùng cho localhost.');
  }
  return url.toString().replace(/\/$/, '');
}

export function readHeaders(token) {
  if (typeof token !== 'string' || !/^[!-~]+$/.test(token)) throw new Error('Nhập mã truy cập hợp lệ.');
  return { Authorization: `Bearer ${token}`, Accept: 'application/json' };
}

export async function requestJson(base, path, token, options = {}) {
  if (!path.startsWith('/v1/') || path.includes('://')) throw new Error('Đường dẫn API không hợp lệ.');
  const controller = new AbortController();
  const abort = () => controller.abort();
  options.signal?.addEventListener('abort', abort, { once: true });
  if (options.signal?.aborted) abort();
  const timeout = setTimeout(abort, options.timeoutMs ?? 15000);
  try {
    const response = await fetch(`${base}${path}`, {
      method: options.body === undefined ? 'GET' : 'POST',
      headers: { ...readHeaders(token), ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }) },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal, credentials: 'omit', redirect: 'error', cache: 'no-store',
    });
    const reader = response.body?.getReader();
    if (!reader) throw new Error('Máy chủ trả phản hồi rỗng.');
    const chunks = []; let size = 0;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_RESPONSE_BYTES) { await reader.cancel(); throw new Error('Phản hồi API vượt giới hạn.'); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    let result;
    try { result = JSON.parse(new TextDecoder().decode(bytes)); } catch { throw new Error('Phản hồi API không phải JSON hợp lệ.'); }
    if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Cấu trúc phản hồi API không hợp lệ.');
    if (!response.ok) {
      const reason = typeof result.error === 'string' ? result.error.slice(0, 160) : `HTTP ${response.status}`;
      throw new Error(reason);
    }
    return result;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', abort);
  }
}

export function candleWindow(nowMs) {
  const end = Math.floor(nowMs / 900000) * 900000;
  return `/v1/candles?symbol=BTCUSDT&timeframe=15m&startMs=${end - 96 * 900000}&endMs=${end}`;
}

export function displayNumber(value, digits = 2) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return '—';
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : '—';
}
