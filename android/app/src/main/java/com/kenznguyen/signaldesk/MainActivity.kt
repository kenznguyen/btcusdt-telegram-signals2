package com.kenznguyen.signaldesk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.ShowChart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Bg = Color(0xFF07111F)
private val Panel = Color(0xFF101E30)
private val Line = Color(0xFF20334A)
private val Muted = Color(0xFF91A5BC)
private val Mint = Color(0xFF25D69A)
private val Amber = Color(0xFFFFD27A)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SignalDeskApp() }
    }
}

private enum class Screen(val label: String) {
    DASHBOARD("Dashboard"), SIGNALS("Tín hiệu"), BACKTEST("Backtest")
}

@Composable
private fun SignalDeskApp() {
    var screen by remember { mutableStateOf(Screen.DASHBOARD) }
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Mint, background = Bg, surface = Panel,
            onBackground = Color(0xFFEDF5FF), onSurface = Color(0xFFEDF5FF)
        )
    ) {
        Scaffold(
            containerColor = Bg,
            bottomBar = {
                NavigationBar(containerColor = Color(0xFF081321), contentColor = Muted) {
                    NavigationBarItem(
                        selected = screen == Screen.DASHBOARD,
                        onClick = { screen = Screen.DASHBOARD },
                        icon = { Icon(Icons.Default.Dashboard, contentDescription = null) },
                        label = { Text("Tổng quan") }
                    )
                    NavigationBarItem(
                        selected = screen == Screen.SIGNALS,
                        onClick = { screen = Screen.SIGNALS },
                        icon = { Icon(Icons.Default.ShowChart, contentDescription = null) },
                        label = { Text("Tín hiệu") }
                    )
                    NavigationBarItem(
                        selected = screen == Screen.BACKTEST,
                        onClick = { screen = Screen.BACKTEST },
                        icon = { Icon(Icons.Default.BarChart, contentDescription = null) },
                        label = { Text("Backtest") }
                    )
                }
            }
        ) { padding ->
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 18.dp, bottom = 20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                item {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = RoundedCornerShape(14.dp), color = Color(0xFF0E3D3B)) {
                            Text("₿", color = Mint, fontSize = 25.sp, fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 13.dp, vertical = 7.dp))
                        }
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text("Signal Desk", fontSize = 21.sp, fontWeight = FontWeight.Bold)
                            Text("BTCUSDT · M15 / H1", color = Muted, fontSize = 12.sp)
                        }
                        Surface(color = Color(0xFF332A18), shape = RoundedCornerShape(50)) {
                            Text("CHỈ ĐỌC", color = Amber, fontSize = 11.sp,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp))
                        }
                    }
                }
                item {
                    when (screen) {
                        Screen.DASHBOARD -> DashboardScreen()
                        Screen.SIGNALS -> SignalsScreen()
                        Screen.BACKTEST -> BacktestScreen()
                    }
                }
                item {
                    Text(
                        "Bản thử nghiệm · Chưa kết nối dữ liệu live · Không đặt lệnh giao dịch",
                        color = Muted, fontSize = 11.sp,
                        modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun DashboardScreen() {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Surface(color = Color(0xFF10283B), shape = RoundedCornerShape(22.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF21445A))) {
            Column(Modifier.fillMaxWidth().padding(18.dp)) {
                Text("BTCUSDT · Signal bot", color = Muted, fontSize = 12.sp)
                Text("Chưa có dữ liệu", fontSize = 27.sp, fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(top = 5.dp, bottom = 7.dp))
                Text("Giá, trạng thái scanner và tín hiệu sẽ xuất hiện sau khi cấu hình nguồn dữ liệu.",
                    color = Muted, fontSize = 13.sp)
                Spacer(Modifier.height(12.dp))
                StatusPill("CHƯA KẾT NỐI API", Amber)
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard("Tín hiệu mới", "—", "Chưa tải dữ liệu", Modifier.weight(1f))
            MetricCard("Backtest gần nhất", "—", "Chưa tải báo cáo", Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard("Scanner", "Chưa rõ", "Cần đọc Actions", Modifier.weight(1f))
            MetricCard("Nguồn dữ liệu", "Offline", "Chưa cấu hình", Modifier.weight(1f))
        }
        NoticeCard("Không hiển thị số liệu giả. Bot hiện quét bằng GitHub Actions; cần tạo cơ chế đọc dữ liệu an toàn trước khi dashboard có thể cập nhật.")
    }
}

@Composable
private fun SignalsScreen() {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Tín hiệu gần đây", fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text("ENTRY · DCA · TAKE PROFIT · SOFT SL · EMERGENCY SL", color = Muted, fontSize = 12.sp)
        EmptyCard("Chưa có dữ liệu tín hiệu được kết nối. Màn hình sẽ hiển thị thời gian nến, hướng, giá tham chiếu và loại sự kiện khi có nguồn dữ liệu.")
        NoticeCard("Chỉ đọc tín hiệu mô phỏng. Ứng dụng không đặt lệnh và không yêu cầu API key Binance.")
    }
}

@Composable
private fun BacktestScreen() {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Báo cáo backtest", fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard("Net PnL", "—", "Chưa có báo cáo", Modifier.weight(1f))
            MetricCard("Win Rate", "—", "Chưa có báo cáo", Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard("Profit Factor", "—", "Chưa có báo cáo", Modifier.weight(1f))
            MetricCard("Max Drawdown", "—", "Chưa có báo cáo", Modifier.weight(1f))
        }
        EmptyCard("Chưa tải backtest_last_result.json hoặc artifact tương ứng từ GitHub Actions.")
        NoticeCard("Artifact hiện có thời hạn lưu trữ và cần quyền đọc repository. Không nhúng token GitHub vào APK.")
    }
}

@Composable
private fun MetricCard(title: String, value: String, caption: String, modifier: Modifier = Modifier) {
    Surface(modifier = modifier, color = Panel, shape = RoundedCornerShape(17.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
        Column(Modifier.padding(14.dp)) {
            Text(title, color = Muted, fontSize = 12.sp)
            Text(value, fontSize = 19.sp, fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(top = 7.dp, bottom = 4.dp))
            Text(caption, color = Muted, fontSize = 11.sp)
        }
    }
}

@Composable
private fun StatusPill(text: String, color: Color) {
    Surface(color = color.copy(alpha = .13f), shape = RoundedCornerShape(50)) {
        Text(text, color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp))
    }
}

@Composable
private fun EmptyCard(message: String) {
    Surface(color = Panel, shape = RoundedCornerShape(17.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
        Text(message, color = Muted, fontSize = 13.sp,
            modifier = Modifier.fillMaxWidth().padding(18.dp))
    }
}

@Composable
private fun NoticeCard(message: String) {
    Surface(color = Color(0xFF292517), shape = RoundedCornerShape(14.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF5B4A29))) {
        Text(message, color = Amber, fontSize = 12.sp,
            modifier = Modifier.fillMaxWidth().padding(13.dp))
    }
}
