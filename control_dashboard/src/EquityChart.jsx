import React from 'react';
import { displayNumber } from './api.js';
import { date } from './CandleChart.jsx';

export default function EquityChart({ points }) {
  const rows = Array.isArray(points) ? points.filter(point =>
    point && Number.isFinite(Number(point.equity)) && Number.isFinite(Number(point.observedAtMs))).slice(-240) : [];
  if (!rows.length) return <div className="empty chart-empty" role="status"><span>CHƯA CÓ EQUITY HISTORY</span><p>Biểu đồ sẽ xuất hiện sau khi máy chủ ghi nhận Equity hợp lệ.</p></div>;
  const values = rows.map(point => Number(point.equity));
  const min = Math.min(...values), max = Math.max(...values), range = max-min || Math.max(1,Math.abs(max)*0.001);
  const x = index => rows.length === 1 ? 24 : 24 + index*672/(rows.length-1);
  const y = value => 188 - (value-min)/range*154;
  const line = rows.map((point,index) => `${x(index)},${y(Number(point.equity))}`).join(' ');
  return <>
    <svg className="equity-chart" viewBox="0 0 720 220" role="img" aria-label={`Equity Curve gồm ${rows.length} điểm Paper`}>
      <title>Paper Equity Curve · USDT</title>
      {[0,1,2,3].map(index => {
        const value=max-index*range/3;
        return <g key={index}><line x1="18" x2="700" y1={34+index*51} y2={34+index*51} className="gridline"/><text x="700" y={28+index*51} textAnchor="end">{displayNumber(value,2)}</text></g>;
      })}
      <polyline points={line} className="equity-line" fill="none" />
      {rows.filter((_,index)=>index===0||index===rows.length-1||index%Math.max(1,Math.floor(rows.length/12))===0).map((point,index)=>
        <circle key={`${point.id}-${index}`} cx={x(rows.indexOf(point))} cy={y(Number(point.equity))} r="2.6" className="equity-point">
          <title>{date(point.observedAtMs)} UTC · {displayNumber(point.equity,4)} USDT</title>
        </circle>)}
    </svg>
    <div className="chart-time"><span>{date(rows[0].observedAtMs)} UTC</span><span>{date(rows.at(-1).observedAtMs)} UTC</span></div>
  </>;
}
