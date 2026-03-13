import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional, Tuple

from dotenv import load_dotenv


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
DEFAULT_DB_PATH: Final[Path] = DATA_DIR / "nursery_final.db"
LEGACY_DB_PATH: Final[Path] = BASE_DIR / "nursery_final.db"

load_dotenv(BASE_DIR / ".env")


def _parse_prefixes(value: Optional[str]) -> Tuple[str, ...]:
    raw_value = value or "k!,K!"
    prefixes = tuple(prefix.strip() for prefix in raw_value.split(",") if prefix.strip())
    return prefixes or ("k!", "K!")


@dataclass(frozen=True)
class Settings:
    token: Optional[str]
    owner_id: int
    prefixes: Tuple[str, ...]
    extensions: Tuple[str, ...]
    base_dir: Path
    data_dir: Path
    db_path: Path
    legacy_db_path: Path


settings = Settings(
    token=os.getenv("DISCORD_TOKEN"),
    owner_id=int(os.getenv("OWNER_ID", "914831312295165982")),
    prefixes=_parse_prefixes(os.getenv("COMMAND_PREFIXES")),
    extensions=(
        "cogs.admin",
        "cogs.classroom",
        "cogs.economy",
        "cogs.games",
        "cogs.help",
    ),
    base_dir=BASE_DIR,
    data_dir=DATA_DIR,
    db_path=DEFAULT_DB_PATH,
    legacy_db_path=LEGACY_DB_PATH,
)