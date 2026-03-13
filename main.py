from config.settings import settings
from core.bot import build_bot


def main() -> None:
    if not settings.token:
        print("❌ Lỗi: Không tìm thấy DISCORD_TOKEN trong file .env")
        return

    bot = build_bot()
    bot.run(settings.token)


if __name__ == "__main__":
    main()