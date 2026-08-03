from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_prefix="LEDGER_", extra="ignore"
    )
    data_dir: Path = PROJECT_ROOT / "data" / "runtime"
    review_threshold: float = 0.8
    max_upload_mb: int = 12
    tesseract_cmd: str = ""
    template_dir: Path = PROJECT_ROOT / "ledger_lens" / "templates"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "ledger.sqlite3"
