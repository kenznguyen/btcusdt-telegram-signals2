class FileBackedSharedRiskAdmission:
    """Synthetic POSIX multi-process gate using flock + durable atomic replace.

    This is a local-filesystem reference implementation for CI only. It is not
    a distributed lock, network-filesystem guarantee, or production database.
    """

    STATE_NAME = "risk-state.json"
    LOCK_NAME = "risk-state.lock"

    def __init__(self, directory: str, policy: RiskPolicy, portfolio: PortfolioSnapshot) -> None:
        import os
        from pathlib import Path

        self._directory = Path(directory)
        self._policy = policy
        self._portfolio = portfolio
        self._directory.mkdir(parents=True, exist_ok=True)
        self._state_path = self._directory / self.STATE_NAME
        self._lock_path = self._directory / self.LOCK_NAME

    def _locked(self):
        import fcntl
        handle = self._lock_path.open("a+b")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def initialize(self) -> None:
        import fcntl
        with self._locked() as handle:
            if not self._state_path.exists():
                model = SharedRiskAdmission(self._policy, self._portfolio)
                self._write(model.export_state())
            else:
                self._load()
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def admit(self, intent: dict[str, Any], *, fault_at: str | None = None) -> dict[str, Any]:
        import fcntl
        with self._locked() as handle:
            try:
                model = SharedRiskAdmission.restore_state(self._load())
                decision = model.admit(intent)
                self._write(model.export_state(), fault_at=fault_at)
                return decision
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def inspect(self) -> dict[str, Any]:
        import fcntl
        with self._locked() as handle:
            try:
                model = SharedRiskAdmission.restore_state(self._load())
                return {
                    "reserved_exposure": model.reserved_exposure,
                    "open_reservation_count": model.open_reservation_count,
                    "reservation_count": model.reservation_count,
                }
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def recover(self) -> dict[str, Any]:
        """Validate the committed journal, then remove only orphan temp files."""
        import fcntl
        import os
        with self._locked() as handle:
            try:
                # Never clean up or reinitialize until the authoritative state validates.
                model = SharedRiskAdmission.restore_state(self._load())
                removed = []
                for candidate in sorted(self._directory.glob(".risk-state-*.tmp")):
                    if candidate.is_file():
                        candidate.unlink()
                        removed.append(candidate.name)
                if removed:
                    directory_fd = os.open(self._directory, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                return {
                    "reserved_exposure": model.reserved_exposure,
                    "open_reservation_count": model.open_reservation_count,
                    "reservation_count": model.reservation_count,
                    "orphan_temp_files_removed": len(removed),
                }
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, Any]:
        import json
        try:
            raw = self._state_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ValueError("state missing: explicit initialize required")
        try:
            state = json.loads(raw)
            # Validate checksum and schema before returning untrusted disk data.
            SharedRiskAdmission.restore_state(state)
            return state
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as exc:
            raise ValueError("state integrity validation failed") from exc

    def _write(self, state: dict[str, Any], *, fault_at: str | None = None) -> None:
        import json
        import os
        import tempfile

        exit_codes = {
            "after_temp_write": 93,
            "after_file_fsync": 94,
            "before_replace": 91,
            "after_replace": 92,
            "before_directory_fsync": 95,
        }
        if fault_at not in (None, *exit_codes):
            raise ValueError("unsupported synthetic fault point")
        payload = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        fd, temp_name = tempfile.mkstemp(prefix=".risk-state-", suffix=".tmp", dir=self._directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                if fault_at == "after_temp_write":
                    os._exit(exit_codes[fault_at])
                stream.flush()
                os.fsync(stream.fileno())
                if fault_at == "after_file_fsync":
                    os._exit(exit_codes[fault_at])
            if fault_at == "before_replace":
                os._exit(exit_codes[fault_at])
            os.replace(temp_name, self._state_path)
            if fault_at == "after_replace":
                os._exit(exit_codes[fault_at])
            if fault_at == "before_directory_fsync":
                os._exit(exit_codes[fault_at])
            directory_fd = os.open(self._directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
