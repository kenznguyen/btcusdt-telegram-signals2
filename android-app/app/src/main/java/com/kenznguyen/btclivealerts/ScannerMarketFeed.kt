package com.kenznguyen.btclivealerts

import java.io.Closeable

/** Network boundary used by the scanner; tests can supply a feed without contacting Binance. */
internal interface ScannerMarketFeed {
    suspend fun symbols(): List<String>
    suspend fun candles(symbol: String, interval: String): List<Candle>
    fun connect(
        symbols: List<String>,
        onConnected: () -> Unit,
        onDisconnected: (String) -> Unit,
        onCandle: (String, String, Candle) -> Unit,
        onMarkPrice: (String, Double) -> Unit,
        onStatus: (String) -> Unit
    ): Closeable
}

internal class BinanceScannerMarketFeed(private val market: MarketEngine) : ScannerMarketFeed {
    override suspend fun symbols() = market.fetchTopPerpetualSymbols(20)
    override suspend fun candles(symbol: String, interval: String) = market.fetchCandles(interval, 500, symbol)
    override fun connect(
        symbols: List<String>,
        onConnected: () -> Unit,
        onDisconnected: (String) -> Unit,
        onCandle: (String, String, Candle) -> Unit,
        onMarkPrice: (String, Double) -> Unit,
        onStatus: (String) -> Unit
    ): Closeable {
        val socket = market.connectMultiplex(symbols, onCandle = onCandle,
            onMarkPrice = onMarkPrice, onStatus = onStatus,
            onConnected = onConnected, onDisconnected = onDisconnected)
        return Closeable { socket.cancel() }
    }
}

internal typealias ScannerBookFactory =
    (String, (OrderBookMetrics) -> Unit, (String) -> Unit) -> Closeable
