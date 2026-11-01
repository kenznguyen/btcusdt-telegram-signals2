package com.kenznguyen.btclivealerts

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

private val paperHistoryMuted = Color(0xFF91A0B5)
private val paperHistoryTimeFormat = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss 'UTC'").withZone(ZoneOffset.UTC)
private fun paperHistoryTime(value: Long) = paperHistoryTimeFormat.format(Instant.ofEpochMilli(value))
private fun PaperOrderView.isOpen() = status == "OPEN" || status == "PARTIALLY_FILLED"

/** Pagination only covers the bounded history returned by the current server snapshot. */
@Composable
internal fun PaperOrderHistory(orders: List<PaperOrderView>?, canCancel: Boolean, onCancel: (String) -> Unit) {
    var filter by remember { mutableIntStateOf(0) }
    var page by remember(filter) { mutableIntStateOf(0) }
    var selectedId by remember { mutableStateOf<String?>(null) }
    val clipboard = LocalClipboardManager.current
    var copied by remember(selectedId) { mutableStateOf(false) }
    val filtered = orders?.filter { order ->
        when (filter) {
            1 -> order.isOpen()
            2 -> order.status == "FILLED"
            3 -> order.status == "CANCELED"
            4 -> order.status == "REJECTED"
            else -> true
        }
    }
    val lastPage = filtered?.let { ((it.size - 1) / 10).coerceAtLeast(0) }
    val currentPage = if (lastPage == null) page else page.coerceIn(0, lastPage)
    LaunchedEffect(lastPage) { if (lastPage != null) page = page.coerceIn(0, lastPage) }

    Text("LỊCH SỬ LỆNH PAPER", color = Color.White, fontWeight = FontWeight.SemiBold)
    Text("Tối đa 100 bản ghi gần nhất từ máy chủ.", color = paperHistoryMuted,
        style = MaterialTheme.typography.bodySmall)
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        listOf("Tất cả", "Đang mở", "Đã khớp", "Đã hủy", "Từ chối").forEachIndexed { index, title ->
            FilterChip(selected = filter == index, onClick = { filter = index }, label = { Text(title) })
        }
    }
    if (filtered == null) Text("Chưa có lịch sử mới để hiển thị. Đang chờ đọc lại sổ paper.", color = paperHistoryMuted)
    else {
        val finalPage = requireNotNull(lastPage)
        Text("${filtered.size}/${orders.orEmpty().size} lệnh phù hợp", color = paperHistoryMuted,
            style = MaterialTheme.typography.bodySmall)
        if (filtered.isEmpty()) Text("Không có lệnh trong bộ lọc này.", color = paperHistoryMuted)
        filtered.drop(currentPage * 10).take(10).forEach { order ->
            HorizontalDivider(color = Color(0xFF263448))
            Text("${fiveLayerStatusVi(order.side)} · ${fiveLayerStatusVi(order.status)} · …${order.orderId.takeLast(12)}",
                color = Color.White)
            Text("Đã khớp ${order.filledBase}/${order.quantityBase} BTC · Giá ${order.averagePrice ?: "—"}",
                color = paperHistoryMuted, style = MaterialTheme.typography.bodySmall)
            Text("Cập nhật ${paperHistoryTime(order.updatedAtMs)}", color = paperHistoryMuted,
                style = MaterialTheme.typography.bodySmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = { selectedId = order.orderId }) { Text("Chi tiết") }
                if (order.isOpen()) TextButton(enabled = canCancel, onClick = { onCancel(order.orderId) }) {
                    Text("Hủy phần còn lại")
                }
            }
        }
        if (filtered.isNotEmpty()) Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            TextButton(enabled = currentPage > 0, onClick = { page = currentPage - 1 }) { Text("Trang trước") }
            Text("${currentPage + 1}/${finalPage + 1}", color = paperHistoryMuted,
                modifier = Modifier.padding(vertical = 12.dp))
            TextButton(enabled = currentPage < finalPage, onClick = { page = currentPage + 1 }) { Text("Trang sau") }
        }
    }

    if (selectedId != null) {
        // A retained ID never retains an old actionable snapshot when a read fails.
        val order = orders?.firstOrNull { it.orderId == selectedId }
        AlertDialog(
            onDismissRequest = { selectedId = null },
            title = { Text("Chi tiết lệnh paper") },
            text = {
                Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (order == null) Text(if (orders == null) "Chưa có dữ liệu mới của lệnh. Đang chờ đọc lại sổ paper."
                        else "Lệnh không còn nằm trong lịch sử gần nhất được máy chủ trả về.")
                    else {
                        Text("${fiveLayerStatusVi(order.side)} · ${fiveLayerStatusVi(order.status)}", fontWeight = FontWeight.SemiBold)
                        SelectionContainer {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("ID lệnh: ${order.orderId}")
                                Text("ID ý định: ${order.intentId}")
                            }
                        }
                        TextButton(onClick = { clipboard.setText(AnnotatedString(order.orderId)); copied = true }) {
                            Text(if (copied) "Đã sao chép ID lệnh" else "Sao chép ID lệnh")
                        }
                        Text("Khối lượng: ${order.quantityBase} BTC")
                        Text("Đã khớp: ${order.filledBase} BTC")
                        Text("Chưa khớp: ${order.remainingBase} BTC")
                        Text("Giá khớp trung bình: ${order.averagePrice ?: "—"} USDT")
                        Text("Phí ghi nhận: ${order.feeQuote} USDT")
                        Text(fiveLayerReasonVi(order.reason))
                        Text("Tạo: ${paperHistoryTime(order.createdAtMs)}")
                        Text("Cập nhật: ${paperHistoryTime(order.updatedAtMs)}")
                    }
                }
            },
            confirmButton = { TextButton(onClick = { selectedId = null }) { Text("Đóng") } },
            dismissButton = {
                if (order?.isOpen() == true) TextButton(enabled = canCancel, onClick = { onCancel(order.orderId) }) {
                    Text("Hủy phần còn lại")
                }
            }
        )
    }
}
