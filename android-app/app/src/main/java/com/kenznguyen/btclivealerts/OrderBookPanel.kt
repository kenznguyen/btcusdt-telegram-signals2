package com.kenznguyen.btclivealerts

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.isActive
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private data class BookUpdate(val metrics: OrderBookMetrics? = null, val status: String = "")

@Composable
internal fun OrderBookPanel(context: Context, symbol: String) {
    val prefs = remember { context.getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE) }
    var hummingbot by remember { mutableStateOf(prefs.getBoolean("order_book_hummingbot", false)) }
    var url by remember { mutableStateOf(prefs.getString("hummingbot_bridge_url", "").orEmpty()) }
    // Only the dedicated gateway token enters the app, kept in memory for this screen.
    var token by remember { mutableStateOf("") }
    var activeUrl by remember { mutableStateOf("") }
    var activeToken by remember { mutableStateOf("") }
    var configError by remember { mutableStateOf("") }
    var metrics by remember(symbol, hummingbot, activeUrl, activeToken) { mutableStateOf<OrderBookMetrics?>(null) }
    var snapshot by remember(symbol, hummingbot, activeUrl, activeToken) { mutableStateOf<HummingbotSnapshot?>(null) }
    var status by remember(symbol, hummingbot) { mutableStateOf("Đang chờ kết nối…") }
    var clock by remember { mutableLongStateOf(System.currentTimeMillis()) }
    val lifecycle = (context as LifecycleOwner).lifecycle
    LaunchedEffect(Unit) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            while (isActive) { clock = System.currentTimeMillis(); delay(1_000L) }
        }
    }
    LaunchedEffect(symbol, hummingbot, activeUrl, activeToken) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            metrics = null
            snapshot = null
            if (hummingbot) {
                if (activeUrl.isBlank()) { status = "Nhập máy chủ và mã truy cập để kết nối"; return@repeatOnLifecycle }
                while (isActive) {
                    try {
                        val book = HummingbotClient.fetch(activeUrl, activeToken, symbol)
                        snapshot = book
                        metrics = book.metrics
                        status = "Đã nhận snapshot Hummingbot · làm mới mỗi 5 giây"
                    } catch (e: CancellationException) { throw e }
                    catch (_: Exception) {
                        metrics = null
                        snapshot = null
                        status = "Chưa nhận được snapshot hợp lệ. Kiểm tra máy chủ, mã truy cập và cặp giao dịch."
                    }
                    delay(5_000L)
                }
            } else {
                callbackFlow {
                    val engine = OrderBookEngine(
                        onMetrics = { trySend(BookUpdate(metrics = it)) },
                        onStatus = { trySend(BookUpdate(status = it)) }, symbol = symbol
                    )
                    engine.start()
                    awaitClose { engine.close() }
                }.collect { update ->
                    if (update.metrics != null) { metrics = update.metrics; status = "Đã nhận Order Book Binance Futures" }
                    else { metrics = null; status = update.status }
                }
            }
        }
    }
    val panel = Color(0xFF151D29)
    val muted = Color(0xFF91A0B5)
    val green = Color(0xFF20C997)
    val red = Color(0xFFFF647C)
    val ageMs = metrics?.let { clock - it.updatedAtMs }
    val valid = ageMs != null && ageMs in -5_000L..(if (hummingbot) 30_000L else 10_000L)
    Column(Modifier.fillMaxWidth().background(panel, RoundedCornerShape(16.dp)).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("ORDER BOOK · $symbol", fontWeight = FontWeight.Bold, color = Color.White)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(false to "Binance trực tiếp", true to "Hummingbot").forEach { (source, label) ->
                FilterChip(selected = hummingbot == source, onClick = {
                    hummingbot = source
                    prefs.edit().putBoolean("order_book_hummingbot", source).apply()
                }, label = { Text(label) })
            }
        }
        if (hummingbot) {
            OutlinedTextField(value = url, onValueChange = { url = it }, modifier = Modifier.fillMaxWidth(),
                singleLine = true, label = { Text("Máy chủ Hummingbot (HTTPS)") })
            OutlinedTextField(value = token, onValueChange = { token = it }, modifier = Modifier.fillMaxWidth(),
                singleLine = true, visualTransformation = PasswordVisualTransformation(), label = { Text("Mã truy cập") })
            Button(onClick = {
                configError = runCatching {
                    hummingbotEndpoint(url, symbol)
                    require(token.isNotBlank() && token.all { it.code in 33..126 })
                }.exceptionOrNull()?.let { "Nhập URL HTTPS và mã truy cập hợp lệ" }.orEmpty()
                if (configError.isBlank()) {
                    activeUrl = url.trim()
                    activeToken = token
                    prefs.edit().putString("hummingbot_bridge_url", activeUrl).apply()
                }
            }) { Text("Kết nối") }
            if (configError.isNotBlank()) Text(configError, color = red)
            Text("Mã truy cập chỉ dùng cho phiên này.", color = muted, style = MaterialTheme.typography.bodySmall)
        }
        Text(if (metrics != null && !valid) "Dữ liệu đã cũ · đang chờ snapshot mới" else status,
            color = if (valid) green else muted, style = MaterialTheme.typography.bodySmall)
        val book = metrics?.takeIf { valid }
        fun number(value: Double?) = value?.let { "%,.4f".format(Locale.US, it) } ?: "—"
        Text("Bid: ${number(book?.bestBid)} · Ask: ${number(book?.bestAsk)}", color = Color.White)
        Text("Spread: ${number(book?.spreadBps)} bps", color = muted)
        Text("Độ sâu 20 mức · đơn vị ${symbol.removeSuffix("USDT")}", color = muted, style = MaterialTheme.typography.bodySmall)
        Text("Mua: ${number(book?.bidDepth)} · Bán: ${number(book?.askDepth)}", color = Color.White)
        Text("Chênh lệch thanh khoản: ${book?.let { "%.1f%%".format(Locale.US, it.imbalance * 100) } ?: "—"}",
            color = if (book == null) muted else if (book.imbalance >= 0) green else red)
        Text("Có trọng số theo khoảng cách giá: ${book?.let { "%.1f%%".format(Locale.US, it.weightedImbalance * 100) } ?: "—"}", color = muted)
        if (book != null) {
            Text("${if (hummingbot) "Lấy snapshot" else "Cập nhật"} lúc " +
                SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).format(Date(book.updatedAtMs)),
                color = muted, style = MaterialTheme.typography.bodySmall)
        }
        if (hummingbot) {
            Text("Snapshot cho biết thanh khoản đang chào. Thời điểm lấy dữ liệu không xác nhận lần cập nhật cuối của sàn.",
                color = muted, style = MaterialTheme.typography.bodySmall)
            snapshot?.takeIf { valid }?.let { data ->
                Text("5 MỨC GIÁ GẦN NHẤT", color = Color.White, fontWeight = FontWeight.SemiBold)
                data.bids.take(5).zip(data.asks.take(5)).forEach { (bid, ask) ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("${number(bid.price)} · ${number(bid.quantity)}", color = green, style = MaterialTheme.typography.labelSmall)
                        Text("${number(ask.price)} · ${number(ask.quantity)}", color = red, style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
    }
}
