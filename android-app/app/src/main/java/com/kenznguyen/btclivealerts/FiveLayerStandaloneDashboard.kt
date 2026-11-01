package com.kenznguyen.btclivealerts

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** Dedicated Paper app shell. It does not mount BTC Chart Pro tabs or its monitor service. */
@Composable
internal fun FiveLayerStandaloneDashboard(context: Context) {
    Surface(modifier = Modifier.fillMaxSize(), color = Color(0xFF0B1018)) {
        Column(
            modifier = Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth().background(Color(0xFF151D29)).padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("HỆ THỐNG 5 TẦNG", color = Color.White,
                        style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text("BTCUSDT · FUTURES INTELLIGENCE · PAPER", color = Color(0xFF91A0B5),
                        style = MaterialTheme.typography.labelSmall)
                }
                Text("PAPER ONLY", color = Color(0xFFFFC857),
                    style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
            }
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item { FiveLayerPanel(context) }
            }
        }
    }
}
