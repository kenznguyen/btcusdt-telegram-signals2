function finite(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function deriveRiskSnapshot(paper, markPrice, initialCapital = 100) {
  const capital = finite(initialCapital);
  const position = finite(paper?.positionBase);
  const average = finite(paper?.averageEntryPrice);
  const realized = finite(paper?.realizedPnlQuote);
  const fees = finite(paper?.feesQuote);
  const mark = finite(markPrice);
  const available = capital !== null && capital > 0 && position !== null &&
    average !== null && realized !== null && fees !== null &&
    (position === 0 || mark !== null && mark > 0);
  if (!available) return {
    available: false, initialCapital: capital, equity: null, unrealizedPnl: null,
    realizedPnl: realized, fees, exposure: null, exposurePct: null,
    highWaterMark: null, maxDrawdown: null, dailyLoss: null,
    reason: 'Thiếu vốn gốc, giá đánh dấu hoặc dữ liệu sổ Paper.'
  };
  const unrealizedPnl = position === 0 ? 0 : position * (mark - average);
  const equity = capital + realized - fees + unrealizedPnl;
  const exposure = Math.abs(position * (mark ?? 0));
  return {
    available: true, initialCapital: capital, equity, unrealizedPnl,
    realizedPnl: realized, fees, exposure,
    exposurePct: equity > 0 ? exposure / equity : null,
    highWaterMark: null, maxDrawdown: null, dailyLoss: null,
    reason: 'Equity hiện tại = vốn gốc + PnL đã thực hiện − phí + PnL chưa thực hiện.'
  };
}
