package com.kenznguyen.btclivealerts

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val fiveMuted = Color(0xFF91A0B5)
private val fiveGreen = Color(0xFF20C997)
private val fiveAmber = Color(0xFFFFC857)

private data class FiveLayerConnection(val url: String, val readToken: String, val controlToken: String)
private data class FiveLayerReading<T>(val value: T? = null, val fetchedAtMs: Long = 0L) {
    fun fresh(nowMs: Long): T? = value?.takeIf { nowMs - fetchedAtMs in -5_000L..15_000L }
}

private suspend fun <T> readFiveLayer(block: suspend () -> T): FiveLayerReading<T> = try {
    FiveLayerReading(block(), System.currentTimeMillis())
} catch (e: CancellationException) {
    throw e
} catch (_: Exception) {
    FiveLayerReading()
}

private fun fiveTime(value: Long?): String = value?.let {
    SimpleDateFormat("HH:mm:ss dd/MM", Locale.getDefault()).format(Date(it))
} ?: "—"

@Composable
private fun FiveLayerCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(
        Modifier.fillMaxWidth().background(Color(0xFF151D29), RoundedCornerShape(16.dp)).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(title, color = Color.White, fontWeight = FontWeight.Bold)
        content()
    }
}

/** Common API controls are paper-only and never share state with the local chart simulation. */
@Composable
internal fun FiveLayerPanel(context: Context) {
    val prefs = remember { context.getSharedPreferences("strategy_state_v1", Context.MODE_PRIVATE) }
    var url by remember { mutableStateOf(prefs.getString("five_layer_api_url", "").orEmpty()) }
    // Tokens deliberately use remember, never rememberSaveable or SharedPreferences.
    var readToken by remember { mutableStateOf("") }
    var controlToken by remember { mutableStateOf("") }
    var connection by remember { mutableStateOf<FiveLayerConnection?>(null) }
    var configError by remember { mutableStateOf("") }
    var refresh by remember { mutableIntStateOf(0) }
    var clock by remember { mutableLongStateOf(System.currentTimeMillis()) }
    var system by remember(connection, refresh) { mutableStateOf(FiveLayerReading<SystemView>()) }
    var intelligence by remember(connection, refresh) { mutableStateOf(FiveLayerReading<IntelligenceView>()) }
    var decision by remember(connection, refresh) { mutableStateOf(FiveLayerReading<DecisionView>()) }
    var paper by remember(connection, refresh) { mutableStateOf(FiveLayerReading<PaperView>()) }
    var writing by remember { mutableStateOf(false) }
    var mutationJob by remember { mutableStateOf<Job?>(null) }
    var actionMessage by remember { mutableStateOf("") }
    val lifecycle = (context as LifecycleOwner).lifecycle
    val scope = rememberCoroutineScope()

    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) mutationJob?.cancel()
        }
        lifecycle.addObserver(observer)
        onDispose { lifecycle.removeObserver(observer); mutationJob?.cancel() }
    }
    LaunchedEffect(Unit) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            while (isActive) { clock = System.currentTimeMillis(); delay(1_000L) }
        }
    }
    LaunchedEffect(connection, refresh) {
        system = FiveLayerReading(); intelligence = FiveLayerReading()
        decision = FiveLayerReading(); paper = FiveLayerReading()
        val config = connection ?: return@LaunchedEffect
        lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            try {
                while (isActive) {
                    coroutineScope {
                        val nextSystem = async { readFiveLayer { FiveLayerClient.getSystem(config.url, config.readToken) } }
                        val nextIntel = async { readFiveLayer { FiveLayerClient.getIntelligence(config.url, config.readToken) } }
                        val nextDecision = async { readFiveLayer { FiveLayerClient.getDecision(config.url, config.readToken) } }
                        val nextPaper = async { readFiveLayer { FiveLayerClient.getPaper(config.url, config.readToken) } }
                        system = nextSystem.await(); intelligence = nextIntel.await()
                        decision = nextDecision.await(); paper = nextPaper.await()
                    }
                    delay(5_000L)
                }
            } finally {
                system = FiveLayerReading(); intelligence = FiveLayerReading()
                decision = FiveLayerReading(); paper = FiveLayerReading()
            }
        }
    }

    val currentSystem = system.fresh(clock)
    val currentPaper = paper.fresh(clock)
    val config = connection
    val canControl = config != null && config.controlToken.isNotBlank() &&
        currentSystem != null && currentPaper != null && !writing &&
        lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)

    fun submit(command: suspend (FiveLayerConnection) -> String) {
        val target = connection ?: return
        // Recheck wall time at the tap; a UI frame can lag the one-second clock.
        val now = System.currentTimeMillis()
        if (writing || !canControl || !lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED) ||
            system.fresh(now) == null || paper.fresh(now) == null) return
        writing = true
        paper = FiveLayerReading(); decision = FiveLayerReading()
        actionMessage = "Đang gửi yêu cầu paper…"
        mutationJob = scope.launch {
            try {
                actionMessage = command(target)
            } catch (e: CancellationException) {
                actionMessage = "Chưa xác định kết quả. Kiểm tra sổ paper trước khi gửi lại."
                throw e
            } catch (_: Exception) {
                actionMessage = "Chưa xác định kết quả. Đang đọc lại sổ paper; kiểm tra trước khi gửi lại."
            } finally {
                writing = false
                refresh++
            }
        }
    }

    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        FiveLayerCard("KẾT NỐI · BTCUSDT PAPER") {
            Text("Binance USDⓈ-M · Sổ mô phỏng trên máy chủ", color = fiveMuted)
            OutlinedTextField(url, { if (it.length <= 2048) url = it }, Modifier.fillMaxWidth(),
                enabled = connection == null, singleLine = true, label = { Text("API chung (HTTPS)") })
            OutlinedTextField(readToken, { if (it.length <= 4096) readToken = it }, Modifier.fillMaxWidth(),
                enabled = connection == null, singleLine = true, visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                label = { Text("Token đọc") })
            OutlinedTextField(controlToken, { if (it.length <= 4096) controlToken = it }, Modifier.fillMaxWidth(),
                enabled = connection == null, singleLine = true, visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                label = { Text("Token điều khiển paper (tùy chọn)") })
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (connection == null) Button(onClick = {
                    configError = runCatching {
                        fiveLayerEndpoint(url, "system")
                        require(readToken.isNotBlank() && readToken.all { it.code in 33..126 })
                        require(controlToken.isEmpty() ||
                            (controlToken != readToken && controlToken.all { it.code in 33..126 }))
                    }.exceptionOrNull()?.let { "Cần URL HTTPS, token đọc hợp lệ và token điều khiển riêng." }.orEmpty()
                    if (configError.isEmpty()) {
                        connection = FiveLayerConnection(url.trim(), readToken, controlToken)
                        prefs.edit().putString("five_layer_api_url", url.trim()).apply()
                        actionMessage = ""
                    }
                }) { Text("Kết nối") }
                else {
                    OutlinedButton(enabled = !writing, onClick = {
                        connection = null; readToken = ""; controlToken = ""; actionMessage = ""
                    }) { Text("Ngắt kết nối") }
                    TextButton(enabled = !writing, onClick = { refresh++ }) { Text("Làm mới") }
                }
            }
            if (configError.isNotEmpty()) Text(configError, color = fiveAmber)
            Text("Chỉ lưu URL. Token giữ trong phiên màn hình; nhập lại sau khi rời tab.",
                color = fiveMuted, style = MaterialTheme.typography.bodySmall)
            Text(if (connection == null) "Chưa kết nối" else if (currentSystem != null)
                "Đã đọc API lúc ${fiveTime(system.fetchedAtMs)} · làm mới mỗi 5 giây"
                else "Đang chờ API hợp lệ. Kiểm tra HTTPS, token và máy chủ.",
                color = if (currentSystem != null) fiveGreen else fiveMuted,
                style = MaterialTheme.typography.bodySmall)
        }

        FiveLayerCard("TRẠNG THÁI 5 TẦNG") {
            if (currentSystem == null) Text("Chưa có trạng thái hệ thống hợp lệ.", color = fiveMuted)
            currentSystem?.layers?.forEach { layer ->
                Text("${layer.level} · ${layer.name} · ${layer.status}", color = Color.White,
                    style = MaterialTheme.typography.titleSmall)
                Text(layer.detail, color = fiveMuted, style = MaterialTheme.typography.bodySmall)
            }
        }

        FiveLayerCard("DÒNG TIỀN FUTURES · NGUỒN QUAN SÁT") {
            val intel = intelligence.fresh(clock)
            if (intel == null || !intel.available) {
                Text(intel?.reason ?: "Chưa đọc được snapshot dòng tiền.", color = fiveMuted)
            } else {
                val old = clock - requireNotNull(intel.availableAtMs) !in -5_000L..60_000L
                Text("Snapshot nguồn: ${fiveTime(intel.availableAtMs)}${if (old) " · ĐÃ CŨ" else ""}",
                    color = if (old) fiveAmber else fiveMuted, style = MaterialTheme.typography.bodySmall)
                Text("Funding rate: ${intel.fundingRate ?: "—"} · lúc ${fiveTime(intel.fundingAtMs)}", color = Color.White)
                Text("Open Interest: ${intel.openInterestBase ?: "—"} BTC", color = Color.White)
                Text("Thay đổi OI: ${intel.openInterestChangeBase ?: "—"} BTC", color = fiveMuted)
                Text("Taker mua / bán: ${intel.takerBuyQuote ?: "—"} / ${intel.takerSellQuote ?: "—"} USDT", color = Color.White)
                Text("Taker ròng: ${intel.netTakerQuote ?: "—"} USDT", color = Color.White)
                Text("Giao dịch lớn: ${intel.largeTradeQuote ?: "—"} USDT", color = fiveMuted)
                Text("Thanh lý mua / bán ghi nhận: ${intel.observedLiquidationBuyQuote ?: "—"} / ${intel.observedLiquidationSellQuote ?: "—"} USDT", color = fiveMuted)
                intel.coverage.forEach { feed ->
                    Text("${feed.name}: ${feed.status} · ${feed.rows} dòng · sự kiện cuối ${fiveTime(feed.lastEventAtMs)}" +
                        (feed.tradeIdGaps?.let { " · khoảng thiếu ID: $it" } ?: ""),
                        color = fiveMuted, style = MaterialTheme.typography.bodySmall)
                }
                Text("Thanh lý quan sát không đại diện toàn bộ thị trường. Dấu — là dữ liệu chưa có.",
                    color = fiveMuted, style = MaterialTheme.typography.bodySmall)
            }
        }

        FiveLayerCard("QUYẾT ĐỊNH FREQAI") {
            val result = decision.fresh(clock)
            val intent = result?.intent
            val expired = intent != null && clock >= intent.validUntilMs
            val action = if (expired) "WAIT" else result?.action ?: "WAIT"
            Text(action, style = MaterialTheme.typography.headlineMedium,
                color = if (action == "BUY") fiveGreen else fiveAmber, fontWeight = FontWeight.Bold)
            Text(if (expired) "Ý định đã hết hạn · đang chờ đánh giá mới" else
                result?.reason ?: "Chưa có quyết định hợp lệ từ máy chủ.", color = fiveMuted)
            if (intent != null && !expired) {
                Text("Vị thế mục tiêu ${intent.targetPositionBase} BTC · Limit ${intent.limitPrice} USDT", color = Color.White)
                Text("Model ${intent.modelVersion} · Chiến lược ${intent.strategyVersion}", color = fiveMuted)
                Text("Dataset ${intent.datasetVersion}", color = fiveMuted, style = MaterialTheme.typography.bodySmall)
                Text("Hiệu lực đến ${fiveTime(intent.validUntilMs)}", color = fiveMuted)
            }
        }

        FiveLayerCard("SỔ PAPER TRÊN MÁY CHỦ") {
            if (currentPaper == null) Text("Chưa đọc được sổ paper. Điều khiển đang khóa.", color = fiveMuted)
            else {
                Text(if (currentPaper.paused) "ĐÃ TẠM DỪNG" else "PAPER SẴN SÀNG", color = fiveAmber)
                Text("Vị thế: ${currentPaper.positionBase} BTC · Giá vốn ${currentPaper.averageEntryPrice} USDT", color = Color.White)
                Text("PnL đã chốt: ${currentPaper.realizedPnlQuote} USDT", color = Color.White)
                Text("Phí: ${currentPaper.feesQuote} · PnL ròng: ${currentPaper.netRealizedPnlQuote} USDT", color = fiveMuted)
            }
            if (config?.controlToken.isNullOrEmpty())
                Text("Kết nối với token điều khiển riêng để thao tác paper.", color = fiveMuted)
            Button(enabled = canControl && currentPaper?.paused == false, onClick = {
                submit { target ->
                    val result = FiveLayerClient.evaluate(target.url, target.controlToken)
                    "Đánh giá: ${result.decision.action} · ${result.order?.status ?: result.decision.reason}"
                }
            }) { Text("Đánh giá và mô phỏng một lần") }
            OutlinedButton(enabled = canControl, onClick = {
                val pause = currentPaper?.paused?.not() ?: return@OutlinedButton
                submit { target ->
                    val result = FiveLayerClient.setPaused(target.url, target.controlToken, pause)
                    if (result.paused) "Đã tạm dừng paper." else "Đã cho phép đánh giá paper."
                }
            }) { Text(if (currentPaper?.paused == true) "Cho phép paper" else "Tạm dừng paper") }
            if (actionMessage.isNotEmpty()) Text(actionMessage, color = fiveAmber)
            Text("Chỉ thao tác sổ mô phỏng. Khi mất phản hồi, ứng dụng đọc lại sổ và không tự gửi lại yêu cầu.",
                color = fiveMuted, style = MaterialTheme.typography.bodySmall)
            Text("LỆNH PAPER GẦN NHẤT", color = Color.White, fontWeight = FontWeight.SemiBold)
            if (currentPaper?.orders?.isEmpty() == true) Text("Chưa có lệnh paper.", color = fiveMuted)
            currentPaper?.orders?.take(5)?.forEach { order ->
                HorizontalDivider(color = Color(0xFF263448))
                Text("${order.side} · ${order.status} · …${order.orderId.takeLast(12)}", color = Color.White)
                Text("Đã khớp ${order.filledBase}/${order.quantityBase} BTC · Giá ${order.averagePrice ?: "—"}", color = fiveMuted)
                Text(order.reason, color = fiveMuted, style = MaterialTheme.typography.bodySmall)
                Text("Cập nhật ${fiveTime(order.updatedAtMs)}", color = fiveMuted, style = MaterialTheme.typography.bodySmall)
                if (order.status in setOf("OPEN", "PARTIALLY_FILLED"))
                    TextButton(enabled = canControl, onClick = {
                        submit { target ->
                            val result = FiveLayerClient.cancel(target.url, target.controlToken, order.orderId)
                            "Lệnh …${result.orderId.takeLast(12)}: ${result.status}"
                        }
                    }) { Text("Hủy phần còn lại") }
            }
        }
    }
}
