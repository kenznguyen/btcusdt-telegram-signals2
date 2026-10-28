package com.kenznguyen.btclivealerts

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Offline imported report only: this UI does not train a model or place trades. */
@Composable
fun FreqaiResearchPanel(context: Context) {
    val scope = rememberCoroutineScope()
    var report by remember { mutableStateOf<FreqaiResearchReport?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) scope.launch {
            loading = true
            error = null
            try {
                report = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { input ->
                        // Strictly bounded research report: do not open untrusted huge files.
                        val limit = 2 * 1024 * 1024
                        val out = java.io.ByteArrayOutputStream()
                        val buffer = ByteArray(8192)
                        while (true) {
                            val n = input.read(buffer)
                            if (n == -1) break
                            require(out.size() + n <= limit) { "Tệp báo cáo vượt 2 MB" }
                            out.write(buffer, 0, n)
                        }
                        FreqaiResearchReportParser.parse(out.toString("UTF-8"))
                    } ?: throw IllegalArgumentException("Không thể đọc báo cáo FreqAI")
                }
            } catch (ex: Exception) {
                error = ex.message ?: ex.javaClass.simpleName
                report = null
            } finally {
                loading = false
            }
        }
    }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        HorizontalDivider()
        Text("FREQAI · LIGHTGBM RESEARCH", color = Color.White, style = MaterialTheme.typography.titleMedium)
        Text("AI dự báo lợi suất 60 phút tiếp theo; không thay đổi BUY/SELL, không đặt lệnh.",
            color = Color(0xFF91A0B5), style = MaterialTheme.typography.bodySmall)
        OutlinedButton(onClick = { picker.launch(arrayOf("application/json", "*/*")) }, enabled = !loading) {
            Text(if (loading) "ĐANG ĐỌC…" else "MỞ FREQAI-RESEARCH-REPORT.JSON")
        }
        TextButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://codemagic.io/apps")))
        }) { Text("CHẠY FREQAI RESEARCH TRÊN CODEMAGIC") }
        if (error != null) Text("Không thể đọc: $error", color = Color(0xFFFF647C))
        report?.let { r ->
            Text("Mẫu ngoài kỳ: ${r.samples} · ${r.windows} cửa sổ", color = Color.White)
            Text("MAE: ${"%.5f".format(r.mae)} · Mốc lợi suất 0: ${"%.5f".format(r.baselineMae)}", color = Color.White)
            Text("Độ chính xác hướng: ${"%.2f".format(r.directionAccuracy * 100.0)}%", color = Color.White)
            Text(if (r.improvesBaseline) "MAE tốt hơn dự báo lợi suất bằng 0 trên tập kiểm định."
                 else "MAE chưa vượt dự báo lợi suất bằng 0.", color = Color(0xFF91A0B5))
            Text("Đây là báo cáo LightGBM walk-forward độc lập, KHÔNG phải dự báo được xuất trực tiếp từ nội bộ FreqAI; chưa chứng minh lợi nhuận giao dịch.",
                color = Color(0xFF91A0B5), style = MaterialTheme.typography.bodySmall)
        }
    }
}
