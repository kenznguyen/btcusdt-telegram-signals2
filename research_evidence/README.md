# Phase14 original Codemagic evidence upload

Upload the **unchanged** downloadable file phase14-frozen-original-evidence.zip here via GitHub web UI. Target path: research_evidence/phase14-frozen-original-evidence.zip.

Expected SHA256: 4758457154f8a23f92e0b48e0122cec0e4d5b92b813c9bed7fe4358c11008c7d.

This 945 KB subset carries exact SHA-verified original model bundle (436,330 bytes), metadata, original Phase13B audit, 180d closed M15 and original last-fold LightGBM prediction matrix. Do not re-generate or re-train a replacement bundle. The manual Codemagic Phase14 job refuses changed bytes before Python, and separately loads the immutable Git seal commit. No GitHub Actions execution.
