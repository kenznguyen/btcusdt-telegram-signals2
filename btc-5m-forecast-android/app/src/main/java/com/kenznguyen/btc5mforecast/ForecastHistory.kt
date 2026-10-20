package com.kenznguyen.btc5mforecast

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

class ForecastHistory(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("forecast_history", Context.MODE_PRIVATE)

    @Synchronized fun all(): List<SettledForecast> {
        val arr = runCatching { JSONArray(prefs.getString("items", "[]")) }.getOrDefault(JSONArray())
        return (0 until arr.length()).mapNotNull { i -> runCatching { decode(arr.getJSONObject(i)) }.getOrNull() }
    }

    @Synchronized fun add(item: SettledForecast) {
        val next = (all() + item).takeLast(1000)
        prefs.edit().putString("items", JSONArray().apply { next.forEach { put(encode(it)) } }.toString()).apply()
    }

    @Synchronized fun pending(): List<Forecast> {
        val arr = runCatching { JSONArray(prefs.getString("pending", "[]")) }.getOrDefault(JSONArray())
        return (0 until arr.length()).mapNotNull { i -> runCatching { decodeForecast(arr.getJSONObject(i)) }.getOrNull() }
    }

    @Synchronized fun savePending(items: List<Forecast>) {
        prefs.edit().putString("pending", JSONArray().apply { items.takeLast(100).forEach { put(encodeForecast(it)) } }.toString()).apply()
    }

    private fun encodeForecast(f: Forecast) = JSONObject().apply {
        put("created", f.createdAt); put("target", f.targetAt); put("reference", f.referencePrice)
        put("pUp", f.pUp); put("pDown", f.pDown); put("pTie", f.pTie)
        put("lower", f.lower); put("median", f.median); put("upper", f.upper)
        put("samples", f.sampleCount); put("model", f.model)
    }

    private fun decodeForecast(j: JSONObject) = Forecast(j.getLong("created"), j.getLong("target"),
        j.getDouble("reference"), j.getDouble("pUp"), j.getDouble("pDown"), j.getDouble("pTie"),
        j.getDouble("lower"), j.getDouble("median"), j.getDouble("upper"), j.getInt("samples"),
        j.optString("model", "historical-frequency-baseline-v1"))

    private fun encode(s: SettledForecast) = JSONObject().apply {
        put("created", s.forecast.createdAt); put("target", s.forecast.targetAt)
        put("reference", s.forecast.referencePrice); put("pUp", s.forecast.pUp)
        put("pDown", s.forecast.pDown); put("pTie", s.forecast.pTie)
        put("lower", s.forecast.lower); put("median", s.forecast.median); put("upper", s.forecast.upper)
        put("samples", s.forecast.sampleCount); put("model", s.forecast.model)
        put("actualPrice", s.actualPrice); put("actual", s.actual.name)
        put("settled", s.settledAt); put("brier", s.brier)
    }

    private fun decode(j: JSONObject): SettledForecast {
        val f = Forecast(j.getLong("created"), j.getLong("target"), j.getDouble("reference"),
            j.getDouble("pUp"), j.getDouble("pDown"), j.getDouble("pTie"),
            j.getDouble("lower"), j.getDouble("median"), j.getDouble("upper"),
            j.getInt("samples"), j.optString("model", "historical-frequency-baseline-v1"))
        return SettledForecast(f, j.getDouble("actualPrice"), Direction.valueOf(j.getString("actual")),
            j.getLong("settled"), j.getDouble("brier"))
    }
}
