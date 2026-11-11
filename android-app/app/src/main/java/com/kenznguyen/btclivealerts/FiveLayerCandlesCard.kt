package com.kenznguyen.btclivealerts

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import java.math.BigDecimal
import java.math.MathContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.math.abs

/** Only observed closed candles are drawn; missing time slots stay empty. */
@Composable
internal fun CanonicalCandlesContent(window: CandleWindowView) {
    val muted = Color(0xFF91A0B5)
    val latest = window.candles.lastOrNull()
    Text("BTCUSDT · M15 · ${window.returned}/${window.expected} nến đã đóng", color = Color.White)
    if (!window.complete) Text("Kho nến chưa đủ · ${window.expected - window.returned} nến thiếu trong ${window.gaps.size} khoảng.",
        color = Color(0xFFFFC857), style = MaterialTheme.typography.bodySmall)
    if (latest == null) {
        Text("Chưa có nến chuẩn trong cửa sổ này.", color = muted)
        return
    }
    val low = window.candles.minOf { it.low.toBigDecimal() }
    val high = window.candles.maxOf { it.high.toBigDecimal() }
    val range = high - low
    val description = "Biểu đồ BTCUSDT M15, ${window.returned} trên ${window.expected} nến. " +
        "Giá đóng cuối ${latest.close} USDT. ${window.expected - window.returned} nến thiếu."
    Text("Cao ${high.toPlainString()} · Thấp ${low.toPlainString()} USDT", color = muted,
        style = MaterialTheme.typography.bodySmall)
    Canvas(Modifier.fillMaxWidth().height(160.dp).background(Color(0xFF0B1018), RoundedCornerShape(8.dp))
        .semantics { contentDescription = description }) {
        val padding = 8.dp.toPx()
        val plotHeight = size.height - padding * 2
        fun y(price: String): Float = if (range.signum() == 0) size.height / 2 else
            padding + (BigDecimal.ONE - (price.toBigDecimal() - low).divide(range, MathContext.DECIMAL64)).toFloat() * plotHeight
        for (fraction in listOf(0.25f, 0.5f, 0.75f)) {
            val at = padding + fraction * plotHeight
            drawLine(Color(0xFF263448), Offset(0f, at), Offset(size.width, at), 1.dp.toPx())
        }
        val slotWidth = size.width / window.expected
        window.candles.forEach { candle ->
            val slot = (candle.openTimeMs - window.startMs) / 900_000L
            val x = (slot.toFloat() + 0.5f) * slotWidth
            val color = if (candle.close.toBigDecimal() >= candle.open.toBigDecimal()) Color(0xFF20C997) else Color(0xFFFF647C)
            drawLine(color, Offset(x, y(candle.high)), Offset(x, y(candle.low)), 1.5.dp.toPx())
            val openY = y(candle.open)
            val closeY = y(candle.close)
            val width = slotWidth * 0.56f
            drawRect(color, Offset(x - width / 2, minOf(openY, closeY)),
                Size(width, maxOf(1.5.dp.toPx(), abs(openY - closeY))))
        }
    }
    Text("Nến cuối · O ${latest.open} · H ${latest.high}", color = Color.White,
        style = MaterialTheme.typography.bodySmall)
    Text("L ${latest.low} · C ${latest.close} · V ${latest.volume} BTC", color = Color.White,
        style = MaterialTheme.typography.bodySmall)
    val closeTime = SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }.format(Date(latest.closeTimeMs))
    Text("Đóng lúc $closeTime UTC · Khoảng trống trên biểu đồ là nến chưa có.", color = muted,
        style = MaterialTheme.typography.bodySmall)
}
