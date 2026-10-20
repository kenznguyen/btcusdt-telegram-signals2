package com.kenznguyen.btc5mforecast

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val Background = Color(0xFF0B1018)
private val Panel = Color(0xFF151E2B)
private val TextMain = Color(0xFFE6EDF7)
private val Muted = Color(0xFF93A4BA)
private val Green = Color(0xFF31D49B)
private val Red = Color(0xFFFF6878)
private val Amber = Color(0xFFFFC857)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val api = BinanceSpotApi()
        val history = ForecastHistory(this)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme(
                background = Background, surface = Panel, primary = Green,
                onBackground = TextMain, onSurface = TextMain
            )) {
                var candles by remember { mutableStateOf<List<Candle>>(emptyList()) }
                var pending by remember { mutableStateOf(history.pending()) }
                var records by remember { mutableStateOf(history.all().reversed()) }
                var error by remember { mutableStateOf<String?>(null) }
                var updated by remember { mutableLongStateOf(0L) }
                var busy by remember { mutableStateOf(false) }
                var now by remember { mutableLongStateOf(System.currentTimeMillis()) }

                LaunchedEffect(Unit) {
                    while (true) {
                        now = System.currentTimeMillis()
                        if (!busy) {
                            busy = true
                            try {
                                val fresh = withContext(Dispatchers.IO) { api.fetchOneMinute(1000) }
                                candles = fresh
                                val openCandidates = fresh.filter {
                                    val boundary = it.closeTime + 1
                                    boundary % ForecastCore.FIVE_MINUTES == 0L &&
                                        now - boundary in 0L..60_000L
                                }
                                for (boundaryCandle in openCandidates) {
                                    if (pending.none { it.createdAt == boundaryCandle.closeTime + 1 } &&
                                        records.none { it.forecast.createdAt == boundaryCandle.closeTime + 1 }
                                    ) {
                                        val atBoundary = boundaryCandle.closeTime + 1
                                        val historyAtBoundary = fresh.filter { it.closeTime < atBoundary }
                                        val candidate = ForecastCore.forecast(historyAtBoundary, atBoundary)
                                        if (candidate != null) {
                                            pending = pending + candidate
                                            history.savePending(pending)
                                        }
                                    }
                                }

                                val keep = pending.toMutableList()
                                for (forecast in pending) {
                                    val target = fresh.firstOrNull { it.closeTime + 1 == forecast.targetAt }
                                    if (target != null && target.closeTime < System.currentTimeMillis()) {
                                        val result = ForecastCore.settle(forecast, target.close, target.closeTime + 1)
                                        if (result != null) history.add(result)
                                        keep.remove(forecast)
                                    } else if (System.currentTimeMillis() - forecast.targetAt > 90_000L) {
                                        keep.remove(forecast)
                                    }
                                }
                                pending = keep
                                history.savePending(pending)
                                records = history.all().reversed()
                                error = null
                                updated = System.currentTimeMillis()
                            } catch (e: Exception) {
                                error = e.message ?: e.javaClass.simpleName
                            } finally {
                                busy = false
                            }
                        }
                        delay(15_000L)
                    }
                }

                val latest = pending.lastOrNull() ?: records.firstOrNull()?.forecast
                val completed = records.size
                val accuracy = if (records.isEmpty()) null else records.count { it.actual == it.forecast.predicted }.toDouble() / records.size
                val meanBrier = records.take(200).map { it.brier }.takeIf { it.isNotEmpty() }?.average()

                Column(
                    Modifier.fillMaxSize().background(Background).padding(horizontal = 16.dp, vertical = 12.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                        Column {
                            Text("BTC 5m FORECAST", fontSize = 21.sp, fontWeight = FontWeight.Black, color = TextMain)
                            Text("BINANCE SPOT · PAPER ONLY", fontSize = 11.sp, color = Amber, fontWeight = FontWeight.Bold)
                        }
                        Text(if (busy) "SYNC…" else "LIVE", color = if (error == null) Green else Red, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.height(10.dp))
                    Text("Dự đoán hướng BTC/USDT trong 5 phút · Không đặt lệnh", color = Muted, fontSize = 12.sp)
                    Spacer(Modifier.height(12.dp))

                    if (latest != null) {
                        Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp)) {
                                Text("DỰ BÁO GẦN NHẤT", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                Spacer(Modifier.height(6.dp))
                                val best = latest.predicted
                                Text(
                                    when (best) { Direction.UP -> "▲ TĂNG"; Direction.DOWN -> "▼ GIẢM"; Direction.TIE -> "＝ HÒA" },
                                    color = when (best) { Direction.UP -> Green; Direction.DOWN -> Red; Direction.TIE -> Amber },
                                    fontSize = 32.sp, fontWeight = FontWeight.Black
                                )
                                Text("Thời điểm dự báo: ${time(latest.createdAt)}  ·  Mục tiêu: ${time(latest.targetAt)}", color = Muted, fontSize = 11.sp)
                                Spacer(Modifier.height(14.dp))
                                ProbabilityRow("TĂNG", latest.pUp, Green)
                                ProbabilityRow("GIẢM", latest.pDown, Red)
                                ProbabilityRow("HÒA", latest.pTie, Amber)
                                Spacer(Modifier.height(12.dp))
                                HorizontalDivider(color = Color(0xFF2B394B))
                                Spacer(Modifier.height(10.dp))
                                PriceLine("Giá tham chiếu", latest.referencePrice)
                                PriceLine("Trung vị mô hình", latest.median)
                                PriceLine("Khoảng lịch sử P10–P90", latest.lower, latest.upper)
                                Text("Mẫu lịch sử: ${latest.sampleCount} · Mô hình tần suất lịch sử", color = Muted, fontSize = 11.sp)
                            }
                        }
                    } else {
                        Card(colors = CardDefaults.cardColors(containerColor = Panel), modifier = Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp)) {
                                Text("Đang thu thập dữ liệu", fontWeight = FontWeight.Bold)
                                Text("Dự báo xuất hiện ở ranh giới 5 phút sau khi có đủ nến lịch sử liên tục.", color = Muted, fontSize = 12.sp)
                            }
                        }
                    }

                    Spacer(Modifier.height(10.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                        MetricCard("ĐÃ ĐỐI CHIẾU", completed.toString(), Modifier.weight(1f))
                        MetricCard("ĐÚNG HƯỚNG", accuracy?.let { "${"%.1f".format(Locale.US, it * 100)}%" } ?: "—", Modifier.weight(1f))
                        MetricCard("BRIER TB", meanBrier?.let { "%.3f".format(Locale.US, it) } ?: "—", Modifier.weight(1f))
                    }
                    Spacer(Modifier.height(10.dp))
                    if (error != null) Text("Lỗi dữ liệu: $error", color = Red, fontSize = 12.sp)
                    Text("Nguồn: api.binance.com/api/v3/klines · Cập nhật: ${if (updated > 0) time(updated) else "—"}", color = Muted, fontSize = 10.sp)
                    Text("Proxy tham khảo, không phải Chainlink Data Streams. Kết quả quá khứ không đảm bảo dự báo tương lai.", color = Amber, fontSize = 10.sp)
                    Spacer(Modifier.height(8.dp))
                    Text("LỊCH SỬ PAPER", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(6.dp))
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.weight(1f)) {
                        items(records.take(100), key = { it.forecast.createdAt }) { row ->
                            Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(10.dp), modifier = Modifier.fillMaxWidth()) {
                                Row(Modifier.fillMaxWidth().padding(10.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                                    Column(Modifier.weight(1f)) {
                                        Text("${time(row.forecast.createdAt)}  ·  ${directionText(row.forecast.predicted)} → ${directionText(row.actual)}", fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
                                        Text("${price(row.forecast.referencePrice)} → ${price(row.actualPrice)}", color = Muted, fontSize = 11.sp)
                                    }
                                    Text(if (row.forecast.predicted == row.actual) "ĐÚNG" else "SAI", color = if (row.forecast.predicted == row.actual) Green else Red, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                    Text("Nguồn dữ liệu và quy tắc có thể khác thị trường dự đoán của bên thứ ba; đối chiếu này chỉ là paper tracking.", color = Muted, fontSize = 10.sp)
                }
            }
        }
    }
}

@Composable
private fun ProbabilityRow(label: String, probability: Double, color: Color) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Text(label, color = Muted, fontSize = 12.sp, modifier = Modifier.width(60.dp))
        Box(Modifier.weight(1f).height(7.dp).background(Color(0xFF263243), RoundedCornerShape(8.dp))) {
            Box(Modifier.fillMaxHeight().fillMaxWidth(probability.toFloat().coerceIn(0f, 1f)).background(color, RoundedCornerShape(8.dp)))
        }
        Text("${"%.1f".format(Locale.US, probability * 100)}%", color = TextMain, fontWeight = FontWeight.Bold, fontSize = 12.sp, modifier = Modifier.width(55.dp))
    }
}

@Composable
private fun PriceLine(label: String, value: Double) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = Muted, fontSize = 12.sp)
        Text(price(value), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
    }
}
@Composable
private fun PriceLine(label: String, low: Double, high: Double) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = Muted, fontSize = 12.sp)
        Text("${price(low)} – ${price(high)}", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
    }
}
@Composable
private fun MetricCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(12.dp), modifier = modifier) {
        Column(Modifier.padding(10.dp)) {
            Text(label, color = Muted, fontSize = 9.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(4.dp))
            Text(value, color = TextMain, fontSize = 17.sp, fontWeight = FontWeight.Black)
        }
    }
}
private fun price(value: Double) = String.format(Locale.US, "%,.2f", value)
private fun time(value: Long) = SimpleDateFormat("HH:mm:ss", Locale("vi", "VN")).format(Date(value))
private fun directionText(value: Direction) = when (value) { Direction.UP -> "TĂNG"; Direction.DOWN -> "GIẢM"; Direction.TIE -> "HÒA" }
