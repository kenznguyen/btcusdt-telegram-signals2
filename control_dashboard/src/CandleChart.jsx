import React from 'react';
import { displayNumber } from './api.js';

export const date = value => Number.isFinite(Number(value)) && value !== null && value !== undefined && value !== ''
  ? new Date(Number(value)).toLocaleString('vi-VN', { timeZone: 'UTC', hour12: false }) : '—';

export default function CandleChart({ result }) {
  const candles = (Array.isArray(result?.candles) ? result.candles : []).filter(c => c && c.isClosed === true &&
    ['open', 'high', 'low', 'close'].every(key => c[key] !== null && Number.isFinite(Number(c[key])) && Number(c[key]) > 0)).slice(-60);
  if (!candles.length) return <div className="empty chart-empty" role="status"><span>CHƯA CÓ NẾN</span><p>Đồng bộ nến M15 đã đóng vào kho dữ liệu để xem biểu đồ.</p></div>;
  const high = Math.max(...candles.map(c => Number(c.high))), low = Math.min(...candles.map(c => Number(c.low)));
  const spread = high - low || high * 0.001, y = value => 18 + (high - value) / spread * 190;
  const step = 620 / candles.length;
  return <>
    <svg className="chart" viewBox="0 0 720 230" role="img" aria-label={`Biểu đồ ${candles.length} nến BTCUSDT M15 đã đóng, giờ UTC`}>
      <title>BTCUSDT M15 · Nến đã đóng</title>
      {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1="12" x2="640" y1={18 + i * 47.5} y2={18 + i * 47.5} className="gridline" /><text x="648" y={22 + i * 47.5}>{displayNumber(high - i * spread / 4, 1)}</text></g>)}
      {candles.map((c, i) => {
        const x = 16 + (i + 0.5) * step, top = Math.min(y(Number(c.open)), y(Number(c.close)));
        return <g key={c.openTimeMs} className={Number(c.close) >= Number(c.open) ? 'candle-up' : 'candle-down'}>
          <title>{date(c.openTimeMs)} UTC · O {c.open} H {c.high} L {c.low} C {c.close}</title>
          <line x1={x} x2={x} y1={y(Number(c.high))} y2={y(Number(c.low))} />
          <rect x={x - Math.max(1, step * .29)} y={top} width={Math.max(2, step * .58)} height={Math.max(1.5, Math.abs(y(Number(c.open)) - y(Number(c.close))))} />
        </g>;
      })}
    </svg>
    <div className="chart-time"><span>{date(candles[0].openTimeMs)} UTC</span><span>{date(candles.at(-1).closeTimeMs)} UTC</span></div>
  </>;
}
