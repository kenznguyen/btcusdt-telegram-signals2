package com.kenznguyen.btclivealerts

import org.json.JSONObject

/** Machine-learning research metrics, NOT Freqtrade trading results. */
data class FreqaiResearchReport(
    val engine: String,
    val target: String,
    val samples: Int,
    val mae: Double,
    val baselineMae: Double,
    val directionAccuracy: Double,
    val windows: Int
) {
    val improvesBaseline get() = mae < baselineMae
}

object FreqaiResearchReportParser {
    fun parse(json: String): FreqaiResearchReport {
        val root = JSONObject(json)
        require(root.getString("engine").startsWith("independent LightGBM")) {
            "Không phải báo cáo walk-forward LightGBM đã hỗ trợ"
        }
        require(root.getBoolean("not_profitability_evidence")) {
            "Thiếu nhãn giới hạn nghiên cứu"
        }
        val windows = root.getJSONArray("windows")
        val samples = root.getInt("oos_rows")
        require(windows.length() > 0 && samples > 0) { "Không có mẫu kiểm định ngoài kỳ" }
        val mae = root.getDouble("oos_mae")
        val baseline = root.getDouble("zero_return_mae")
        val accuracy = root.getDouble("oos_direction_accuracy")
        require(mae.isFinite() && mae >= 0 && baseline.isFinite() && baseline >= 0) {
            "Sai số dự báo không hợp lệ"
        }
        require(accuracy.isFinite() && accuracy in 0.0..1.0) {
            "Độ chính xác hướng không hợp lệ"
        }
        return FreqaiResearchReport(root.getString("engine"), root.getString("target"),
            samples, mae, baseline, accuracy, windows.length())
    }
}
