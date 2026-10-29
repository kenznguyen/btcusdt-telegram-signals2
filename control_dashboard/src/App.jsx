import React, { useEffect, useRef, useState } from 'react';
import { apiBase, displayNumber as n, requestJson } from './api.js';
import { useTerminal } from './useTerminal.js';
import CandleChart, { date } from './CandleChart.jsx';

const names = ['Kho dữ liệu', 'Trinh sát futures', 'Chiến lược & FreqAI', 'Hummingbot / paper', 'Trung tâm điều khiển'];
const pct = value => value === null || value === undefined || value === '' || typeof value === 'boolean' || !Number.isFinite(Number(value)) ? '—' : `${n(Number(value) * 100, 4)} %`;
const text = value => typeof value === 'string' ? value : '—';
function Metric({ name, value, unit = '', tone = '' }) {
  return <div className={`metric ${tone}`}><dt>{name}</dt><dd>{value}<small>{unit}</small></dd></div>;
}
function LayerStatus({ system }) {
  const layers = Array.isArray(system?.layers) ? system.layers : [];
  return <section aria-label="Trạng thái năm tầng" className="layers">{names.map((name, level) => {
    const layer = layers.find(item => item?.level === level), status = text(layer?.status);
    const ready = /^(READY|OK|AVAILABLE|ready|ok|available)$/.test(status);
    return <article className="layer" key={name}><div className="layer-heading"><span className="layer-index">0{level}</span><span className={`state ${ready ? 'positive' : ''}`}>{layer ? status : 'CHƯA KẾT NỐI'}</span></div><h2>{name}</h2><p>{layer ? text(layer.detail) : 'Chờ trạng thái từ máy chủ'}</p></article>;
  })}</section>;
}
function Orders({ rows, disabled, cancel }) {
  return <div className="table-wrap"><table><caption className="sr-only">Lịch sử lệnh paper trading</caption><thead><tr><th>Lệnh / giờ UTC</th><th>Hướng</th><th>Trạng thái</th><th>Đã khớp / lượng BTC</th><th>Giá trung bình</th><th>Thao tác</th></tr></thead>
    <tbody>{rows.length ? rows.map(order => <tr key={order.orderId}><td><strong title={text(order.orderId)}>{text(order.orderId).slice(0, 16)}…</strong><small>{date(order.updatedAtMs)}</small></td><td className={order.side === 'BUY' ? 'positive' : 'negative'}>{text(order.side)}</td><td><span className="status-label">{text(order.status)}</span>{order.reason && <small>{text(order.reason)}</small>}</td><td>{n(order.filledBase, 6)} / {n(order.quantityBase, 6)}</td><td>{n(order.averagePrice)}</td><td>{['OPEN', 'PARTIALLY_FILLED'].includes(order.status) ? <button className="button secondary compact" disabled={disabled} onClick={() => cancel(order.orderId)}>Hủy phần còn lại</button> : '—'}</td></tr>) : <tr><td colSpan="6" className="empty-row">Chưa có lệnh được ghi nhận.</td></tr>}</tbody>
  </table></div>;
}

export default function App() {
  const [form, setForm] = useState({ base: '', readToken: '', controlToken: '' }), [connection, setConnection] = useState(null);
  const [formError, setFormError] = useState(''), [pending, setPending] = useState(false), [notice, setNotice] = useState('');
  const command = useRef(null), { data, errors, busy, updatedAt, refresh } = useTerminal(connection);
  const { system, candles, intelligence: intel, decision, paper } = data;
  useEffect(() => () => { command.current?.abort(); }, [connection]);
  const paperMode = system?.mode === 'PAPER' && system?.liveTradingSupported === false;
  const enabled = Boolean(connection?.controlToken && paperMode && paper?.mode === 'PAPER') && !pending;
  const rows = Array.isArray(paper?.orders) ? paper.orders.filter(order => order && typeof order.orderId === 'string') : [];
  const latest = Array.isArray(candles?.candles) ? candles.candles.at(-1) : null;
  const saveConnection = event => {
    event.preventDefault(); setFormError(''); setNotice('');
    try {
      const base = apiBase(form.base, window.location.origin);
      if (!/^[!-~]+$/.test(form.readToken.trim()) || (form.controlToken && !/^[!-~]+$/.test(form.controlToken.trim()))) throw new Error('Nhập mã đọc hợp lệ; mã điều khiển có thể để trống.');
      setConnection({ base, readToken: form.readToken.trim(), controlToken: form.controlToken.trim() });
    } catch (error) { setFormError(error.message); }
  };
  const perform = async (path, body) => {
    if (!enabled) return;
    const activeConnection = connection; command.current?.abort(); command.current = new AbortController();
    const controller = command.current; setPending(true); setNotice('Đang chờ máy chủ xác nhận…');
    try {
      const result = await requestJson(activeConnection.base, path, activeConnection.controlToken, { body, signal: controller.signal });
      if (controller.signal.aborted) return;
      if (path.endsWith('/evaluate') && ['WAIT', 'BUY', 'SELL'].includes(result.decision?.action)) setNotice(`${result.decision.action} · ${text(result.decision.reason)}${result.order ? ` · ${text(result.order.status)}` : ''}`);
      else if (path.endsWith('/pause') && typeof result.paused === 'boolean') setNotice(result.paused ? 'Máy chủ đã tạm dừng ý định paper mới.' : 'Máy chủ đã cho phép đánh giá paper trở lại.');
      else if (path.endsWith('/cancel') && typeof result.status === 'string') setNotice(`Máy chủ xác nhận: ${result.status}`);
      else throw new Error('Máy chủ chưa xác nhận thao tác.');
      refresh();
    } catch (error) {
      if (!controller.signal.aborted) { setNotice(`Chưa xác nhận thao tác: ${error.name === 'AbortError' ? 'hết thời gian chờ; kiểm tra sổ lệnh trước khi thử lại' : error.message}`); refresh(); }
    } finally { if (command.current === controller) setPending(false); }
  };
  return <div className="terminal">
    <a className="skip" href="#overview">Đến nội dung chính</a>
    <header className="topbar"><div className="brand"><span className="brand-mark">CP</span><div><span className="eyebrow">CHART PRO / CONTROL</span><h1>Trung tâm điều khiển</h1></div></div><div className="connection-status"><span className={`dot ${system ? 'online' : ''}`} /><span>{busy ? 'ĐANG ĐỒNG BỘ' : system ? 'ĐÃ NHẬN DỮ LIỆU' : 'CHƯA KẾT NỐI'}</span><strong className="paper-badge">PAPER ONLY</strong></div></header>
    <main id="overview">
      <section className="connection-panel" aria-labelledby="connection-heading"><div><h2 id="connection-heading">Kết nối máy chủ</h2><p>Token chỉ giữ trong bộ nhớ phiên này. Quyền điều khiển dùng mã riêng.</p></div><form onSubmit={saveConnection}><label>URL API<input value={form.base} placeholder="Cùng máy chủ hiện tại" type="url" onChange={e => setForm({ ...form, base: e.target.value })} autoComplete="off" /></label><label>Mã đọc dữ liệu<input value={form.readToken} type="password" onChange={e => setForm({ ...form, readToken: e.target.value })} autoComplete="off" required /></label><label>Mã điều khiển paper<input value={form.controlToken} type="password" onChange={e => setForm({ ...form, controlToken: e.target.value })} autoComplete="off" placeholder="Tùy chọn" /></label><button className="button" type="submit">{connection ? 'Áp dụng kết nối' : 'Kết nối'}</button>{connection && <button className="button secondary" type="button" onClick={() => { setConnection(null); setForm({ base: '', readToken: '', controlToken: '' }); setNotice(''); }}>Ngắt kết nối</button>}</form>{formError && <p role="alert" className="negative">{formError}</p>}</section>
      {errors.length > 0 && <div role="alert" className="error-banner"><strong>Một số nguồn chưa khả dụng.</strong><span>{errors.join(' · ')}</span></div>}
      <LayerStatus system={system} />
      <div className="workspace"><section className="panel market-panel"><div className="section-heading"><div><span className="eyebrow">BINANCE USDⓈ-M · PERPETUAL</span><h2>BTCUSDT <span className="timeframe">M15</span></h2></div><div className="last-price">{n(latest?.close)}<small>USDT · giá đóng gần nhất</small></div></div><CandleChart result={candles} /><div className="panel-note">{candles ? `Kho nến: ${candles.coverage?.returned ?? '—'}/${candles.coverage?.expected ?? '—'} · ${candles.coverage?.complete === true ? 'Đủ cửa sổ' : 'Có khoảng thiếu'}` : 'Đang chờ kho nến chuẩn'}<span>UTC · Chỉ nến đã đóng</span></div></section>
      <section className="panel decision-panel"><div className="section-heading"><h2>Quyết định chiến lược</h2><span className="state">FREQAI</span></div><div className={`decision ${decision?.action === 'BUY' ? 'positive' : decision?.action === 'SELL' ? 'negative' : ''}`}>{['WAIT', 'BUY', 'SELL'].includes(decision?.action) ? decision.action : '—'}</div><p className="reason">{decision ? text(decision.reason) : 'Chưa có quyết định từ máy chủ. Thiếu dự báo hoặc dữ liệu sẽ giữ WAIT.'}</p><dl className="intent-details"><div><dt>Model</dt><dd>{text(decision?.intent?.modelVersion)}</dd></div><div><dt>Mục tiêu BTC</dt><dd>{n(decision?.intent?.targetPositionBase, 6)}</dd></div><div><dt>Giá limit</dt><dd>{n(decision?.intent?.limitPrice)}</dd></div></dl><button className="button wide" disabled={!enabled || paper?.paused} onClick={() => perform('/v1/paper/evaluate', {})}>{pending ? 'Đang xử lý…' : 'Đánh giá & mô phỏng'}</button><p className="fine">Hệ thống mô phỏng theo thanh khoản hiển thị. Không gửi lệnh giao dịch lên sàn.</p></section></div>
      <section className="panel"><div className="section-heading"><div><span className="eyebrow">TẦNG 1</span><h2>Trinh sát futures</h2></div><span className="state">{intel?.windowEndMs && Date.now() - intel.windowEndMs > 60000 ? 'SNAPSHOT LỊCH SỬ' : intel?.quality ?? 'CHƯA CÓ DỮ LIỆU'}</span></div><dl className="metrics"><Metric name="Funding rate" value={pct(intel?.fundingRate)} /><Metric name="Open Interest" value={n(intel?.openInterestBase, 4)} unit="BTC" /><Metric name="Thay đổi OI" value={n(intel?.openInterestChangeBase, 4)} unit="BTC" /><Metric name="Delta mua / bán chủ động" value={n(intel?.netTakerQuote)} unit="USDT" /><Metric name="Giao dịch lớn quan sát" value={n(intel?.largeTradeQuote)} unit="USDT" /><Metric name="Thanh lý bán / mua quan sát" value={`${n(intel?.observedLiquidationSellQuote)} / ${n(intel?.observedLiquidationBuyQuote)}`} unit="USDT" /></dl><div className="coverage-list" aria-label="Bao phủ các luồng dữ liệu">{Object.entries(intel?.coverage && typeof intel.coverage === 'object' ? intel.coverage : {}).map(([name, coverage]) => <span key={name}>{({ trades: 'Giao dịch', funding: 'Funding', open_interest: 'OI', liquidations: 'Thanh lý' })[name] ?? name}: {text(coverage?.status)} · {n(coverage?.rows, 0)} dòng</span>)}</div><div className="panel-note"><span>{intel?.windowEndMs ? `Cửa sổ: ${date(intel.windowStartMs)} → ${date(intel.windowEndMs)} UTC` : intel?.reason ?? 'Chưa có snapshot trinh sát'}<br />{intel?.availableAtMs ? `Nhận snapshot: ${date(intel.availableAtMs)} UTC` : ''}</span><span>Chỉ sự kiện quan sát được; không đại diện toàn bộ dòng tiền.</span></div></section>
      <section className="panel"><div className="section-heading"><div><span className="eyebrow">SỔ MÔ PHỎNG · TẦNG 3</span><h2>Vị thế & lệnh paper</h2></div><button className="button secondary" disabled={!enabled || typeof paper?.paused !== 'boolean'} onClick={() => perform('/v1/paper/pause', { paused: !paper.paused })}>{paper?.paused ? 'Tiếp tục paper' : 'Tạm dừng paper'}</button></div><dl className="metrics ledger-metrics"><Metric name="Vị thế ròng" value={n(paper?.positionBase, 6)} unit="BTC" /><Metric name="PnL đã thực hiện" value={n(paper?.realizedPnlQuote)} unit="USDT" /><Metric name="Phí mô phỏng" value={n(paper?.feesQuote)} unit="USDT" /><Metric name="Trạng thái" value={paper ? paper.paused ? 'ĐÃ TẠM DỪNG' : 'CHO PHÉP PAPER' : '—'} /></dl><p role="status" aria-live="polite" className="command-notice">{notice || (!connection?.controlToken ? 'Nhập mã điều khiển để thao tác. Bạn vẫn có thể theo dõi bằng mã đọc.' : 'Thao tác chỉ thay đổi sổ paper trên máy chủ.')}</p><Orders rows={rows} disabled={!enabled} cancel={orderId => perform('/v1/paper/cancel', { orderId })} /></section>
      <footer><span>{updatedAt ? `Đồng bộ ${date(updatedAt)} UTC` : 'Chưa đồng bộ'} · Tự làm mới 5 giây khi trang hiển thị</span><button className="text-button" disabled={!connection || busy} onClick={refresh}>Đồng bộ ngay</button></footer>
    </main>
  </div>;
}
