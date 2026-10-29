package com.kenznguyen.btclivealerts

import java.io.Reader

/** Strict offline CSV replay; never mutates the live Android state store. */
internal object StrategyCsvReplay {
    fun parse(reader: Reader, stepMs: Long): List<Candle> {
        require(stepMs > 0)
        val lines = reader.buffered().readLines()
        require(lines.isNotEmpty() && lines.first().trim() ==
            "open_time,open,high,low,close,volume,closed") { "Invalid CSV header" }
        val rows = lines.drop(1).filter { it.isNotBlank() }.map { line ->
            val cells = line.split(',')
            require(cells.size == 7 && cells[6].trim() in setOf("1", "true", "True")) { "Unclosed or invalid candle" }
            val time = cells[0].trim().toLong()
            require(time >= 0 && time % stepMs == 0L) { "Unaligned candle" }
            val values = (1..5).map { cells[it].trim().toDouble() }
            require(values.all { it.isFinite() }) { "Nonfinite OHLCV" }
            Candle(time, values[0], values[1], values[2], values[3], values[4], true)
        }
        require(rows.isNotEmpty()) { "Empty candle dataset" }
        require(rows.zipWithNext().all { (a, b) -> b.openTime - a.openTime == stepMs }) {
            "Missing, duplicate or unsorted candle"
        }
        return rows
    }

    fun replay(m15: Reader, h1: Reader): KotlinReplayTrace =
        StrategyTraceExporter.replay(
            StrategyEngine(), parse(m15, 900_000L), parse(h1, 3_600_000L), StrategyState()
        )
}
