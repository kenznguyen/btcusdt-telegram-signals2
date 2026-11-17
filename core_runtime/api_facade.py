"""Fail-closed adapter for Core Bundle v1 decisions exposed by the common API."""


class CoreApiFacadeError(RuntimeError):
    """Stable, credential-safe failure at the common Core API boundary."""


def preview_core(*, now_ms, environ=None):
    raise NotImplementedError("CORE_API_FACADE_NOT_IMPLEMENTED")


def evaluate_core(*, now_ms, environ=None):
    raise NotImplementedError("CORE_API_FACADE_NOT_IMPLEMENTED")
