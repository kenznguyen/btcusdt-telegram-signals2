package com.kenznguyen.btclivealerts

import org.junit.Test
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.zip.GZIPInputStream

/** Replay actual StrategyEngine against Freqtrade's checksum-controlled OKX candles. */
class OkxCommonOhlcvParityTest {
    private fun readCandles(path: File): List<Candle> =
        GZIPInputStream(path.inputStream()).bufferedReader().useLines { lines ->
            lines.drop(1).filter { it.isNotBlank() }.map { line ->
                val v = line.split(",")
                require(v.size == 6)
                Candle(v[0].toLong(), v[1].toDouble(), v[2].toDouble(), v[3].toDouble(),
                    v[4].toDouble(), v[5].toDouble(), true)
            }.toList()
        }

    @Test fun exportActualKotlinTrace() {
        val dir = System.getProperty("okx.parity.ohlcv.dir") ?: return
        val output = System.getProperty("okx.parity.android.events")
            ?: error("Missing Kotlin replay trace destination")
        val root = File(dir)
        val m15 = readCandles(File(root, "btc-usdt-okx-futures-15m-utc.csv.gz"))
        val h1 = readCandles(File(root, "btc-usdt-okx-futures-1h-utc.csv.gz"))
        require(m15.size > 100 && h1.size > 100)
        val trace = JSONArray()
        val engine = StrategyEngine()
        val (_, emitted) = engine.processClosedCandles(m15, h1, StrategyState()) { candle, before, after ->
            val changed = before.position !== after.position
            if (!changed) return@processClosedCandles
            val entry = before.position == null && after.position != null
            val exit = before.position != null && after.position == null
            val dca = before.position != null && after.position != null &&
                !before.position.dcaUsed && after.position.dcaUsed
            if (!entry && !exit && !dca) return@processClosedCandles
            val event = after.recentEvents.firstOrNull { it.candleTime == candle.openTime }
                ?: error("Missing Kotlin StrategyEvent")
            val type = when {
                entry -> "ENTRY"
                dca -> "DCA"
                event.kind == "TAKE PROFIT" -> "TP"
                event.kind == "SOFT SL" -> "SOFT_SL"
                event.kind == "EMERGENCY SL" -> "EMERGENCY_SL"
                else -> error("Unsupported Kotlin exit event: ${event.kind}")
            }
            val amount = when {
                entry -> after.position!!.qty
                dca -> after.position!!.qty - before.position!!.qty
                else -> before.position!!.qty
            }
            trace.put(JSONObject().put("timestamp_ms", candle.openTime + 900000L)
                .put("signal_candle_open_ms", candle.openTime)
                .put("type", type).put("side", event.side)
                .put("price", event.price).put("quantity", amount)
                .put("source", "real_kotlin_strategy_engine"))
        }
        require(emitted.isNotEmpty() && trace.length() > 0) { "Kotlin replay produced no actual events" }
        File(output).apply { parentFile?.mkdirs(); writeText(trace.toString(2) + "\n") }
    }
}
