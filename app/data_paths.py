"""Centralized paths for mutable customer data."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApplicationDataPaths:
    root: Path
    database: Path

    @classmethod
    def from_config(cls, config: dict) -> "ApplicationDataPaths":
        database = Path(config["DATABASE"]).resolve()
        root = Path(config.get("DATA_ROOT", database.parent)).resolve()
        try:
            database.relative_to(root)
        except ValueError as error:
            raise ValueError("DATABASE must be beneath DATA_ROOT.") from error
        paths = cls(root, database)
        paths.ensure_directories()
        return paths

    @property
    def automatic_recovery(self) -> Path:
        return self.root / "automatic-recovery"

    @property
    def staging(self) -> Path:
        return self.root / "staging"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def shell_temporary(self) -> Path:
        return self.root / "shell-temp"

    def ensure_directories(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.automatic_recovery.mkdir(exist_ok=True)
        self.staging.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)
        self.shell_temporary.mkdir(exist_ok=True)

    def safe_child(self, directory: Path, filename: str) -> Path:
        if Path(filename).name != filename or filename in {"", ".", ".."}:
            raise ValueError("Unsafe customer-data filename.")
        target = (directory / filename).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as error:
            raise ValueError("Path escapes the application-data root.") from error
        return target
