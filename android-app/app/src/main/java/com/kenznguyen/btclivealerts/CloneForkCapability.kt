package com.kenznguyen.btclivealerts

/**
 * Current-release capability boundary for canonical database clone/fork.
 *
 * This is a pure policy contract. It does not inspect or copy a database, mutate identity,
 * alter schema triggers, provision a child, or grant writer admission.
 */
enum class CloneForkRequest {
    CLONE,
    FORK,
}

enum class CloneForkDecision {
    REJECT_UNSUPPORTED,
}

enum class CloneForkRejectionReason {
    CAPABILITY_DISABLED,
}

data class CloneForkResult(
    val decision: CloneForkDecision,
    val reason: CloneForkRejectionReason,
    val message: String,
    val childInstanceId: String? = null,
    val writerAdmissionGranted: Boolean = false,
)

object CloneForkCapability {
    const val isEnabled: Boolean = false

    fun evaluate(request: CloneForkRequest): CloneForkResult {
        val operation = when (request) {
            CloneForkRequest.CLONE -> "clone"
            CloneForkRequest.FORK -> "fork"
        }
        return CloneForkResult(
            decision = CloneForkDecision.REJECT_UNSUPPORTED,
            reason = CloneForkRejectionReason.CAPABILITY_DISABLED,
            message = "Canonical database $operation is unsupported in this release.",
        )
    }
}
