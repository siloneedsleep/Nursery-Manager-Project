# Nursery Manager Bot

Discord bot quản lý lớp học, hồ sơ bé, kinh tế và mini-game theo cấu trúc module rõ ràng để dễ bảo trì.

## Khởi chạy

1. Cài dependency bằng `pip install -r requirements.txt`
2. Tạo file `.env` từ `.env.example`
3. Chạy bot bằng `python main.py`

## Cấu trúc

- `main.py`: entry point tối giản, chỉ khởi tạo và chạy bot.
- `config/`: cấu hình môi trường và đường dẫn.
- `core/`: bot lifecycle, database và helper dùng chung.
- `cogs/`: từng nhóm command độc lập.
- `data/`: nơi lưu database cho các môi trường mới.

Chi tiết hơn xem trong `STRUCTURE.md`.