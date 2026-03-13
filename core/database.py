import sqlite3
from pathlib import Path
from typing import Optional, Tuple


class DatabaseManager:
    def __init__(self, preferred_path: Path, legacy_path: Optional[Path] = None) -> None:
        self.db_path = self._resolve_db_path(preferred_path, legacy_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._setup_db()

    @staticmethod
    def _resolve_db_path(preferred_path: Path, legacy_path: Optional[Path]) -> Path:
        preferred_path.parent.mkdir(parents=True, exist_ok=True)

        if preferred_path.exists():
            return preferred_path

        if legacy_path and legacy_path.exists():
            return legacy_path

        return preferred_path

    def _setup_db(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                lvl INTEGER DEFAULT 1,
                candies INTEGER DEFAULT 100,
                bank INTEGER DEFAULT 0,
                last_daily TEXT,
                mood INTEGER DEFAULT 100,
                title TEXT DEFAULT 'Bé Ngoan'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classrooms (
                class_name TEXT PRIMARY KEY,
                role_id INTEGER,
                teacher_id INTEGER
            )
            """
        )
        cursor.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_name TEXT,
                quantity INTEGER,
                PRIMARY KEY(user_id, item_name)
            )
            """
        )
        cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value INTEGER)")

        self.conn.commit()

    def get_user_profile(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT xp, lvl, candies, bank, last_daily, mood, title FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            return (0, 1, 100, 0, None, 100, "Bé Ngoan")

        return row

    def update_user_profile(
        self,
        user_id: int,
        candy: int = 0,
        bank: int = 0,
        xp: int = 0,
        mood: int = 0,
    ) -> Tuple[bool, int]:
        xp_old, level, candies_old, bank_old, _, mood_old, _ = self.get_user_profile(user_id)

        new_xp = xp_old + xp
        new_level = level

        while new_xp >= new_level * 500:
            new_xp -= new_level * 500
            new_level += 1

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET xp = ?, lvl = ?, candies = ?, bank = ?, mood = ? WHERE user_id = ?",
            (
                new_xp,
                new_level,
                max(0, candies_old + candy),
                max(0, bank_old + bank),
                min(100, max(0, mood_old + mood)),
                user_id,
            ),
        )
        self.conn.commit()

        return new_level > level, new_level

    def close(self) -> None:
        self.conn.close()